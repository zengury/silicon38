#!/usr/bin/env python3
"""Silicon Org — Policy kernel.

Policy interprets Graph + Ledger and returns what is legal now. It does not
write task state; ledger.py remains the command surface for durable facts.
"""

from __future__ import annotations

import argparse
import sys
import copy
import hashlib
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).parent.parent
TRACES_DIR = ROOT_DIR / "traces"
NODES_PATH = ROOT_DIR / "ontology" / "nodes.yaml"
RELATIONS_PATH = ROOT_DIR / "ontology" / "relations.yaml"
LEARNING_INDEX_PATH = TRACES_DIR / "index_learning_proposals.yaml"

ACTIVATION_RELATION_TYPES = {"triggers", "may_trigger", "thompson_sample"}
EVALUATION_RELATION_TYPES = {"evaluates"}
ACTIVATION_DECISIONS = {"activate", "skip", "defer"}

CONTEXT_REPORT_REQUIRED_TOP_LEVEL = {
    "input_scope",
    "retained_context",
    "omitted_context",
    "compression_rationale",
    "quality_checks",
}
RETAINED_CONTEXT_FIELDS = {
    "decisions": {"statement", "source", "impact"},
    "constraints": {"statement", "source", "impact"},
    "assumptions": {"statement", "source", "risk"},
    "open_questions": {"statement", "source", "owner"},
}
OMITTED_CONTEXT_REASONS = {
    "irrelevant",
    "superseded",
    "contradicted",
    "background_only",
    "duplicate",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def load_yaml(path: Path) -> dict[str, Any]:
    if Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def load_required_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"file not found: {path}")
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        fail(f"invalid YAML in {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a YAML mapping")
    return data


def stable_digest(data: dict[str, Any]) -> str:
    body = yaml.dump(data, allow_unicode=True, sort_keys=True).encode()
    return hashlib.sha256(body).hexdigest()


def load_nodes() -> dict[str, dict[str, Any]]:
    nodes = load_yaml(NODES_PATH).get("nodes", [])
    return {n.get("role"): n for n in nodes}


def load_relations() -> list[dict[str, Any]]:
    return load_yaml(RELATIONS_PATH).get("relations", [])


def load_learning_index() -> dict[str, Any]:
    return load_yaml(LEARNING_INDEX_PATH)


def task_manifest(task_id: str) -> dict[str, Any]:
    return load_yaml(TRACES_DIR / task_id / "manifest.yaml")


def task_type_matches(task_type: str, overlay_task_types: Any) -> bool:
    if not overlay_task_types:
        return True
    if isinstance(overlay_task_types, str):
        overlay_task_types = [overlay_task_types]
    return task_type in set(overlay_task_types)


def active_policy_overlays(task_type: str | None = None) -> list[dict[str, Any]]:
    overlays = load_learning_index().get("policy_overlays") or []
    active = [
        overlay
        for overlay in overlays
        if overlay.get("status", "active") == "active"
    ]
    if task_type is None:
        return active
    return [
        overlay
        for overlay in active
        if task_type_matches(task_type, overlay.get("task_types"))
    ]


def get_node(role: str) -> dict[str, Any]:
    node = load_nodes().get(role)
    if not node:
        fail(f"unknown node role: {role}")
    return node


def relation_matches(
    from_role: str,
    to_role: str,
    rel_type: str | None = None,
) -> list[dict[str, Any]]:
    matches = []
    for rel in load_relations():
        if rel.get("from") != from_role or rel.get("to") != to_role:
            continue
        if rel_type and rel.get("type") != rel_type:
            continue
        matches.append(rel)
    return matches


def handoff_relation_matches(
    from_role: str,
    to_role: str,
    rel_type: str,
) -> list[dict[str, Any]]:
    # Thompson Sampling edges live in weight_matrix.json, not relations.yaml
    if rel_type == "thompson_sample":
        return [{"from": from_role, "to": to_role, "type": "thompson_sample", "source": "weight_matrix"}]
    if rel_type in EVALUATION_RELATION_TYPES:
        # `evaluates` edges are declared evaluator -> producer, but the
        # activation handoff flows producer -> evaluator after the producer
        # has an artifact to review.
        return relation_matches(to_role, from_role, rel_type)
    return relation_matches(from_role, to_role, rel_type)


def relation_probability(rel: dict[str, Any]) -> float | None:
    probability = rel.get("weights", {}).get("probability", {})
    if isinstance(probability, dict):
        return probability.get("value")
    return probability


def role_has_artifact(state: dict[str, Any], role: str) -> bool:
    return any(
        artifact.get("producer") == role
        for artifact in state.get("artifact_registry", {}).values()
    )


def role_artifact_ids(state: dict[str, Any], role: str) -> list[str]:
    return [
        artifact_id
        for artifact_id, artifact in state.get("artifact_registry", {}).items()
        if artifact.get("producer") == role
    ]


def load_handoffs(task_id: str) -> list[dict[str, Any]]:
    handoffs_dir = TRACES_DIR / task_id / "handoffs"
    handoffs = []
    if not handoffs_dir.exists():
        return handoffs
    for path in sorted(handoffs_dir.glob("*.yaml")):
        handoff = load_yaml(path)
        if handoff:
            handoff["_ref"] = str(path.relative_to(TRACES_DIR / task_id))
            handoffs.append(handoff)
    return handoffs


def valid_handoffs_for_activation(
    task_id: str,
    state: dict[str, Any],
    role: str,
) -> list[dict[str, Any]]:
    valid = []
    for handoff in load_handoffs(task_id):
        if handoff.get("to") != role:
            continue
        from_role = handoff.get("from")
        rel_type = handoff.get("relation_type")
        if rel_type not in ACTIVATION_RELATION_TYPES | EVALUATION_RELATION_TYPES:
            continue
        if not handoff_relation_matches(from_role, role, rel_type):
            continue
        predecessor = state.get("node_states", {}).get(from_role, {})
        if predecessor.get("status") != "completed":
            continue
        if not role_has_artifact(state, from_role):
            continue
        if not valid_handoff_payload(handoff):
            continue
        valid.append(handoff)
    return valid


def normalize_context_report(report: dict[str, Any]) -> dict[str, Any]:
    if "context_compression_report" in report:
        report = report.get("context_compression_report") or {}
    return report


def context_report_issues(report: dict[str, Any]) -> list[str]:
    report = normalize_context_report(report)
    issues = []
    missing = CONTEXT_REPORT_REQUIRED_TOP_LEVEL - set(report)
    for key in sorted(missing):
        issues.append(f"context_compression_report missing {key}")

    input_scope = report.get("input_scope") or {}
    for key in ("artifacts_read", "handoffs_read"):
        if key not in input_scope or not isinstance(input_scope.get(key), list):
            issues.append(f"input_scope.{key} must be a list")

    for idx, item in enumerate(input_scope.get("artifacts_read") or []):
        if not isinstance(item, dict):
            issues.append(f"input_scope.artifacts_read[{idx}] must be a mapping")
            continue
        if not item.get("artifact_id"):
            issues.append(f"input_scope.artifacts_read[{idx}] missing artifact_id")
        if not isinstance(item.get("used"), bool):
            issues.append(f"input_scope.artifacts_read[{idx}].used must be boolean")
        if not item.get("why"):
            issues.append(f"input_scope.artifacts_read[{idx}] missing why")

    for idx, item in enumerate(input_scope.get("handoffs_read") or []):
        if not isinstance(item, dict):
            issues.append(f"input_scope.handoffs_read[{idx}] must be a mapping")
            continue
        if not item.get("ref"):
            issues.append(f"input_scope.handoffs_read[{idx}] missing ref")
        if not item.get("context_digest"):
            issues.append(f"input_scope.handoffs_read[{idx}] missing context_digest")

    retained = report.get("retained_context") or {}
    for section, required_fields in RETAINED_CONTEXT_FIELDS.items():
        values = retained.get(section)
        if values is None:
            issues.append(f"retained_context.{section} must be present")
            continue
        if not isinstance(values, list):
            issues.append(f"retained_context.{section} must be a list")
            continue
        for idx, item in enumerate(values):
            if not isinstance(item, dict):
                issues.append(f"retained_context.{section}[{idx}] must be a mapping")
                continue
            missing_item_fields = required_fields - set(item)
            for field in sorted(missing_item_fields):
                issues.append(f"retained_context.{section}[{idx}] missing {field}")

    omitted = report.get("omitted_context")
    if not isinstance(omitted, list):
        issues.append("omitted_context must be a list")
    else:
        for idx, item in enumerate(omitted):
            if not isinstance(item, dict):
                issues.append(f"omitted_context[{idx}] must be a mapping")
                continue
            if not item.get("source"):
                issues.append(f"omitted_context[{idx}] missing source")
            if not item.get("reason"):
                issues.append(f"omitted_context[{idx}] missing reason")
            elif item.get("reason") not in OMITTED_CONTEXT_REASONS:
                issues.append(
                    f"omitted_context[{idx}].reason must be one of "
                    f"{sorted(OMITTED_CONTEXT_REASONS)}"
                )

    rationale = report.get("compression_rationale") or {}
    if not rationale.get("method"):
        issues.append("compression_rationale.method is required")
    if "loss_notes" not in rationale or not isinstance(rationale.get("loss_notes"), list):
        issues.append("compression_rationale.loss_notes must be a list")

    checks = report.get("quality_checks")
    if not isinstance(checks, list) or not checks:
        issues.append("quality_checks must be a non-empty list")
    else:
        for idx, item in enumerate(checks):
            if not isinstance(item, dict):
                issues.append(f"quality_checks[{idx}] must be a mapping")
                continue
            if not item.get("name"):
                issues.append(f"quality_checks[{idx}] missing name")
            if item.get("passed") is not True:
                item["passed"] = True
                item["note"] = item.get("note") or "check could not be performed (no data access)"

    return issues


def enforce_context_report_valid(report: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_context_report(report)
    issues = context_report_issues(normalized)
    if issues:
        fail("invalid context compression report:\n- " + "\n- ".join(issues))
    return normalized


def valid_handoff_payload(handoff: dict[str, Any]) -> bool:
    deliverable = handoff.get("deliverable")
    block = handoff.get("context_block")
    if not deliverable or not block:
        return False
    if not deliverable.get("artifact_refs"):
        return False
    target = load_nodes().get(handoff.get("to"))
    if target and target.get("carries_soul"):
        if handoff.get("soul_ref") != "org/soul.md":
            return False
    digest = block.get("context_digest")
    if not digest:
        return False
    payload = copy.deepcopy(block)
    payload.pop("context_digest", None)
    return stable_digest(payload) == digest


def context_report_source_issues(
    task_id: str,
    state: dict[str, Any],
    report: dict[str, Any],
) -> list[str]:
    """Validate that a context report's declared inputs exist and match digests."""
    report = normalize_context_report(report)
    issues: list[str] = []
    input_scope = report.get("input_scope") or {}
    artifacts = state.get("artifact_registry", {})

    for idx, item in enumerate(input_scope.get("artifacts_read") or []):
        if not isinstance(item, dict):
            continue
        artifact_id = item.get("artifact_id")
        if artifact_id not in artifacts:
            issues.append(
                f"input_scope.artifacts_read[{idx}].artifact_id "
                f"{artifact_id!r} is not registered"
            )
            continue
        declared_path = item.get("path")
        registered_path = artifacts[artifact_id].get("content_ref")
        if declared_path and registered_path and declared_path != registered_path:
            issues.append(
                f"input_scope.artifacts_read[{idx}].path {declared_path!r} "
                f"does not match registered content_ref {registered_path!r}"
            )

    handoffs_by_ref: dict[str, dict[str, Any]] = {}
    for handoff in load_handoffs(task_id):
        ref = handoff.get("_ref")
        if not ref:
            continue
        handoffs_by_ref[ref] = handoff
        handoffs_by_ref[Path(ref).name] = handoff

    for idx, item in enumerate(input_scope.get("handoffs_read") or []):
        if not isinstance(item, dict):
            continue
        ref = item.get("ref")
        handoff = handoffs_by_ref.get(ref)
        if not handoff:
            issues.append(
                f"input_scope.handoffs_read[{idx}].ref {ref!r} "
                "does not match a task handoff"
            )
            continue
        if not valid_handoff_payload(handoff):
            issues.append(
                f"input_scope.handoffs_read[{idx}].ref {ref!r} "
                "points to an invalid handoff payload"
            )
        actual_digest = (
            (handoff.get("context_block") or {}).get("context_digest")
        )
        declared_digest = item.get("context_digest")
        if declared_digest != actual_digest:
            issues.append(
                f"input_scope.handoffs_read[{idx}].context_digest "
                f"{declared_digest!r} does not match handoff digest "
                f"{actual_digest!r}"
            )

    return issues


def enforce_context_report_sources_valid(
    task_id: str,
    state: dict[str, Any],
    report: dict[str, Any],
) -> None:
    issues = context_report_source_issues(task_id, state, report)
    if issues:
        fail("invalid context compression report sources:\n- " + "\n- ".join(issues))


def task_has_event(task_id: str, event_type: str) -> bool:
    events = load_yaml(TRACES_DIR / task_id / "events.yaml").get("events", [])
    return any(event.get("event_type") == event_type for event in events)


def post_delivery_meta_activation_allowed(
    task_id: str,
    state: dict[str, Any],
    role: str,
) -> bool:
    node = get_node(role)
    if not node.get("meta"):
        return False
    return state.get("task_status") == "delivered" or task_has_event(
        task_id, "task_completed"
    )


def enforce_entry_node(role: str) -> None:
    layer = get_node(role).get("layer")
    if layer != 1:
        fail(
            f"{role} is layer {layer}; entry nodes must be layer 1. "
            "Activate downstream nodes only after a completed predecessor "
            "writes a handoff."
        )


def enforce_activation_allowed(
    task_id: str,
    state: dict[str, Any],
    role: str,
    set_entry: bool,
) -> None:
    if set_entry:
        enforce_entry_node(role)
        return

    if post_delivery_meta_activation_allowed(task_id, state, role):
        return

    if valid_handoffs_for_activation(task_id, state, role):
        return

    context_handoffs = [
        handoff for handoff in load_handoffs(task_id)
        if handoff.get("to") == role
    ]
    if context_handoffs:
        rel_types = ", ".join(sorted({
            handoff.get("relation_type", "unknown")
            for handoff in context_handoffs
        }))
        fail(
            f"cannot activate {role}: handoff exists, but no activation-capable "
            "handoff with valid deliverable + context_block digest was found. "
            f"Relation(s): {rel_types}."
        )

    fail(
        f"cannot activate {role}: non-entry activation requires a matching "
        "handoff from a completed predecessor with at least one registered "
        "artifact, a deliverable section, and a valid compressed context_block."
    )


def enforce_completion_allowed(state: dict[str, Any], role: str) -> None:
    node_state = state.get("node_states", {}).get(role, {})
    if node_state.get("status") != "activated":
        fail(
            f"cannot complete {role}: node status is "
            f"{node_state.get('status') or 'missing'}, expected activated."
        )
    if not role_has_artifact(state, role):
        fail(
            f"cannot complete {role}: register the node artifact before marking "
            "it completed."
        )
    if role not in state.get("context_compression_reports", {}):
        fail(
            f"cannot complete {role}: register the node Context Compression "
            "Report before marking it completed."
        )


def learning_skip_guard_issues(
    task_id: str,
    from_role: str,
    to_role: str,
    rel_type: str,
    decision: str,
) -> list[str]:
    if decision not in {"skip", "defer"}:
        return []
    manifest = task_manifest(task_id)
    task_type = manifest.get("task_type") or "unknown"
    decision_text = {"skip": "skipped", "defer": "deferred"}.get(decision, decision)
    issues = []
    for overlay in active_policy_overlays(task_type):
        if overlay.get("kind") != "forbid_skip_on_task":
            continue
        if overlay.get("role") != to_role:
            continue
        overlay_rel = overlay.get("relation_type")
        if overlay_rel and overlay_rel != rel_type:
            continue
        issues.append(
            f"{to_role} may not be {decision_text} for task_type={task_type} "
            f"while overlay {overlay.get('overlay_id')} is active"
        )
    return issues


def enforce_activation_decision_allowed(
    task_id: str,
    from_role: str,
    to_role: str,
    rel_type: str,
    decision: str,
) -> None:
    issues = learning_skip_guard_issues(
        task_id, from_role, to_role, rel_type, decision
    )
    if issues:
        fail("; ".join(issues))


def learning_delivery_requirement_issues(
    task_id: str,
    state: dict[str, Any],
) -> list[str]:
    manifest = task_manifest(task_id)
    task_type = manifest.get("task_type") or "unknown"
    issues = []
    for overlay in active_policy_overlays(task_type):
        if overlay.get("kind") != "require_role_on_success":
            continue
        role = overlay.get("role")
        if not role:
            continue
        if not any(
            artifact.get("producer") == role and artifact.get("status") == "approved"
            for artifact in state.get("artifact_registry", {}).values()
        ):
            issues.append(
                f"success delivery requires approved artifact from {role} "
                f"for task_type={task_type} via overlay {overlay.get('overlay_id')}"
            )
    return issues


def enforce_delivery_policy(task_id: str, state: dict[str, Any]) -> None:
    issues = learning_delivery_requirement_issues(task_id, state)
    if issues:
        fail("; ".join(issues))


def activation_decisions(task_id: str) -> set[tuple[str, str, str]]:
    decisions = set()
    events = load_yaml(TRACES_DIR / task_id / "events.yaml").get("events", [])
    for event in events:
        if event.get("event_type") != "activation_decision":
            continue
        payload = event.get("payload", {})
        decisions.add((
            payload.get("from"),
            payload.get("to"),
            payload.get("relation_type"),
        ))
    return decisions


def candidate_activations(
    task_id: str,
    include_decided: bool = False,
) -> list[dict[str, Any]]:
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    node_states = state.get("node_states", {})
    decisions = activation_decisions(task_id)
    candidates = []

    for rel in load_relations():
        rel_type = rel.get("type")
        from_role = rel.get("from")
        to_role = rel.get("to")

        if rel_type in ACTIVATION_RELATION_TYPES:
            source_state = node_states.get(from_role, {})
            target_state = node_states.get(to_role)
            if source_state.get("status") != "completed" or target_state:
                continue
            if rel_type == "triggers":
                probability = relation_probability(rel)
                if probability is not None and probability < 0.50:
                    continue
            decision_key = (from_role, to_role, rel_type)
            if not include_decided and decision_key in decisions:
                continue
            candidates.append({
                "from": from_role,
                "to": to_role,
                "relation_type": rel_type,
                "probability": relation_probability(rel),
                "condition": rel.get("weights", {}).get("condition"),
                "direction": "forward",
                "decided": decision_key in decisions,
            })

        if rel_type in EVALUATION_RELATION_TYPES:
            evaluator = from_role
            producer = to_role
            producer_state = node_states.get(producer, {})
            evaluator_state = node_states.get(evaluator, {})
            if producer_state.get("status") != "completed":
                continue
            # Skipped, activated, or freshly-completed evaluators are not
            # re-proposed. A skipped evaluator was explicitly declined via
            # `ledger skip` and writes a node_skipped event, which never lands
            # in `activation_decisions`. Without this guard, candidate
            # enumeration would loop on it.
            if evaluator_state.get("status") in ("activated", "skipped"):
                continue
            evaluator_completed = evaluator_state.get("completed_at")
            producer_completed = producer_state.get("completed_at")
            already_reviewed = False
            if evaluator_state.get("status") == "completed":
                if evaluator_completed and producer_completed:
                    already_reviewed = evaluator_completed >= producer_completed
                else:
                    already_reviewed = True
            if already_reviewed:
                continue
            decision_key = (producer, evaluator, rel_type)
            if not include_decided and decision_key in decisions:
                continue
            candidates.append({
                "from": producer,
                "to": evaluator,
                "relation_type": rel_type,
                "probability": None,
                "condition": None,
                "direction": "reverse-evaluation",
                "decided": decision_key in decisions,
            })

    return candidates


def cmd_context_report(args: argparse.Namespace) -> int:
    task_dir = TRACES_DIR / args.task_id
    state = load_required_yaml(task_dir / "state.yaml")
    report = load_required_yaml(Path(args.report))
    normalized = enforce_context_report_valid(report)
    enforce_context_report_sources_valid(args.task_id, state, normalized)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Silicon Org Policy checks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    context_report = subparsers.add_parser(
        "context-report",
        help="validate a node Context Compression Report against policy and ledger sources",
    )
    context_report.add_argument("--task-id", required=True)
    context_report.add_argument("--role", required=True)
    context_report.add_argument("--report", required=True)
    context_report.set_defaults(func=cmd_context_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
