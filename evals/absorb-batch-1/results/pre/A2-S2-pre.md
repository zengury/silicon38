# Document Knowledge Base API — Design

## Design Rationale

The caller is an AI agent that needs to search documents, retrieve specific pages, and attach annotations. However, the same interfaces should be usable by any caller — human-facing frontends, batch jobs, or test harnesses — without any caller-specific branching in the API surface.

The three operations form natural resource groups:
- **Documents** — the top-level unit, searchable by content or metadata
- **Pages** — addressable sub-units of a document; returned as a projection of a document fetch or directly by page reference
- **Annotations** — caller-created notes attached to a page at a specific location

All mutations are explicit (no implicit side effects). Error conditions are typed; callers never inspect raw HTTP status codes to determine what went wrong.

Versioning: this API is versioned by URL prefix (`/v1/`). Breaking changes require a new major version with a deprecation notice period of at least 90 days.

---

## TypeScript Types

```typescript
// ─── Shared Primitives ────────────────────────────────────────────────────────

/** Stable, opaque identifier. Never parse or construct — treat as a string. */
type DocumentId = string & { readonly __brand: "DocumentId" };
type PageId     = string & { readonly __brand: "PageId" };
type AnnotationId = string & { readonly __brand: "AnnotationId" };

type ISOTimestamp = string; // "2026-06-23T14:00:00Z"

// ─── Document Search ──────────────────────────────────────────────────────────

interface SearchDocumentsRequest {
  /** Full-text query string. Required — cannot search with an empty query. */
  query: string;

  /** Constrain results to documents with all of these tags. Optional. */
  tags?: string[];

  /** Constrain results to documents authored by this user/system ID. Optional. */
  authorId?: string;

  /** Maximum number of results to return. Default 20, max 100. */
  limit?: number;

  /** Opaque cursor from a previous response's `nextCursor` field. */
  cursor?: string;
}

interface DocumentSummary {
  id: DocumentId;
  title: string;
  authorId: string;
  tags: string[];
  pageCount: number;
  createdAt: ISOTimestamp;
  updatedAt: ISOTimestamp;

  /** Excerpt of the best-matching passage, with match terms highlighted via <mark>. */
  excerpt: string;

  /** Relevance score in [0, 1]. Higher is more relevant. */
  relevanceScore: number;
}

interface SearchDocumentsResponse {
  results: DocumentSummary[];

  /** Present only when more results exist. Pass as `cursor` to fetch the next page. */
  nextCursor?: string;

  /** Total number of matching documents. May be an estimate for large corpora. */
  totalCount: number;
}

// ─── Page Retrieval ───────────────────────────────────────────────────────────

interface GetPageRequest {
  documentId: DocumentId;

  /**
   * 1-based page number within the document.
   * Use DocumentSummary.pageCount to know the valid range.
   */
  pageNumber: number;
}

interface PageContent {
  id: PageId;
  documentId: DocumentId;
  pageNumber: number;

  /** Plain-text content of the page. */
  text: string;

  /** Structured content as Markdown. Present when the source document supports it. */
  markdown?: string;
}

// ─── Annotations ─────────────────────────────────────────────────────────────

/**
 * A text range within a page, identified by character offsets into PageContent.text.
 * start is inclusive, end is exclusive (standard half-open interval).
 */
interface TextAnchor {
  start: number;
  end: number;
}

interface CreateAnnotationRequest {
  pageId: PageId;

  /** The passage being annotated. Anchors the annotation to a stable location. */
  anchor: TextAnchor;

  /** The annotation text. Plain text only; no embedded HTML. Max 4000 characters. */
  note: string;

  /**
   * Caller-supplied key/value pairs for filtering or downstream processing.
   * Example: { "source": "retrieval-pipeline", "confidence": "0.87" }
   */
  metadata?: Record<string, string>;
}

interface Annotation {
  id: AnnotationId;
  pageId: PageId;
  documentId: DocumentId;
  anchor: TextAnchor;
  note: string;
  metadata: Record<string, string>;
  createdAt: ISOTimestamp;
  createdBy: string; // authenticated caller identity
}

interface ListAnnotationsRequest {
  pageId: PageId;

  /** Return only annotations created by this caller identity. Optional. */
  createdBy?: string;
}

interface ListAnnotationsResponse {
  annotations: Annotation[];
}

// ─── Error Types ─────────────────────────────────────────────────────────────

type ApiErrorCode =
  | "QUERY_REQUIRED"           // SearchDocuments called with empty query
  | "DOCUMENT_NOT_FOUND"       // No document with that ID
  | "PAGE_OUT_OF_RANGE"        // pageNumber < 1 or > document.pageCount
  | "ANNOTATION_NOTE_TOO_LONG" // note exceeds 4000 characters
  | "ANCHOR_OUT_OF_BOUNDS"     // anchor references characters outside page text
  | "UNAUTHENTICATED"          // No valid credential presented
  | "FORBIDDEN"                // Caller lacks permission for this document
  | "RATE_LIMITED";            // Caller has exceeded their request quota

interface ApiError {
  code: ApiErrorCode;
  message: string; // human-readable; do not parse programmatically
  details?: Record<string, unknown>;
}
```

---

## REST Endpoint Mapping

| Operation | Method | Path |
|---|---|---|
| Search documents | `POST` | `/v1/documents/search` |
| Get a page | `GET` | `/v1/documents/{documentId}/pages/{pageNumber}` |
| Create annotation | `POST` | `/v1/pages/{pageId}/annotations` |
| List annotations | `GET` | `/v1/pages/{pageId}/annotations` |

`POST` is used for search (rather than `GET`) so the query body is never URL-encoded and length limits never apply.

---

## Usage Examples

### 1. Search, then read a matching page

```typescript
// Step 1: find documents about a topic
const searchResp: SearchDocumentsResponse = await api.post("/v1/documents/search", {
  query: "transformer attention mechanism",
  tags: ["machine-learning"],
  limit: 5,
} satisfies SearchDocumentsRequest);

const first = searchResp.results[0];
console.log(first.excerpt); // "…the <mark>attention mechanism</mark> maps a query…"

// Step 2: read the first page of the top result
const page: PageContent = await api.get(
  `/v1/documents/${first.id}/pages/1`
);

console.log(page.text.slice(0, 200));
```

### 2. Annotate a passage

```typescript
// Annotate characters 142–198 of a page
const annotation: Annotation = await api.post(
  `/v1/pages/${page.id}/annotations`,
  {
    pageId: page.id,
    anchor: { start: 142, end: 198 },
    note: "This passage contradicts the claim in Section 3 of doc XYZ.",
    metadata: { pipeline: "fact-check-v2", runId: "run-00441" },
  } satisfies CreateAnnotationRequest
);

console.log(annotation.id); // "ann_8f3a…"
```

### 3. Handle errors explicitly — no string-matching on messages

```typescript
try {
  await api.get(`/v1/documents/${docId}/pages/999`);
} catch (err: ApiError) {
  if (err.code === "PAGE_OUT_OF_RANGE") {
    // Caller knows the valid range from DocumentSummary.pageCount
    console.error("Requested page does not exist in this document.");
  } else if (err.code === "DOCUMENT_NOT_FOUND") {
    console.error("Document was deleted or ID is wrong.");
  }
}
```

---

## Design Decisions

**Search uses POST, not GET.** Queries can be long and structured. A GET with a long `?q=` parameter risks URL-length truncation at proxies and logging systems.

**Pagination uses opaque cursors, not page offsets.** Offset pagination breaks when the underlying index is updated between requests. Cursors are stable.

**`TextAnchor` uses character offsets into `PageContent.text`.** This makes anchors unambiguous regardless of rendering environment. Callers must use the `text` field (not `markdown`) to compute offsets.

**No batch-get endpoint at v1.** The primary use case is retrieving individual pages on demand. A batch endpoint would be added in v1.1 once access patterns are known.

**`metadata` on annotations is `Record<string, string>` only.** Restricting values to strings prevents callers from embedding nested objects that become opaque to search and filtering. Callers who need structured data should serialize it themselves.

**`createdBy` is server-assigned.** The server derives caller identity from the authentication credential. Callers cannot forge or spoof authorship.
