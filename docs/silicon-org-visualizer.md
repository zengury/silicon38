# Silicon Org 3D Visualizer Demo

Run the local read-only visualizer:

```bash
python3 tools/org_viz_server.py --port 8765 --task-id task-20260527T223527-0b0ecd01
```

Open:

```text
http://127.0.0.1:8765/
```

The first screen is the working operations surface, not a landing page. It renders
the current Silicon Org graph in 3D and projects live Ledger facts from the
selected trace.

## What It Shows

- 41 org nodes and 152 typed graph edges.
- Control planes for Graph, Policy, Ledger, Runtime, and Learning.
- Node activity derived from `state.yaml` and `events.yaml`.
- Handoff blocks moving between nodes.
- Inspectable context-block digests, retained decisions, constraints,
  assumptions, omissions, and previous-block chains.
- Timeline replay for Ledger events.
- Filters for control plane, relation type, node state, and search.

## API Routes

- `GET /api/health`
- `GET /api/org`
- `GET /api/tasks`
- `GET /api/runs`
- `GET /api/snapshot?task_id=<task-id|latest>`
- `GET /api/runs/{task_id}/snapshot`
- `GET /api/runs/{task_id}/events`
- `GET /api/runs/{task_id}/policy`
- `GET /api/runs/{task_id}/artifacts/{artifact_id}`
- `GET /api/runs/{task_id}/handoffs/{handoff_id}`
- `GET /api/learning`

## Local Safety Boundary

The server is read-only and serves from loopback by default. It does not expose
Ledger mutation commands. Invalid trace ids are rejected before file reads, and
missing valid trace ids return `TRACE_NOT_FOUND`.

The frontend uses vendored browser assets under `visualizer/vendor/`; the live
demo does not need CDN scripts. JSON and static responses include defensive
headers, and wildcard CORS is not enabled.

## Verification Snapshot

The current proof run verified:

- live mode
- task `task-20260527T223527-0b0ecd01`
- 41 nodes
- 152 edges
- 76 events
- 19 handoffs
- one rendered Three.js canvas
- no page errors
- no external browser requests
