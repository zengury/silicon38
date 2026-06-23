"""Machine-readable learning proposals derived from task traces.

These proposals close part of the Learning -> Policy/Runtime loop without
automatically mutating the graph. A proposal is evidence for review, not law.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


AGGREGATE_MIN_SUPPORT = 2


def _proposal(
    task_id: str,
    task_type: str,
    proposal_type: str,
    severity: str,
    finding: str,
    recommended_action: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    subject = evidence.get("role") or evidence.get("gate") or evidence.get("source")
    return {
        "proposal_key": f"{task_id}:{proposal_type}:{subject}",
        "task_id": task_id,
        "task_type": task_type,
        "type": proposal_type,
        "severity": severity,
        "finding": finding,
        "recommended_action": recommended_action,
        "evidence": evidence,
        "status": "proposed",
        "auto_apply": False,
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def _trace_task_type(task_dir: Path) -> str:
    manifest = _load_yaml(task_dir / "manifest.yaml")
    return manifest.get("task_type") or "unknown"


def _aggregate_proposal(
    proposal_key: str,
    task_type: str,
    proposal_type: str,
    severity: str,
    finding: str,
    recommended_action: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    proposal = _proposal(
        task_id=f"aggregate:{task_type}",
        task_type=task_type,
        proposal_type=proposal_type,
        severity=severity,
        finding=finding,
        recommended_action=recommended_action,
        evidence=evidence,
    )
    proposal["proposal_key"] = proposal_key
    proposal["basis"] = "aggregate"
    return proposal


def trace_learning_proposals(
    task_id: str,
    manifest: dict[str, Any],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return conservative review proposals for one completed task trace."""
    proposals: list[dict[str, Any]] = []
    outcome = manifest.get("outcome") or {}
    quality = outcome.get("quality_signal") or {}
    status = outcome.get("status")
    task_type = manifest.get("task_type") or "unknown"

    if status == "success" and quality.get("source") == "runtime_decoder_unverified":
        proposals.append(_proposal(
            task_id,
            task_type,
            "verification_gap",
            "major",
            "Task was delivered as success without an approved delivery-prover signal.",
            "Require delivery-prover for implementation tasks or downgrade delivery to partial.",
            {
                "task_type": task_type,
                "source": quality.get("source"),
                "quality_value": quality.get("value"),
                "detail": quality.get("detail"),
            },
        ))

    if state.get("task_status") == "delivered":
        for gate, value in (state.get("convergence") or {}).items():
            if gate == "settled_at" or value is True:
                continue
            proposals.append(_proposal(
                task_id,
                task_type,
                "convergence_gate_breach",
                "critical",
                f"Delivered task has unresolved convergence gate: {gate}.",
                "Reject future success delivery until this convergence gate is true.",
                {"task_type": task_type, "gate": gate, "value": value},
            ))

    for role, info in (state.get("node_states") or {}).items():
        if info.get("status") != "skipped":
            continue
        skip_cost = info.get("skip_cost") or {}
        severity = skip_cost.get("severity")
        if severity not in {"warning", "review_required"}:
            continue
        proposals.append(_proposal(
            task_id,
            task_type,
            "skip_policy_review",
            "major" if severity == "review_required" else "minor",
            f"{role} has repeated or high-cost skip behavior.",
            "Review whether this node needs a task-type gate, stronger trigger condition, or mandatory evaluation rule.",
            {
                "task_type": task_type,
                "role": role,
                "skip_reason": info.get("skip_reason"),
                "skip_cost": skip_cost,
            },
        ))

    return proposals


def aggregate_learning_proposals(
    root_dir: Path,
    task_id: str,
    manifest: dict[str, Any],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return cross-trace proposals when a pattern repeats for one task type."""
    proposals: list[dict[str, Any]] = []
    traces_dir = root_dir / "traces"
    task_type = manifest.get("task_type") or "unknown"
    current_outcome = manifest.get("outcome") or {}
    current_quality = current_outcome.get("quality_signal") or {}

    if (
        current_outcome.get("status") == "success"
        and current_quality.get("source") == "runtime_decoder_unverified"
    ):
        support = []
        for task_dir in traces_dir.glob("task-*/"):
            candidate_manifest = _load_yaml(task_dir / "manifest.yaml")
            if (candidate_manifest.get("task_type") or "unknown") != task_type:
                continue
            candidate_outcome = candidate_manifest.get("outcome") or {}
            candidate_quality = candidate_outcome.get("quality_signal") or {}
            if (
                candidate_outcome.get("status") == "success"
                and candidate_quality.get("source") == "runtime_decoder_unverified"
            ):
                support.append(task_dir.name)
        if len(support) >= AGGREGATE_MIN_SUPPORT:
            proposals.append(_aggregate_proposal(
                proposal_key=(
                    f"aggregate:verification_gap_cluster:{task_type}:"
                    "runtime_decoder_unverified"
                ),
                task_type=task_type,
                proposal_type="verification_gap_cluster",
                severity="critical",
                finding=(
                    f"{len(support)} {task_type} task(s) delivered success without "
                    "approved delivery proof."
                ),
                recommended_action=(
                    "Require delivery-prover before success delivery for this "
                    "task type."
                ),
                evidence={
                    "task_type": task_type,
                    "source": "runtime_decoder_unverified",
                    "support_count": len(support),
                    "supporting_task_ids": sorted(support),
                    "trigger_task_id": task_id,
                },
            ))

    breached_gates = [
        gate
        for gate, value in (state.get("convergence") or {}).items()
        if gate != "settled_at" and value is not True and state.get("task_status") == "delivered"
    ]
    for gate in breached_gates:
        support = []
        for task_dir in traces_dir.glob("task-*/"):
            candidate_state = _load_yaml(task_dir / "state.yaml")
            if _trace_task_type(task_dir) != task_type:
                continue
            convergence = candidate_state.get("convergence") or {}
            if candidate_state.get("task_status") == "delivered" and convergence.get(gate) is not True:
                support.append(task_dir.name)
        if len(support) >= AGGREGATE_MIN_SUPPORT:
            proposals.append(_aggregate_proposal(
                proposal_key=f"aggregate:convergence_gate_cluster:{task_type}:{gate}",
                task_type=task_type,
                proposal_type="convergence_gate_cluster",
                severity="critical",
                finding=(
                    f"{len(support)} {task_type} task(s) were delivered with "
                    f"convergence gate {gate} unresolved."
                ),
                recommended_action=(
                    "Reject future success delivery for this task type until "
                    f"{gate} is true."
                ),
                evidence={
                    "task_type": task_type,
                    "gate": gate,
                    "support_count": len(support),
                    "supporting_task_ids": sorted(support),
                    "trigger_task_id": task_id,
                },
            ))

    for role, info in (state.get("node_states") or {}).items():
        if info.get("status") != "skipped":
            continue
        skip_cost = info.get("skip_cost") or {}
        severity = skip_cost.get("severity")
        if severity not in {"warning", "review_required"}:
            continue
        support = []
        for task_dir in traces_dir.glob("task-*/"):
            if _trace_task_type(task_dir) != task_type:
                continue
            candidate_state = _load_yaml(task_dir / "state.yaml")
            candidate_info = (candidate_state.get("node_states") or {}).get(role) or {}
            candidate_skip_cost = candidate_info.get("skip_cost") or {}
            if (
                candidate_info.get("status") == "skipped"
                and candidate_skip_cost.get("severity") in {"warning", "review_required"}
            ):
                support.append(task_dir.name)
        if len(support) >= AGGREGATE_MIN_SUPPORT:
            proposals.append(_aggregate_proposal(
                proposal_key=f"aggregate:skip_policy_cluster:{task_type}:{role}",
                task_type=task_type,
                proposal_type="skip_policy_cluster",
                severity="critical" if severity == "review_required" else "major",
                finding=(
                    f"{role} was repeatedly skipped in {len(support)} {task_type} "
                    "task(s) with non-free skip cost."
                ),
                recommended_action=(
                    "Prevent skip/defer for this evaluator on this task type "
                    "until the graph or harness is adjusted."
                ),
                evidence={
                    "task_type": task_type,
                    "role": role,
                    "support_count": len(support),
                    "supporting_task_ids": sorted(support),
                    "latest_skip_cost": skip_cost,
                    "trigger_task_id": task_id,
                },
            ))

    return proposals
