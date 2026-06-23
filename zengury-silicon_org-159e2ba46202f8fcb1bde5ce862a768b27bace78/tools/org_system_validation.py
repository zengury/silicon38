#!/usr/bin/env python3
"""Validate Silicon Org behavior after LangGraph-native runtime integration.

This is an organization-level release check. It does not test LangGraph as a
library; it tests whether Silicon Org can use the runtime to propagate a real
multi-domain product task through Graph, Policy, Ledger, runners, Topologist,
and Learning without corrupting the task trace.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
TASK_ID = "task-robot-fleet-org-system-validation"
TRACE_DIR = ROOT / "traces" / TASK_ID
PRODUCT_TASK = (
    "Design and implement a Web operations monitoring panel for a fleet of humanoid robots. "
    "It must show real-time battery, joint temperature, CPU, network latency, task and location; "
    "normalize inconsistent JSON/protobuf-derived telemetry; show fleet health dashboards with "
    "donut, line and heatmap views; alert on fall, joint disconnect and low battery; show 30-day "
    "history; provide per-robot threshold, sampling and reconnect configuration; support engineer "
    "comments, mentions and claimed handling; export PDF and Excel reports; support dark/light "
    "theme, multilingual UI and draggable layouts."
)
REQUIRED_ROLES = {
    "triage",
    "caveman",
    "to-prd",
    "diagnose",
    "architect",
    "to-issues",
    "tdd",
    "code-reviewer",
    "senior-engineer",
    "devops-engineer",
    "security-engineer",
    "release-manager",
    "senior-frontend",
    "api-designer",
    "observability-engineer",
    "ux-researcher-designer",
    "graph-topologist",
}
FORBIDDEN_SERVICE_ENV = {
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


def fail(message: str) -> None:
    raise AssertionError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing file: {path.relative_to(ROOT)}")
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        fail(f"expected YAML mapping: {path.relative_to(ROOT)}")
    return data


def run_org_task() -> None:
    if TRACE_DIR.exists():
        shutil.rmtree(TRACE_DIR)
    env = {key: value for key, value in os.environ.items() if key not in FORBIDDEN_SERVICE_ENV}
    command = [
        sys.executable,
        "tools/langgraph_run.py",
        "--task-id",
        TASK_ID,
        "--task-type",
        "product_delivery",
        "--description",
        PRODUCT_TASK,
        "--entry-roles",
        "triage,caveman",
        "--runner-mode",
        "external_command",
        "--external-runner-command",
        f"{sys.executable} tools/local_node_executor.py",
        "--max-role-executions",
        "18",
        "--max-parallel-dispatch",
        "3",
        "--activation-threshold",
        "0.5",
        "--replace",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)


def validate_trace() -> dict[str, Any]:
    manifest = load_yaml(TRACE_DIR / "manifest.yaml")
    state = load_yaml(TRACE_DIR / "state.yaml")
    events = load_yaml(TRACE_DIR / "events.yaml")
    learning = load_yaml(TRACE_DIR / "learning.yaml")

    node_states = state.get("node_states") or {}
    completed_roles = {
        role for role, node_state in node_states.items()
        if node_state.get("status") == "completed"
    }
    missing = sorted(REQUIRED_ROLES - completed_roles)
    if missing:
        fail(f"system validation missed required organization roles: {missing}")

    terminal_nodes = manifest.get("terminal_nodes") or []
    duplicates = sorted({role for role in terminal_nodes if terminal_nodes.count(role) > 1})
    if duplicates:
        fail(f"duplicate terminal role completions: {duplicates}")

    artifact_registry = state.get("artifact_registry") or {}
    context_reports = state.get("context_compression_reports") or {}
    handoffs = manifest.get("handoff_trail") or []
    activation_events = [
        event for event in events.get("events", [])
        if event.get("event_type") == "activation_decision"
    ]
    if len(artifact_registry) < 18:
        fail(f"expected broad artifact production, got {len(artifact_registry)}")
    if len(context_reports) < 18:
        fail(f"expected context reports for completed roles, got {len(context_reports)}")
    if len(handoffs) < 14:
        fail(f"expected multi-wave handoff trail, got {len(handoffs)}")
    if len(activation_events) < 18:
        fail(f"expected weighted activation/defer decisions, got {len(activation_events)}")
    if (manifest.get("outcome") or {}).get("status") != "partial":
        fail("expected explicit partial outcome at max_role_executions release bound")

    role_signals = learning.get("role_signals") or []
    relation_signals = learning.get("relation_signals") or []
    proposals = learning.get("proposals") or []
    if len(role_signals) < len(completed_roles):
        fail("learning did not produce role signals for the completed organization")
    if len(relation_signals) < len(handoffs):
        fail("learning did not produce relation signals for the handoff trail")
    if not proposals:
        fail("learning produced no topology/policy proposals from the run")

    return {
        "task_id": TASK_ID,
        "completed_roles": sorted(completed_roles),
        "artifact_count": len(artifact_registry),
        "context_report_count": len(context_reports),
        "handoff_count": len(handoffs),
        "activation_decision_count": len(activation_events),
        "learning_proposal_count": len(proposals),
        "outcome": manifest.get("outcome"),
    }


def main() -> int:
    run_org_task()
    summary = validate_trace()
    if os.environ.get("SILICON_ORG_KEEP_SYSTEM_TRACE") != "1":
        shutil.rmtree(TRACE_DIR)
    print(yaml.dump({"ok": True, **summary}, sort_keys=False, allow_unicode=True).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
