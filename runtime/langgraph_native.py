"""LangGraph-native runtime contract for Silicon Org.

This is not an adapter around the legacy CLI loop. It is the target runtime
shape: Silicon Policy decides dynamic propagation from the full weighted Graph,
LangGraph executes those decisions durably, and Ledger receives transactional
fact commits.

The module is intentionally importable without LangGraph installed so design
validation and harness coverage checks can run in lightweight environments. To
execute the graph, install LangGraph and call `compile_native_runtime`.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT_DIR / "ontology" / "nodes.yaml"
RELATIONS_PATH = ROOT_DIR / "ontology" / "relations.yaml"
HARNESS_PROFILES_PATH = ROOT_DIR / "runtime" / "harness_profiles.yaml"
MODEL_EXAMPLE_PATH = ROOT_DIR / "org" / "models.example.yaml"
MODEL_LOCAL_PATH = ROOT_DIR / "org" / "models.local.yaml"
WEIGHT_MATRIX_PATH = ROOT_DIR / "ontology" / "weight_matrix.json"

ACTIVATION_EDGE_TYPES = {"triggers", "may_trigger", "evaluates"}
CONTEXT_EDGE_TYPES = {"supports", "constrains", "complements", "augments", "precedes"}
COMMERCIAL_SERVICE_ENV_VARS = {
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_TRACING",
    "LANGCHAIN_TRACING_V2",
    "LANGGRAPH_API_KEY",
    "LANGGRAPH_API_URL",
    "LANGGRAPH_CLOUD_URL",
    "LANGSMITH_API_KEY",
    "LANGSMITH_ENDPOINT",
    "LANGSMITH_PROJECT",
}


class LangGraphUnavailable(RuntimeError):
    """Raised when execution is requested without LangGraph installed."""


class NonOssRuntimeConfigured(RuntimeError):
    """Raised when hosted/commercial LangChain/LangGraph services are configured."""


def merge_unique_list(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    merged: list[Any] = []
    seen = set()
    for item in (left or []) + (right or []):
        marker = repr(item)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
    return merged


def append_list(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    return (left or []) + (right or [])


class OrgRunState(TypedDict, total=False):
    """LangGraph checkpoint state.

    This is execution state, not the canonical fact store. Durable facts still
    live in Ledger and must be committed through idempotent ledger transactions.
    """

    task_id: str
    task_type: str
    task_description: str
    workspace_dir: str
    pending_candidates: list[dict[str, Any]]
    candidate_backlog: list[dict[str, Any]]
    max_role_executions: int
    max_parallel_dispatch: int
    activation_threshold: float
    entry_roles: list[str]
    routed_entry_roles: Annotated[list[str], merge_unique_list]
    routed_completed_roles: Annotated[list[str], merge_unique_list]
    active_roles: Annotated[list[str], merge_unique_list]
    completed_roles: Annotated[list[str], merge_unique_list]
    deferred_roles: Annotated[list[str], merge_unique_list]
    blocked_roles: Annotated[list[str], merge_unique_list]
    current_role: str
    current_candidate: dict[str, Any]
    handoff_ref: str
    artifact_refs: Annotated[list[str], merge_unique_list]
    interrupts: Annotated[list[dict[str, Any]], append_list]
    node_results: Annotated[list[dict[str, Any]], append_list]
    model_selections: Annotated[list[dict[str, Any]], append_list]
    ledger_events: Annotated[list[dict[str, Any]], append_list]
    ledger_mode: Literal["memory", "write"]
    runner_mode: Literal["harness_dry_run", "prompt_package", "external_command", "semantic_command"]
    external_runner_command: str
    delivery_status: Literal["pending", "success", "partial", "failed"]
    topologist_status: Literal["pending", "completed"]
    hrbp_status: Literal["pending", "completed"]
    learning_status: Literal["pending", "completed"]
    use_thompson_sampling: bool


@dataclass(frozen=True)
class HarnessProfile:
    role: str
    purpose: str
    model_profile: str
    tool_groups: tuple[str, ...]
    write_scope: str
    output_artifacts: tuple[dict[str, Any], ...]
    completion_gates: tuple[str, ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class ModelSelection:
    role: str
    model_profile: str
    runner_pool: str
    provider: str
    model: str
    reasoning_effort: str
    source: Literal[
        "role_override",
        "role_runner_pool",
        "harness_runner_pool",
        "inferred_runner_pool",
        "profile_override",
        "default",
        "runtime_default",
    ]
    raw: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_nodes() -> dict[str, dict[str, Any]]:
    data = load_yaml(NODES_PATH)
    return {node["role"]: node for node in data.get("nodes", [])}


def load_relations() -> list[dict[str, Any]]:
    return load_yaml(RELATIONS_PATH).get("relations", [])


def load_harness_profiles() -> dict[str, HarnessProfile]:
    data = load_yaml(HARNESS_PROFILES_PATH)
    profiles = data.get("profiles", {})
    result: dict[str, HarnessProfile] = {}
    for role, raw in profiles.items():
        result[role] = HarnessProfile(
            role=role,
            purpose=raw["purpose"],
            model_profile=raw["model_profile"],
            tool_groups=tuple(raw.get("tool_groups", [])),
            write_scope=raw["write_scope"],
            output_artifacts=tuple(raw.get("output_artifacts", [])),
            completion_gates=tuple(raw.get("completion_gates", [])),
            raw=raw,
        )
    return result


def load_model_config() -> dict[str, Any]:
    """Load user-local model routing when present, otherwise the example defaults."""

    path = MODEL_LOCAL_PATH if MODEL_LOCAL_PATH.exists() else MODEL_EXAMPLE_PATH
    return load_yaml(path) if path.exists() else {}


def normalize_model_entry(entry: Any) -> dict[str, Any]:
    if isinstance(entry, str):
        return {"provider": "runtime", "model": entry, "reasoning_effort": "inherit"}
    if isinstance(entry, dict):
        return {
            "provider": entry.get("provider", "runtime"),
            "agent": entry.get("agent"),
            "model": entry.get("model", "runtime-default"),
            "reasoning_effort": entry.get("reasoning_effort", "inherit"),
            **{k: v for k, v in entry.items() if k not in {"provider", "agent", "model", "reasoning_effort"}},
        }
    return {"provider": "runtime", "model": "runtime-default", "reasoning_effort": "inherit"}


def explicit_model_overrides(entry: Any) -> dict[str, Any]:
    """Return only fields explicitly supplied by the config entry."""

    if isinstance(entry, str):
        return {"model": entry}
    if isinstance(entry, dict):
        return {k: v for k, v in entry.items() if v not in (None, "")}
    return {}


def default_runner_pool_for_profile(profile: HarnessProfile) -> str:
    execution = profile.raw.get("execution") or {}
    if isinstance(execution, dict) and execution.get("default_runner_pool"):
        return str(execution["default_runner_pool"])

    tool_groups = set(profile.tool_groups)
    write_scope = str(profile.write_scope)
    can_modify = profile.raw.get("can_modify_product_code")
    if (
        can_modify is True
        or (isinstance(can_modify, str) and can_modify not in {"", "false", "False", "none"})
        or "repo_write_scoped" in tool_groups
        or "repo_write_tests_scoped" in tool_groups
        or "repo_write_ops_scoped" in tool_groups
        or "product_code" in write_scope
        or "tests_and_trace" in write_scope
        or "prototype_paths" in write_scope
    ):
        if "browser_optional" in tool_groups or profile.role in {"senior-frontend", "prototype", "epic-design"}:
            return "frontend_browser"
        if profile.role in {"code-reviewer", "security-engineer", "tdd", "dependency-auditor"}:
            return "coding_reviewer"
        return "coding_builder"

    if profile.role in {"code-reviewer", "security-engineer", "grill-me", "delivery-prover"}:
        return "coding_reviewer"
    return "api_model"


def resolve_runner_pool_entry(
    pool_name: str,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    pools = config.get("runner_pools") or {}
    entry = pools.get(pool_name)
    return normalize_model_entry(entry) if entry is not None else None


def resolve_model_for_role(role: str, model_config: dict[str, Any] | None = None) -> ModelSelection:
    """Resolve provider/model per role without hard-coding concrete IDs in Graph."""

    profiles = load_harness_profiles()
    if role not in profiles:
        raise KeyError(f"no harness profile for role: {role}")
    profile = profiles[role].model_profile
    harness_profile = profiles[role]
    config = model_config or load_model_config()
    role_entry = (config.get("roles") or {}).get(role)
    runner_pool = ""
    if role_entry is not None:
        role_overrides = explicit_model_overrides(role_entry)
        runner_pool = str(role_overrides.get("runner_pool") or "")
        if runner_pool:
            pool_raw = resolve_runner_pool_entry(runner_pool, config) or {}
            raw = {**pool_raw, **role_overrides}
            source: Literal[
                "role_override",
                "role_runner_pool",
                "harness_runner_pool",
                "inferred_runner_pool",
                "profile_override",
                "default",
                "runtime_default",
            ] = "role_runner_pool"
        else:
            raw = normalize_model_entry(role_entry)
            source = "role_override"
    else:
        runner_pool = default_runner_pool_for_profile(harness_profile)
        pool_raw = resolve_runner_pool_entry(runner_pool, config)
        if pool_raw is not None:
            raw = pool_raw
            execution = harness_profile.raw.get("execution") or {}
            source = "harness_runner_pool" if isinstance(execution, dict) and execution.get("default_runner_pool") else "inferred_runner_pool"
        elif (config.get("profiles") or {}).get(profile) is not None:
            raw = normalize_model_entry((config.get("profiles") or {}).get(profile))
            runner_pool = ""
            source = "profile_override"
        elif config.get("default") is not None:
            raw = normalize_model_entry(config.get("default"))
            runner_pool = ""
            source = "default"
        else:
            raw = {"provider": "runtime", "model": "runtime-default", "reasoning_effort": "inherit"}
            runner_pool = ""
            source = "runtime_default"
    provider = raw.get("agent") or raw.get("provider", "runtime")
    return ModelSelection(
        role=role,
        model_profile=profile,
        runner_pool=runner_pool,
        provider=provider,
        model=raw["model"],
        reasoning_effort=raw["reasoning_effort"],
        source=source,
        raw=raw,
    )


def validate_full_node_mapping() -> list[str]:
    """Return coverage issues for ontology nodes versus harness profiles."""

    node_roles = set(load_nodes())
    profile_roles = set(load_harness_profiles())
    issues: list[str] = []
    for role in sorted(node_roles - profile_roles):
        issues.append(f"missing harness profile for ontology node: {role}")
    for role in sorted(profile_roles - node_roles):
        issues.append(f"harness profile has no ontology node: {role}")
    return issues


def relation_dimensions(relation: dict[str, Any]) -> dict[str, Any]:
    """Return all weight dimensions without flattening them into one edge."""

    weights = relation.get("weights") or {}
    return weights if isinstance(weights, dict) else {}


def score_candidate(relation: dict[str, Any], ledger_facts: dict[str, Any]) -> dict[str, Any]:
    """Build a transparent candidate score envelope.

    The first implementation keeps every dimension explicit. Learning can later
    tune the scoring formula without changing LangGraph topology.
    """

    weights = relation_dimensions(relation)
    probability = weights.get("probability", {})
    strictness = weights.get("strictness", {})
    necessity = weights.get("necessity", {})
    base = 0.0
    if isinstance(probability, dict):
        base = float(probability.get("value") or 0.0)
    elif isinstance(strictness, dict):
        base = float(strictness.get("value") or 0.0)
    elif isinstance(necessity, dict):
        base = float(necessity.get("value") or 0.0)
    confidence_values = [
        value.get("confidence")
        for value in weights.values()
        if isinstance(value, dict) and isinstance(value.get("confidence"), (int, float))
    ]
    confidence = max(confidence_values) if confidence_values else 0.0
    return {
        "from": relation.get("from"),
        "to": relation.get("to"),
        "relation_type": relation.get("type"),
        "legal": relation.get("type") in ACTIVATION_EDGE_TYPES,
        "score": base,
        "confidence": confidence,
        "dimensions": weights,
        "ledger_signal": ledger_facts.get("learning_signal", {}),
        "condition": weights.get("condition"),
    }


def policy_candidates_for_completed_role(
    completed_role: str,
    ledger_facts: dict[str, Any],
) -> list[dict[str, Any]]:
    """Full-graph dynamic propagation entrypoint for the Policy router.

    This function deliberately reads the entire Silicon Graph. It does not
    compile a reduced route and it does not map relation weights into static
    LangGraph edges.
    """

    candidates: list[dict[str, Any]] = []
    for relation in load_relations():
        relation_type = relation.get("type")
        if relation_type in {"triggers", "may_trigger"} and relation.get("from") == completed_role:
            candidates.append(score_candidate(relation, ledger_facts))
        if relation_type == "evaluates" and relation.get("to") == completed_role:
            reverse = dict(relation)
            reverse["from"], reverse["to"] = relation.get("to"), relation.get("from")
            candidates.append(score_candidate(reverse, ledger_facts))
    return candidates


def thompson_candidates_for_completed_role(
    completed_role: str,
    completed_nodes: set[str],
    task_type: str,
    top_k: int = 5,
    exploration_budget: int = 1,
) -> list[dict[str, Any]]:
    """Thompson Sampling variant: consider ALL potential downstream nodes,
    sample from Beta posteriors, return top-k activated candidates.

    This replaces the symbolist edge-type-based activation with probabilistic
    exploration of the full 38×38 weight matrix.
    """
    try:
        from tools.thompson_policy import ThompsonPolicy
    except ImportError:
        return []
    
    policy = ThompsonPolicy.load(WEIGHT_MATRIX_PATH)
    wave = policy.evaluate_candidates(
        completed_role, completed_nodes, task_type,
        top_k=top_k, exploration_budget=exploration_budget,
    )
    
    candidates: list[dict[str, Any]] = []
    # Load relations to propagate any gating constraints to Thompson candidates
    relations_lookup = {}
    for rel in load_relations():
        key = (rel["from"], rel["to"])
        if key not in relations_lookup:
            relations_lookup[key] = []
        relations_lookup[key].append(rel)
    
    for c in wave.activated:
        # Propagate any gating constraints from relations.yaml
        dimensions = {
            "probability": {"value": c.sampled_score, "confidence": 0.5, "samples": 0},
        }
        # Check if this edge exists in relations.yaml with gating
        edge_key = (c.from_role, c.to_role)
        has_any_gating = False
        if edge_key in relations_lookup:
            for rel in relations_lookup[edge_key]:
                w = rel.get("weights", {})
                if "activation_task_types" in w:
                    dimensions["activation_task_types"] = w["activation_task_types"]
                    has_any_gating = True
                if "activation_skip_on_task_types" in w:
                    dimensions["activation_skip_on_task_types"] = w["activation_skip_on_task_types"]
                    has_any_gating = True
                if "activation_verdicts" in w:
                    dimensions["activation_verdicts"] = w["activation_verdicts"]
                    has_any_gating = True
                if "activation_unconditional" in w:
                    dimensions["activation_unconditional"] = w["activation_unconditional"]
                    has_any_gating = True
        # Only set unconditional=True if no gating constraints exist
        if not has_any_gating:
            dimensions["activation_unconditional"] = True
        
        candidates.append({
            "from": c.from_role,
            "to": c.to_role,
            "relation_type": "thompson_sample",
            "legal": True,
            "score": c.sampled_score,
            "confidence": 0.5,
            "dimensions": dimensions,
            "ledger_signal": {},
            "condition": f"Thompson sample α={c.alpha:.1f} β={c.beta_param:.1f} [{c.source}]",
            "thompson_alpha": c.alpha,
            "thompson_beta": c.beta_param,
        })
    return candidates


def thompson_bayesian_update(task_id: str) -> None:
    """After task delivery, update edge weights with real outcomes.
    
    Activated edges that produced quality output get alpha incremented.
    Skipped/deferred edges get beta incremented (evidence of non-relevance).
    """
    try:
        from tools.thompson_policy import ThompsonPolicy
    except ImportError:
        return
    
    import yaml as _yaml
    manifest_path = ROOT_DIR / "traces" / task_id / "manifest.yaml"
    state_path = ROOT_DIR / "traces" / task_id / "state.yaml"
    if not manifest_path.exists() or not state_path.exists():
        return
    
    manifest = _yaml.safe_load(manifest_path.read_text())
    state = _yaml.safe_load(state_path.read_text())
    
    policy = ThompsonPolicy.load(WEIGHT_MATRIX_PATH)
    node_states = state.get("node_states", {})
    handoffs = manifest.get("handoff_trail", [])
    
    # Score each completed node's output quality (0-1)
    quality_scores: dict[str, float] = {}
    for role, info in node_states.items():
        if info.get("status") != "completed":
            continue
        artifacts = info.get("output_artifact_ids", [])
        has_context_report = bool(info.get("context_report_valid"))
        artifact_count = len(artifacts)
        
        score = 0.5  # base
        if artifact_count >= 2:
            score += 0.2
        elif artifact_count == 1:
            score += 0.1
        if has_context_report:
            score += 0.2
        
        quality_scores[role] = min(score, 1.0)
    
    # Update edges: each handoff represents an (from, to) edge that was activated
    for h in handoffs:
        fr = h.get("from", "")
        to = h.get("to", "")
        if fr and to:
            success = quality_scores.get(to, 0.5)
            policy.update_edge(fr, to, success)
    
    # Also update edges for completed nodes without handoffs (weak negative signal)
    for role in node_states:
        if node_states[role].get("status") == "completed":
            # Check if this role produced handoffs to anyone
            has_outgoing = any(h.get("from") == role for h in handoffs)
            if not has_outgoing:
                # Node completed but produced no handoffs — weak negative for its incoming edges
                for h2 in handoffs:
                    if h2.get("to") == role:
                        fr = h2.get("from", "")
                        policy.update_edge(fr, role, 0.2, weight=0.3)
    
    policy.save(WEIGHT_MATRIX_PATH)


def default_entry_roles(task_type: str | None = None) -> list[str]:
    """Conservative bootstrap when caller does not provide entry roles."""

    return ["triage"]


def policy_entry_candidates(state: OrgRunState) -> list[dict[str, Any]]:
    """Create legal entry candidates without hard-coding downstream topology."""

    if state.get("routed_entry_roles"):
        return []
    roles = state.get("entry_roles") or default_entry_roles(state.get("task_type"))
    nodes = load_nodes()
    candidates: list[dict[str, Any]] = []
    for role in roles:
        node = nodes.get(role)
        if not node:
            continue
        candidates.append({
            "from": None,
            "to": role,
            "relation_type": "entry",
            "legal": node.get("layer") == 1,
            "score": 1.0,
            "confidence": 1.0,
            "dimensions": {"entry": {"value": True, "source": "runtime_bootstrap"}},
            "ledger_signal": {},
            "condition": "entry role selected by runtime bootstrap",
        })
    return candidates


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[float, float, str]:
    return (
        float(candidate.get("score") or 0.0),
        float(candidate.get("confidence") or 0.0),
        str(candidate.get("to") or ""),
    )


def best_candidate_per_target(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one executable candidate per target role in a policy wave."""

    best: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        target = candidate.get("to")
        if not target:
            continue
        existing = best.get(target)
        if existing is None or candidate_sort_key(candidate) > candidate_sort_key(existing):
            best[target] = candidate
    return list(best.values())


def candidate_activation_decision(
    candidate: dict[str, Any],
    threshold: float,
    state: OrgRunState | None = None,
) -> tuple[str, str]:
    """Return Policy's activation decision and a durable reason."""

    relation_type = candidate.get("relation_type")
    score = float(candidate.get("score") or 0.0)
    dimensions = candidate.get("dimensions") or {}
    task_type = str((state or {}).get("task_type") or "unknown")
    task_type_hint = (state or {}).get("task_type_hint")
    # If task_type is "general" but a hint was provided, use the hint for gating.
    effective_task_type = task_type if task_type != "general" else (task_type_hint or task_type)
    metric = {}
    if isinstance(dimensions.get("probability"), dict):
        metric = dimensions["probability"]
    elif isinstance(dimensions.get("strictness"), dict):
        metric = dimensions["strictness"]

    unconditional = dimensions.get("activation_unconditional") is True
    allowed_task_types = dimensions.get("activation_task_types")
    if isinstance(allowed_task_types, list) and effective_task_type not in allowed_task_types:
        return (
            "defer",
            f"Candidate gated by task_type={effective_task_type}; allowed task types: {allowed_task_types}."
            + (f" (hint={task_type_hint})" if task_type_hint and task_type == "general" else ""),
        )
    skip_task_types = dimensions.get("activation_skip_on_task_types") or dimensions.get("blocking_skip_on_task_types")
    if isinstance(skip_task_types, list) and effective_task_type in skip_task_types:
        return (
            "defer",
            f"Candidate gated by task_type={task_type}; skipped task types: {skip_task_types}.",
        )
    allowed_verdicts = dimensions.get("activation_verdicts")
    if isinstance(allowed_verdicts, list):
        verdict = (state or {}).get("latest_verdict") or (state or {}).get("delivery_verdict")
        if verdict not in allowed_verdicts:
            return (
                "defer",
                f"Candidate gated by verdict={verdict or 'unknown'}; allowed verdicts: {allowed_verdicts}.",
            )
    has_executable_gate = (
        unconditional
        or isinstance(allowed_task_types, list)
        or isinstance(skip_task_types, list)
        or isinstance(allowed_verdicts, list)
    )
    samples = metric.get("samples") if isinstance(metric, dict) else None
    confidence = metric.get("confidence") if isinstance(metric, dict) else None
    low_sample_prior = samples in (None, 0) and (
        not isinstance(confidence, (int, float)) or float(confidence) <= 0.25
    )
    if (
        relation_type in ACTIVATION_EDGE_TYPES
        and score >= 0.80
        and low_sample_prior
        and not has_executable_gate
    ):
        return (
            "defer",
            "Candidate is a high-weight low-sample prior without an executable "
            "activation gate or activation_unconditional=true.",
        )
    if relation_type == "entry":
        return "activate", "Entry role selected by runtime bootstrap."
    if relation_type == "evaluates":
        return "activate", "Evaluator edge activates after producer artifact exists."
    if relation_type == "triggers" and score >= threshold:
        return "activate", f"Trigger score {score:.2f} meets activation threshold {threshold:.2f}."
    if relation_type == "may_trigger" and score >= threshold:
        return "activate", f"Conditional score {score:.2f} meets activation threshold {threshold:.2f}."
    if relation_type == "thompson_sample" and score >= threshold:
        return "activate", f"Thompson sample {score:.2f} meets threshold {threshold:.2f}."
    return "defer", (
        f"Candidate score {score:.2f} is below activation threshold "
        f"{threshold:.2f}; deferred for later policy review."
    )


def apply_policy_decisions(
    state: OrgRunState,
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Choose executable candidates and record non-executed decisions."""

    threshold = float(state.get("activation_threshold", 0.5))
    max_dispatch = int(state.get("max_parallel_dispatch", 1) or 1)
    completed_count = len(state.get("completed_roles", []))
    max_role_executions = state.get("max_role_executions")
    remaining = None
    if max_role_executions:
        remaining = max(0, int(max_role_executions) - completed_count)
        max_dispatch = min(max_dispatch, remaining)

    ranked = sorted(best_candidate_per_target(candidates), key=candidate_sort_key, reverse=True)
    activations: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    backlog: list[dict[str, Any]] = []
    for candidate in ranked:
        decision, reason = candidate_activation_decision(candidate, threshold, state)
        if decision == "activate" and len(activations) < max_dispatch:
            enriched = {**candidate, "decision": decision, "decision_reason": reason}
            activations.append(enriched)
            decisions.append(enriched)
            continue
        if decision == "activate":
            backlog.append({
                **candidate,
                "decision": "backlog",
                "decision_reason": (
                    f"Candidate kept in backlog because max_parallel_dispatch={max_dispatch} "
                    "was already reached in this policy wave."
                ),
            })
            continue
        decisions.append({**candidate, "decision": decision, "decision_reason": reason})

    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction

        ledger_tx = LedgerTransaction(state["task_id"])
        for decision in decisions:
            if decision.get("relation_type") == "entry":
                continue
            if decision.get("decision") == "activate":
                # Activation is durably recorded by the handoff transaction.
                continue
            ledger_tx.commit_activation_decision(
                decision["from"],
                decision["to"],
                decision["relation_type"],
                decision["decision"],
                decision["decision_reason"],
            )

    return activations, decisions, backlog


def _imports() -> dict[str, Any]:
    enforce_oss_only_runtime()
    try:
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Send, interrupt
    except ImportError as exc:
        raise LangGraphUnavailable(
            "LangGraph is required to execute the native runtime. The design and "
            "harness coverage checks can run without it."
        ) from exc
    return {"END": END, "START": START, "StateGraph": StateGraph, "Send": Send, "interrupt": interrupt}


def configured_commercial_service_vars() -> list[str]:
    return sorted(key for key in COMMERCIAL_SERVICE_ENV_VARS if os.environ.get(key))


def enforce_oss_only_runtime() -> None:
    """Allow only local MIT LangGraph OSS runtime execution.

    Silicon Org must not silently connect to LangGraph Platform, LangSmith, or
    LangChain hosted tracing services.
    """

    configured = configured_commercial_service_vars()
    if configured:
        raise NonOssRuntimeConfigured(
            "Silicon Org LangGraph-native runtime is OSS-only. Unset hosted "
            "service variables before running: " + ", ".join(configured)
        )


def encoder_node(state: OrgRunState) -> OrgRunState:
    """Create or load task ledger facts before routing begins."""

    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction

        task_id = state.get("task_id")
        if not task_id:
            raise ValueError("task_id is required when ledger_mode=write")
        tx = LedgerTransaction(task_id)
        tx.ensure_task_initialized(
            state.get("task_type", "unknown"),
            state.get("task_description", ""),
        )
        ws = state.get("workspace_dir", "")
        if ws:
            tx.save_workspace_dir(ws)
    return {
        "delivery_status": state.get("delivery_status", "pending"),
        "topologist_status": state.get("topologist_status", "pending"),
        "hrbp_status": state.get("hrbp_status", "pending"),
        "learning_status": state.get("learning_status", "pending"),
        "ledger_mode": state.get("ledger_mode", "memory"),
        "runner_mode": state.get("runner_mode", "harness_dry_run"),
        "activation_threshold": state.get("activation_threshold", 0.5),
        "max_parallel_dispatch": state.get("max_parallel_dispatch", 1),
        "use_thompson_sampling": state.get("use_thompson_sampling", True),
    }


def policy_router_node(state: OrgRunState) -> OrgRunState:
    """Ask Silicon Policy for legal full-graph candidates."""

    if state.get("delivery_status") in {"success", "partial", "failed"}:
        return {"pending_candidates": []}

    completed_roles = state.get("completed_roles", [])
    max_role_executions = state.get("max_role_executions")
    if max_role_executions and len(completed_roles) >= max_role_executions:
        return {"pending_candidates": [], "candidate_backlog": state.get("candidate_backlog", [])}

    routed_completed = set(state.get("routed_completed_roles", []))
    settled_targets = set(completed_roles)
    settled_targets.update(state.get("active_roles", []))
    settled_targets.update(state.get("deferred_roles", []))
    settled_targets.update(state.get("blocked_roles", []))
    for node_result in state.get("node_results", []):
        role = node_result.get("role")
        if role:
            settled_targets.add(role)

    if not completed_roles:
        entry_candidates = [
            candidate for candidate in policy_entry_candidates(state)
            if candidate.get("to") not in settled_targets
        ]
        activations, decisions, backlog = apply_policy_decisions(state, entry_candidates)
        return {
            "pending_candidates": activations,
            "candidate_backlog": backlog,
            "routed_entry_roles": [
                candidate["to"] for candidate in activations
                if candidate.get("legal")
            ],
            "ledger_events": [{
                "type": "policy_decision",
                "from": decision.get("from"),
                "to": decision.get("to"),
                "relation_type": decision.get("relation_type"),
                "decision": decision.get("decision"),
                "reason": decision.get("decision_reason"),
            } for decision in decisions],
        }

    ledger_facts = {
        "task_id": state.get("task_id"),
        "completed_roles": completed_roles,
        "learning_signal": {},
    }
    newly_completed = [
        role for role in completed_roles
        if role not in routed_completed
    ]
    candidates: list[dict[str, Any]] = []
    for completed in newly_completed:
        candidates.extend(policy_candidates_for_completed_role(completed, ledger_facts))
    
    # Thompson Sampling: probabilistic exploration of full weight matrix
    if state.get("use_thompson_sampling"):
        task_type = str(state.get("task_type") or "unknown")
        for completed in newly_completed[:1]:
            thompson_candidates = thompson_candidates_for_completed_role(
                completed, set(completed_roles), task_type,
                top_k=2, exploration_budget=0,
            )
            candidates.extend(thompson_candidates)
    
    candidates = best_candidate_per_target(state.get("candidate_backlog", []) + candidates)

    filtered = [
        candidate for candidate in candidates
        if candidate.get("to") not in settled_targets
    ]
    activations, decisions, backlog = apply_policy_decisions(state, filtered)
    return {
        "pending_candidates": activations,
        "candidate_backlog": backlog,
        "routed_completed_roles": newly_completed,
        "ledger_events": [{
            "type": "policy_decision",
            "from": decision.get("from"),
            "to": decision.get("to"),
            "relation_type": decision.get("relation_type"),
            "decision": decision.get("decision"),
            "reason": decision.get("decision_reason"),
        } for decision in decisions],
    }


def route_policy_candidates(state: OrgRunState) -> list[Any]:
    """LangGraph conditional route: dynamic fan-out with Send.

    Silicon Policy owns the candidate list. LangGraph only receives executable
    envelopes and schedules `run_role_node` in parallel.
    """

    imports = _imports()
    send = imports["Send"]
    sends = []
    settled_targets = set(state.get("completed_roles", []))
    settled_targets.update(state.get("active_roles", []))
    settled_targets.update(state.get("deferred_roles", []))
    settled_targets.update(state.get("blocked_roles", []))
    for candidate in state.get("pending_candidates", []):
        if not candidate.get("legal"):
            continue
        if candidate.get("to") in settled_targets:
            continue
        sends.append(send("run_role_node", {
            "task_id": state.get("task_id"),
            "task_type": state.get("task_type", "unknown"),
            "task_description": state.get("task_description", ""),
            "workspace_dir": state.get("workspace_dir", ""),
            "current_role": candidate["to"],
            "current_candidate": candidate,
            "handoff_ref": candidate.get("handoff_ref", ""),
            "ledger_mode": state.get("ledger_mode", "memory"),
            "runner_mode": state.get("runner_mode", "harness_dry_run"),
            "entry_roles": state.get("entry_roles", []),
            "activation_threshold": state.get("activation_threshold", 0.5),
            "max_parallel_dispatch": state.get("max_parallel_dispatch", 1),
            "external_runner_command": state.get("external_runner_command", ""),
        }))
    if sends:
        return sends
    return ["convergence_policy"]


def _capture_workspace_code(task_id: str, workspace_dir: str, role: str) -> None:
    """Copy new/changed code files from workspace into trace artifacts/code/."""
    import shutil
    wsp = Path(workspace_dir)
    if not wsp.is_dir():
        return
    code_dir = ROOT_DIR / "traces" / task_id / "artifacts" / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    # Collect recently modified Python files (last 30 min)
    cutoff = __import__("time").time() - 1800
    captured = 0
    for py_file in wsp.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".pytest_cache" in str(py_file):
            continue
        try:
            if py_file.stat().st_mtime > cutoff:
                rel = py_file.relative_to(wsp)
                dest = code_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(py_file, dest)
                captured += 1
        except Exception:
            pass
    if captured:
        # Write manifest
        import yaml
        manifest = {"role": role, "captured_files": captured, "workspace": workspace_dir}
        (code_dir / "MANIFEST.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )


def run_role_node(state: OrgRunState) -> OrgRunState:
    """Execute any of the 35 Silicon Org roles using its harness profile."""

    role = state["current_role"]
    profiles = load_harness_profiles()
    if role not in profiles:
        raise KeyError(f"no harness profile for role: {role}")
    profile = profiles[role]
    model_selection = resolve_model_for_role(role)
    candidate = state.get("current_candidate", {})
    artifact_refs: list[str]
    ledger_events: list[dict[str, Any]] = []

    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction
        from .node_runner import (
            ExternalCommandNodeRunner,
            HarnessDryRunNodeRunner,
            PromptPackageNodeRunner,
            SemanticCommandNodeRunner,
        )

        ledger_tx = LedgerTransaction(state["task_id"])
        handoff_ref = state.get("handoff_ref", "")
        if (
            candidate.get("relation_type")
            and candidate.get("relation_type") != "entry"
            and candidate.get("from")
        ):
            handoff_ref = ledger_tx.commit_handoff(
                candidate["from"],
                role,
                candidate["relation_type"],
                candidate.get("condition") or f"Activate {role} from {candidate['from']}",
            )
        request = ledger_tx.build_node_run_request(
            task_type=state.get("task_type", "unknown"),
            task_description=state.get("task_description", ""),
            workspace_dir=state.get("workspace_dir", ""),
            role=role,
            harness_profile=profile,
            model_selection=model_selection,
            candidate=candidate,
            input_handoff_ref=handoff_ref,
        )
        runner_mode = state.get("runner_mode", "harness_dry_run")
        if runner_mode == "prompt_package":
            runner = PromptPackageNodeRunner()
        elif runner_mode == "semantic_command":
            runner = SemanticCommandNodeRunner(command=state.get("external_runner_command", ""))
        elif runner_mode == "external_command":
            runner = ExternalCommandNodeRunner(command=state.get("external_runner_command", ""))
        else:
            runner = HarnessDryRunNodeRunner()
        result = runner.run(request)
        commit = ledger_tx.commit_role_result(
            result,
            candidate=candidate,
            entry=candidate.get("relation_type") == "entry",
            task_type=state.get("task_type", "unknown"),
            task_summary=state.get("task_description", ""),
        )
        artifact_refs = [commit.artifact_id]
        ledger_events.append({
            "role": role,
            "artifact_id": commit.artifact_id,
            "artifact_ref": commit.artifact_ref,
            "context_report_ref": commit.context_report_ref,
            "context_report_digest": commit.context_report_digest,
            "status": commit.status,
        })

        # ── Capture code files written by implementation nodes ──
        workspace_dir = state.get("workspace_dir", "")
        if workspace_dir and result.metadata.get("runner") not in ("harness_dry_run",):
            _capture_workspace_code(state["task_id"], workspace_dir, role)
    else:
        artifact_refs = [
            f"{role}-{profile.output_artifacts[0]['type']}-v1"
        ] if profile.output_artifacts else []

    return {
        "active_roles": [role],
        "completed_roles": [role],
        "artifact_refs": artifact_refs,
        "ledger_events": ledger_events,
        "node_results": [{
            "role": role,
            "artifact_refs": artifact_refs,
            "runner_mode": state.get("runner_mode", "harness_dry_run"),
            "ledger_mode": state.get("ledger_mode", "memory"),
        }],
        "model_selections": [{
            "role": model_selection.role,
            "model_profile": model_selection.model_profile,
            "provider": model_selection.provider,
            "model": model_selection.model,
            "reasoning_effort": model_selection.reasoning_effort,
            "source": model_selection.source,
        }],
    }


def _resolve_delivery_outcome(tx: Any, default_summary: str) -> tuple[str, str]:
    """Decide success/partial/failed from convergence gates and node failures.

    `convergence_policy_node` previously hardcoded every termination as
    "partial", which pinned the learning quality signal to a constant 0.5
    regardless of whether the graph actually converged. This recomputes the
    convergence gates (`ledger converge`) at the moment of termination and
    only falls back to "partial" when gates remain unmet.
    """

    convergence = tx.run_convergence_check()
    if not convergence:
        return "partial", default_summary

    node_states = tx.load_state().get("node_states", {})
    failed_roles = sorted(
        role for role, info in node_states.items()
        if info.get("status") in ("failed", "blocked")
    )
    if failed_roles:
        return "failed", f"{default_summary} Failed/blocked nodes: {', '.join(failed_roles)}."

    unmet = sorted(
        key for key, value in convergence.items()
        if key != "settled_at" and value is not True
    )
    if not unmet:
        return "success", f"{default_summary} All convergence gates passed."

    return "partial", f"{default_summary} Unmet convergence gates: {', '.join(unmet)}."


def _commit_resolved_delivery(tx: Any, status: str, detail: str) -> str:
    """Commit the resolved outcome, downgrading "success" to "partial" if a
    delivery policy overlay rejects it (e.g. a required delivery-prover
    artifact is missing for this task type)."""

    from .ledger_transactions import LedgerTransactionError

    try:
        tx.commit_delivery(status, detail)
        return status
    except LedgerTransactionError as exc:
        if status != "success":
            raise
        tx.commit_delivery("partial", f"{detail} Delivery policy rejected success: {exc}")
        return "partial"


def convergence_policy_node(state: OrgRunState) -> OrgRunState:
    """Policy verdict, not an org node."""

    max_role_executions = state.get("max_role_executions")
    if (
        max_role_executions
        and len(state.get("completed_roles", [])) >= max_role_executions
        and state.get("delivery_status") == "pending"
    ):
        status = "partial"
        if state.get("ledger_mode") == "write":
            from .ledger_transactions import LedgerTransaction

            tx = LedgerTransaction(state["task_id"])
            status, detail = _resolve_delivery_outcome(
                tx,
                "LangGraph-native runtime stopped at explicit "
                f"max_role_executions={max_role_executions}.",
            )
            status = _commit_resolved_delivery(tx, status, detail)
        return {
            "delivery_status": status,
            "candidate_backlog": [],  # Drain backlog when capped
            "pending_candidates": [],
            "interrupts": [{
                "type": "max_role_executions_reached",
                "limit": max_role_executions,
                "detail": "Stopped by explicit runtime smoke/development limit.",
            }],
        }

    # No pending candidates and no active roles → all graph paths exhausted
    pending = state.get("pending_candidates", [])
    backlog = state.get("candidate_backlog", [])
    active = state.get("active_roles", [])

    # When capped and no pending work, drain backlog and deliver
    if max_role_executions and not pending and state.get("completed_roles"):
        status = "partial"
        if state.get("delivery_status") == "pending" and state.get("ledger_mode") == "write":
            from .ledger_transactions import LedgerTransaction
            tx = LedgerTransaction(state["task_id"])
            status, detail = _resolve_delivery_outcome(tx, "Graph propagation capped — backlog drained.")
            status = _commit_resolved_delivery(tx, status, detail)
        return {"delivery_status": status, "candidate_backlog": [], "pending_candidates": []}

    if not pending and not backlog and not active and state.get("completed_roles"):
        status = "partial"
        if state.get("delivery_status") == "pending" and state.get("ledger_mode") == "write":
            from .ledger_transactions import LedgerTransaction
            tx = LedgerTransaction(state["task_id"])
            status, detail = _resolve_delivery_outcome(tx, "Graph propagation exhausted — no more legal candidates.")
            status = _commit_resolved_delivery(tx, status, detail)
        return {"delivery_status": status}

    return {}


def route_after_convergence(state: OrgRunState) -> str:
    if state.get("delivery_status") in {"success", "partial", "failed"}:
        return "graph_topologist_node"
    return "policy_router"


def graph_topologist_node(state: OrgRunState) -> OrgRunState:
    """Mandatory post-delivery learning role. Reads full trace and produces structured analysis."""

    ledger_events: list[dict[str, Any]] = []
    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction
        from .node_runner import NodeRunResult

        ledger_tx = LedgerTransaction(state["task_id"])
        manifest = ledger_tx.load_manifest()
        task_state = ledger_tx.load_state()
        handoff_count = len(manifest.get("handoff_trail", []))
        artifact_count = len(task_state.get("artifact_registry", {}))
        completed_roles = [
            role for role, info in task_state.get("node_states", {}).items()
            if info.get("status") == "completed"
        ]
        failed_roles = [
            role for role, info in task_state.get("node_states", {}).items()
            if info.get("status") in ("failed", "blocked")
        ]
        total_elapsed = 0
        for role in completed_roles:
            info = task_state["node_states"][role]
            if info.get("activated_at") and info.get("completed_at"):
                from datetime import datetime
                try:
                    start_t = datetime.fromisoformat(str(info["activated_at"]).replace("Z", "+00:00"))
                    end_t = datetime.fromisoformat(str(info["completed_at"]).replace("Z", "+00:00"))
                    total_elapsed += (end_t - start_t).total_seconds()
                except Exception:
                    pass

        findings: list[str] = []
        if failed_roles:
            findings.append(f"- Failed nodes: {', '.join(failed_roles)}")
        if handoff_count < len(completed_roles):
            findings.append(f"- Missing handoffs: {len(completed_roles) - handoff_count} orphan artifacts")
        if total_elapsed > 600:
            findings.append(f"- Slow execution: {total_elapsed:.0f}s total for {len(completed_roles)} roles")
        if not findings:
            findings.append("- No structural issues identified in trace topology.")

        body = "\n".join([
            "# Graph Topologist Runtime Review",
            "",
            f"- task_id: `{state.get('task_id')}`",
            f"- outcome: `{(manifest.get('outcome') or {}).get('status', 'unknown')}`",
            f"- completed_roles: {', '.join(completed_roles) or '(none)'}",
            f"- failed_roles: {', '.join(failed_roles) or '(none)'}",
            f"- artifact_count: {artifact_count}",
            f"- handoff_count: {handoff_count}",
            f"- total_elapsed: {total_elapsed:.0f}s",
            "",
            "## Findings",
            "",
        ] + findings + ["", "## Signal", "", "The trace is readable by the learning layer. Relation handoffs, "
            "role artifacts, context reports, and delivery outcome are durable Ledger facts."])

        commit = ledger_tx.commit_role_result(NodeRunResult(
            role="graph-topologist",
            artifact_type="topology-review",
            artifact_body=body + "\n",
            artifact_extension="md",
            metadata={"runner": "runtime_topology_review"},
        ))
        ledger_events.append({
            "role": "graph-topologist",
            "artifact_id": commit.artifact_id,
            "artifact_ref": commit.artifact_ref,
            "status": commit.status,
        })
    return {
        "current_role": "graph-topologist",
        "topologist_status": "completed",
        "ledger_events": ledger_events,
    }


def hrbp_node(state: OrgRunState) -> OrgRunState:
    """HRBP: Evaluate talent (skill performance) with granular scoring from trace data."""

    ledger_events: list[dict[str, Any]] = []
    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction
        from .node_runner import NodeRunResult
        from datetime import datetime

        ledger_tx = LedgerTransaction(state["task_id"])
        task_state = ledger_tx.load_state()
        manifest = ledger_tx.load_manifest()
        nodes = load_nodes()

        scores: list[dict] = []
        tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}

        for role, info in task_state.get("node_states", {}).items():
            if info.get("status") != "completed":
                continue
            node = nodes.get(role, {})
            skill = node.get("skill_ref", "unknown")
            artifacts = task_state.get("artifact_registry", {})
            artifact_ids = info.get("output_artifact_ids", [])

            # ── Scoring dimensions ──
            total = 0
            reasons: list[str] = []

            # 1. Artifact count (0-2 pts)
            artifact_count = len(artifact_ids)
            if artifact_count >= 2:
                total += 2; reasons.append("multiple artifacts")
            elif artifact_count == 1:
                total += 1; reasons.append("single artifact")
            else:
                reasons.append("no artifacts produced")

            # 2. Artifact size (0-2 pts)
            max_size = 0
            for aid in artifact_ids:
                art = artifacts.get(aid, {})
                ref = art.get("content_ref", "")
                if ref:
                    try:
                        artifact_path = ROOT_DIR / "traces" / state["task_id"] / ref
                        sz = artifact_path.stat().st_size
                        max_size = max(max_size, sz)
                    except Exception:
                        pass
            if max_size > 5000:
                total += 2; reasons.append(f"substantial output ({max_size}B)")
            elif max_size > 1000:
                total += 1; reasons.append(f"adequate output ({max_size}B)")
            else:
                reasons.append(f"thin output ({max_size}B)")

            # 3. Context report validity (0-2 pts)
            reports = task_state.get("context_compression_reports", {})
            report = reports.get(role, {})
            if report.get("status") == "valid":
                total += 2; reasons.append("valid context report")
            elif report:
                total += 1; reasons.append("context report present")
            else:
                reasons.append("no context report")

            # 4. Execution time (0-1 pts)
            elapsed = 0
            if info.get("activated_at") and info.get("completed_at"):
                try:
                    start_t = datetime.fromisoformat(str(info["activated_at"]).replace("Z", "+00:00"))
                    end_t = datetime.fromisoformat(str(info["completed_at"]).replace("Z", "+00:00"))
                    elapsed = (end_t - start_t).total_seconds()
                except Exception:
                    pass
            if elapsed > 0 and elapsed < 120:
                total += 1; reasons.append(f"fast ({elapsed:.0f}s)")
            elif elapsed >= 120:
                reasons.append(f"slow ({elapsed:.0f}s)")

            # 5. Skill-source quality adjustment
            skill_source = node.get("skill_source", "")
            source_bonus = 0
            if "claude-skills" in skill_source:
                source_bonus = 1; reasons.append("validated skill source")
            total += source_bonus

            # ── Tier calculation (max 7 pts) ──
            if total >= 6:
                tier = "A"
            elif total >= 4:
                tier = "B"
            elif total >= 2:
                tier = "C"
            else:
                tier = "D"
            tier_counts[tier] += 1

            scores.append({
                "role": role,
                "skill": skill,
                "score": total,
                "tier": tier,
                "artifact_count": artifact_count,
                "max_artifact_size": max_size,
                "elapsed_s": int(elapsed),
                "reasons": reasons,
            })

        # Sort by score descending
        scores.sort(key=lambda s: -s["score"])
        score_lines = [
            f"| {'Role':25s} | {'Skill':30s} | Score | Tier | {'Artifacts':>4} | {'Size':>6} | {'Time':>6} |",
            f"|{'':-^27}|{'':-^32}|{'':-^8}|{'':-^7}|{'':-^11}|{'':-^8}|{'':-^8}|"
        ]
        for s in scores:
            score_lines.append(
                f"| {s['role']:25s} | {s['skill']:30s} |   {s['score']}   |  {s['tier']}  |"
                f"    {s['artifact_count']}    | {s['max_artifact_size']:6d} | {s['elapsed_s']:5d}s |"
            )

        detail_lines = []
        for s in scores:
            if s["tier"] in ("C", "D"):
                detail_lines.append(f"- **{s['role']}** [{s['tier']}]: skill={s['skill']}, issues={s['reasons']}")
        if not detail_lines:
            detail_lines.append("- No underperforming roles detected.")

        # Recommendations
        recs = []
        if tier_counts["D"] > 0:
            recs.append(f"**CRITICAL**: {tier_counts['D']} role(s) at tier D — immediate skill replacement required.")
        if tier_counts["C"] > 0:
            recs.append(f"**WATCH**: {tier_counts['C']} role(s) at tier C — monitor next run; consider alternative skills.")
        if tier_counts["A"] + tier_counts["B"] == len(scores):
            recs.append("No replacement recommendations at this time — all roles B+.")
        recs.append(f"Distribution: A={tier_counts['A']} B={tier_counts['B']} C={tier_counts['C']} D={tier_counts['D']}")

        body = "\n".join([
            "# HRBP Talent Evaluation",
            "",
            f"- task_id: `{state.get('task_id')}`",
            f"- roles_evaluated: {len(scores)}",
            "",
            "## Score Table",
            "",
        ] + score_lines + ["", "## Underperformers", ""] + detail_lines + ["", "## Recommendations", ""] + recs)

        commit = ledger_tx.commit_role_result(NodeRunResult(
            role="hrbp",
            artifact_type="talent-evaluation",
            artifact_body=body + "\n",
            artifact_extension="md",
            metadata={"runner": "runtime_hrbp_review"},
        ))
        ledger_events.append({
            "role": "hrbp",
            "artifact_id": commit.artifact_id,
            "artifact_ref": commit.artifact_ref,
            "status": commit.status,
        })
    return {
        "hrbp_status": "completed",
        "ledger_events": ledger_events,
    }


def learning_engine_node(state: OrgRunState) -> OrgRunState:
    """Apply conservative learning updates to relation weights after topologist review."""

    ledger_events: list[dict[str, Any]] = []
    if state.get("ledger_mode") == "write":
        from .ledger_transactions import LedgerTransaction

        ledger_tx = LedgerTransaction(state["task_id"])
        commit = ledger_tx.commit_learning_snapshot()
        ledger_events.append({
            "type": "learning_snapshot",
            "ref": commit.ref,
            "role_signal_count": commit.role_signal_count,
            "relation_signal_count": commit.relation_signal_count,
            "proposal_count": commit.proposal_count,
        })

        # ── Apply learning: update relation weights in ontology/relations.yaml ──
        _apply_learning_to_weights(state["task_id"])

        # ── Thompson Sampling: Bayesian update on weight matrix ──
        if state.get("use_thompson_sampling"):
            thompson_bayesian_update(state["task_id"])

    return {
        "learning_status": "completed",
        "ledger_events": ledger_events,
    }


def _apply_learning_to_weights(task_id: str) -> None:
    """Update relation weights from trace evidence. Conservative Bayesian update."""
    manifest_path = ROOT_DIR / "traces" / task_id / "manifest.yaml"
    if not manifest_path.exists():
        return
    import yaml
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    relations_data = yaml.safe_load(RELATIONS_PATH.read_text(encoding="utf-8"))
    relations = relations_data.get("relations", [])
    handoff_trail = manifest.get("handoff_trail", [])

    # Build index of activated edge keys
    activated: set[tuple] = set()
    for h in handoff_trail:
        activated.add((h.get("from"), h.get("to"), h.get("relation_type")))

    changed = 0
    for rel in relations:
        edge_key = (rel.get("from"), rel.get("to"), rel.get("type"))
        weights = rel.get("weights", {})

        for dim_name in ("probability", "necessity", "strictness", "synergy", "strength"):
            dim = weights.get(dim_name)
            if not isinstance(dim, dict):
                continue
            old_samples = int(dim.get("samples", 0))
            old_confidence = float(dim.get("confidence", 0.10))

            evidence = 0.75 if edge_key in activated else 0.15
            new_samples = old_samples + 1
            new_confidence = round(
                (old_confidence * old_samples + evidence) / new_samples, 4
            )
            # If activated multiple times, edge becomes more reliable
            if edge_key in activated and old_samples >= 2:
                dim["value"] = min(1.0, round(float(dim.get("value", 0.5)) + 0.02, 2))
            dim["samples"] = new_samples
            dim["confidence"] = new_confidence
            changed += 1

    if changed:
        RELATIONS_PATH.write_text(
            yaml.dump(relations_data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )


def compile_native_runtime(checkpointer: Any | None = None) -> Any:
    """Compile the terminal LangGraph-native runtime.

    The graph topology is intentionally small and stable. Silicon Org topology
    remains in ontology/relations.yaml and is traversed dynamically by Policy.
    """

    issues = validate_full_node_mapping()
    if issues:
        raise ValueError("invalid harness mapping:\n- " + "\n- ".join(issues))

    imports = _imports()
    state_graph = imports["StateGraph"]
    start = imports["START"]
    end = imports["END"]

    graph = state_graph(OrgRunState)
    graph.add_node("encoder", encoder_node)
    graph.add_node("policy_router", policy_router_node)
    graph.add_node("run_role_node", run_role_node)
    graph.add_node("convergence_policy", convergence_policy_node)
    graph.add_node("graph_topologist_node", graph_topologist_node)
    graph.add_node("hrbp_node", hrbp_node)
    graph.add_node("learning_engine_node", learning_engine_node)

    graph.add_edge(start, "encoder")
    graph.add_edge("encoder", "policy_router")
    graph.add_conditional_edges("policy_router", route_policy_candidates)
    graph.add_edge("run_role_node", "policy_router")
    graph.add_conditional_edges(
        "convergence_policy",
        route_after_convergence,
        {
            "policy_router": "policy_router",
            "graph_topologist_node": "graph_topologist_node",
        },
    )
    graph.add_edge("graph_topologist_node", "hrbp_node")
    graph.add_edge("hrbp_node", "learning_engine_node")
    graph.add_edge("learning_engine_node", end)
    return graph.compile(checkpointer=checkpointer)


def native_runtime_status() -> dict[str, Any]:
    nodes = load_nodes()
    profiles = load_harness_profiles()
    resolved_models = {
        role: resolve_model_for_role(role)
        for role in sorted(profiles)
    }
    return {
        "schema": "silicon_org.langgraph_native_runtime.status.v1",
        "mode": "langgraph_native",
        "ontology_nodes": len(nodes),
        "harness_profiles": len(profiles),
        "mapping_issues": validate_full_node_mapping(),
        "model_routing": {
            role: {
                "model_profile": selection.model_profile,
                "runner_pool": selection.runner_pool,
                "provider": selection.provider,
                "model": selection.model,
                "reasoning_effort": selection.reasoning_effort,
                "source": selection.source,
            }
            for role, selection in resolved_models.items()
        },
        "langgraph_topology": [
            "encoder",
            "policy_router",
            "run_role_node",
            "convergence_policy",
            "graph_topologist_node",
            "learning_engine_node",
        ],
        "silicon_topology_source": "ontology/relations.yaml",
        "relation_weight_owner": "Silicon Policy, not LangGraph static edges",
        "oss_only": {
            "allowed": "local MIT-licensed LangGraph OSS packages",
            "forbidden": [
                "LangGraph Platform",
                "LangSmith hosted tracing",
                "LangChain hosted tracing",
                "remote LangGraph API execution",
            ],
            "configured_service_vars": configured_commercial_service_vars(),
        },
    }
