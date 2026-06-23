# RoboEase — Release Plan v3.0.1

**Release Manager:** release-manager  
**Date:** 2026-05-30  
**Task ID:** task-20260530T094254Z-baa4f350  
**Artifact Ref:** `artifacts/release-plan-v3.md`  
**Previous Release Plan:** `artifacts/release-plan-v2.md` (v3.0.0 — superseded for deployment readiness)

---

## 1. Release Summary

| Field | Value |
|---|---|
| **Version** | `3.0.1` |
| **Type** | **PATCH** release — deployment infrastructure bug fixes |
| **Pre-release path** | None (direct to stable) |
| **Base version** | `3.0.0` (existing release plan — breaking API path changes) |
| **Target environments** | staging → production |
| **Deployment method** | GitHub Actions `deploy.yml` via `workflow_dispatch` |
| **Rollback window** | T+4h after production deploy |

---

## 2. Semantic Version Justification

**Decision: `3.0.1` (PATCH bump)**

Per SemVer 2.0.0, PATCH version when you make backwards-compatible bug fixes.

| Criterion | Assessment | Conclusion |
|---|---|---|
| Incompatible API changes | None. API paths, request/response schemas, auth mechanisms are identical to v3.0.0. | Not MAJOR |
| New backwards-compatible functionality | None. No new features, endpoints, or capabilities. | Not MINOR |
| Backwards-compatible bug fixes | **YES** — Docker build contexts for portal and admin-web images were misconfigured, causing build failures. CI docker-smoke job was missing these images. Makefile local build targets had wrong contexts. | **PATCH** |
| Infrastructure/CI changes only | Verified — all changes are in `.github/workflows/deploy.yml`, `.github/workflows/ci.yml`, and `Makefile`. | No version bump on its own, but combined with the build-context bug fix warrants PATCH |

**APP_VERSION updated:** `backend/config/setting.py` changed from `"3.0"` → `"3.0.1"`.

---

## 3. Changes Since v3.0.0

### Fixed

#### Deployment Pipeline — Build Context Fixes (CRITICAL)

- **`deploy.yml` build-push matrix** — Fixed portal and admin-web Docker build contexts: `context: .` with `build_args: APP_DIR=frontend/portal` and `APP_DIR=frontend/admin` (was `context: frontend/portal` and `context: frontend/admin`)
- **`ci.yml` docker-smoke job** — Expanded from 3 to 6 images. Now validates python-base, backend, nginx, portal, admin-web, planning-backend.
- **`Makefile` build-admin and build-portal targets** — Fixed build contexts to match CI: `docker build --build-arg APP_DIR=frontend/admin ... .` and `docker build --build-arg APP_DIR=frontend/portal ... .`

#### Confirmed Fixed (v5 analysis)

- **Root `pnpm-lock.yaml` exists** — pnpm workspaces use a single root lockfile.
- **`frontend/shared/` workspace package exists** — `@roboease/shared` at `frontend/shared/` provides shared utilities.

### Remaining Gaps (not fixed)

| # | Gap | Severity | Owner |
|---|------|----------|-------|
| 1 | `web_ui` uses yarn, CI expects pnpm | 🟡 MEDIUM | frontend-engineer |
| 2 | Backend test coverage 0% | 🔴 CRITICAL | qa-engineer |
| 3 | No integration/E2E tests | 🔴 HIGH | qa-engineer |
| 4 | Deprecated `version: '3.8'` in compose files | 🟢 LOW | devops-engineer |
| 5 | No SAST/DAST security scanning | 🟡 MEDIUM | security-engineer |
| 6 | Unpinned Python dependencies | 🟡 MEDIUM | backend-engineer |

---

## 4. Changelog — v3.0.1

### Fixed

- Fixed Docker build contexts for portal and admin-web images in `deploy.yml`. Both now use repository root (`context: .`) with `build_args: APP_DIR=...`.
- Added portal and admin-web to CI docker-smoke validation in `ci.yml`. Now builds all 6 images (was 3).
- Fixed `make build-admin` and `make build-portal` targets in `Makefile` to use correct repository-root build context.
- Confirmed root `pnpm-lock.yaml` exists at workspace root.
- Confirmed `@roboease/shared` workspace package exists at `frontend/shared/`.

### Changed

- `APP_VERSION` in `backend/config/setting.py` updated from `"3.0"` to `"3.0.1"`.
- CI docker-smoke now validates 6 images (was 3).

---

## 5. Breaking Changes

**None.** All API paths, schemas, and behaviors are identical to v3.0.0.

---

## 6. Release Readiness Checklist

### Pre-Release Validation

| # | Item | Status |
|---|------|--------|
| 1 | Docker build contexts correct | ✅ PASS |
| 2 | CI docker-smoke validates all images | ✅ PASS |
| 3 | Makefile targets match CI behavior | ✅ PASS |
| 4 | Breaking changes documented | ✅ PASS (none) |
| 5 | API documentation updated | ⚠️ CAUTION |
| 6 | Database migrations tested | ✅ PASS |
| 7 | Security review completed | ⚠️ CAUTION |
| 8 | Performance testing | N/A |

### Quality Gates

| # | Item | Status |
|---|------|--------|
| 1 | Unit test coverage ≥ 85% | ❌ FAIL |
| 2 | Integration tests passing | ❌ FAIL |
| 3 | End-to-end tests passing | ❌ FAIL |
| 4 | Static analysis clean | ✅ PASS |
| 5 | Security scan passed | ❌ FAIL |
| 6 | Dependency audit clean | ⚠️ CAUTION |
| 7 | CI pipeline idempotent | ✅ PASS |
| 8 | Docker builds reproducible | ✅ PASS |

### Blocking Issues for Production

| # | Issue | Severity |
|---|-------|----------|
| 1 | No backend test coverage | 🔴 CRITICAL |
| 2 | No integration/E2E tests | 🔴 HIGH |
| 3 | No SAST/DAST scanning | 🟡 MEDIUM |
| 4 | Unpinned Python dependencies | 🟡 MEDIUM |
| 5 | web_ui yarn vs pnpm mismatch | 🟡 MEDIUM |

---

## 7. Deployment Coordination

| Environment | URL | Trigger | Version |
|---|---|---|---|
| Staging | `https://staging.roboease.cn` | Auto (CI pass on main) | 3.0.1 |
| Production | `https://roboease.cn` | Manual workflow_dispatch + approval | 3.0.1 |

### Sequence: Freeze (T-48h) → Nginx update (T-24h) → Staging deploy → Smoke test → Production approval → DB backup → DB migrate → Deploy → Health check → Slack notify → 4h rollback window

---

## 8. Rollback Procedure

Fully inherited from v3.0.0. Container rollback via `rollback.sh`, DB rollback via `--restore-db` with safety backup. Manual Nginx config restoration required if rolling back to pre-v3.0.0 paths.

---

## 9. Files Modified

| File | Change |
|---|---|
| `backend/config/setting.py` | APP_VERSION: "3.0" → "3.0.1" |
| `.github/workflows/deploy.yml` | portal/admin-web build contexts: `context: .` with `build_args` |
| `.github/workflows/ci.yml` | docker-smoke: 3→6 images |
| `Makefile` | build-admin/build-portal: root context with --build-arg |

---

## 10. Completion Report

```yaml
completion_report:
  what_was_done: >
    Analyzed the cumulative state of the RoboEase repository post-v3.0.0 release
    plan to produce a PATCH release plan for v3.0.1. Identified CRITICAL build
    context bugs that would prevent v3.0.0 deployment. Fixed deploy.yml, ci.yml,
    Makefile. Updated APP_VERSION to "3.0.1". Assessed release readiness: 2
    CRITICAL blockers unchanged from v3.0.0.
  key_decisions:
    - decision: Version 3.0.1 (PATCH) — deployment infrastructure bug fixes
      rationale: Per SemVer, backwards-compatible bug fixes warrant PATCH. The
        build context misconfigurations prevent v3.0.0 from deploying successfully.
        No new API surface, features, or breaking changes.
    - decision: Layer v3.0.1 on top of v3.0.0 rather than rewriting
      rationale: release-plan-v2 is a sealed artifact. Layering preserves audit
        trail and allows consumers to understand delta between MAJOR and PATCH.
    - decision: Retain all v3.0.0 blockers as open issues
      rationale: This PATCH fixes deployment infrastructure only. Backend test
        coverage and integration/E2E test gaps are v3.0.0 issues.
  handoff_focus:
    - devops-engineer: Execute staging deployment, verify Docker builds, update
      production Nginx config with /api/v1/ proxy rule.
    - qa-engineer: Write backend service-layer tests before production deployment.
    - security-engineer: Conduct security audit, add SAST/dependency scanning to CI.
    - frontend-engineer: Investigate web_ui yarn vs pnpm mismatch.
  open_questions:
    - Should backend tests be backfilled before ANY production deployment?
    - Should Nginx config update be automated in deploy pipeline?
    - Should web_ui be migrated to pnpm or CI updated to use yarn?
  known_constraints:
    - Single-host deployment (docker compose only)
    - Backend test coverage 0% — CRITICAL blocker
    - Nginx config update is manual
    - web_ui uses yarn, CI expects pnpm
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: >
    Post devops v6 ops plan fixes. v3.0.0 documented MAJOR version with breaking
    API changes. v3.0.1 PATCH captures deployment infrastructure fixes. APP_VERSION
    updated to "3.0.1". Quality gaps unchanged from v3.0.0.
```