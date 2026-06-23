# A2 — Scenario S2 — Post-Absorb Run
**Role**: api-designer (post-absorb: MCP Server Design section active)
**Task**: Design an API for a document knowledge base. An AI agent will use it to search documents, retrieve specific pages, and add annotations. The service will be hosted and the agent will call it remotely.
**Harness snapshot**: 2026-06-23 post-absorb

---

## MCP Server Design: Document Knowledge Base

### Applicability check

The task description names "AI agent" as the consumer. This triggers the MCP Server Design section. The service is hosted and the agent calls it remotely, which selects **HTTP+SSE transport**.

Standard TypeScript interface output is NOT produced. MCP tool manifest replaces it.

---

## Transport

**HTTP+SSE** — the service is hosted remotely and the agent calls it over the network. stdio would require local subprocess execution, which is not possible for a remote hosted service. HTTP+SSE provides the required network-accessible server endpoint with streaming support for long-running operations (e.g. search over a large corpus).

Both transports are not used in v1 — stdio is excluded.

---

## Tool Count

**3 tools total** — well within the ≤ 20 per server limit.

---

## MCP Primitives

The three capabilities map to different MCP primitive types:

| Capability | Primitive | Reason |
|---|---|---|
| Search documents | Tool | Requires fresh query evaluation; not cacheable |
| Retrieve a specific page | Resource | Read-only, stable URI by document ID and page number |
| Add annotation | Tool | Mutation — creates state; cannot be a resource |

---

### Tools (queries requiring fresh computation and mutations)

#### `search_documents`

Search the knowledge base for documents matching a query.

```json
{
  "name": "search_documents",
  "description": "Search the knowledge base using a full-text query. Returns ranked document summaries with relevance scores and match excerpts. Use document IDs from results to retrieve pages via the doc:// resource.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Full-text search query. Cannot be empty."
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Optional. Constrain results to documents that have ALL of these tags."
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "description": "Maximum number of results to return. Defaults to 20."
      },
      "cursor": {
        "type": "string",
        "description": "Optional. Opaque pagination cursor from a previous response's next_cursor field."
      }
    },
    "required": ["query"]
  }
}
```

**Tradeoff**: `query` is required (not optional with a default). An empty or absent query would scan the entire corpus, return thousands of results, and produce no useful ranking — this is almost certainly a caller mistake. Failing fast with a typed error (`QUERY_REQUIRED`) is preferable to returning noise.

---

#### `add_annotation`

Add an annotation to a specific passage on a document page.

```json
{
  "name": "add_annotation",
  "description": "Attach a text annotation to a specific character range on a document page. The anchor must reference character offsets within the page's plain-text content. Returns the created annotation including its stable ID.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "page_id": {
        "type": "string",
        "description": "Stable page identifier, obtained from the doc:// resource response."
      },
      "anchor_start": {
        "type": "integer",
        "minimum": 0,
        "description": "Start character offset (inclusive) within the page's plain-text content."
      },
      "anchor_end": {
        "type": "integer",
        "minimum": 1,
        "description": "End character offset (exclusive) within the page's plain-text content. Must be greater than anchor_start."
      },
      "note": {
        "type": "string",
        "maxLength": 4000,
        "description": "Annotation text. Plain text only; no embedded HTML or Markdown."
      },
      "metadata": {
        "type": "object",
        "additionalProperties": { "type": "string" },
        "description": "Optional caller-supplied key/value pairs (string values only). Example: {\"source\": \"retrieval-pipeline\", \"confidence\": \"0.91\"}."
      }
    },
    "required": ["page_id", "anchor_start", "anchor_end", "note"]
  }
}
```

**Tradeoff**: Anchor is split into `anchor_start` / `anchor_end` rather than a nested object. Flat fields are less error-prone for an AI agent that generates JSON: a nested object requires the agent to produce a sub-object correctly, while two flat integers are unambiguous.

**Tradeoff**: `metadata` values are `string` only (not `any`). Nested objects in metadata become opaque to the server's search and filtering. Callers who need structured data should JSON-serialize it into a string value.

---

#### `list_annotations`

List annotations on a specific page, optionally filtered.

```json
{
  "name": "list_annotations",
  "description": "Return all annotations on a given page. Use to review existing annotations before adding a new one, or to retrieve annotation IDs for downstream processing.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "page_id": {
        "type": "string",
        "description": "Stable page identifier."
      },
      "created_by": {
        "type": "string",
        "description": "Optional. Return only annotations created by this caller identity."
      }
    },
    "required": ["page_id"]
  }
}
```

**Design note**: `list_annotations` is a tool (not a resource) because its results change over time as annotations are added. A resource is appropriate only for content that is stable and cacheable given the same URI. Annotation lists are mutable.

---

### Resources (read-only, stable URIs, cacheable)

#### `doc://{doc_id}/pages/{page_number}`

Read the content of a specific page from a document.

- **URI pattern**: `doc://{doc_id}/pages/{page_number}`
- **Examples**:
  - `doc://d8f3a1b2/pages/1`
  - `doc://d8f3a1b2/pages/7`
- **Read-only**: yes. Document page content does not change (documents are immutable after ingestion).
- **Cacheable**: yes. The URI is stable — same `doc_id` and `page_number` always returns the same content.
- **Response fields**:
  - `page_id` (string) — stable page identifier for use in `add_annotation` and `list_annotations`
  - `document_id` (string)
  - `page_number` (integer)
  - `text` (string) — plain-text content; use character offsets from this field for annotation anchors
  - `markdown` (string, optional) — structured Markdown content when available
- **Error conditions**: `DOCUMENT_NOT_FOUND`, `PAGE_OUT_OF_RANGE`, `FORBIDDEN`

**Design note**: Page retrieval is a resource, not a tool. Page content is immutable (documents are ingested once), so the same URI always returns the same bytes. The HTTP+SSE transport enables the host to cache resource responses by URI. If documents were mutable, this would need to be a tool.

---

### Prompts (parameterized templates)

Two prompt templates are provided.

#### `synthesize_search_results`

Synthesize a coherent answer from a set of retrieved document passages.

**Parameters**:
- `user_question` (string, required) — the original question the agent was asked
- `search_results_json` (string, required) — JSON-serialized array of `DocumentSummary` objects from `search_documents`
- `pages_json` (string, required) — JSON-serialized array of page contents retrieved for the top results

**Template**:
```
You are a knowledge retrieval assistant. The user asked:

"{{user_question}}"

The following documents were retrieved from the knowledge base:

Search Results:
{{search_results_json}}

Retrieved Pages:
{{pages_json}}

Synthesize a concise, accurate answer to the user's question based only on the retrieved
content. Cite the document ID and page number for each claim you make.
If the retrieved documents do not contain enough information to answer the question,
say so clearly rather than speculating.
```

**Test input A**: Question: "What is the attention mechanism in transformers?" Results include 3 documents with high relevance scores, pages contain the relevant sections.
Expected output: Concise explanation with citations like "(doc://d8f3a/pages/3)".

**Test input B**: Question: "What is the company's vacation policy?" Results have low relevance scores; pages contain unrelated HR documents.
Expected output: States that the knowledge base does not contain a clear answer to this question.

---

#### `annotate_key_claim`

Generate an annotation for a key claim found during retrieval, suitable for `add_annotation`.

**Parameters**:
- `page_text` (string, required) — plain-text content of the page from the resource response
- `claim` (string, required) — the specific claim or passage the agent identified as noteworthy
- `reason` (string, required) — why this claim is noteworthy (e.g. "contradicts source X", "supports hypothesis Y")

**Template**:
```
Given the following page text and identified claim, locate the exact character offsets
(anchor_start and anchor_end) for the claim within the page text, and compose a
concise annotation note (under 200 characters) explaining its significance.

Page text:
{{page_text}}

Claim:
{{claim}}

Reason this claim is noteworthy:
{{reason}}

Respond with a JSON object:
{
  "anchor_start": <integer>,
  "anchor_end": <integer>,
  "note": "<annotation text>"
}
```

**Test input A**: Page text is 800 characters. Claim: "attention weights sum to 1 via softmax." Reason: "Confirms the normalization assumption."
Expected output: JSON with correct character offsets and a concise note.

**Test input B**: Page text is 1200 characters. Claim: "the model achieves 94.2% accuracy." Reason: "Higher than baseline reported in Section 2."
Expected output: JSON with character offsets pointing to the accuracy figure and a comparative note.

---

## Error Conditions

All tools return structured errors. Consumers must not inspect HTTP status codes to determine error type.

| Code | Meaning |
|---|---|
| `QUERY_REQUIRED` | `search_documents` called with empty or absent query |
| `DOCUMENT_NOT_FOUND` | No document with the given ID exists |
| `PAGE_OUT_OF_RANGE` | `page_number` is < 1 or > document's page count |
| `ANCHOR_OUT_OF_BOUNDS` | Annotation anchor references characters outside the page text |
| `ANNOTATION_NOTE_TOO_LONG` | `note` exceeds 4000 characters |
| `UNAUTHENTICATED` | No valid credential presented |
| `FORBIDDEN` | Caller lacks access to this document |
| `RATE_LIMITED` | Caller has exceeded request quota; `retry_after` seconds included |

---

## Design Decisions with Tradeoffs

**Search is a tool, not a resource**: Search results depend on query content and corpus state; they are not stable for a given URI. Making search a resource would require encoding the query in the URI, which is fragile and prevents proper result caching semantics.

**Page retrieval is a resource, not a tool**: Documents are immutable after ingestion. `doc://{id}/pages/{n}` always returns the same content. The HTTP+SSE transport can cache resource responses, reducing latency for the agent when the same page is read multiple times during a session.

**Annotation mutation is a tool**: `add_annotation` creates server-side state. Resources are read-only by MCP convention; mutations must be tools.

**Flat anchor fields on `add_annotation`**: Reduces JSON generation error surface for an AI agent. A nested `anchor` object is easy to malform; two sibling integers `anchor_start` / `anchor_end` are unambiguous.

**HTTP+SSE transport, not stdio**: The service is hosted remotely. stdio requires a local subprocess; it cannot be used for a remote service.

---

## Versioning

This is a hosted public service. Versioning strategy: the MCP server URL includes the major version prefix (e.g. `https://kb.example.com/mcp/v1`). Breaking changes — removing tools, changing required fields, renaming tools — require incrementing the major version with a 90-day deprecation period for the previous version. New optional input fields and new tools are non-breaking and do not require a version bump.

---

```yaml
completion_report:
  what_was_done: >
    Designed an MCP server for a document knowledge base consumed by an AI agent
    over a remote hosted connection. Produced 3 tool definitions with JSON Schema,
    1 resource URI pattern (doc:// pages), and 2 parameterized prompt templates.
    Transport selected as HTTP+SSE (remote hosted service). Required vs optional
    fields are explicit in every schema. Tool/resource/prompt distinction is applied
    and justified for each capability.
  rubric_self_assessment:
    R1_verb_noun_names: PASS
    R2_json_schema_all_tools: PASS
    R3_transport_selected_justified: PASS  # HTTP+SSE, remote hosted rationale given
    R4_tool_count_stated_lte_20: PASS      # 3 tools stated
    R5_resources_read_only_stable_uris: PASS
    R6_tools_vs_resources_vs_prompts: PASS
  key_decisions:
    - decision: HTTP+SSE transport
      rationale: Remote hosted service; stdio requires local subprocess
    - decision: Page retrieval as MCP resource not tool
      rationale: Documents immutable after ingestion; same URI always returns same content
    - decision: Flat anchor fields (not nested object)
      rationale: Reduces JSON generation error surface for AI agent caller
    - decision: query required on search_documents
      rationale: Empty query is almost certainly a caller mistake; fail fast with typed error
```
