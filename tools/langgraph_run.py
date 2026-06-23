#!/usr/bin/env python3
"""Run Silicon Org through the LangGraph-native runtime.

This is the local executable entrypoint. It does not call hosted LangGraph,
LangSmith, or remote graph APIs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
TRACES_DIR = ROOT / "traces"
sys.path.insert(0, str(ROOT))

from runtime.langgraph_native import compile_native_runtime  # noqa: E402


def default_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"task-langgraph-{stamp}"


def parse_entry_roles(raw: str) -> list[str]:
    return [r.strip() for r in raw.split(",") if r.strip()]


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Silicon Org task with the LangGraph-native runtime."
    )
    parser.add_argument("--task-id", default=default_task_id())
    parser.add_argument("--task-type", default="general")
    parser.add_argument("--task-type-hint", default="")
    parser.add_argument("--description", required=True)
    parser.add_argument("--entry-roles", default="triage")
    parser.add_argument(
        "--runner-mode",
        choices=["harness_dry_run", "prompt_package", "external_command", "semantic_command"],
        default="semantic_command",
    )
    parser.add_argument(
        "--external-runner-command",
        default="",
        help=(
            "Local command used by external_command or semantic_command. "
            "semantic_command defaults to tools/semantic_node_executor.py."
        ),
    )
    parser.add_argument("--max-role-executions", type=int, default=2)
    parser.add_argument("--max-parallel-dispatch", type=int, default=1)
    parser.add_argument("--activation-threshold", type=float, default=0.5)
    parser.add_argument("--recursion-limit", type=int, default=100)
    parser.add_argument("--workspace", default="", help="Target project directory for code-reading nodes.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove an existing trace with the same task id before running.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an interrupted task from ledger state instead of starting fresh.",
    )
    return parser


def build_resume_state(trace_dir: Path) -> dict[str, Any]:
    """Reconstruct LangGraph state from ledger facts for resume."""
    state_yaml = load_yaml(trace_dir / "state.yaml")
    manifest = load_yaml(trace_dir / "manifest.yaml")

    completed_roles: list[str] = []
    active_roles: list[str] = []
    for role, info in state_yaml.get("node_states", {}).items():
        if info.get("status") == "completed":
            completed_roles.append(role)
        elif info.get("status") == "active":
            active_roles.append(role)

    routed_completed = [r for r in completed_roles]
    handoff_trail = manifest.get("handoff_trail", [])

    return {
        "task_id": state_yaml.get("task_id"),
        "task_type": manifest.get("task_type", "general"),
        "task_type_hint": manifest.get("task_type_hint"),
        "task_description": manifest.get("task_summary", ""),
        "workspace_dir": manifest.get("workspace_dir", ""),
        "entry_roles": manifest.get("entry_nodes", []),
        "completed_roles": completed_roles,
        "routed_completed_roles": routed_completed,
        "active_roles": active_roles,
        "routed_entry_roles": completed_roles,
        "ledger_mode": "write",
        "runner_mode": manifest.get("runner_mode", "semantic_command"),
        "external_runner_command": manifest.get("external_runner_command", ""),
        "delivery_status": "pending",
        "topologist_status": "pending",
        "hrbp_status": "pending",
        "learning_status": "pending",
    }


def summarize_trace(task_id: str, result: dict[str, Any]) -> dict[str, Any]:
    trace_dir = TRACES_DIR / task_id
    manifest = load_yaml(trace_dir / "manifest.yaml")
    state = load_yaml(trace_dir / "state.yaml")
    events_yaml = load_yaml(trace_dir / "events.yaml")
    events = events_yaml.get("events", []) if isinstance(events_yaml, dict) else []
    artifact_refs = result.get("artifact_refs", [])
    handoffs_dir = trace_dir / "handoffs"
    handoff_count = len(list(handoffs_dir.glob("*.yaml"))) if handoffs_dir.exists() else 0
    return {
        "ok": True,
        "task_id": task_id,
        "trace": str(trace_dir.relative_to(ROOT)),
        "runner_mode": result.get("runner_mode"),
        "delivery_status": result.get("delivery_status"),
        "manifest_outcome": manifest.get("outcome"),
        "terminal_nodes": manifest.get("terminal_nodes", []),
        "completed_roles": result.get("completed_roles", []),
        "artifact_refs": artifact_refs,
        "artifact_count": len(state.get("artifact_registry", {})),
        "handoff_count": handoff_count,
        "activation_decision_count": len([
            event for event in events
            if isinstance(event, dict) and event.get("event_type") == "activation_decision"
        ]),
        "candidate_backlog_count": len(result.get("candidate_backlog", [])),
        "topologist_status": result.get("topologist_status"),
        "hrbp_status": result.get("hrbp_status"),
        "learning_status": result.get("learning_status"),
        "files": {
            "manifest": str((trace_dir / "manifest.yaml").relative_to(ROOT)),
            "state": str((trace_dir / "state.yaml").relative_to(ROOT)),
            "events": str((trace_dir / "events.yaml").relative_to(ROOT)),
            "learning": (
                str((trace_dir / "learning.yaml").relative_to(ROOT))
                if (trace_dir / "learning.yaml").exists()
                else None
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runner_mode == "external_command" and not args.external_runner_command.strip():
        raise SystemExit("--external-runner-command is required for external_command mode.")

    trace_dir = TRACES_DIR / args.task_id

    # ── Resume path ──
    if args.resume:
        if not trace_dir.exists():
            raise SystemExit(f"trace not found for resume: {trace_dir}")
        initial_state = build_resume_state(trace_dir)
        print(f"Resuming task {args.task_id} with {len(initial_state['completed_roles'])} completed roles: {initial_state['completed_roles']}", flush=True)
    else:
        if trace_dir.exists():
            if not args.replace:
                raise SystemExit(
                    f"trace already exists: {trace_dir}. Use --replace to overwrite it."
                )
            shutil.rmtree(trace_dir)
        initial_state = {
            "task_id": args.task_id,
            "task_type": args.task_type,
            "task_type_hint": args.task_type_hint or None,
            "task_description": args.description,
            "workspace_dir": args.workspace,
            "entry_roles": parse_entry_roles(args.entry_roles),
            "ledger_mode": "write",
            "runner_mode": args.runner_mode,
            "external_runner_command": args.external_runner_command,
            "max_role_executions": args.max_role_executions,
            "max_parallel_dispatch": args.max_parallel_dispatch,
            "activation_threshold": args.activation_threshold,
        }

    graph = compile_native_runtime()
    result = graph.invoke(
        initial_state,
        config={
            "recursion_limit": args.recursion_limit,
            "configurable": {"thread_id": args.task_id},
        },
    )
    print(json.dumps(summarize_trace(args.task_id, result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
