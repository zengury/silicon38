# Eval A2 — MCP Server Design in `api-designer`

**Absorb action**: Add an MCP Server Design section that activates when the
API target is an AI agent consumer. Rules: verb-noun tool names, pure functions,
resources are read-only stable URIs, ≤20 tools per server, JSON Schema for all
inputs, stdio (local) vs HTTP+SSE (remote) transport selection.

**Hypothesis**: After absorb, api-designer will produce MCP-compliant schemas
when the caller is an AI agent — instead of generic REST/TypeScript API designs
that are difficult or impossible for agents to consume correctly.

---

## Pre-absorb baseline (current harness behavior)

`api-designer.md` as of 2026-06-23:
- Quality criteria address naming (caller-oriented), nullable/optional/required
  fields, no god objects, typed errors, versioning strategy.
- Output format: TypeScript types/interfaces or "API schema."
- No concept of MCP protocol, tool/resource/prompt distinction, transport
  selection, or agent-specific naming conventions.

**Expected pre-absorb behavior**: api-designer produces a REST-style or
TypeScript interface design. Naming follows human-caller conventions (e.g.
`/documents/search`, `GET /files/{id}`). No tool-count constraint. No
transport selection. No agent-specific design guidance applied.

---

## Rubric (apply to both pre and post outputs)

Score 1 point for each criterion met. Max score: 6.

| # | Criterion | Signal to look for |
|---|---|---|
| R1 | Tool names follow verb-noun convention | All tools named as `verb_noun` or `verbNoun` (e.g. `list_files`, `get_document`) |
| R2 | All tool inputs have JSON Schema | Each tool has explicit `type`, `properties`, `required` array |
| R3 | Transport is selected and justified | stdio OR HTTP+SSE chosen, not both, with one-sentence rationale |
| R4 | Tool count is stated and ≤ 20 | Output explicitly counts tools and confirms ≤ 20 |
| R5 | Resources are read-only with stable URIs | If resources exist: they are GET-only, URIs don't change per request |
| R6 | Output distinguishes tools vs. resources vs. prompts | Three MCP primitive types used appropriately or absence of each justified |

**Expected pre-absorb scores**: R1: FAIL, R2: partial (may have types), R3: FAIL, R4: FAIL, R5: FAIL, R6: FAIL → ~1/6  
**Expected post-absorb scores**: R1–R6 all PASS → 6/6

---

## Scenario S1 — GitHub integration for an AI coding assistant

**Task input to submit:**
```
Design an API for a GitHub integration that an AI coding assistant will use.
The assistant needs to read PRs, check CI status, read files, and create
branches. The integration will run locally on the developer's machine.
```

**Why this probes the gate**: "For an AI coding assistant" signals MCP context.
Local execution signals stdio transport. Operations map clearly to MCP primitives:
file reading → resources, operations → tools. Pre-absorb: will likely produce
REST paths or TypeScript interfaces. Post-absorb: MCP tool definitions with
`list_pull_requests`, `get_file_contents`, `create_branch`, etc.

**Pre-absorb expected output**: TypeScript interface with methods like
`getPullRequests(repo: string): Promise<PR[]>`, REST schema with `/api/github/pulls`,
or similar. No transport discussion. No tool count. No MCP primitives.

**Post-absorb expected output**: MCP tool manifest. Tools: `list_pull_requests`,
`get_file_contents`, `create_branch`, `get_check_run_status`. Resources:
`file://{owner}/{repo}/{path}` (read-only). Transport: stdio (local). Tool
count stated (e.g. 8 tools). Each tool has JSON Schema with `required` fields
explicit.

---

## Scenario S2 — Document Q&A knowledge base for an agent

**Task input to submit:**
```
Design an API for a document knowledge base. An AI agent will use it to
search documents, retrieve specific pages, and add annotations. The service
will be hosted and the agent will call it remotely.
```

**Why this probes the gate**: Remote hosting signals HTTP+SSE transport (not
stdio). Search + retrieve maps to tools. Documents themselves map to resources.
Annotations are mutations (tools, not resources).

**Pre-absorb expected output**: REST API design: `POST /search`, `GET /docs/{id}`,
`POST /annotations`. TypeScript response types. No MCP-specific structure.

**Post-absorb expected output**: MCP design. Resources: `doc://{doc_id}` (stable,
read-only). Tools: `search_documents` (with JSON Schema: `query: string, limit?: number`),
`get_document_page`, `add_annotation`. Transport: HTTP+SSE (remote). Prompts:
none (no parameterized prompt templates needed). Tool count: 3, well within limit.
Schema explicitly marks `query` as required.

---

## Scenario S3 — Ambiguous: internal service API, consumer unclear

**Task input to submit:**
```
Design an API for our internal user permissions service. It needs to check
if a user has a given permission, list all permissions for a user, grant and
revoke permissions. Other services in the system will call this.
```

**Why this probes the gate**: "Other services" is ambiguous — could be AI agents
or human-authored code. Pre-absorb: will design a service API without asking.
Post-absorb: the MCP section should prompt api-designer to clarify whether the
callers include AI agents before applying MCP rules — or note that it's applying
human-API design and MCP rules are not triggered.

**Pre-absorb expected output**: TypeScript interface or REST schema. Methods:
`checkPermission(userId, permission)`, `listPermissions(userId)`,
`grantPermission(userId, permission)`, `revokePermission(userId, permission)`.
No MCP consideration.

**Post-absorb expected output (variant A — agent callers confirmed)**:
MCP design: `check_permission`, `list_user_permissions`, `grant_permission`,
`revoke_permission`. JSON schemas with `user_id: string` and `permission: string`
as required. Tool count: 4. Transport: HTTP+SSE (service-to-service remote).

**Post-absorb expected output (variant B — human callers confirmed)**:
Standard TypeScript interface design. Output notes: "MCP Server Design section
not applied — callers are human-authored microservices, not AI agents."

**Scoring note**: Either variant B qualifies as PASS for R3 (transport decision
made) and R6 (MCP section explicitly considered and opted out).
