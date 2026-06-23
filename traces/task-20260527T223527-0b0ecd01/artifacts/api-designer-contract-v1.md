# API Contract: Local Silicon Org Visualizer Snapshot Service

## Scope

This contract defines a local, read-only JSON service for the Three.js Silicon Org operations visualizer. It projects Graph files, Ledger trace files, policy gates, handoff blocks, context-block summaries, runtime status, and learning indices into stable frontend snapshots.

The service is an audit surface, not a control plane. It must not mutate Graph, Policy, Ledger, artifacts, handoffs, learning weights, or runtime state.

## Transport

- Bind default: `127.0.0.1`
- Default port: `5179`
- Content type: `application/json; charset=utf-8`
- Auth: none for localhost v1
- Caching: `Cache-Control: no-store`
- Time format: ISO-8601 UTC strings
- Source refs: every durable object includes a `source_ref` or `source_refs` field

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service health and schema versions |
| GET | `/api/org` | Static Graph snapshot from `ontology/*.yaml` |
| GET | `/api/runs` | List local trace runs |
| GET | `/api/runs/{task_id}` | Run metadata and current status |
| GET | `/api/runs/{task_id}/snapshot` | Full visualizer snapshot for one run |
| GET | `/api/runs/{task_id}/events?after={sequence}&limit={n}` | Incremental normalized events |
| GET | `/api/runs/{task_id}/artifacts/{artifact_id}` | Artifact metadata and read-only content |
| GET | `/api/runs/{task_id}/handoffs/{handoff_id}` | Handoff block and context-block summary |
| GET | `/api/runs/{task_id}/policy` | Activation candidates, decisions, and convergence gates |
| GET | `/api/learning` | Learning indices and graph weight deltas |

Optional query parameters:

- `include=raw_refs`: include raw source file refs only, not raw file bodies.
- `at={sequence}`: return snapshot projected to an event sequence for replay.
- `status=active|completed|failed|all`: filter `/api/runs`.
- `limit`: default `200`, max `1000` for events and runs.

## Response Envelope

```json
{
  "schema": "silicon_org.visualizer.response.v1",
  "generated_at": "2026-05-27T14:55:30.000000Z",
  "data": {},
  "errors": [],
  "warnings": [],
  "source_refs": []
}
```

## Full Snapshot Schema

`GET /api/runs/{task_id}/snapshot`

```json
{
  "schema": "silicon_org.visualizer.snapshot.v1",
  "generated_at": "2026-05-27T14:55:30.000000Z",
  "graph": {},
  "run": {},
  "node_status": {},
  "handoff_blocks": [],
  "context_block_summary": {},
  "policy": {},
  "ledger": {},
  "learning": {},
  "errors": [],
  "warnings": []
}
```

## Graph Contract

```json
{
  "graph": {
    "schema": "silicon_org.graph.v1",
    "node_count": 35,
    "edge_count": 122,
    "nodes": [
      {
        "id": "architect",
        "title": "Architect",
        "layer": 2,
        "domain": "architecture",
        "carries_soul": true,
        "skill_ref": ".agents/skills/senior-architect/SKILL.md",
        "registry_ref": "org/REGISTRY.md#architect",
        "model_profile": "runtime-default",
        "status": "completed",
        "position_hint": {
          "zone": "execution",
          "ring": 2,
          "order": 12
        },
        "source_refs": ["ontology/nodes.yaml"]
      }
    ],
    "relations": [
      {
        "id": "architect->api-designer:triggers",
        "from": "architect",
        "to": "api-designer",
        "relation_type": "triggers",
        "activation_capable": true,
        "evaluation_reverse_aware": false,
        "weight": 0.7,
        "confidence": 0.5,
        "condition": "API/data contract needed",
        "visual": {
          "lane": "activation",
          "thickness": 0.7,
          "opacity": 0.5
        },
        "source_ref": "ontology/relations.yaml"
      }
    ]
  }
}
```

Relation semantics:

- `triggers`, `may_trigger`: activation-capable from `from` to `to`.
- `evaluates`: activation-capable in reverse handoff direction when an artifact producer hands work to an evaluator.
- `supports`, `constrains`, `complements`, `augments`, `precedes`: visible context/pressure edges, never direct activation edges.

## Run, Node Status, and Events

```json
{
  "run": {
    "task_id": "task-20260527T223527-0b0ecd01",
    "task_summary": "Build a Three.js realtime Silicon Org 3D operations visualizer",
    "task_status": "propagating",
    "timestamp_start": "2026-05-27T14:35:27.486496Z",
    "timestamp_end": null,
    "context_block": {
      "ref": "org/CONTEXT_BLOCK.md",
      "sha256": "d82dc247c04f8cd2e797dd394ecd8d9cd927f1e194f2800d4fcf1e2be41f2a66"
    },
    "source_refs": [
      "traces/task-20260527T223527-0b0ecd01/manifest.yaml",
      "traces/task-20260527T223527-0b0ecd01/state.yaml"
    ]
  },
  "node_status": {
    "architect": {
      "status": "completed",
      "activated_at": "2026-05-27T14:44:35.446530Z",
      "completed_at": "2026-05-27T14:53:20.079120Z",
      "iteration": 1,
      "output_artifact_ids": ["architect-architecture-v1"],
      "blocked_reason": null,
      "source_ref": "traces/task-20260527T223527-0b0ecd01/state.yaml"
    }
  },
  "events": [
    {
      "sequence": 41,
      "timestamp": "2026-05-27T14:55:27.666739Z",
      "event_type": "handoff_created",
      "actor": "architect",
      "node_id": "api-designer",
      "edge_id": "architect->api-designer:triggers",
      "handoff_id": "architect-api-designer-20260527-145527",
      "artifact_id": "architect-architecture-v1",
      "payload": {},
      "source_ref": "traces/task-20260527T223527-0b0ecd01/handoffs/architect→api-designer-20260527-145527.yaml"
    }
  ]
}
```

Allowed node statuses:

```json
["idle", "candidate", "activated", "running", "completed", "skipped", "deferred", "failed", "approved", "invalid"]
```

## Handoff Block Contract

```json
{
  "handoff_blocks": [
    {
      "id": "architect-api-designer-20260527-145527",
      "from": "architect",
      "to": "api-designer",
      "relation_type": "triggers",
      "timestamp": "2026-05-27T14:55:27.666739Z",
      "focus": "specify read-only snapshot API and JSON contracts",
      "status": "received",
      "deliverable": {
        "producer": "architect",
        "artifact_refs": ["architect-architecture-v1"],
        "artifacts": [
          {
            "artifact_id": "architect-architecture-v1",
            "producer": "architect",
            "type": "architecture",
            "version": 1,
            "status": "draft",
            "content_ref": "artifacts/architect-architecture-v1.md"
          }
        ]
      },
      "context_block": {
        "schema": "silicon_org.context_chain.v1",
        "task_id": "task-20260527T223527-0b0ecd01",
        "from": "architect",
        "to": "api-designer",
        "relation_type": "triggers",
        "focus": "specify read-only snapshot API and JSON contracts",
        "context_digest": "2c3178b86f61778e163e9da4ea8f6405db78aafbaa80c1c9034088545474a22e",
        "previous_blocks": [
          {
            "ref": "handoffs/caveman→architect-20260527-144434.yaml",
            "context_digest": "d39f77d1e7a7f400cf4c44334e04146346f62d972d886346305a2c49398dd909"
          }
        ],
        "compressed_context": {
          "decisions": [],
          "constraints": [],
          "assumptions": [],
          "open_questions": []
        },
        "source": {
          "producer_role": "architect",
          "context_compression_report_ref": "artifacts/architect-context-report-v1.yaml",
          "input_handoffs": [
            {
              "ref": "handoffs/caveman→architect-20260527-144434.yaml",
              "context_digest": "d39f77d1e7a7f400cf4c44334e04146346f62d972d886346305a2c49398dd909"
            }
          ],
          "input_artifacts": ["caveman-analysis-v1"]
        }
      },
      "source_ref": "traces/task-20260527T223527-0b0ecd01/handoffs/architect→api-designer-20260527-145527.yaml"
    }
  ]
}
```

Block slices for the 3D frontend:

- `deliverable`: artifact refs and producer metadata.
- `context`: retained decisions, constraints, assumptions, and open questions.
- `digest`: current digest and previous block digest chain.
- `soul`: `soul_ref` when present.

## Policy Gates

```json
{
  "policy": {
    "activation_candidates": [
      {
        "from": "architect",
        "to": "api-designer",
        "relation_type": "triggers",
        "edge_id": "architect->api-designer:triggers",
        "weight": 0.7,
        "decision": "activate",
        "reason": "Architect completed and handed architecture artifact to API designer.",
        "source_refs": [
          "ontology/relations.yaml",
          "traces/task-20260527T223527-0b0ecd01/handoffs/architect→api-designer-20260527-145527.yaml"
        ]
      }
    ],
    "decisions": [
      {
        "candidate_id": "architect->api-designer:triggers",
        "decision": "activate",
        "decided_at": "2026-05-27T14:55:30.648590Z",
        "decided_by": "runtime",
        "source_ref": "traces/task-20260527T223527-0b0ecd01/events.yaml"
      }
    ],
    "gates": [
      {
        "id": "no_undecided_activation_candidates",
        "status": "blocked",
        "blockers": ["Some downstream candidates are activated but not completed."],
        "source_ref": "traces/task-20260527T223527-0b0ecd01/state.yaml"
      }
    ],
    "convergence": {
      "status": "not_converged",
      "blockers": [
        "all_non_loop_nodes_settled",
        "all_blocking_evals_resolved",
        "all_artifacts_resolved",
        "no_undecided_activation_candidates"
      ],
      "checked_at": null
    }
  }
}
```

Allowed decision values:

```json
["activate", "skip", "defer", "undecided"]
```

## Ledger View

```json
{
  "ledger": {
    "task_id": "task-20260527T223527-0b0ecd01",
    "manifest": {
      "ref": "traces/task-20260527T223527-0b0ecd01/manifest.yaml",
      "timestamp_start": "2026-05-27T14:35:27.486496Z",
      "timestamp_end": null,
      "outcome": null
    },
    "artifact_index": [
      {
        "artifact_id": "architect-architecture-v1",
        "type": "architecture",
        "producer": "architect",
        "version": 1,
        "status": "draft",
        "path": "artifacts/architect-architecture-v1.md",
        "provenance_ref": "artifacts/architect-architecture-v1.provenance.yaml"
      }
    ],
    "handoff_trail": [
      {
        "ref": "handoffs/architect→api-designer-20260527-145527.yaml",
        "from": "architect",
        "to": "api-designer",
        "relation_type": "triggers",
        "context_block_digest": "2c3178b86f61778e163e9da4ea8f6405db78aafbaa80c1c9034088545474a22e"
      }
    ],
    "unresolved": [],
    "source_refs": [
      "traces/task-20260527T223527-0b0ecd01/manifest.yaml",
      "traces/task-20260527T223527-0b0ecd01/state.yaml",
      "traces/task-20260527T223527-0b0ecd01/events.yaml"
    ]
  }
}
```

## Learning Indices

```json
{
  "learning": {
    "signals": [
      {
        "id": "task-20260527T223527-0b0ecd01:architect->api-designer",
        "task_id": "task-20260527T223527-0b0ecd01",
        "target_type": "edge",
        "target_id": "architect->api-designer:triggers",
        "signal": 0.0,
        "confidence": 0.0,
        "source": "pending_outcome",
        "detail": "No final outcome has been written yet.",
        "source_ref": "traces/index_by_edge.yaml"
      }
    ],
    "edge_deltas": [],
    "proposals": []
  }
}
```

If learning index files are absent or stale, return empty arrays and a warning rather than failing the snapshot.

## Error Handling

All endpoints use the same error shape.

```json
{
  "code": "TRACE_NOT_FOUND",
  "message": "Trace task-unknown was not found.",
  "severity": "error",
  "source_ref": "traces/task-unknown",
  "recoverable": false,
  "details": {}
}
```

Common errors:

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | `INVALID_QUERY` | Query parameter is malformed |
| 404 | `TRACE_NOT_FOUND` | Requested task trace does not exist |
| 404 | `ARTIFACT_NOT_FOUND` | Artifact id is not in the run artifact index |
| 422 | `TRACE_PARSE_ERROR` | A trace file exists but cannot be parsed |
| 422 | `SCHEMA_VERSION_UNSUPPORTED` | File schema is newer than adapter support |
| 500 | `SNAPSHOT_BUILD_FAILED` | Unexpected adapter failure |

Partial failure rule:

- Malformed optional files produce `warnings`.
- Malformed core files produce `errors` but still return a best-effort snapshot if `manifest.yaml` and `state.yaml` can be read.
- Objects with parse issues are included with `status: "invalid"` and a source ref.

## Polling Expectations

Live local mode:

- Poll `/api/runs/{task_id}/events?after={sequence}` every `500-1000 ms`.
- Poll `/api/runs/{task_id}/snapshot` every `1000 ms` while `task_status` is active.
- Back off to `2000-5000 ms` after `timestamp_end` is present.
- Treat event application as idempotent; sequence numbers are stable per adapter process.
- If polling fails, keep the last good snapshot and display `stale_age_ms`.

Replay mode:

- Load one full snapshot.
- Replay `events` in sequence order.
- Use `at={sequence}` for deterministic inspector state at a timeline point.
- Never infer durable facts from animation state; animation is a projection of Ledger facts.

## Non-Goals

- No POST, PUT, PATCH, or DELETE endpoints in v1.
- No graph editing.
- No artifact approval.
- No runtime activation command.
- No learning weight mutation.
- No authentication or remote deployment contract.

## Completion Report

```yaml
completion_report:
  what_was_done: "Defined the read-only local Snapshot API and JSON data contract for the Silicon Org Three.js visualizer."
  key_decisions:
    - decision: "Use one full snapshot endpoint plus incremental events."
      rationale: "The frontend needs both deterministic replay and smooth local live updates."
    - decision: "Keep every rendered object source-ref preserving."
      rationale: "The visualizer is an audit surface and Ledger remains the source of truth."
    - decision: "Expose policy gates and handoff blocks as first-class resources."
      rationale: "The user needs to see why nodes run and what context each transfer carries."
    - decision: "Return warnings and invalid objects for partial parse failures."
      rationale: "Operational visibility should degrade gracefully instead of hiding broken trace evidence."
  downstream_focus:
    - "Prototype can build against /api/runs/{task_id}/snapshot and /events first."
    - "Senior frontend should preserve idempotent event reconciliation."
    - "Senior engineer can implement the adapter without adding control-plane mutation."
  known_constraints:
    - "Read-only local service."
    - "Ledger-derived facts are authoritative."
    - "Context-only relation types cannot activate nodes."
    - "LangGraph events are future adapter input, not organizational truth."
  confidence_differential: 0.13
  dissent_if_alone: "Do not add WebSocket or command endpoints before the snapshot schema is proven against several real traces."
```
