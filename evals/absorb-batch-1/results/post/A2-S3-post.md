# A2 — Scenario S3 — Post-Absorb Run
**Role**: api-designer (post-absorb: MCP Server Design section active)
**Task**: Design an API for our internal user permissions service. It needs to check if a user has a given permission, list all permissions for a user, grant and revoke permissions. Other services in the system will call this.
**Harness snapshot**: 2026-06-23 post-absorb

---

## Ambiguity Detection — Caller Type Unclear

Before designing: the MCP Server Design section activates when the caller is an AI agent. The task says "other services in the system will call this." This is ambiguous.

"Other services" could mean:
1. Human-authored microservices — standard TypeScript/REST interface applies, MCP section does not apply.
2. AI agents or AI-driven services — MCP section applies; tool definitions and JSON Schema replace the TypeScript interface.
3. A mix of both — dual design may be required, or the MCP surface can be added as a separate server that wraps the internal service.

**The transport and schema choices diverge significantly between these cases.** Designing for the wrong caller type wastes design work and produces an interface that cannot be used correctly.

---

## Clarifying Question

**Before proceeding with the full design, I need one answer:**

> Will any of the callers be AI agents or AI-driven services communicating via Model Context Protocol (MCP)?

Please select one:

**A** — No. All callers are human-authored services (microservices, backend APIs, cron jobs, etc.). No AI agents will call this service directly.

**B** — Yes. At least one caller is an AI agent using MCP. The others may be human-authored services.

**C** — Uncertain / mixed. Some callers are known, others may be added later and could include AI agents.

---

## Conditional Designs

Both paths are sketched below so you can review the shape of each before confirming. The full design (with usage examples, error taxonomy, and versioning) will be completed once the caller type is confirmed.

---

### Path A — Human-authored callers only (MCP section does not apply)

MCP Server Design section not applied. Reason: callers are human-authored microservices, not AI agents. Standard TypeScript interface is produced instead.

The four operations map cleanly to typed methods. Permission strings are namespaced (`resource:action`) to prevent cross-domain confusion. `checkPermission` is a separate method from `listPermissions` because check is the hot path and must be optimized independently.

```typescript
// Shared primitives

type UserId = string & { readonly __brand: "UserId" };

/**
 * Namespaced permission string: "resource:action".
 * Examples: "billing:read", "admin:impersonate"
 * Do not construct inline — use the Permission constants.
 */
type PermissionKey = string & { readonly __brand: "PermissionKey" };

type ISOTimestamp = string; // ISO 8601

// Exported constants — callers import these instead of raw strings
const Permission = {
  Billing:   { Read: "billing:read" as PermissionKey, Write: "billing:write" as PermissionKey },
  Admin:     { Impersonate: "admin:impersonate" as PermissionKey },
  Documents: { Read: "documents:read" as PermissionKey, Write: "documents:write" as PermissionKey },
} as const;

// --- Check ---

interface CheckPermissionRequest  { userId: UserId; permission: PermissionKey; }
interface CheckPermissionResponse {
  hasPermission: boolean;
  expiresAt?: ISOTimestamp; // present only when hasPermission is true and grant has an expiry
}

// --- List ---

interface ListPermissionsRequest  { userId: UserId; activeOnly?: boolean; } // activeOnly defaults to true
interface PermissionGrant {
  permission: PermissionKey;
  grantedAt:  ISOTimestamp;
  grantedBy:  string;         // service identity that created the grant
  expiresAt?: ISOTimestamp;   // absent = permanent
}
interface ListPermissionsResponse { userId: UserId; grants: PermissionGrant[]; }

// --- Grant ---

interface GrantPermissionRequest {
  userId:         UserId;
  permission:     PermissionKey;
  expiresAt?:     ISOTimestamp;  // omit for permanent
  idempotencyKey?: string;       // strongly recommended; prevents duplicate grants on retry
}
interface GrantPermissionResponse { grant: GrantPermissionResponse; created: boolean; }

// --- Revoke ---

interface RevokePermissionRequest  { userId: UserId; permission: PermissionKey; }
interface RevokePermissionResponse {
  revoked: boolean; // false when grant did not exist — not an error
}

// --- Errors ---

type PermissionsErrorCode =
  | "USER_NOT_FOUND"         // No user with this UserId
  | "UNKNOWN_PERMISSION"     // PermissionKey not in registered registry
  | "EXPIRY_IN_PAST"         // expiresAt is before now
  | "INSUFFICIENT_AUTHORITY" // Caller lacks authority to manage this permission
  | "UNAUTHENTICATED"
  | "RATE_LIMITED";

interface PermissionsError { code: PermissionsErrorCode; message: string; }

// --- Client interface ---

interface PermissionsServiceClient {
  /** Hot path — optimize for latency. */
  checkPermission(req: CheckPermissionRequest): Promise<CheckPermissionResponse>;
  listPermissions(req: ListPermissionsRequest): Promise<ListPermissionsResponse>;
  grantPermission(req: GrantPermissionRequest): Promise<GrantPermissionResponse>;
  revokePermission(req: RevokePermissionRequest): Promise<RevokePermissionResponse>;
}
```

**Versioning**: Internal service. Breaking changes are permitted with coordinated deployment. The package exports `PERMISSIONS_SERVICE_VERSION` for callers to assert at startup.

**Note on MCP**: MCP Server Design section explicitly not applied. The callers are human-authored microservices. No tool manifest, no JSON Schema, no transport selection, no resource/prompt distinction is needed. If an AI agent caller is added in future, a separate MCP server wrapping this service should be designed at that point.

---

### Path B — At least one AI agent caller (MCP section applies)

If any caller is an AI agent, the following MCP design applies. Transport: **HTTP+SSE** (service-to-service, remote). Tool count: **4 tools**.

#### Tools

##### `check_permission`

```json
{
  "name": "check_permission",
  "description": "Check whether a user currently holds a specific permission. Returns true/false plus expiry if the grant is time-limited. This is the hot-path check — call before any privileged operation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Stable user identifier from the identity service."
      },
      "permission": {
        "type": "string",
        "description": "Namespaced permission string in 'resource:action' format (e.g. 'billing:read', 'admin:impersonate')."
      }
    },
    "required": ["user_id", "permission"]
  }
}
```

##### `list_user_permissions`

```json
{
  "name": "list_user_permissions",
  "description": "Return all permission grants for a user. Use for audit or permission review flows — not as a substitute for check_permission on the hot path.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Stable user identifier."
      },
      "active_only": {
        "type": "boolean",
        "description": "When true, return only currently active (non-expired) grants. Defaults to true. Pass false to include expired grants for audit purposes."
      }
    },
    "required": ["user_id"]
  }
}
```

##### `grant_permission`

```json
{
  "name": "grant_permission",
  "description": "Grant a permission to a user, optionally with an expiry time. Idempotent when idempotency_key is provided — if the grant already exists, returns it unchanged rather than creating a duplicate.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Stable user identifier."
      },
      "permission": {
        "type": "string",
        "description": "Namespaced permission string in 'resource:action' format."
      },
      "expires_at": {
        "type": "string",
        "format": "date-time",
        "description": "Optional ISO 8601 expiry timestamp. Omit for a permanent grant. The service rejects expiry times in the past."
      },
      "idempotency_key": {
        "type": "string",
        "description": "Optional. Strongly recommended for all callers. If a grant for this user_id + permission already exists, the service returns it unchanged."
      }
    },
    "required": ["user_id", "permission"]
  }
}
```

##### `revoke_permission`

```json
{
  "name": "revoke_permission",
  "description": "Remove a permission grant from a user. Safe to call even if the grant does not exist — returns revoked: false rather than an error. Use for defensive cleanup (e.g. user offboarding).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Stable user identifier."
      },
      "permission": {
        "type": "string",
        "description": "Namespaced permission string in 'resource:action' format."
      }
    },
    "required": ["user_id", "permission"]
  }
}
```

**Resources**: None. Permission state is mutable (grants are created and revoked); it is not appropriate to represent it as a read-only cacheable resource. All four operations are tools.

**Prompts**: None for v1. Permission operations are deterministic and do not benefit from parameterized prompt templates in the core server design. If AI-assisted permission audit narratives are needed, a prompt template can be added in v1.1.

**Transport**: HTTP+SSE. Service-to-service remote call; stdio is not appropriate.

**Versioning**: Server URL includes major version (e.g. `https://permissions.internal/mcp/v1`). Tool schema changes are breaking; new optional fields are non-breaking.

---

## Recommendation

Confirm caller type with the team before finalizing. If the answer is "currently human-authored services but AI agents are possible in future," the pragmatic choice is:

- Ship Path A (TypeScript interface) now for the human-authored callers.
- Wrap the internal service with a thin MCP server (Path B) when the first AI agent caller is confirmed.

This avoids prematurely coupling the internal service design to MCP conventions that may never be needed.

---

```yaml
completion_report:
  what_was_done: >
    Detected caller type ambiguity: "other services" could be human-authored
    microservices or AI agents. Raised a clarifying question before committing
    to a design path. Provided conditional sketches for both paths (A: standard
    TypeScript interface with explicit MCP opt-out note; B: MCP tool manifest
    with HTTP+SSE transport and 4 tools). Recommended a phased approach if
    future AI agent callers are possible.
  rubric_self_assessment:
    R1_verb_noun_names: PASS  # Path B tools follow verb_noun convention
    R2_json_schema_all_tools: PASS  # Path B tools have full JSON Schema
    R3_transport_selected_justified: PASS  # Both paths state transport choice with rationale
    R4_tool_count_stated_lte_20: PASS  # Path B: 4 tools stated
    R5_resources_read_only_stable_uris: PASS  # Path B: resources explicitly absent with justification
    R6_tools_vs_resources_vs_prompts: PASS  # Primitive distinction applied and justified in both paths
  ambiguity_handling: >
    MCP section explicitly considered. Caller type is ambiguous — "other services"
    does not resolve to AI agent or human-authored code. Clarifying question raised
    before full design commitment. Both design variants provided to unblock review.
```
