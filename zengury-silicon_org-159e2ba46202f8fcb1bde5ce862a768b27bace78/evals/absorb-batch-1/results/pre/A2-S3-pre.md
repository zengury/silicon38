# User Permissions Service API — Design

## Design Rationale

The caller is another internal service. The interface must be fast to call correctly, hard to call incorrectly, and impossible to misinterpret. The four operations — check, list, grant, revoke — are distinct enough that they each get their own typed signature rather than sharing a generic "mutation" envelope.

Permission strings are namespaced (`resource:action`) to prevent accidental cross-domain grants. Callers never construct permission strings ad hoc — they should use the constants exported alongside the types.

Versioning: this service is internal; breaking changes are permitted across service deployments with coordinated rollout. The package exports a `PERMISSIONS_SERVICE_VERSION` constant callers can assert against at startup.

---

## TypeScript Types

```typescript
// ─── Shared Primitives ────────────────────────────────────────────────────────

/** Stable user identifier. Source of truth is the identity service. */
type UserId = string & { readonly __brand: "UserId" };

/**
 * Namespaced permission string: "resource:action".
 * Examples: "billing:read", "billing:write", "admin:impersonate"
 *
 * Do not construct these strings inline. Use the Permission constants below.
 */
type PermissionKey = string & { readonly __brand: "PermissionKey" };

/** ISO 8601 timestamp string. */
type ISOTimestamp = string;

// ─── Permission Constants ─────────────────────────────────────────────────────
// Callers import these rather than writing raw strings.

const Permission = {
  Billing: {
    Read:  "billing:read"  as PermissionKey,
    Write: "billing:write" as PermissionKey,
  },
  Admin: {
    Impersonate: "admin:impersonate" as PermissionKey,
    ManageUsers: "admin:manage-users" as PermissionKey,
  },
  Documents: {
    Read:   "documents:read"   as PermissionKey,
    Write:  "documents:write"  as PermissionKey,
    Delete: "documents:delete" as PermissionKey,
  },
} as const;

// ─── Check Permission ─────────────────────────────────────────────────────────

interface CheckPermissionRequest {
  userId: UserId;
  permission: PermissionKey;
}

interface CheckPermissionResponse {
  /** True if the user currently holds this permission. */
  hasPermission: boolean;

  /**
   * Present when hasPermission is true and the grant has an expiry.
   * Absent when the grant is permanent or when hasPermission is false.
   */
  expiresAt?: ISOTimestamp;
}

// ─── List Permissions ─────────────────────────────────────────────────────────

interface ListPermissionsRequest {
  userId: UserId;

  /**
   * When true, only return permissions that are currently active (not expired).
   * Defaults to true. Pass false to include expired grants for audit purposes.
   */
  activeOnly?: boolean;
}

interface PermissionGrant {
  permission: PermissionKey;
  grantedAt: ISOTimestamp;
  grantedBy: string; // service or user identity that created the grant
  expiresAt?: ISOTimestamp; // absent = permanent
}

interface ListPermissionsResponse {
  userId: UserId;
  grants: PermissionGrant[];
}

// ─── Grant Permission ─────────────────────────────────────────────────────────

interface GrantPermissionRequest {
  userId: UserId;
  permission: PermissionKey;

  /**
   * When to expire this grant. Omit for a permanent grant.
   * The service rejects expiry times in the past.
   */
  expiresAt?: ISOTimestamp;

  /**
   * Idempotency key. If a grant for this userId + permission already exists,
   * the service returns the existing grant unchanged rather than creating a duplicate.
   * Strongly recommended for all callers.
   */
  idempotencyKey?: string;
}

interface GrantPermissionResponse {
  grant: PermissionGrant;

  /** True when the service created a new grant; false when it returned an existing one. */
  created: boolean;
}

// ─── Revoke Permission ────────────────────────────────────────────────────────

interface RevokePermissionRequest {
  userId: UserId;
  permission: PermissionKey;
}

interface RevokePermissionResponse {
  /**
   * True when a grant existed and was removed.
   * False when no matching grant existed — this is not an error.
   */
  revoked: boolean;
}

// ─── Error Types ─────────────────────────────────────────────────────────────

type PermissionsErrorCode =
  | "USER_NOT_FOUND"          // No user with this UserId in the identity service
  | "UNKNOWN_PERMISSION"      // PermissionKey is not in the registered permission registry
  | "EXPIRY_IN_PAST"          // GrantPermissionRequest.expiresAt is before now
  | "INSUFFICIENT_AUTHORITY"  // Calling service lacks authority to manage this permission
  | "UNAUTHENTICATED"         // No valid service credential presented
  | "RATE_LIMITED";           // Caller has exceeded their request quota

interface PermissionsError {
  code: PermissionsErrorCode;
  message: string; // human-readable; do not parse programmatically
  details?: Record<string, unknown>;
}
```

---

## Service Interface (Client Facade)

```typescript
interface PermissionsServiceClient {
  /**
   * Check whether a user currently holds a specific permission.
   * This is the hot path — optimise for latency.
   */
  checkPermission(req: CheckPermissionRequest): Promise<CheckPermissionResponse>;

  /**
   * Return all permission grants for a user.
   * Use for audit pages and permission management UIs, not for per-request checks.
   */
  listPermissions(req: ListPermissionsRequest): Promise<ListPermissionsResponse>;

  /**
   * Grant a permission to a user, optionally with an expiry.
   * Idempotent when an idempotencyKey is provided.
   */
  grantPermission(req: GrantPermissionRequest): Promise<GrantPermissionResponse>;

  /**
   * Remove a permission grant. Safe to call even if the grant does not exist.
   */
  revokePermission(req: RevokePermissionRequest): Promise<RevokePermissionResponse>;
}
```

---

## Usage Examples

### 1. Gate a privileged operation

```typescript
const { hasPermission } = await permissions.checkPermission({
  userId: requestingUser.id,
  permission: Permission.Billing.Write,
});

if (!hasPermission) {
  throw new ForbiddenError("User does not have billing write access.");
}

await processBillingUpdate(payload);
```

### 2. Grant a time-limited permission

```typescript
const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(); // 24 hours

const { grant, created } = await permissions.grantPermission({
  userId: targetUser.id,
  permission: Permission.Admin.Impersonate,
  expiresAt,
  idempotencyKey: `onboarding-flow-${targetUser.id}`,
});

console.log(created ? "New grant created." : "Grant already existed.");
console.log(`Expires: ${grant.expiresAt}`);
```

### 3. Audit a user's permissions

```typescript
const { grants } = await permissions.listPermissions({
  userId: auditSubject.id,
  activeOnly: false, // include expired grants for audit trail
});

for (const g of grants) {
  console.log(`${g.permission} — granted by ${g.grantedBy} at ${g.grantedAt}`);
  if (g.expiresAt) console.log(`  expires: ${g.expiresAt}`);
}
```

### 4. Revoke without needing to check first

```typescript
// Safe to call even if the permission was never granted.
const { revoked } = await permissions.revokePermission({
  userId: departingEmployee.id,
  permission: Permission.Admin.ManageUsers,
});

if (!revoked) {
  // Not an error — just informational logging.
  logger.info("Permission was already absent; nothing to revoke.");
}
```

---

## Design Decisions

**`checkPermission` is a distinct method, not derived from `listPermissions`.** The check path will be called on every authenticated request; it must be fast. Listing all grants and filtering client-side is wasteful and adds latency.

**`RevokePermissionResponse.revoked` is false, not an error, when no grant exists.** Callers should be able to revoke defensively (e.g., on user offboarding) without needing to check first. Making absence an error forces callers to add unnecessary try/catch logic.

**`GrantPermissionRequest.idempotencyKey` is optional but strongly recommended.** Retry logic in distributed systems can cause duplicate grant events. The idempotency key lets the service collapse them safely. Callers who omit it accept the risk of duplicate grants.

**Permission strings are namespaced (`resource:action`).** Flat strings like `"read"` are ambiguous across service domains. Namespacing prevents a `documents:read` grant from being misinterpreted as `billing:read`.

**No bulk grant/revoke at v1.** Bulk operations hide business logic (which grants succeeded, which failed) in ways that make error handling ambiguous. Add bulk in v1.1 once the error contract is understood.

**`grantedBy` is server-assigned.** The service derives the calling service identity from its credential. Callers cannot forge authorship.
