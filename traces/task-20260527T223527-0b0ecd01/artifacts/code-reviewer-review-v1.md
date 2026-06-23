# Code Reviewer Review: Org Visualizer Snapshot Server, Policy, and Frontend

verdict: BLOCKED

## Correctness Findings

### P0 - Live server snapshots render as an empty/idle ledger view in the frontend

`tools/org_viz_server.py:656` returns the authoritative run data under `taskId` and `trace` (`trace.events`, `trace.handoffs`, `trace.artifacts`, `trace.state`). `visualizer/app.js:334` normalizes only `raw.run`, `raw.task`, and `raw.ledger`; it never reads `raw.trace` and only checks snake-case `raw.task_id` at `visualizer/app.js:361`.

When the frontend is served by `tools/org_viz_server.py`, the API request succeeds, so the static YAML fallback is not used. The UI then shows the graph but drops Ledger events, handoffs, artifacts, node activity, and the real task metadata. That directly fails the acceptance requirement that the UI reflect Graph, Policy, Ledger, Runtime, Learning, node activity, handoffs, and Context Blocks.

Suggested resolution: teach `normalizeSnapshot` to accept the server shape, for example by deriving `run` from `raw.trace.manifest`/`raw.trace.state`, deriving `ledger` from `raw.trace.events`/`handoffs`/`artifacts`, and reading `raw.taskId`.

Evidence:

```text
GET /api/snapshot?task_id=task-20260527T223527-0b0ecd01
top-level keys: errors, generatedAt, graph, learning, policy, schema, taskId, trace
trace counts: events=76, handoffs=19, artifacts=11
ledger key exists: false
run key exists: false
```

### P0 - The documented policy context-report command silently does nothing

`tools/policy.py:177` contains context report validation helpers, but `tools/policy.py:530` is the end of the file and there is no CLI parser or `if __name__ == "__main__"` dispatch. As a result, the command shape required by the task exits successfully even when the report path does not exist:

```text
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role code-reviewer --report traces/task-20260527T223527-0b0ecd01/artifacts/does-not-exist.yaml
EXIT:0
```

This weakens the Policy layer because invalid or missing context reports can appear validated by automation. It also makes the user's requested validation command unreliable.

Suggested resolution: add an argparse entrypoint for `context-report` that loads state and report YAML, calls `enforce_context_report_valid` and `enforce_context_report_sources_valid`, and exits non-zero on any validation error.

### P1 - Context report validation still crashes on non-mapping list items

The change in `tools/policy.py:212` and `tools/policy.py:224` adds mapping checks for `retained_context.*` and `omitted_context`, but the same guard is missing for `input_scope.artifacts_read`, `input_scope.handoffs_read`, and `quality_checks`. `tools/policy.py:189`, `tools/policy.py:197`, and `tools/policy.py:248` call `.get(...)` on each item without checking that the item is a mapping.

Malformed reports should produce policy issues, not an `AttributeError`. This matters because context compression is a hard runtime invariant.

Suggested resolution: add `isinstance(item, dict)` checks to all list-item validation loops before dereferencing fields.

Evidence:

```text
context_report_issues({"input_scope": {"artifacts_read": ["not-a-map"], ...}})
AttributeError: 'str' object has no attribute 'get'
```

### P1 - Task picker does not populate from the server's `/api/tasks` response

`tools/org_viz_server.py:709` emits task rows with `taskId`, but `visualizer/app.js:223` only reads `item.task_id || item.id`. With the live server, `/api/tasks` returns rows successfully, but every row is skipped because `taskId` is ignored. The trace picker remains stuck on the hard-coded `latest` option.

Suggested resolution: read `item.taskId` in `loadTasks`, and consider keeping both camelCase and snake_case compatibility because the codebase currently uses both.

### P2 - Omitted context is normalized but not inspectable

`tools/org_viz_server.py:526` includes `contextBlock.omittedContext` in each normalized handoff, and raw Ledger handoffs store `context_block.omitted_context` as a sibling of `compressed_context`. `visualizer/app.js:428` normalizes only `compressed_context`/`compressedContext`, then `visualizer/app.js:914` tries to render `compressed.omitted_context`. In both the API path and the raw YAML fallback path, omitted context is dropped from the inspector.

Suggested resolution: preserve `block.omitted_context || block.omittedContext` in `normalizeHandoff` and render that field directly, falling back to `compressed.omitted_context` only for older demo data.

## Maintainability Findings

### P2 - Server and API contract have drifted far enough to hide integration bugs

The API contract artifact defines `/api/runs/{task_id}/snapshot`, `/api/runs`, and a response envelope, while `tools/org_viz_server.py:742` exposes `/api/health`, `/api/tasks`, and `/api/snapshot`. A smaller first implementation can be acceptable, but the frontend/server shape mismatch above shows that the contract drift is no longer just naming preference.

Suggested resolution: either align the server/frontend to the contract or write a short v0 adapter contract in the implementation artifact and test against that exact shape.

## Style Notes

- No blocking style-only issues.

## Verification

- `python3 -m py_compile tools/org_viz_server.py tools/policy.py`: passed.
- `node --check visualizer/app.js`: passed.
- Started `tools/org_viz_server.py` on port `8876` and checked `/api/snapshot` plus `/api/tasks`.
- Imported `tools.policy.context_report_issues` and reproduced the non-mapping list crash.

## Completion Report

```yaml
completion_report:
  what_was_done: "Reviewed tools/org_viz_server.py, tools/policy.py, and visualizer/ for correctness, regressions, maintainability, and coverage of Graph, Policy, Ledger, Runtime, Learning, node activity, handoffs, and Context Blocks."
  key_decisions:
    - decision: "Return BLOCKED rather than CHANGES_REQUIRED."
      rationale: "The live server/frontend integration drops Ledger and handoff data, and the requested policy validation command silently accepts missing reports."
    - decision: "Treat context-report validator behavior as in scope."
      rationale: "The task explicitly required a report valid for the policy context-report command, and Policy truthfulness is a load-bearing Silicon Org concept."
  handoff_focus:
    - "Fix the snapshot shape consumed by visualizer/app.js before delivery proof."
    - "Add an actual tools/policy.py context-report CLI before relying on that validation command."
    - "Extend context_report_issues mapping checks to every schema list."
  open_questions:
    - "Should the visualizer align to api-designer-contract-v1 endpoints now, or should a smaller v0 contract be documented and used consistently?"
  known_constraints:
    - "No implementation files were modified by this review node."
    - "Only code-reviewer review and context report artifacts were written."
    - "Existing unrelated workspace changes were not reverted or disturbed."
  confidence_differential: 0.08
  dissent_if_alone: null
  iteration_context: "First code-reviewer pass for task-20260527T223527-0b0ecd01."
```
