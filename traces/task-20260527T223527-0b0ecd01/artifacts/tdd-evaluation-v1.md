# TDD Evaluation: Visualizer Snapshot Server and Frontend

Task: `task-20260527T223527-0b0ecd01`
Role: `tdd`
Outcome: `CHANGES_REQUIRED`
Blocking: `required`

## Scope Evaluated

- `tools/org_viz_server.py`
- `tools/policy.py`
- `visualizer/index.html`
- `visualizer/styles.css`
- `visualizer/app.js`

No implementation files were modified.

## Summary

Core Python syntax and the server's implemented `/api/health`, `/api/tasks`, `/api/snapshot`, and static `GET` serving paths are functional. The snapshot builder successfully reads the current trace and reports 35 nodes, 122 edges, 76 events, 19 handoffs, 11 artifacts, and zero errors for the target task.

The implementation is not ready to approve because the live frontend does not consume the server snapshot shape correctly, several API contract endpoints from the API designer artifact are absent, missing traces return `200 OK` instead of contract-style `404`, and `tools/policy.py` has no executable CLI for the `context-report` command the task explicitly depends on.

## Blocking Issues

1. Live frontend drops server trace data.
   - Evidence: `tools/org_viz_server.py` returns trace data under `trace` and task id under `taskId`.
   - Evidence: `visualizer/app.js` `normalizeSnapshot` reads `run`, `ledger`, and `task_id`, but not server `trace` or top-level `taskId`.
   - Smoke result: applying the frontend-visible field access to `/api/snapshot` produced 0 events, 0 handoffs, and 0 node states even though the server snapshot contained 76 events, 19 handoffs, and current trace state.
   - Impact: When the API succeeds, the UI can render graph nodes/edges but loses Ledger state, handoff animation inputs, timeline events, and selected task identity for non-default selections.

2. Snapshot service does not implement the API designer contract.
   - Expected by `api-designer-contract-v1.md`: `/api/org`, `/api/runs`, `/api/runs/{task_id}/snapshot`, `/api/runs/{task_id}/events`, `/api/runs/{task_id}/artifacts/{artifact_id}`, `/api/runs/{task_id}/handoffs/{handoff_id}`, `/api/runs/{task_id}/policy`, and `/api/learning`.
   - Observed: `/api/org`, `/api/runs`, and `/api/runs/task-20260527T223527-0b0ecd01/snapshot` returned `404 Not Found`.
   - Impact: Frontend and downstream tests written against the agreed contract will fail or need to depend on undocumented compatibility endpoints.

3. Missing task traces return `200 OK` with embedded file errors.
   - Command: `curl -sS -D - 'http://127.0.0.1:8776/api/snapshot?task_id=task-does-not-exist' -o /tmp/silicon-org-viz-missing.json`
   - Observed: `HTTP/1.0 200 OK`; payload had `taskId: task-does-not-exist`, empty counts, and file-not-found errors.
   - Expected by API contract: `404 TRACE_NOT_FOUND`.
   - Impact: Clients cannot reliably distinguish a valid empty trace from a nonexistent trace by HTTP status.

4. `tools/policy.py` has no CLI dispatch for `context-report`.
   - Command: `python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role tdd --report /tmp/definitely-missing-context-report.yaml; printf 'exit=%s\n' "$?"`
   - Observed: `exit=0`.
   - Impact: The exact validation command named in this task is a no-op and will report success for missing or invalid reports. Validation logic exists as importable functions and is used by `tools/ledger.py`, but `tools/policy.py` itself does not enforce the command surface.

## Nonblocking Observations

- `/api/tasks` returned one embedded error for an older trace missing `state.yaml`: `traces/task-20260525T010808-9010ac70/state.yaml: file not found`. The endpoint still returned the task list. This matches the server's tolerant-reader intent but should be displayed as a warning in clients.
- `HEAD /` and `HEAD /app.js` returned `501 Unsupported method`. The API contract only requires `GET`, so this is not blocking.
- Browser/canvas automation was not completed because local Playwright/Chromium were unavailable. Static and HTTP smoke checks covered syntax, data shape, and served assets, but not actual WebGL frame rendering.

## Commands Run

```bash
python3 -m py_compile tools/policy.py tools/org_viz_server.py
```

Result: PASS, exit 0.

```bash
python3 - <<'PY'
from tools.org_viz_server import build_snapshot
snap = build_snapshot('task-20260527T223527-0b0ecd01')
print(snap['schema'])
print(snap['taskId'])
print(snap['graph']['counts'])
print(snap['trace']['counts'])
print(len(snap['errors']))
PY
```

Result: PASS. Output:

```text
silicon_org.visualizer.snapshot.v1
task-20260527T223527-0b0ecd01
{'nodes': 35, 'edges': 122, 'activationCapableEdges': 82}
{'events': 76, 'handoffs': 19, 'artifacts': 11}
0
```

```bash
node --check visualizer/app.js
```

Result: PASS, exit 0.

```bash
node -e "new Function(require('fs').readFileSync('visualizer/app.js','utf8').replace(/^import .*$/mg,'')); console.log('syntax ok')"
```

Result: PASS. Output: `syntax ok`.

```bash
python3 tools/org_viz_server.py --port 8776 --task-id task-20260527T223527-0b0ecd01
```

Result: PASS. Server started at `http://127.0.0.1:8776` and was stopped after smoke checks.

```bash
curl -sS -D - http://127.0.0.1:8776/api/health -o /tmp/silicon-org-viz-health.json && python3 -m json.tool /tmp/silicon-org-viz-health.json
```

Result: PASS. Returned `HTTP/1.0 200 OK` and JSON with `ok: true`.

```bash
curl -sS http://127.0.0.1:8776/api/tasks -o /tmp/silicon-org-viz-tasks.json && python3 - <<'PY'
import json
with open('/tmp/silicon-org-viz-tasks.json') as f: data=json.load(f)
print(data['schema'])
print(len(data.get('tasks', [])))
print(data.get('tasks', [{}])[0].get('taskId'))
print(len(data.get('errors', [])))
PY
```

Result: PARTIAL PASS. Output:

```text
silicon_org.visualizer.tasks.v1
18
task-20260527T223527-0b0ecd01
1
```

```bash
python3 - <<'PY'
import json
with open('/tmp/silicon-org-viz-tasks.json') as f: data=json.load(f)
print(data.get('errors'))
PY
```

Result: PASS for error visibility. Output showed one missing old trace state file.

```bash
curl -sS 'http://127.0.0.1:8776/api/snapshot?task_id=task-20260527T223527-0b0ecd01' -o /tmp/silicon-org-viz-snapshot.json && python3 - <<'PY'
import json
with open('/tmp/silicon-org-viz-snapshot.json') as f: data=json.load(f)
print(data['schema'])
print(data['taskId'])
print(data['graph']['counts'])
print(data['trace']['counts'])
print(len(data['errors']))
PY
```

Result: PASS. Output:

```text
silicon_org.visualizer.snapshot.v1
task-20260527T223527-0b0ecd01
{'nodes': 35, 'edges': 122, 'activationCapableEdges': 82}
{'events': 76, 'handoffs': 19, 'artifacts': 11}
0
```

```bash
curl -sS -D /tmp/silicon-org-viz-root.headers http://127.0.0.1:8776/ -o /tmp/silicon-org-viz-root.html && sed -n '1,12p' /tmp/silicon-org-viz-root.headers && wc -c /tmp/silicon-org-viz-root.html
```

Result: PASS. Returned `HTTP/1.0 200 OK`, `Content-Type: text/html`, 5960 bytes.

```bash
curl -sS -D /tmp/silicon-org-viz-app.headers http://127.0.0.1:8776/app.js -o /tmp/silicon-org-viz-app.js && sed -n '1,12p' /tmp/silicon-org-viz-app.headers && wc -c /tmp/silicon-org-viz-app.js
```

Result: PASS. Returned `HTTP/1.0 200 OK`, `Content-Type: text/javascript`, 48729 bytes.

```bash
curl --path-as-is -sS -D - http://127.0.0.1:8776/../AGENTS.md -o /tmp/silicon-org-viz-traversal-path-as-is.out
```

Result: PASS. Returned `HTTP/1.0 403 Forbidden`.

```bash
curl -sS -D - http://127.0.0.1:8776/api/runs/task-20260527T223527-0b0ecd01/snapshot -o /tmp/silicon-org-viz-contract-snapshot.out
```

Result: FAIL. Returned `HTTP/1.0 404 Not Found`.

```bash
curl -sS -D - http://127.0.0.1:8776/api/org -o /tmp/silicon-org-viz-api-org.out
```

Result: FAIL. Returned `HTTP/1.0 404 Not Found`.

```bash
curl -sS -D - http://127.0.0.1:8776/api/runs -o /tmp/silicon-org-viz-api-runs.out
```

Result: FAIL. Returned `HTTP/1.0 404 Not Found`.

```bash
curl -sS -D - 'http://127.0.0.1:8776/api/snapshot?task_id=task-does-not-exist' -o /tmp/silicon-org-viz-missing.json && python3 - <<'PY'
import json
with open('/tmp/silicon-org-viz-missing.json') as f: data=json.load(f)
print(data['taskId'])
print(data.get('trace', {}).get('counts'))
print([e.get('source_ref')+': '+e.get('message') for e in data.get('errors', [])[:5]])
PY
```

Result: FAIL against API contract. Returned `HTTP/1.0 200 OK`; output:

```text
task-does-not-exist
{'events': 0, 'handoffs': 0, 'artifacts': 0}
['traces/task-does-not-exist/manifest.yaml: file not found', 'traces/task-does-not-exist/state.yaml: file not found', 'traces/task-does-not-exist/events.yaml: file not found']
```

```bash
python3 - <<'PY'
import json
with open('/tmp/silicon-org-viz-snapshot.json') as f: raw=json.load(f)
run = raw.get('run') or raw.get('task') or {}
ledger = raw.get('ledger') or {}
task_id = run.get('task_id') or run.get('taskId') or raw.get('task_id') or 'task-20260527T223527-0b0ecd01'
events = ledger.get('events') or run.get('events') or []
handoffs = ledger.get('handoffs') or run.get('handoffs') or []
node_states = run.get('node_states') or ledger.get('nodes') or {}
print(task_id)
print(len(events))
print(len(handoffs))
print(len(node_states))
PY
```

Result: FAIL. This mirrors the relevant `visualizer/app.js` live normalization field access and outputs:

```text
task-20260527T223527-0b0ecd01
0
0
0
```

```bash
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role senior-engineer --report traces/task-20260527T223527-0b0ecd01/artifacts/senior-engineer-context-report-v1.yaml
```

Result: FAIL as a meaningful validation command. Exit 0, no output.

```bash
python3 tools/policy.py context-report --task-id task-20260527T223527-0b0ecd01 --role tdd --report /tmp/definitely-missing-context-report.yaml; printf 'exit=%s\n' "$?"
```

Result: FAIL. Output: `exit=0`.

```bash
python3 - <<'PY'
from tools.policy import candidate_activations
candidates = candidate_activations('task-20260527T223527-0b0ecd01')
print(len(candidates))
for item in candidates[:10]:
    print(item)
PY
```

Result: PASS. Output: `0`.

```bash
python3 - <<'PY'
from pathlib import Path
from tools.org_viz_server import MiniYaml
text = Path('traces/task-20260527T223527-0b0ecd01/handoffs/senior-engineer→tdd-20260527-151239.yaml').read_text()
parser = MiniYaml('handoff')
data = parser.parse(text)
print(data['deliverable']['artifact_refs'])
print(data['context_block']['context_digest'])
print(len(parser.errors))
PY
```

Result: PASS. Output:

```text
['senior-engineer-implementation-v1']
109ce10079e735af510c669994694915a59da0d9a9d9fd53109b7dc5231af2f8
0
```

```bash
python3 - <<'PY'
try:
    import playwright
    print('python-playwright available')
except Exception as exc:
    print(f'python-playwright unavailable: {exc}')
PY
```

Result: Browser automation unavailable. Output: `python-playwright unavailable: No module named 'playwright'`.

```bash
node - <<'JS'
try {
  require.resolve('playwright');
  console.log('node-playwright available');
} catch (error) {
  console.log(`node-playwright unavailable: ${error.message}`);
}
JS
```

Result: Browser automation unavailable. Output: `node-playwright unavailable: Cannot find module 'playwright'`.

```bash
which chromium || which google-chrome || which playwright || which npx || which node
```

Result: Browser automation unavailable without installing tooling. Output: `/Users/manas/.npm-global/bin/npx`.

## Recommended Regression Tests

- Add a server/API test that asserts the frontend-consumed snapshot shape includes task id, node states, events, handoffs, artifacts, policy, and learning at the paths the frontend reads.
- Add contract tests for the API designer endpoints or update the contract and frontend together if `/api/snapshot` and `/api/tasks` are the intended v1 surface.
- Add a negative HTTP test for unknown `task_id` returning a structured `404 TRACE_NOT_FOUND`.
- Add a CLI test for `python3 tools/policy.py context-report ...` that fails for missing files and malformed reports.

## Completion Report

```yaml
completion_report:
  what_was_done: "Evaluated server, policy CLI, and frontend smoke behavior without modifying implementation files."
  key_decisions:
    - decision: "Mark evaluation CHANGES_REQUIRED with required blocking."
      rationale: "Core server checks pass, but live frontend data flow, API contract compatibility, missing trace status, and policy CLI validation are broken."
    - decision: "Use smoke checks through public HTTP and CLI boundaries."
      rationale: "The TDD role should verify observable behavior rather than internals."
  handoff_focus:
    - "Fix snapshot schema alignment between tools/org_viz_server.py and visualizer/app.js."
    - "Either implement the API designer endpoints or revise all consumers/contracts to the implemented endpoint names."
    - "Add executable CLI dispatch to tools/policy.py for context-report validation."
  open_questions:
    - "Should /api/snapshot remain as a compatibility alias after /api/runs/{task_id}/snapshot is implemented?"
    - "Should missing task_id fail hard with 404 or remain partial-success only for malformed files inside existing task folders?"
  known_constraints:
    - "No implementation files were modified by this evaluator."
    - "Ledger remains the source of truth."
    - "Context-only relations must not become activation paths."
  confidence_differential: 0.22
  dissent_if_alone: "Do not approve until the browser consumes live server trace data and the policy context-report command actually validates missing/invalid reports."
  iteration_context: "First tdd evaluation for senior-engineer visualizer server and current frontend files."
```
