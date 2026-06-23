# Senior Engineer Implementation: Read-only Org Visualizer Snapshot Server

## Scope

Implemented `tools/org_viz_server.py`, a Python-stdlib-only local HTTP server for the Silicon Org visualizer.

The server is read-only. It reads Graph files, Ledger traces, handoff records, artifact provenance, and learning indexes, then emits normalized JSON snapshots for the Three.js frontend.

## Implemented

- `GET /api/snapshot?task_id=<id|latest>`
  - Returns `schema: silicon_org.visualizer.snapshot.v1`.
  - Includes Graph nodes/edges from `ontology/`.
  - Includes trace manifest, state, normalized events, handoffs, artifact summaries, policy decisions, convergence state, and learning index summaries.
  - Tolerates missing files and malformed old traces by collecting structured `errors` instead of aborting the response.
  - Rejects invalid `task_id` values before reading files and returns `404 TRACE_NOT_FOUND` for valid-looking but absent trace ids.

- Compatibility API endpoints
  - `GET /api/org`
  - `GET /api/runs`
  - `GET /api/runs/{task_id}/snapshot`
  - `GET /api/runs/{task_id}/events`
  - `GET /api/runs/{task_id}/policy`
  - `GET /api/runs/{task_id}/artifacts/{artifact_id}`
  - `GET /api/runs/{task_id}/handoffs/{handoff_id}`
  - `GET /api/learning`

- `GET /api/tasks`
  - Lists local `traces/task-*` directories.
  - Includes task summary, status, timestamps, entry/terminal nodes, artifact count, handoff count, and source ref when available.

- `GET /api/health`
  - Lightweight health response for local tooling.

- Static serving
  - Serves `/` as `visualizer/index.html` when present.
  - Serves other files from `visualizer/`.
  - Rejects path traversal.
  - Serves shared security headers and supports `HEAD` for static assets.

- CLI
  - `python3 tools/org_viz_server.py --port 8765 [--task-id ...]`
  - Also supports `--host`, defaulting to `127.0.0.1`.

## Engineering Notes

- Uses only Python standard library modules.
- Implements a small tolerant YAML subset reader because PyYAML is not part of the Python stdlib.
- Keeps source refs on normalized objects so the frontend inspector can show evidence paths.
- Does not call Ledger commands and does not mutate `manifest.yaml`, `state.yaml`, `events.yaml`, handoffs, artifacts, Graph files, or learning indexes.
- Does not emit wildcard CORS headers; the browser UI uses same-origin API calls.
- Adds `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer` to JSON and static responses.
- Uses polling-friendly full snapshots first; SSE/WebSocket can be layered later without changing the snapshot boundary.

## Validation

```text
python3 -m py_compile tools/org_viz_server.py

python3 - <<'PY'
from tools.org_viz_server import build_snapshot
snap = build_snapshot('task-20260527T223527-0b0ecd01')
print(snap['graph']['counts'])
print(snap['trace']['counts'])
print(len(snap['errors']))
PY
```

Result:

```text
{'nodes': 35, 'edges': 122, 'activationCapableEdges': 82}
{'events': 76, 'handoffs': 19, 'artifacts': 11}
0
```

HTTP validation:

```text
python3 tools/org_viz_server.py --port 8765 --task-id task-20260527T223527-0b0ecd01
GET http://127.0.0.1:8765/api/tasks
GET http://127.0.0.1:8765/api/snapshot?task_id=task-20260527T223527-0b0ecd01
GET http://127.0.0.1:8765/api/runs/task-20260527T223527-0b0ecd01/snapshot
GET http://127.0.0.1:8765/api/health
```

Validated snapshot response included 35 nodes, 122 edges, current trace events, handoffs, and zero parse errors.
Security validation verified invalid traversal-style `task_id` values return `400 INVALID_TASK_ID`, absent valid trace ids return `404 TRACE_NOT_FOUND`, and same-origin responses no longer include `Access-Control-Allow-Origin: *`.

## Handoff Compliance

Read the architect handoff:

- `handoffs/architect→senior-engineer-20260527-145527.yaml`
- context digest: `416e13550c7b1d4b2ca6398e28af110fa5482534c01a479fe1968380ee87df22`

Read architect artifact:

- `architect-architecture-v1`
- `artifacts/architect-architecture-v1.md`

The implementation follows the architect decision that the visualizer must be a local read-only projection of Graph and Ledger truth, not a second runtime authority.
