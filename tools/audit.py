#!/usr/bin/env python3
"""Silicon Org — repository and graph audit.

Checks whether graph nodes, relation endpoints, harnesses, skills, runtime
tools, and documentation files have clear ownership and activation paths.
"""

from __future__ import annotations

import sys
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).parent.parent
ACTIVATION_TYPES = {"triggers", "may_trigger"}
CONTEXT_ONLY_TYPES = {"supports", "constrains", "complements", "augments"}
HARNESS_PROFILES_PATH = ROOT_DIR / "runtime" / "harness_profiles.yaml"
MODEL_EXAMPLE_PATH = ROOT_DIR / "org" / "models.example.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def repo_path(ref: str | None) -> Path | None:
    if not ref:
        return None
    return ROOT_DIR / ref


def activation_adjacency(nodes: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, set[str]]:
    roles = {node["role"] for node in nodes}
    adj = {role: set() for role in roles}
    for rel in relations:
        rel_type = rel.get("type")
        source = rel.get("from")
        target = rel.get("to")
        if rel_type in ACTIVATION_TYPES:
            adj[source].add(target)
        elif rel_type == "evaluates":
            # Evaluator -> producer in ontology; activation handoff is reversed.
            adj[target].add(source)
    return adj


def reachable_from_entries(nodes: list[dict[str, Any]], adj: dict[str, set[str]]) -> set[str]:
    entries = {node["role"] for node in nodes if node.get("layer") == 1}
    seen = set(entries)
    stack = list(entries)
    while stack:
        role = stack.pop()
        for nxt in adj.get(role, set()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def graph_audit() -> list[str]:
    issues: list[str] = []
    nodes = load_yaml(ROOT_DIR / "ontology" / "nodes.yaml").get("nodes", [])
    relations = load_yaml(ROOT_DIR / "ontology" / "relations.yaml").get("relations", [])
    roles = {node["role"] for node in nodes}

    for rel in relations:
        if rel.get("from") not in roles:
            issues.append(f"relation from unknown role: {rel}")
        if rel.get("to") not in roles:
            issues.append(f"relation to unknown role: {rel}")

    role_counts = Counter(node["role"] for node in nodes)
    for role, count in role_counts.items():
        if count > 1:
            issues.append(f"duplicate node role: {role} appears {count} times")

    adj = activation_adjacency(nodes, relations)
    reachable = reachable_from_entries(nodes, adj)
    meta_roles = {node["role"] for node in nodes if node.get("meta")}
    for role in sorted(roles - reachable - meta_roles):
        issues.append(f"orphan node: {role} is not reachable through activation-capable edges")

    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    any_outgoing = defaultdict(int)
    for source, targets in adj.items():
        outgoing[source] += len(targets)
        for target in targets:
            incoming[target] += 1
    for rel in relations:
        any_outgoing[rel.get("from")] += 1

    entries = {node["role"] for node in nodes if node.get("layer") == 1}
    for role in sorted(roles - entries - meta_roles):
        if incoming[role] == 0:
            issues.append(f"dead-head node: {role} has no activation-capable incoming edge")

    terminal_without_outgoing = {"handoff", "graph-topologist", "hrbp", "skill-scout", "customer-success"}
    for role in sorted(roles - terminal_without_outgoing):
        if any_outgoing[role] == 0:
            issues.append(f"dead-road node: {role} has no outgoing relation")

    for node in nodes:
        role = node["role"]
        harness = repo_path(node.get("harness_ref"))
        if not harness or not harness.exists():
            issues.append(f"missing harness for {role}: {node.get('harness_ref')}")
        skill_ref = node.get("skill_ref")
        if skill_ref:
            skill = repo_path(f"{skill_ref}/SKILL.md")
            if not skill or not skill.exists():
                issues.append(f"missing skill for {role}: {skill_ref}/SKILL.md")

    active_relation_types = {rel.get("type") for rel in relations}
    defined_relation_types = set(
        load_yaml(ROOT_DIR / "ontology" / "relation_types.yaml")
        .get("relation_types", {})
        .keys()
    )
    for rel_type in sorted(active_relation_types - defined_relation_types):
        issues.append(f"relation type used but not defined: {rel_type}")
    for rel_type in sorted(defined_relation_types - active_relation_types):
        issues.append(f"relation type defined but unused: {rel_type}")

    for rel in relations:
        if rel.get("type") in CONTEXT_ONLY_TYPES and rel.get("weights") is None:
            issues.append(f"context relation missing weights: {rel}")
        if rel.get("type") in ACTIVATION_TYPES | {"evaluates"}:
            weights = rel.get("weights") or {}
            metric = weights.get("probability") or weights.get("strictness") or {}
            value = metric.get("value") if isinstance(metric, dict) else None
            samples = metric.get("samples") if isinstance(metric, dict) else None
            confidence = metric.get("confidence") if isinstance(metric, dict) else None
            executable_gate = any(
                key in weights
                for key in (
                    "activation_task_types",
                    "activation_skip_on_task_types",
                    "activation_verdicts",
                    "activation_unconditional",
                    "blocking_skip_on_task_types",
                )
            )
            if (
                isinstance(value, (int, float))
                and value >= 0.80
                and samples in (None, 0)
                and (not isinstance(confidence, (int, float)) or confidence <= 0.25)
                and not executable_gate
            ):
                issues.append(
                    "high-weight low-sample activation relation lacks executable gate: "
                    f"{rel.get('from')} -> {rel.get('to')} ({rel.get('type')})"
                )

    return issues


def file_audit() -> list[str]:
    issues: list[str] = []
    expected_docs = [
        "README.md",
        "pyproject.toml",
        "docs/SPEC.md",
        "docs/HARNESS_ENGINEERING.md",
        "docs/LANGGRAPH_NATIVE_RUNTIME.md",
        "org/RUNTIME.md",
        "org/ENCODER.md",
        "org/DECODER.md",
        "org/HARNESS.md",
        "org/CONTEXT_BLOCK.md",
        "ontology/artifact_ledger.yaml",
        "ontology/task_graph_state.yaml",
        "ontology/trace_schema.yaml",
    ]
    for ref in expected_docs:
        path = ROOT_DIR / ref
        if not path.exists():
            issues.append(f"expected documentation missing: {ref}")
        elif not path.read_text(errors="ignore").strip():
            issues.append(f"empty documentation file: {ref}")

    ignored_fragments = {".git/", ".ruff_cache/", ".DS_Store", "__pycache__", "node_modules/"}
    for path in ROOT_DIR.rglob("*"):
        rel = str(path.relative_to(ROOT_DIR))
        if any(fragment in rel for fragment in ignored_fragments):
            continue
        if path.is_file() and path.stat().st_size == 0:
            issues.append(f"empty file: {rel}")

    forbidden_snippets = {
        "." + "agents/traces/": "trace path must be traces/<task_id>/",
        "Only " + "four concepts": "current concept model has five concepts",
        "Phase 4 of the Runtime " + "protocol": "Evaluator is optional/manual, not automatic Phase 4",
        "Fires AFTER the Decoder " + "completes": "Evaluator is optional/manual, not automatic Phase 4",
        "Runtime immediately fires the " + "Evaluator": "Evaluator is optional/manual",
        "Target: " + "150 roles": "registry must describe current expansion protocol, not roadmap targets",
        "tools/runners/" + "openai_agents.py": "do not reference nonexistent runner modules",
        "tools/runners/" + "langgraph_node.py": "do not reference nonexistent runner modules",
    }
    text_files = [
        path for path in ROOT_DIR.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and not str(path.relative_to(ROOT_DIR)).startswith("traces/task-")
        and path.suffix in {".md", ".py", ".yaml", ".yml", ".txt", ".sh"}
    ]
    for path in text_files:
        text = path.read_text(errors="ignore")
        rel = path.relative_to(ROOT_DIR)
        for snippet, reason in forbidden_snippets.items():
            if snippet in text:
                issues.append(f"stale wording in {rel}: {reason}")

    for harness in (ROOT_DIR / "org" / "registry").glob("*.md"):
        text = harness.read_text(errors="ignore")
        rel = harness.relative_to(ROOT_DIR)
        if "## Context Compression Report" not in text:
            issues.append(f"harness missing Context Compression Report section: {rel}")
        if "confidence_differential" not in text:
            issues.append(f"harness missing confidence_differential field: {rel}")

    return issues


def runtime_contract_audit() -> list[str]:
    issues: list[str] = []
    nodes = load_yaml(ROOT_DIR / "ontology" / "nodes.yaml").get("nodes", [])
    profiles = load_yaml(HARNESS_PROFILES_PATH).get("profiles", {})
    model_profiles = load_yaml(MODEL_EXAMPLE_PATH).get("profiles", {})

    if not HARNESS_PROFILES_PATH.exists():
        issues.append("missing runtime harness profile registry: runtime/harness_profiles.yaml")
        return issues
    if not (ROOT_DIR / "runtime" / "langgraph_native.py").exists():
        issues.append("missing native runtime contract: runtime/langgraph_native.py")

    node_roles = {node["role"] for node in nodes}
    profile_roles = set(profiles)
    for role in sorted(node_roles - profile_roles):
        issues.append(f"runtime harness missing ontology node: {role}")
    for role in sorted(profile_roles - node_roles):
        issues.append(f"runtime harness has no ontology node: {role}")

    missing_model_profiles = sorted(
        {
            raw.get("model_profile")
            for raw in profiles.values()
            if isinstance(raw, dict) and raw.get("model_profile")
        }
        - set(model_profiles)
    )
    for profile in missing_model_profiles:
        issues.append(
            "models.example missing harness model_profile override slot: "
            f"{profile}"
        )

    return issues


# Substance contract for skill files. A skill is more than an existing file:
# it must carry enough guidance that a subagent invoked with it produces
# useful work. See ai-code-review/patterns/K12-shape-vs-substance.md.
#
# This audit is intentionally simple. Skills come from multiple upstream
# sources (mattpocock, alirezarezvani, local) with different section
# conventions, so structural heading checks produce too many false
# positives. Content-line count is the most reliable signal we can apply
# without LLM judgement: every observed unusable skeleton was below 40
# content lines, and every substantive skill was above it.
SKILL_MIN_CONTENT_LINES = 40
SKILL_LOCAL_MD_LINK = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def _strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4 :]


def skill_substance_audit() -> list[str]:
    """Verify every registered skill is substantive, not just present on disk.

    Existence is checked by graph_audit. Substance is the next layer:
    a 25-line placeholder passes existence and fails the actual job a
    subagent activated with it must do. See K12 for the failure pattern.
    """
    issues: list[str] = []
    nodes = load_yaml(ROOT_DIR / "ontology" / "nodes.yaml").get("nodes", [])
    for node in nodes:
        role = node.get("role")
        skill_ref = node.get("skill_ref")
        if not skill_ref:
            continue
        path = ROOT_DIR / f"{skill_ref}/SKILL.md"
        if not path.exists():
            # Existence is graph_audit's responsibility; do not double-report.
            continue
        text = path.read_text(errors="ignore")
        body = _strip_yaml_frontmatter(text)
        content_lines = [line for line in body.splitlines() if line.strip()]
        for link in SKILL_LOCAL_MD_LINK.findall(body):
            linked_path = (path.parent / link).resolve()
            try:
                linked_path.relative_to(path.parent.resolve())
            except ValueError:
                continue
            if linked_path.exists() and linked_path.is_file():
                linked_body = _strip_yaml_frontmatter(
                    linked_path.read_text(errors="ignore")
                )
                content_lines.extend(
                    line for line in linked_body.splitlines() if line.strip()
                )
        line_count = len(content_lines)
        rel = path.relative_to(ROOT_DIR)

        if line_count < SKILL_MIN_CONTENT_LINES:
            issues.append(
                f"thin skill: {rel} has {line_count} content lines "
                f"(minimum {SKILL_MIN_CONTENT_LINES}); skeleton, not a "
                f"usable skill (role: {role})"
            )
    return issues


def run() -> int:
    issues = graph_audit() + file_audit() + runtime_contract_audit() + skill_substance_audit()
    if issues:
        print("INVALID")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(run())
