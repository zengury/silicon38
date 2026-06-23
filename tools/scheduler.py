#!/usr/bin/env python3
"""Silicon Org — Activation Scheduler.

Proposes activations / skips / deferrals for the next wave, based on the
current ledger state and the ontology. Soft suggestion only: Runtime keeps
final say but must register its override via
`ledger.py activation-decision` (which writes an activation_decision event
with the override reason).

Usage:
    python3 tools/scheduler.py propose <task_id>
    python3 tools/scheduler.py propose <task_id> --json
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Reuse Policy's loaders + candidate enumeration so we don't drift from the
# canonical graph semantics. Mirror ledger.py's import style so both tools
# resolve `tools.policy` the same way.
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
from tools import policy  # noqa: E402  (path-managed import)

TRACES_DIR = ROOT_DIR / "traces"

# Suggestion confidence threshold below which a may_trigger becomes a "defer"
# instead of a "propose activate".
ACTIVATE_THRESHOLD = 0.50


@dataclass(frozen=True)
class Suggestion:
    """A single activation suggestion produced by the scheduler.

    `kind` is one of: 'activate' | 'skip' | 'defer'.
    `confidence` is the prior probability (from relations.yaml) for the
    relation that produced this suggestion, or None for evaluator edges.
    """

    kind: str
    from_role: str
    to_role: str
    relation_type: str
    reason: str
    confidence: float | None
    condition: str | None
    decided: bool


def load_task_state(task_id: str) -> dict[str, Any]:
    path = TRACES_DIR / task_id / "state.yaml"
    if not path.exists():
        policy.fail(f"task {task_id} has no state.yaml")
    return policy.load_yaml(path)


def summarize_candidate(candidate: dict[str, Any]) -> Suggestion:
    """Map a raw Policy candidate into a scheduler Suggestion."""
    rel_type = candidate["relation_type"]
    probability = candidate.get("probability")
    condition = candidate.get("condition")
    decided = bool(candidate.get("decided"))
    from_role = candidate["from"]
    to_role = candidate["to"]

    if rel_type == "triggers":
        # `triggers` is always proposed as activate (Policy already filters
        # probability < 0.50 for this type).
        reason = (
            f"triggered by {from_role} (prob {probability:.2f}, latency immediate)"
            if probability is not None
            else f"triggered by {from_role}"
        )
        return Suggestion(
            kind="activate",
            from_role=from_role,
            to_role=to_role,
            relation_type=rel_type,
            reason=reason,
            confidence=probability,
            condition=condition,
            decided=decided,
        )

    if rel_type == "may_trigger":
        # may_trigger fires only if its condition is met. The scheduler cannot
        # evaluate the condition itself — it asks Runtime to check. Above the
        # ACTIVATE_THRESHOLD we propose activate; below we defer.
        if probability is not None and probability >= ACTIVATE_THRESHOLD:
            kind = "activate"
            verb = "may trigger (prob ≥ threshold)"
        else:
            kind = "defer"
            verb = "may trigger (prob < threshold)"
        cond_text = f" condition: {condition}" if condition else ""
        reason = f"{verb} from {from_role}{cond_text}"
        return Suggestion(
            kind=kind,
            from_role=from_role,
            to_role=to_role,
            relation_type=rel_type,
            reason=reason,
            confidence=probability,
            condition=condition,
            decided=decided,
        )

    if rel_type == "evaluates":
        # Reverse-direction: evaluator is `to_role` here. ledger's
        # candidate_activations flips the direction so to_role is the
        # evaluator about to activate.
        reason = f"evaluator {to_role} should review artifact from {from_role}"
        return Suggestion(
            kind="activate",
            from_role=from_role,
            to_role=to_role,
            relation_type=rel_type,
            reason=reason,
            confidence=None,
            condition=None,
            decided=decided,
        )

    # Unknown activation relation type — surface as defer so Runtime
    # investigates instead of silently dropping it.
    return Suggestion(
        kind="defer",
        from_role=from_role,
        to_role=to_role,
        relation_type=rel_type,
        reason=f"unknown activation relation type: {rel_type}",
        confidence=probability,
        condition=condition,
        decided=decided,
    )


def required_gates(state: dict[str, Any]) -> list[str]:
    """Surface required (blocking) evaluations that are still open.

    Looks for `evaluates` relations with `blocking: required` whose producer
    is completed but the evaluator has not yet completed.
    """
    gates: list[str] = []
    node_states = state.get("node_states", {})
    for rel in policy.load_relations():
        if rel.get("type") != "evaluates":
            continue
        blocking = rel.get("weights", {}).get("blocking")
        if isinstance(blocking, dict):
            blocking_value = blocking.get("value")
        else:
            blocking_value = blocking
        if blocking_value != "required":
            continue
        evaluator = rel["from"]
        producer = rel["to"]
        producer_state = node_states.get(producer, {})
        if producer_state.get("status") != "completed":
            continue
        evaluator_state = node_states.get(evaluator, {})
        if evaluator_state.get("status") == "completed":
            evaluator_completed = evaluator_state.get("completed_at")
            producer_completed = producer_state.get("completed_at")
            if (
                evaluator_completed
                and producer_completed
                and evaluator_completed >= producer_completed
            ):
                continue
        gates.append(
            f"{evaluator} (required) must evaluate {producer} before Phase 3"
        )
    return gates


def propose(task_id: str) -> dict[str, Any]:
    state = load_task_state(task_id)
    raw_candidates = policy.candidate_activations(task_id, include_decided=False)
    suggestions = [summarize_candidate(c) for c in raw_candidates]

    return {
        "task_id": task_id,
        "proposed_activations": [
            asdict(s) for s in suggestions if s.kind == "activate"
        ],
        "deferred": [asdict(s) for s in suggestions if s.kind == "defer"],
        # The scheduler never emits 'skip' itself — Runtime owns that
        # judgement (it requires reading the condition text). Reserved for
        # future condition-evaluation logic.
        "proposed_skips": [asdict(s) for s in suggestions if s.kind == "skip"],
        "required_gates_open": required_gates(state),
    }


def render_human(report: dict[str, Any]) -> str:
    lines: list[str] = [f"Scheduler proposal for {report['task_id']}", ""]
    if report["proposed_activations"]:
        lines.append("PROPOSED ACTIVATIONS:")
        for s in report["proposed_activations"]:
            conf = (
                f" p={s['confidence']:.2f}"
                if s["confidence"] is not None
                else ""
            )
            lines.append(
                f"  → {s['to_role']} "
                f"({s['relation_type']} from {s['from_role']}{conf})"
            )
            lines.append(f"      {s['reason']}")
    else:
        lines.append("PROPOSED ACTIVATIONS: (none)")
    lines.append("")
    if report["deferred"]:
        lines.append("DEFERRED (condition-gated or low-confidence):")
        for s in report["deferred"]:
            lines.append(
                f"  · {s['from_role']} → {s['to_role']}  [{s['relation_type']}]"
            )
            lines.append(f"      {s['reason']}")
    else:
        lines.append("DEFERRED: (none)")
    lines.append("")
    if report["required_gates_open"]:
        lines.append("REQUIRED GATES (must clear before Phase 3):")
        for gate in report["required_gates_open"]:
            lines.append(f"  ! {gate}")
    else:
        lines.append("REQUIRED GATES: all clear")
    lines.append("")
    lines.append(
        "Runtime override: `ledger.py activation-decision <task> <from> <to> "
        "<rel_type> <activate|skip|defer> <reason>`"
    )
    return "\n".join(lines)


def cmd_propose(args: list[str]) -> None:
    if not args:
        policy.fail("usage: scheduler.py propose <task_id> [--json]")
    task_id = args[0]
    as_json = "--json" in args
    report = propose(task_id)
    if as_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render_human(report))


COMMANDS = {"propose": cmd_propose}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scheduler.py <command> [args...]")
        print("Commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        print("Available:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
