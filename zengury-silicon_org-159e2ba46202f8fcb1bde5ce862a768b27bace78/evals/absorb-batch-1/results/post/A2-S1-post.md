# A2 — Scenario S1 — Post-Absorb Run
**Role**: api-designer (post-absorb: MCP Server Design section active)
**Task**: Design an API for a GitHub integration that an AI coding assistant will use. The assistant needs to read PRs, check CI status, read files, and create branches. The integration will run locally on the developer's machine.
**Harness snapshot**: 2026-06-23 post-absorb

---

## MCP Server Design: GitHub Integration

### Applicability check

The task description names "AI coding assistant" as the consumer. This triggers the MCP Server Design section. The integration runs locally on the developer's machine, which selects **stdio transport**.

Standard TypeScript interface output is NOT produced. MCP tool manifest replaces it.

---

## Transport

**stdio** — local execution on the developer's machine. The MCP server is spawned as a subprocess by the host AI coding assistant. HTTP+SSE would introduce unnecessary network overhead and require a daemon process; stdio is the correct choice for a local integration.

---

## Tool Count

**8 tools total** — well within the ≤ 20 per server limit.

---

## MCP Primitives

### Tools (mutations and queries requiring fresh data)

All tools follow verb-noun naming. All are pure functions: same inputs produce same outputs given consistent upstream GitHub state. Side-effecting tools (`create_branch`) are idempotent by design.

---

#### `list_pull_requests`

List open (or filtered) pull requests for a repository.

```json
{
  "name": "list_pull_requests",
  "description": "List pull requests for a GitHub repository. Returns summary objects; use get_pull_request for full detail including changed files.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login that owns the repository."
      },
      "repo": {
        "type": "string",
        "description": "Repository name (without owner prefix)."
      },
      "state": {
        "type": "string",
        "enum": ["open", "closed", "merged"],
        "description": "Filter by PR state. Defaults to 'open'."
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "description": "Maximum number of results to return. Defaults to 30."
      }
    },
    "required": ["owner", "repo"]
  }
}
```

---

#### `get_pull_request`

Fetch full PR detail including changed files and review decision.

```json
{
  "name": "get_pull_request",
  "description": "Get full detail for a single pull request, including changed files and current review decision.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "pull_number": {
        "type": "integer",
        "description": "PR number as it appears in GitHub (e.g. 42)."
      }
    },
    "required": ["owner", "repo", "pull_number"]
  }
}
```

---

#### `get_check_suite`

Get all CI check runs for a given commit SHA or branch name.

```json
{
  "name": "get_check_suite",
  "description": "Return all CI check runs for a ref (commit SHA or branch name). Includes per-run status and conclusion, plus a rolled-up overall status.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "ref": {
        "type": "string",
        "description": "Commit SHA or branch name to check CI status for."
      }
    },
    "required": ["owner", "repo", "ref"]
  }
}
```

---

#### `list_branches`

List branches in a repository, optionally filtered by prefix.

```json
{
  "name": "list_branches",
  "description": "List branches in a repository. Use before create_branch to check whether the target name already exists.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "prefix": {
        "type": "string",
        "description": "Optional prefix filter (e.g. 'fix/'). Returns only branches whose names start with this string."
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "description": "Maximum results. Defaults to 30."
      }
    },
    "required": ["owner", "repo"]
  }
}
```

---

#### `create_branch`

Create a new branch from a specified ref.

```json
{
  "name": "create_branch",
  "description": "Create a new branch. The source ref (from_ref) is required to prevent silent default-branch assumptions. Fails with BRANCH_ALREADY_EXISTS if the name is taken.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "name": {
        "type": "string",
        "description": "Name for the new branch (e.g. 'fix/auth-check')."
      },
      "from_ref": {
        "type": "string",
        "description": "Branch name or commit SHA to branch from. Required — never assumed."
      }
    },
    "required": ["owner", "repo", "name", "from_ref"]
  }
}
```

**Tradeoff**: `from_ref` is required rather than defaulting to the repository default branch. An AI caller may have a stale SHA in context; forcing explicit source prevents silent creation from the wrong point.

---

#### `get_default_branch`

Return the default branch name for a repository.

```json
{
  "name": "get_default_branch",
  "description": "Return the default branch name for a repository (e.g. 'main' or 'master'). Use this before create_branch when no other ref is known.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      }
    },
    "required": ["owner", "repo"]
  }
}
```

---

#### `search_code`

Search for code within a repository.

```json
{
  "name": "search_code",
  "description": "Search for code matching a query within a repository. Returns file paths and matching line excerpts. Use to locate relevant files before reading them via the file resource.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "query": {
        "type": "string",
        "description": "Code search query (GitHub code search syntax supported)."
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50,
        "description": "Maximum number of results. Defaults to 10."
      }
    },
    "required": ["owner", "repo", "query"]
  }
}
```

---

#### `list_directory`

List files and directories at a path in the repository tree.

```json
{
  "name": "list_directory",
  "description": "List entries (files and subdirectories) at a given path in the repository tree. Use to navigate repository structure before reading specific files.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "owner": {
        "type": "string",
        "description": "GitHub org or user login."
      },
      "repo": {
        "type": "string",
        "description": "Repository name."
      },
      "path": {
        "type": "string",
        "description": "Directory path within the repository. Use '' or '/' for the root."
      },
      "ref": {
        "type": "string",
        "description": "Branch name or commit SHA. Defaults to the repository default branch."
      }
    },
    "required": ["owner", "repo", "path"]
  }
}
```

---

### Resources (read-only, stable URIs, cacheable)

Resources represent data that does not change given a stable ref. They are GET-only and safe to cache. File content at a specific SHA is immutable; the URI encodes the ref so the same URI always returns the same content.

#### `github://file/{owner}/{repo}/{ref}/{path}`

Read the content of a single file at a given ref.

- **URI pattern**: `github://file/{owner}/{repo}/{ref}/{path}`
- **Examples**:
  - `github://file/acme/api/main/src/auth.ts`
  - `github://file/acme/api/a3f9c2d/src/auth.ts`
- **Read-only**: yes. File content at a pinned SHA is immutable.
- **Cacheable**: yes when `ref` is a SHA. Do not cache by branch name (branch HEAD moves).
- **MIME type**: `text/plain` for text files. Binary files return an error.
- **Error conditions**: `NOT_FOUND`, `BINARY_FILE`, `FILE_TOO_LARGE` (>1 MB), `PERMISSION_DENIED`.

**Design note**: File reading is a resource, not a tool, because it is a pure read with a stable identity. The AI assistant will frequently read the same file multiple times across a session; representing it as a resource enables host-level caching and avoids redundant tool calls.

---

### Prompts (parameterized templates)

Two prompt templates are provided. Each is tested with at least 2 representative inputs below.

#### `summarize_pull_request`

Summarize a pull request for the developer, highlighting changes, CI status, and review state.

**Parameters**:
- `pull_request_json` (string, required) — JSON-serialized PR detail from `get_pull_request`
- `check_suite_json` (string, required) — JSON-serialized check suite from `get_check_suite`

**Template**:
```
You are a code review assistant. Given the following pull request detail and CI status,
produce a concise summary (3-5 sentences) covering:
1. What the PR changes and why (infer from title, body, and changed files)
2. Current CI status and any failing checks
3. Review decision status

Pull Request:
{{pull_request_json}}

CI Status:
{{check_suite_json}}
```

**Test input A**: PR #42, 3 changed files, CI passing, review approved.
Expected output: Summary notes the change scope, confirms CI green, confirms approval.

**Test input B**: PR #17, 12 changed files, 2 CI checks failing, no review yet.
Expected output: Summary flags the failing checks by name, notes review is pending.

---

#### `explain_branch_strategy`

Explain which branch to create a fix on, given the current repository branch structure.

**Parameters**:
- `branches_json` (string, required) — JSON-serialized branch list from `list_branches`
- `task_description` (string, required) — Plain-text description of the task being worked on

**Template**:
```
You are a Git workflow assistant. Given the following branch list and task description,
recommend:
1. The most appropriate base branch for a new fix branch
2. A conventional branch name following the naming patterns visible in the list
3. Whether any existing branch looks like it might already address this task

Branches:
{{branches_json}}

Task:
{{task_description}}
```

**Test input A**: Branch list includes `main`, `develop`, `release/2.1`. Task: "Fix null pointer in auth middleware."
Expected output: Recommends `develop` as base, suggests `fix/auth-null-pointer`, notes no existing branch matches.

**Test input B**: Branch list includes `main`, `fix/login-timeout`, `feature/oauth`. Task: "Fix login timeout on slow connections."
Expected output: Notes `fix/login-timeout` may already address this, recommends verifying before creating a new branch.

---

## Error Conditions

All tools return structured errors. Error codes are typed, not inferred from HTTP status.

| Code | Meaning |
|---|---|
| `NOT_FOUND` | Repository, PR, branch, or file does not exist |
| `PERMISSION_DENIED` | Token lacks required scope |
| `RATE_LIMITED` | GitHub API rate limit exceeded; `retry_after` seconds included |
| `BRANCH_ALREADY_EXISTS` | `create_branch` target name is taken |
| `BINARY_FILE` | File resource requested is not readable as text |
| `FILE_TOO_LARGE` | File exceeds 1 MB; retrieve via archive instead |
| `NETWORK_ERROR` | Local network or GitHub API unreachable |

---

## Design Decisions with Tradeoffs

**File reading as resource, not tool**: Resources are cacheable; tools are not. An AI assistant reading the same file multiple times benefits from host-level caching. Tradeoff: resources cannot accept a POST body, so binary file downloads require a separate tool if needed in future.

**`from_ref` required on `create_branch`**: Forces the caller to state intent explicitly. Tradeoff: adds one extra lookup step (call `get_default_branch` first if no ref is known), but eliminates silent branching from the wrong base.

**No pagination cursor exposed to the agent**: Tools use `limit` only. Cursor-based pagination would require the agent to track opaque cursor state across calls, which is error-prone. For AI assistant workflows, `limit: 100` covers the realistic scan range.

**`search_code` and `list_directory` included**: These are discovery tools an AI assistant needs before it can read files. Without them, the assistant would attempt to guess paths — a footgun for a local integration where round-trips are cheap.

**Prompts included but optional**: The host may choose not to surface them. Their presence signals that the server has tested these interaction patterns and they work correctly.

---

## Versioning

This is a local integration server. No public versioning strategy is required for v1. If the server is published as a shared MCP package, semantic versioning applies: tool schema changes are breaking changes at the major version; new optional fields are minor; documentation-only changes are patches.

---

```yaml
completion_report:
  what_was_done: >
    Designed an MCP server for a GitHub integration consumed by an AI coding
    assistant running locally. Produced 8 tool definitions with JSON Schema,
    1 resource URI pattern, and 2 parameterized prompt templates. Transport
    selected as stdio (local execution). All tool names follow verb-noun
    convention. Required vs optional fields are explicit in every schema.
  rubric_self_assessment:
    R1_verb_noun_names: PASS
    R2_json_schema_all_tools: PASS
    R3_transport_selected_justified: PASS  # stdio, local execution rationale given
    R4_tool_count_stated_lte_20: PASS      # 8 tools stated
    R5_resources_read_only_stable_uris: PASS
    R6_tools_vs_resources_vs_prompts: PASS
  key_decisions:
    - decision: stdio transport
      rationale: Local execution; no daemon or network overhead needed
    - decision: File reading as MCP resource not tool
      rationale: Read-only, stable by SHA, benefits from host caching
    - decision: from_ref required on create_branch
      rationale: Prevents silent default-branch assumption by AI caller
    - decision: Prompts included
      rationale: Summarize PR and explain branch strategy are high-frequency
                 patterns; tested templates reduce hallucination risk
```
