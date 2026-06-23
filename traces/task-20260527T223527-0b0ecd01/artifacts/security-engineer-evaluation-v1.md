# Security Engineer Evaluation: Local Org Visualizer Snapshot Surface

## Verdict

`FINDINGS_REQUIRE_FIX`

The visualizer is correctly shaped as a read-only surface: I found no implementation path that writes Graph, Ledger, artifact, handoff, or learning files, and static file serving canonicalizes paths back under `visualizer/`. However, read-only local data can still leak. The current server and client have blocking exposure risks around cross-origin access, `task_id` path handling, and third-party scripts running with same-origin access to local trace data.

## Blocking Findings

### S-1: Cross-origin snapshot disclosure from the local API

- Vulnerability: Cross-origin local data exposure.
- Location: `tools/org_viz_server.py:758-765`, especially `Access-Control-Allow-Origin: *`.
- Exploitability condition: If the local server is running, any website visited in the user's browser can issue `fetch("http://127.0.0.1:8765/api/tasks")` and `fetch("http://127.0.0.1:8765/api/snapshot?task_id=latest")`, read the JSON because CORS allows all origins, and exfiltrate task summaries, node state, events, handoff context blocks, source refs, and learning-index summaries.
- Impact: Violates the local-only expectation. "Read-only" prevents mutation, but it does not prevent unauthorized read access from arbitrary browser origins.
- Remediation: Remove wildcard CORS by default. Serve the visualizer from the same local origin and rely on same-origin fetches. If cross-origin development access is truly needed, require an explicit `--allow-origin http://127.0.0.1:<port>` allowlist, reject other `Origin` headers, and consider Host validation for loopback-only access.

### S-2: `task_id` path traversal can read outside `traces/`

- Vulnerability: Path traversal / local file disclosure.
- Location: `tools/org_viz_server.py:344-347` returns non-`latest` `task_id` values unvalidated; `tools/org_viz_server.py:637-650` joins that value directly into `TRACES_DIR / resolved_task_id` and reads fixed filenames plus handoff/provenance YAML under that derived path.
- Exploitability condition: A request such as `/api/snapshot?task_id=../../..` is accepted. I verified `build_snapshot("../../..")` reports `taskId: ../../..`, `taskDir: traces/../../..`, and attempts reads from `traces/../../../manifest.yaml`, `state.yaml`, and `events.yaml`. If matching files or directories exist outside `traces/`, their contents are projected into the JSON response. S-1 makes the response readable by arbitrary browser origins.
- Impact: Breaks the snapshot API's trace boundary. The implementation is read-only, but an attacker can steer what local files are read.
- Remediation: Accept only known trace ids from `list_task_dirs()` or validate with a strict pattern such as `^task-\d{8}T\d{6}-[0-9a-f]{8}$`. Resolve the candidate directory and require `candidate.relative_to(TRACES_DIR.resolve())`; reject invalid values with `400 INVALID_QUERY` or `404 TRACE_NOT_FOUND` before reading any files.

### S-3: CDN scripts execute with access to local trace data

- Vulnerability: Supply-chain data exposure / external script execution in a privileged local-data UI.
- Location: `visualizer/index.html:8` loads `js-yaml` from jsDelivr; `visualizer/index.html:12-13` loads Three.js modules from jsDelivr via import map.
- Exploitability condition: If jsDelivr, the package release, or the network path serves malicious JavaScript, that code runs in the same origin as the visualizer. It can call `/api/tasks` and `/api/snapshot`, read local Graph/Ledger data, and send it off-machine. There is no CSP limiting outbound connections or script sources.
- Impact: Undermines the "local-only" design even if the server remains read-only.
- Remediation: Vendor the exact JS assets locally or bundle the app. Serve scripts from `self`, pin hashes in a lockfile or checksum manifest, and add a CSP such as `default-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'`. If CDN use remains for prototypes, treat it as non-production and block convergence for release.

## Advisory Findings

### A-1: One node-inspector field bypasses HTML escaping

- Vulnerability: HTML injection / DOM XSS if graph node titles become untrusted.
- Location: `visualizer/app.js:876-878`; `node.title` is interpolated directly into `innerHTML`, while neighboring helpers like `paragraph`, `list`, `tag`, and `structuredItems` escape values at `visualizer/app.js:1105-1138`.
- Exploitability condition: A malicious or compromised snapshot/ontology node title containing markup can execute when the user selects that node. Current local ontology files are repo-controlled, so this is lower-risk than trace-content injection, but the visualizer should consistently treat displayed operational facts as data.
- Remediation: Escape the title before inserting it, for example `${paragraph(node.title)}` or `${escapeHtml(node.title)}` before the tag row. Prefer DOM construction or escaped helper functions for all inspector fields.

### A-2: Static responses lack defensive browser headers

- Vulnerability: Missing defense-in-depth headers.
- Location: `tools/org_viz_server.py:795-799` serves static files without `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, or `frame-ancestors`/`X-Frame-Options`.
- Exploitability condition: This amplifies S-3 and any future injection bug by leaving script/connect destinations unrestricted and allowing browser MIME sniffing defaults.
- Remediation: Add shared static and JSON security headers. At minimum: `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and a restrictive CSP compatible with local bundled scripts.

## Clean Checks

- No mutation endpoints were found; `OrgVizHandler.do_GET` only handles GET routes and no write methods are implemented.
- No subprocess, shell, ledger command invocation, or filesystem writes were found in `tools/org_viz_server.py`.
- Static file path traversal is handled with `normpath`, `resolve()`, and `relative_to(VISUALIZER_DIR.resolve())` at `tools/org_viz_server.py:770-780`.
- Most inspector-rendered snapshot data is escaped through `paragraph`, `list`, `tag`, `structuredItems`, or `textContent`.

## Completion Report

```yaml
completion_report:
  what_was_done: "Reviewed the local visualizer snapshot server, static frontend, styles, and snapshot API contract for read-only safety, path traversal, XSS/HTML injection, CDN supply-chain exposure, and local data exposure."
  key_decisions:
    - decision: "Treat local trace contents as sensitive even when the server is read-only."
      rationale: "A read-only endpoint still exposes durable task facts, handoffs, context blocks, source refs, and potentially user/task-sensitive summaries."
    - decision: "Classify wildcard CORS, task_id traversal, and external CDN scripts as blocking together."
      rationale: "Each issue expands who can read local trace data; combined, arbitrary web origins or third-party scripts can access and exfiltrate the visualizer's local snapshot surface."
    - decision: "Classify the single unescaped node title as advisory."
      rationale: "It is a real DOM injection pattern, but current exploitability depends on control of local ontology/snapshot node metadata rather than normal trace artifact text."
  handoff_focus:
    - "Senior engineer should remove wildcard CORS, validate task_id against real trace directories, and return contract-shaped errors before reading files."
    - "Senior frontend or senior engineer should vendor/bundle JS dependencies and add CSP/security headers."
    - "Senior frontend should escape node.title in the inspector."
  open_questions:
    - "Should the v1 local server ever support cross-origin development access, or should same-origin serving be the only supported mode?"
    - "Should future artifact-content endpoints redact or opt-in expose artifact bodies separately from the full snapshot?"
  known_constraints:
    - "Do not modify implementation files in this node."
    - "The visualizer must remain local and read-only."
    - "Graph, Policy, Ledger, Runtime, and Learning remain the authoritative concepts; the visualizer is a projection surface only."
  confidence_differential: 0.05
  dissent_if_alone: null
  iteration_context: null
```
