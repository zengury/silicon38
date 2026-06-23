## Frontend Refactoring — Eliminate Duplicates & Improve Module Structure

**Role:** senior-frontend
**Task ID:** task-20260531T163244Z-880b8dd4
**Date:** 2026-06-01

---

### Scope

Targeted the frontend monorepo (`frontend/`) of `/Users/ZQ/roboease` — a pnpm workspace with three packages: `shared`, `admin`, and `portal`. Identified and eliminated code duplication, removed dead code, and consolidated shared utilities into the `@roboease/shared` package.

---

### Changes

#### New Shared Modules (3 files in `frontend/shared/src/`)

| File | Purpose | Lines |
|------|---------|-------|
| `nprogress.ts` | Shared NProgress configuration (easing, speed, spinner, trickleSpeed, minimum) | 17 |
| `dom-utils.ts` | Shared DOM utilities: `hasClass`, `addClass`, `removeClass`, `isExternal` | 37 |
| `format-utils.ts` | Shared formatting: `formatGrowthRate` (growth rate → percentage string) | 21 |

**Total new code in shared:** 75 lines (single canonical copy)

#### Updated Re-exports (4 files)

| File | Before | After |
|------|--------|-------|
| `admin/src/utils/nprogress.ts` | 13-line NProgress config (duplicate) | 7-line re-export from @roboease/shared |
| `admin/src/utils/index.ts` | 57-line utility functions (duplicate) | 13-line re-export from @roboease/shared |
| `portal/src/utils/nprogress.ts` | 13-line NProgress config (duplicate) | 7-line re-export from @roboease/shared |
| `portal/src/utils/index.ts` | 57-line utility functions (duplicate) | 13-line re-export from @roboease/shared |

**Re-exports preserve full backward-compatible API surface** — all existing `@/utils` and `@/utils/nprogress` importers continue to work without changes.

#### Updated Barrel (1 file)

| File | Change |
|------|--------|
| `shared/src/index.ts` | Added 4 new export lines for NProgress, dom-utils, format-utils |

#### Deleted Dead Code (2 files)

| File | Reason |
|------|--------|
| `portal/src/utils/token.ts` | Redundant with `@roboease/shared`'s `cookieTokenStore`. Only consumed by `service.js` (also dead). |
| `portal/src/utils/service.js` | Legacy JS Axios HTTP client. Not imported by any file. References non-existent `@/store`. Portal already uses `@roboease/shared`-based `request.ts`. |

---

### Duplication Eliminated

| Module | Duplicated Between | Lines Consolidated |
|--------|-------------------|-------------------|
| `nprogress.ts` | admin + portal (identical) | 2×13 → 1×17 canonical |
| `utils/index.ts` | admin + portal (identical) | 2×57 → 1×58 canonical (split across dom-utils + format-utils) |
| `token.ts` | portal (redundant with shared `cookieTokenStore`) | Deleted (already exists in shared) |
| `service.js` | portal (redundant with shared HTTP client) | Deleted (dead code) |

**~140 lines of duplicate code eliminated. Net codebase reduction: ~80 lines.**

---

### Import Chain Verification

All existing importers remain intact:

- `admin/src/plugins/permission.ts` → `@/utils/nprogress` → `@roboease/shared` ✓
- `admin/src/views/dashboard/index.vue` → `formatGrowthRate` from `@/utils` → `@roboease/shared` ✓
- `admin/src/layouts/components/Menu/components/MenuItem.vue` → `isExternal` from `@/utils` → `@roboease/shared` ✓
- `admin/src/layouts/components/Menu/BasicMenu.vue` → `isExternal` from `@/utils/index` → `@roboease/shared` ✓
- `admin/src/layouts/views/MixLayout.vue` → `isExternal` from `@/utils/index` → `@roboease/shared` ✓
- `admin/src/components/AppLink/index.vue` → `isExternal` from `@/utils/index` → `@roboease/shared` ✓
- `admin/src/components/MenuSearch/index.vue` → `isExternal` from `@/utils` → `@roboease/shared` ✓

---

### Constraints Preserved

- **No external API behavior changed** — All re-exports expose identical function signatures and behavior.
- **No existing tests broken** — No frontend tests exist in the codebase.
- **Backward compatible** — All `@/utils` import paths resolve identically.
- **Incremental refactoring** — Changes are scoped to utility consolidation only; no structural changes to components, views, or stores.

---

### Open Observations

1. **Shared package has pre-existing type declaration gaps** — `nprogress`, `qs`, `js-cookie` lack `@types/*` devDependencies in shared's `package.json`. These are workspace-resolved at build time by admin/portal but cause `vue-tsc` warnings during type-check. Not introduced by this refactoring.
2. **`addClass`/`removeClass`/`hasClass` are exported but unused** — Present in the original utils/index.ts, preserved in the re-export chain, but no consumer imports them. Candidate for future removal.
3. **Portal has no store directory** — Despite `service.js` referencing `@/store`, the portal has no store implementation. Confirms `service.js` was dead code.
4. **No frontend tests exist** — The entire frontend codebase (admin, portal, shared) has zero test files. This is a gap for future work.

---

### Completion Report

```yaml
completion_report:
  what_was_done: "Eliminated frontend code duplication by consolidating identical utility modules (nprogress.ts, dom-utils.ts, format-utils.ts) into @roboease/shared. Replaced 4 duplicate files in admin and portal with re-exports. Deleted 2 dead files in portal (token.ts, service.js). All import chains verified intact."
  key_decisions:
    - decision: "Consolidate nprogress.ts, utils/index.ts into @roboease/shared rather than keeping separate copies"
      rationale: "Code was byte-for-byte identical between admin and portal. Single source of truth in shared eliminates drift risk."
    - decision: "Use re-exports in admin/portal rather than updating all importers to point to @roboease/shared directly"
      rationale: "Minimizes diff surface. All 7 existing importers continue to work without changes. Re-exports can be removed in a future pass when importers are updated."
    - decision: "Delete portal/src/utils/token.ts and service.js rather than migrating them to shared"
      rationale: "token.ts duplicates shared's cookieTokenStore. service.js is dead code — not imported anywhere, references non-existent @/store. Portal already uses shared-based request.ts."
  handoff_focus:
    - "Pre-existing type declaration gaps in shared package (nprogress, qs, js-cookie @types)"
    - "Zero frontend tests — test infrastructure gap"
    - "Unused exports (addClass, removeClass, hasClass) are preserved but unused"
    - "Portal's legacy service.js pattern may have existed in other branches"
  open_questions:
    - "Should shared's package.json declare nprogress as a peerDependency for cleaner type resolution?"
    - "Are there integration tests that exercise the frontend end-to-end?"
    - "Should the re-exports be removed and all importers updated to import directly from @roboease/shared?"
  known_constraints:
    - "No existing frontend tests to validate against"
    - "Type-check reveals pre-existing issues unrelated to this refactoring"
    - "Must not change external API behavior — all behavioral semantics preserved"
  confidence_differential: 0.05
  dissent_if_alone: null
  iteration_context: null
```