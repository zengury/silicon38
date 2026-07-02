#!/usr/bin/env python3
"""Smoke-test the Silicon Org LangGraph-native runtime.

This verifies the release-critical contract without invoking hosted services:

- all ontology nodes have harness profiles
- local LangGraph can compile the native runtime
- the post-delivery learning path can execute to END
- policy propagation reads weighted Silicon Graph relations
- hosted/commercial service environment variables are not configured
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runtime.langgraph_native import (  # noqa: E402
    NonOssRuntimeConfigured,
    compile_native_runtime,
    configured_commercial_service_vars,
    native_runtime_status,
    policy_candidates_for_completed_role,
)


def main() -> int:
    configured = configured_commercial_service_vars()
    if configured:
        raise NonOssRuntimeConfigured(
            "Hosted/commercial service variables are configured: " + ", ".join(configured)
        )

    status = native_runtime_status()
    assert status["ontology_nodes"] == 41, status["ontology_nodes"]
    assert status["harness_profiles"] == 41, status["harness_profiles"]
    assert status["mapping_issues"] == [], status["mapping_issues"]

    triage_candidates = policy_candidates_for_completed_role("triage", {"learning_signal": {}})
    assert triage_candidates, "triage should produce weighted activation candidates"
    assert all(candidate["legal"] for candidate in triage_candidates), triage_candidates

    graph = compile_native_runtime()
    post_delivery_result = graph.invoke(
        {
            "task_id": "langgraph-native-smoke",
            "task_type": "bug_fix",
            "task_description": "Validate local LangGraph-native Silicon Org runtime.",
            "completed_roles": [],
            "delivery_status": "success",
        },
        config={"recursion_limit": 20},
    )
    assert post_delivery_result["topologist_status"] == "completed", post_delivery_result
    assert post_delivery_result["learning_status"] == "completed", post_delivery_result

    ledger_task_id = "task-langgraph-native-smoke-ledger"
    ledger_trace = ROOT / "traces" / ledger_task_id
    if ledger_trace.exists():
        shutil.rmtree(ledger_trace)
    ledger_result = graph.invoke(
        {
            "task_id": ledger_task_id,
            "task_type": "bug_fix",
            "task_description": "Validate one Ledger-backed LangGraph role execution.",
            "entry_roles": ["triage"],
            "ledger_mode": "write",
            "runner_mode": "harness_dry_run",
            "max_role_executions": 2,
            "max_parallel_dispatch": 1,
            "activation_threshold": 0.5,
        },
        config={"recursion_limit": 20},
    )
    assert ledger_result["delivery_status"] == "partial", ledger_result
    assert ledger_result["topologist_status"] == "completed", ledger_result
    assert ledger_result["learning_status"] == "completed", ledger_result
    assert ledger_result["completed_roles"] in (["triage", "diagnose"], ["triage", "to-prd"]), ledger_result
    assert ledger_trace.joinpath("manifest.yaml").exists()
    assert ledger_trace.joinpath("state.yaml").exists()
    assert ledger_trace.joinpath("events.yaml").exists()
    assert ledger_trace.joinpath("artifacts/triage-analysis-v1.md").exists()
    assert ledger_trace.joinpath("artifacts/triage-context-report-v1.yaml").exists()
    assert ledger_trace.joinpath("artifacts/diagnose-diagnosis-v1.md").exists()
    assert ledger_trace.joinpath("artifacts/diagnose-context-report-v1.yaml").exists()
    assert ledger_trace.joinpath("artifacts/graph-topologist-topology-review-v1.md").exists()
    assert ledger_trace.joinpath("artifacts/graph-topologist-context-report-v1.yaml").exists()
    assert ledger_trace.joinpath("learning.yaml").exists()
    assert list(ledger_trace.joinpath("handoffs").glob("triage→diagnose-*.yaml"))
    events_text = ledger_trace.joinpath("events.yaml").read_text(encoding="utf-8")
    assert "decision: defer" in events_text, events_text
    assert "decision: activate" in events_text, events_text
    assert "learning_snapshot_written" in events_text, events_text
    manifest_text = ledger_trace.joinpath("manifest.yaml").read_text(encoding="utf-8")
    assert "status: partial" in manifest_text, manifest_text
    learning_text = ledger_trace.joinpath("learning.yaml").read_text(encoding="utf-8")
    assert "convergence_gate_breach" in learning_text, learning_text
    if os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") != "1":
        shutil.rmtree(ledger_trace)

    prompt_task_id = "task-langgraph-native-smoke-prompt-package"
    prompt_trace = ROOT / "traces" / prompt_task_id
    if prompt_trace.exists():
        shutil.rmtree(prompt_trace)
    prompt_result = graph.invoke(
        {
            "task_id": prompt_task_id,
            "task_type": "bug_fix",
            "task_description": "Validate prompt package assembly for an external node executor.",
            "entry_roles": ["triage"],
            "ledger_mode": "write",
            "runner_mode": "prompt_package",
            "max_role_executions": 1,
        },
        config={"recursion_limit": 20},
    )
    assert prompt_result["completed_roles"] == ["triage"], prompt_result
    prompt_artifact = prompt_trace / "artifacts" / "triage-invocation-v1.md"
    assert prompt_artifact.exists(), prompt_result
    prompt_text = prompt_artifact.read_text(encoding="utf-8")
    assert "## Runtime Envelope" in prompt_text, prompt_text
    assert "## Registry Harness" in prompt_text, prompt_text
    assert "## Skill" in prompt_text, prompt_text
    assert "## Harness Profile" in prompt_text, prompt_text
    assert "## Required Output Shape" in prompt_text, prompt_text
    if os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") != "1":
        shutil.rmtree(prompt_trace)

    external_task_id = "task-langgraph-native-smoke-external-command"
    external_trace = ROOT / "traces" / external_task_id
    if external_trace.exists():
        shutil.rmtree(external_trace)
    external_result = graph.invoke(
        {
            "task_id": external_task_id,
            "task_type": "bug_fix",
            "task_description": "Validate local external command node execution.",
            "entry_roles": ["triage"],
            "ledger_mode": "write",
            "runner_mode": "external_command",
            "external_runner_command": f"{sys.executable} tools/local_node_executor.py",
            "max_role_executions": 2,
            "max_parallel_dispatch": 1,
            "activation_threshold": 0.5,
        },
        config={"recursion_limit": 20},
    )
    assert external_result["completed_roles"] in (["triage", "diagnose"], ["triage", "to-prd"]), external_result
    assert external_result["delivery_status"] == "partial", external_result
    external_diagnose = external_trace / "artifacts" / "diagnose-diagnosis-v1.md"
    assert external_diagnose.exists(), external_result
    external_text = external_diagnose.read_text(encoding="utf-8")
    assert "External Executor Result" in external_text, external_text
    assert "input_handoff_count: 1" in external_text, external_text
    assert "input_artifact_count: 1" in external_text, external_text
    external_report = external_trace / "artifacts" / "diagnose-context-report-v1.yaml"
    assert external_report.exists(), external_result
    external_report_text = external_report.read_text(encoding="utf-8")
    assert "handoffs_read:" in external_report_text, external_report_text
    assert "artifacts_read:" in external_report_text, external_report_text
    if os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") != "1":
        shutil.rmtree(external_trace)

    print(
        json.dumps(
            {
                "ok": True,
                "mode": status["mode"],
                "ontology_nodes": status["ontology_nodes"],
                "harness_profiles": status["harness_profiles"],
                "triage_candidate_count": len(triage_candidates),
                "langgraph_topology": status["langgraph_topology"],
                "post_delivery": {
                    "topologist_status": post_delivery_result["topologist_status"],
                    "learning_status": post_delivery_result["learning_status"],
                },
                "ledger_backed_role_execution": {
                    "task_id": ledger_task_id,
                    "completed_roles": ledger_result["completed_roles"],
                    "artifact_refs": ledger_result["artifact_refs"],
                    "delivery_status": ledger_result["delivery_status"],
                    "trace_kept": os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") == "1",
                },
                "prompt_package_execution": {
                    "task_id": prompt_task_id,
                    "completed_roles": prompt_result["completed_roles"],
                    "artifact_refs": prompt_result["artifact_refs"],
                    "trace_kept": os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") == "1",
                },
                "external_command_execution": {
                    "task_id": external_task_id,
                    "completed_roles": external_result["completed_roles"],
                    "artifact_refs": external_result["artifact_refs"],
                    "trace_kept": os.environ.get("SILICON_ORG_KEEP_SMOKE_TRACE") == "1",
                },
                "oss_only": {
                    "configured_service_vars": configured,
                    "langchain_tracing": os.environ.get("LANGCHAIN_TRACING_V2", ""),
                    "langsmith_project": os.environ.get("LANGSMITH_PROJECT", ""),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
