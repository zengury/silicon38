#!/usr/bin/env python3
"""Silicon Org — Subagent prompt previewer.

Assembles the full prompt a node would receive (harness + skill + task) and
prints it alongside the resolved model profile. Runtime is responsible for
actually invoking the subagent through its own Agent tool; this module is
preview/audit only and never runs a subprocess.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NODES_FILE = REPO_ROOT / "ontology" / "nodes.yaml"
MODELS_FILE = REPO_ROOT / "org" / "models.local.yaml"

# Capability guidance only. Concrete model IDs are optional user config.
LAYER_RECOMMENDED_PROFILE = {
    1: "fast",
    2: "balanced",
    3: "deep",
}


def load_file(path: str) -> str | None:
    p = REPO_ROOT / path
    if p.exists():
        return p.read_text()
    return None


def load_yaml_file(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def get_node_for_role(role: str) -> dict | None:
    if not NODES_FILE.exists():
        return None
    data = load_yaml_file(NODES_FILE)
    for node in data.get("nodes", []):
        if node.get("role") == role:
            return node
    return None


def get_model_resolution_for_role(role: str) -> dict:
    """Resolve optional user model config and recommended model profile."""
    node = get_node_for_role(role) or {}
    profile = LAYER_RECOMMENDED_PROFILE.get(node.get("layer"), "runtime-default")
    config = load_yaml_file(MODELS_FILE)
    roles = config.get("roles", {}) or {}
    profiles = config.get("profiles", {}) or {}

    if role in roles and roles[role]:
        return {
            "model": roles[role],
            "source": "org/models.local.yaml roles",
            "profile": profile,
        }
    if profile in profiles and profiles[profile]:
        return {
            "model": profiles[profile],
            "source": "org/models.local.yaml profiles",
            "profile": profile,
        }
    if config.get("default"):
        return {
            "model": config["default"],
            "source": "org/models.local.yaml default",
            "profile": profile,
        }
    return {
        "model": "runtime-default",
        "source": "Runtime current/default model",
        "profile": profile,
    }


def build_prompt(
    role: str,
    task_id: str,
    task_description: str,
    input_artifacts: dict | None = None,
    constraints: list | None = None,
) -> str:
    """Build the full subagent prompt from harness + skill + task.

    Skill location is resolved from `ontology/nodes.yaml` (canonical source),
    not by parsing harness frontmatter — that prevents drift between the
    graph definition and what the prompt actually loads.
    """
    harness = load_file(f"org/registry/{role}.md") or f"# {role}\nHarness not found."
    skill = None
    node = get_node_for_role(role)
    if node:
        skill_ref = node.get("skill_ref")
        if skill_ref:
            skill = load_file(f"{skill_ref}/SKILL.md")

    parts = [f"# Task for: {role}\n"]

    if skill:
        parts.append(f"## Skill\n\n{skill}\n")

    parts.append(f"## Harness\n\n{harness}\n")

    parts.append(f"## Task\n\n{task_description}\n")

    if input_artifacts:
        parts.append("## Input Artifacts\n")
        for name, content in input_artifacts.items():
            parts.append(f"### {name}\n\n{content}\n")

    if constraints:
        parts.append("## Constraints\n")
        for c in constraints:
            parts.append(f"- {c}\n")

    parts.append(f"""
## Output Requirements

1. Produce your primary deliverable
2. Include a Completion Report:
   - what_was_done: one sentence
   - key_decisions: list of {{decision, rationale}}
   - handoff_focus: what the next node must attend to
   - open_questions: unresolved issues
   - known_constraints: constraints downstream must respect
   - confidence_differential: 0.0-1.0
   - dissent_if_alone: null or your different judgment if alone
3. Include a Context Compression Report:
   - input_scope.artifacts_read: every upstream artifact you read, marked used true/false with why
   - input_scope.handoffs_read: every upstream handoff you read with context_digest
   - retained_context: decisions, constraints, assumptions, and open_questions that affected your output
     * decisions require statement, source, impact
     * constraints require statement, source, impact
     * assumptions require statement, source, risk
     * open_questions require statement, source, owner
   - omitted_context: upstream context you intentionally dropped, with reason
     * reason must be irrelevant, superseded, contradicted, background_only, or duplicate
   - compression_rationale: method and loss_notes
   - quality_checks: each required check with passed: true

Write your output to: traces/{task_id}/artifacts/{role}-output-v1.md
Write the Context Compression Report as YAML to:
traces/{task_id}/artifacts/{role}-context-report-v1.yaml
""")

    return '\n'.join(parts)


def cmd_preview(args: list[str]) -> None:
    """spawn preview <role> <task_id> <task_description...>"""
    if len(args) < 3:
        print("Usage: spawn.py preview <role> <task_id> <task_description...>", file=sys.stderr)
        sys.exit(2)
    role, task_id = args[0], args[1]
    task_desc = ' '.join(args[2:])
    prompt = build_prompt(role, task_id, task_desc)
    model_info = get_model_resolution_for_role(role)
    print(f"# Model: {model_info['model']}")
    print(f"# Model source: {model_info['source']}")
    print(f"# Recommended profile: {model_info['profile']}")
    print("# (see org/MODELS.md; configure org/models.local.yaml to override)\n")
    print(prompt)


COMMANDS = {
    "preview": cmd_preview,
}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: spawn.py <command> [args...]")
        print("Commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
