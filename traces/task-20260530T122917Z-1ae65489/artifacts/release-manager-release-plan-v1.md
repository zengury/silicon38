# RoboEase — Release Plan v3.1.0

**Release Manager:** release-manager
**Date:** 2026-05-30
**Task ID:** task-20260530T122917Z-1ae65489
**Artifact Ref:** `artifacts/release-plan-v4.md`
**Previous:** `artifacts/release-plan-v3.md` (v3.0.1 PATCH)

---

## 1. Release Summary

| Field | Value |
|---|---|
| **Version** | `3.1.0` |
| **Type** | **MINOR** — new backwards-compatible functionality |
| **Base version** | `3.0.1` (PATCH deployment fixes) |
| **Parent MAJOR** | `3.0.0` (breaking API path changes) |
| **Target environments** | staging → production |
| **Deployment method** | GitHub Actions `deploy.yml` workflow_dispatch |
| **Rollback window** | T+4h after production deploy |

## 2. Semantic Version Justification

**Decision: `3.1.0` (MINOR bump)** — Per SemVer 2.0.0, MINOR when adding backwards-compatible functionality.

| Criterion | Assessment | Conclusion |
|---|---|---|
| Incompatible API changes | **None.** All v3.0.x endpoints, schemas, and auth unchanged. | Not MAJOR |
| New backwards-compatible functionality | **YES.** 18 new infrastructure files: observability middleware (correlation IDs), health endpoints (`/health/live`, `/health/ready`), metrics (counters, gauges, RED), DI container (8 repo impls), domain error hierarchy, abstract port interfaces. CI/CD module governance (7 import-linter contracts, migration tracking). Snapshot-based DB recovery. | **MINOR** |
| Backwards-compatible bug fixes | None — foundation for future fixes via DI-enabled testability. | Not a driver |

**Why not PATCH:** The modular monolith infrastructure is a substantial new feature that adds observability, testability, and error handling — fundamental architectural improvements beyond a bug fix.

**Why not MAJOR:** Zero breaking changes. New modules are additive.

**APP_VERSION** updated in both `core/config.py` and `config/setting.py` from `"3.0.1"` → `"3.1.0"`.

## 3. Changelog — v3.1.0

### Added

#### Backend — Modular Monolith Infrastructure (18 new files)
- **`core/config.py`** — Centralized Settings singleton with 30 configuration values (database, JWT, CORS, Redis, MQTT, Dify, app metadata).
- **`core/security.py`** — `hash_password()` + `verify_password()` using SHA-256.
- **`core/exception_handlers.py`** — Structured JSON error responses with correlation IDs.
- **`infrastructure/db/connection.py`** — Lazy engine with connection pool (pool_size=20, max_overflow=40, pre_ping).
- **`infrastructure/db/entities.py`** — 31 SQLModel entities (~700 lines) mapping all MySQL tables: users, roles, menus, robots, tasks (standard/inspection/inventory), dashboards, AI/agent metadata, devices.
- **`infrastructure/observability/middleware.py`** — Correlation ID middleware. Every request gets `X-Request-ID`. Logs method/path/status/duration.
- **`infrastructure/observability/health.py`** — `/health/live` and `/health/ready` endpoints.
- **`infrastructure/observability/logging.py`** — Structured key=value log format.
- **`infrastructure/observability/metrics.py`** — Thread-safe counters, gauges, RED metrics (Rate/Errors/Duration).
- **`ports/repositories.py`** — 8 abstract repository interfaces: User, Robot, Role, Menu, Task, TaskDetail, TaskResult, Captcha.
- **`ports/config.py`** — `ConfigPort` abstract class for swappable config sources.
- **`di/container.py`** — 8 concrete SQLModel-backed repo implementations. Supports test injection via property setters.
- **`application/dto.py`** — `PageResult[T]` generic paginated result DTO.
- **`common/errors.py`** — Domain error hierarchy: `ConfigurationError`, `DomainError`, `NotFoundError`, `ValidationError`, `UnauthorizedError`, `ForbiddenError`.
- **`config/setting.py`** — Marked `[DEPRECATED]`; directs imports to `core.config`.

#### CI/CD — Module Boundary Governance
- **`.importlinter`** — 7 contracts: `api-layer`, `services-layer`, `infrastructure-layer`, `core-layer`, `schemas-layer`, `legacy-config`, `legacy-db`.
- **`backend-module-check` CI job** — Import-linter enforcement. Advisory (`continue-on-error`) while `LEGACY_IMPORTS_ALLOWED != false`.
- **`backend-migration-check` CI job** — Counts remaining `from config.` and `from db.` imports.

#### CI/CD — Database Recovery
- **Snapshot-based DB rollback** in deploy pipeline: timestamped gzipped `mysqldump` → GitHub Actions artifact (30-day retention).

#### Developer Tooling
- **Makefile** — 30+ targets: dev, CI pre-flight, module checks, deploy, rollback, cleanup.

### Changed
- `APP_VERSION` from `"3.0.1"` → `"3.1.0"` in both config files.
- `config/setting.py` docstring marked `[DEPRECATED]`.
- CI pipeline expanded from 14 to 16 jobs.
- `.env.example` updated with `LEGACY_IMPORTS_ALLOWED` docs.

### Fixed
*(No user-facing bugs. DI container enables fixing zero-test-coverage gap in future releases.)*

## 4. Breaking Changes

**None.** All v3.0.x API endpoints, database schemas, MQTT topics, and container contracts unchanged.

Migration notes (informational only):
- New `/health/live` + `/health/ready` endpoints are additive.
- `X-Request-ID` header is included in all responses.
- `config/setting.py` deprecated — existing imports continue to work.

## 5. Release Readiness Summary

### Quality Gates

| # | Item | Status |
|---|---|---|
| 1 | All new modules import + lint clean | ✅ PASS |
| 2 | Password hashing round-trips | ✅ PASS |
| 3 | DI container provides 8 repo implementations | ✅ PASS |
| 4 | Test injection works (MockRepo → container) | ✅ PASS |
| 5 | .importlinter has 7 valid contracts | ✅ PASS |
| 6 | CI pipeline idempotent + concurrency-locked | ✅ PASS |
| 7 | Docker builds reproducible (frozen-lockfile, pinned versions) | ✅ PASS |
| 8 | Unit test coverage ≥ 85% | ❌ **FAIL** — zero coverage (carry-over) |
| 9 | Integration/E2E tests | ❌ **FAIL** — none exist (carry-over) |
| 10 | SAST/DAST security scanning | ❌ **FAIL** — not in CI (carry-over) |
| 11 | 7 unpinned Python dependencies | ⚠️ CAUTION (carry-over) |
| 12 | web_ui yarn vs pnpm mismatch | ⚠️ CAUTION (carry-over) |

### Blocking Issues for Production

| # | Issue | Severity | Notes |
|---|---|---|---|
| 1 | **No backend test coverage** | 🔴 CRITICAL | DI container now ENABLES testing — previously blocked by @classmethod anti-patterns |
| 2 | No integration/E2E tests | 🔴 HIGH | v3.0.0 API path changes have no automated regression |
| 3 | No SAST/DAST in CI | 🟡 MEDIUM | Only static linting runs |
| 4 | Unpinned Python deps | 🟡 MEDIUM | 7 packages unconstrained |
| 5 | web_ui yarn/pnpm mismatch | 🟡 MEDIUM | CI expects pnpm, project uses yarn |

## 6. Deployment Coordination

### Sequence (staging → production, 14 steps)

| Step | Timing | Action |
|---|---|---|
| 1 | T-24h | Staging auto-deploy on CI pass. Verify snapshot creation. |
| 2 | T-23h | Smoke test: `GET /`, `/health/live`, `/health/ready`, `/api/v1/`, login, CRUD. |
| 3 | T-22h | Snapshot recovery test: download artifact → restore to DB → verify integrity. |
| 4 | T-22h | Verify `X-Request-ID` header in responses. |
| 5 | T-21h | Verify ALL v3.0.0 route prefixes unchanged. |
| 6 | T-21h | `make check-modules` → record baseline legacy import counts. |
| 7 | T-4h | Production approval gate. |
| 8 | T-0 | DB snapshot + backup + migration. |
| 9 | T-0 | Container deploy (6 images from GHCR). |
| 10 | T+2m | Health check (6 retries × 10s). |
| 11 | T+3m | Manual API smoke test. |
| 12 | T+4m | Verify X-Request-ID on production. |
| 13 | T+5m | Slack notification. |
| 14 | T+4h | Rollback window — monitor error rates, compare against correlation-ID logs. |

## 7. Rollback Procedure

### Container Rollback
```bash
./scripts/rollback.sh backend          # single service
./scripts/rollback.sh all              # all services
./scripts/rollback.sh portal abc1234   # specific SHA
```

### Database Rollback (NEW — Snapshot Recovery)
```bash
# Download from GitHub Actions → Artifacts → latest deploy run
# File: rollback-snapshot-{environment}-{timestamp}.sql.gz

gunzip -c rollback-snapshot-production-20260530-120000.sql.gz | \
  docker exec -i roboease-mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" digit_raas

# Or via rollback script
./scripts/rollback.sh --list-backups
./scripts/rollback.sh --restore-db rollback-snapshot-production-20260530-120000.sql.gz
```

### Decision Matrix

| Condition | Threshold | Action |
|---|---|---|
| Error rate spike | >2× baseline / 30 min | Immediate full rollback |
| Health endpoint failure | /health/live → non-200 | Rollback backend if persistent |
| API 404 spike | Any /api/v1/* 404 | Immediate full rollback |
| Core functionality broken | Login/Crud/Robot control | Immediate full rollback |
| MQTT disconnect | Robot fleet offline | Rollback EMQX if version-related |

### Nginx Requirement (MANUAL — pre-deploy)
```nginx
# Backend API (REQUIRED for v3.0.0+)
location ^~ /api/v1/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    # ... standard headers ...
}

# Health endpoints (NEW in v3.1.0)
location ^~ /health/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_read_timeout 5;
}
```

## 8. Files Modified

### New (21 files)
18 infrastructure files in `backend/` (core, infrastructure/db, infrastructure/observability, ports, di, application, common) + `.importlinter` + `Makefile` + `.env.example` update.

### Modified (4 files)
`backend/config/setting.py` (version + deprecated), `backend/core/config.py` (version), `.github/workflows/ci.yml` (2 new jobs), `.github/workflows/deploy.yml` (snapshot recovery).

### Verified Stable (20+ files)
All existing API routers, services, Docker configs, rollback script, deploy-build.sh, gitignore, dockerignore, pnpm workspace files — unchanged.

---

Full artifact at `artifacts/release-plan-v4.md` (832 lines).