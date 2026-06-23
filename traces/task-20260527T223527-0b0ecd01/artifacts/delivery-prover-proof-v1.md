# Delivery Prover Proof: Silicon Org 3D Operations Visualizer

Task: `task-20260527T223527-0b0ecd01`
Outcome: `PASS_WITH_REMEDIATION`

## What Was Proven

The local demo runs at:

```text
http://127.0.0.1:8765/
```

The visualizer renders the current Silicon Org in live API mode:

- 35 nodes
- 122 edges
- 76 ledger events
- 19 handoff blocks
- 1 nonblank Three.js canvas
- 35 node labels
- 0 browser page errors
- 0 external network requests

Screenshot evidence:

```text
/tmp/silicon-org-visualizer.png
```

## Commands And Results

```bash
python3 -m py_compile tools/org_viz_server.py tools/policy.py
node --check visualizer/app.js
```

Result: PASS.

```bash
python3 tools/org_viz_server.py --port 8765 --task-id task-20260527T223527-0b0ecd01
```

Result: PASS. Server started on loopback.

```bash
curl -s 'http://127.0.0.1:8765/api/snapshot?task_id=task-20260527T223527-0b0ecd01'
```

Result: PASS. Returned `taskId=task-20260527T223527-0b0ecd01`, 35 nodes, 122 edges, 76 events, 19 handoffs, and zero snapshot parse errors.

```bash
curl -s -D - 'http://127.0.0.1:8765/api/runs/task-20260527T223527-0b0ecd01/snapshot'
```

Result: PASS. Contract-compatible route returned the same snapshot.

```bash
curl -s -D - 'http://127.0.0.1:8765/api/snapshot?task_id=../../..'
curl -s -D - 'http://127.0.0.1:8765/api/snapshot?task_id=task-20260527T000000-deadbeef'
```

Result: PASS. Invalid traversal-style id returns `400 INVALID_TASK_ID`; missing valid trace id returns `404 TRACE_NOT_FOUND`.

```bash
curl -s -D - -H 'Origin: https://evil.example' http://127.0.0.1:8765/api/tasks
```

Result: PASS. Response does not include `Access-Control-Allow-Origin: *`.

```bash
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role senior-frontend --report traces/task-20260527T223527-0b0ecd01/artifacts/senior-frontend-context-report-v1.yaml
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role tdd --report traces/task-20260527T223527-0b0ecd01/artifacts/tdd-context-report-v1.yaml
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role security-engineer --report traces/task-20260527T223527-0b0ecd01/artifacts/security-engineer-context-report-v1.yaml
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role code-reviewer --report traces/task-20260527T223527-0b0ecd01/artifacts/code-reviewer-context-report-v1.yaml
```

Result: PASS. The Policy CLI now validates reports and exits non-zero for missing report files.

Browser verification used installed Google Chrome through Playwright. Result:

```json
{
  "ok": true,
  "errors": [],
  "data": {
    "mode": "live",
    "task": "task-20260527T223527-0b0ecd01",
    "nodes": "35",
    "edges": "122",
    "events": "76",
    "handoffs": "19",
    "canvasCount": 1,
    "labelCount": 35
  },
  "externalRequests": []
}
```

## Remediated Findings

- TDD P0: live server snapshot data was dropped by the frontend. Fixed by normalizing the server `trace` shape and top-level `taskId`.
- TDD P0/P1: API contract drift. Fixed with compatibility endpoints for org, runs, run snapshot, events, policy, artifact, handoff, and learning.
- Security S-1: wildcard CORS. Fixed by removing wildcard CORS from JSON responses.
- Security S-2: `task_id` traversal. Fixed by validating trace ids and requiring existing trace directories.
- Security S-3: external CDN scripts. Fixed by vendoring Three.js, OrbitControls, and js-yaml under `visualizer/vendor/`.
- Security A-1: unescaped node title. Fixed by rendering node title through the escaped paragraph helper.
- Code-reviewer P0: `tools/policy.py context-report` was a no-op. Fixed with an argparse CLI and non-zero failures.
- Code-reviewer P1: context report validator crashed on non-mapping list items. Fixed by validating mapping types for artifacts, handoffs, and quality checks.

## Residual Risk

This is a local no-build demo, not a packaged production app. The server is intentionally read-only and loopback-first. Realtime streaming is still polling-based; SSE/WebSocket can be added later without changing the visualizer's normalized state model.
