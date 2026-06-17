#!/usr/bin/env python3
"""Local test executor for Silicon Org external_command runner.

This is intentionally deterministic and offline. It proves the executor
contract without calling a hosted model provider.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def load_invocation() -> dict:
    ref = os.environ.get("SILICON_ORG_INVOCATION_JSON")
    if not ref:
        raise SystemExit("SILICON_ORG_INVOCATION_JSON is required")
    return json.loads(Path(ref).read_text(encoding="utf-8"))


def context_report(invocation: dict) -> dict:
    artifacts = []
    for artifact in invocation.get("input_artifacts", []):
        artifacts.append({
            "artifact_id": artifact.get("artifact_id"),
            "path": artifact.get("content_ref"),
            "used": True,
            "why": "Read by local external executor contract validation.",
        })

    handoffs = []
    for handoff in invocation.get("input_handoffs", []):
        handoffs.append({
            "ref": handoff.get("ref"),
            "context_digest": handoff.get("context_digest"),
        })

    role = invocation.get("role", "unknown")
    return {
        "context_compression_report": {
            "input_scope": {
                "artifacts_read": artifacts,
                "handoffs_read": handoffs,
            },
            "retained_context": {
                "decisions": [{
                    "statement": f"{role} executed through the local external executor contract.",
                    "source": "tools/local_node_executor.py",
                    "impact": "Validates that LangGraph can call an external node executor.",
                }],
                "constraints": [],
                "assumptions": [{
                    "statement": "This executor is deterministic and offline; it does not perform model reasoning.",
                    "source": "tools/local_node_executor.py",
                    "risk": "Use a real model/tool executor for semantic production work.",
                }],
                "open_questions": [],
            },
            "omitted_context": [],
            "compression_rationale": {
                "method": "local_external_executor_contract_validation",
                "loss_notes": [],
            },
            "quality_checks": [{
                "name": "context_report_schema_complete",
                "passed": True,
            }],
        }
    }


def artifact_body(invocation: dict) -> str:
    role = invocation.get("role", "unknown")
    model = invocation.get("model_selection", {})
    candidate = invocation.get("candidate", {})
    return "\n".join([
        f"# {role} External Executor Result",
        "",
        "This artifact was returned by a local external node executor.",
        "",
        f"- task_id: `{invocation.get('task_id', '')}`",
        f"- task_type: `{invocation.get('task_type', '')}`",
        f"- role: `{role}`",
        f"- artifact_type: `{invocation.get('default_artifact_type', 'analysis')}`",
        f"- model_profile: `{model.get('model_profile', '')}`",
        f"- model: `{model.get('model', '')}`",
        f"- relation_type: `{candidate.get('relation_type', 'entry')}`",
        f"- input_handoff_count: {len(invocation.get('input_handoffs', []))}",
        f"- input_artifact_count: {len(invocation.get('input_artifacts', []))}",
        "",
        "## Task",
        "",
        invocation.get("task_description", ""),
        "",
        "## Completion Report",
        "",
        "```yaml",
        "completion_report:",
        "  what_was_done: Validated local external executor contract.",
        "  key_decisions:",
        "    - decision: Use local offline executor for smoke validation.",
        "      rationale: Avoids commercial or hosted services while proving the runtime boundary.",
        "  handoff_focus:",
        "    - Downstream nodes can inspect artifact and context report provenance.",
        "  open_questions: []",
        "  known_constraints:",
        "    - This is not semantic model reasoning.",
        "  confidence_differential: 0.0",
        "  dissent_if_alone: null",
        "```",
        "",
    ])


def main() -> int:
    invocation = load_invocation()
    result = {
        "role": invocation.get("role"),
        "artifact_type": invocation.get("default_artifact_type", "analysis"),
        "artifact_extension": "md",
        "artifact_body": artifact_body(invocation),
        "context_report": context_report(invocation),
        "semantic_execution": False,
        "metadata": {
            "executor": "tools/local_node_executor.py",
            "offline": True,
        },
    }
    output = json.dumps(result, ensure_ascii=False, indent=2)
    result_ref = os.environ.get("SILICON_ORG_RESULT_JSON")
    if result_ref:
        Path(result_ref).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
