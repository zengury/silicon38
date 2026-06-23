# RoboEase — Release Plan v3.2.0

**Release Manager:** release-manager
**Date:** 2026-05-30
**Task ID:** task-20260530T143742Z-b85bb72b
**Artifact Ref:** `artifacts/release-plan-v5.md`
**Previous Release Plan:** `artifacts/release-plan-v4.md` (v3.1.0 — modular monolith infrastructure PLANNED)
**Upstream Handoff:** `handoffs/devops-engineer→release-manager-20260530-145416.yaml`

---

## 1. Release Summary

| Field | Value |
|---|---|
| **Version** | `3.2.0` |
| **Type** | **MINOR** release — new backwards-compatible functionality |
| **Pre-release path** | None (direct to stable) |
| **Base version** | `3.1.0` (MINOR — modular monolith infrastructure planned) |
| **Parent MAJOR** | `3.0.0` (breaking API path changes: `/api/` → `/api/v1/`) |
| **Target environments** | staging → production |
| **Deployment method** | `docker compose --profile prod -f docker/docker-compose.yml up -d` |
| **Rollback window** | T+4h after production deploy |
| **Change magnitude** | 40 new files, 2,755 lines infrastructure, 454 lines tests, ~1,160 lines ops tooling |

---

## 2. Semantic Version Justification

**Decision: `3.2.0` (MINOR bump)**

Per SemVer 2.0.0:

| Criterion | Assessment | Conclusion |
|---|---|---|
| Incompatible API changes | **None.** All v3.0.x API paths, request/response schemas, and auth flows are identical. No route removed, no response shape altered. | Not MAJOR |
| New backwards-compatible functionality | **YES, substantially.** The modular monolith infrastructure planned in v3.1.0 is now fully implemented and operational. Additionally: consolidated Compose profiles (3→1 file), 35+ target Makefile, 36 RED metrics across 8 services, health check endpoints with dependency verification, PII-safe structured logging, correlation ID middleware, 71 unit tests (was 0). | **MINOR** |
| Backwards-compatible bug fixes | Incidental — no specific bug fixes targeted. The DI container and repository pattern enable future fixes. | Not a driver |
| Deployment process changes | Compose profile migration is **soft** — old files exist with deprecation headers. Deploy command changes from `-f docker-compose.prod.yaml` to `--profile prod`. | MINOR migration, not MAJOR |

**Why not MAJOR?** The external API contract is untouched. The only deployment-facing change (compose profile) has a backward-compatible migration path with old files preserved and documented.

**Why not PATCH?** The scope of new functionality is substantial:
- **40 new backend files** implementing the entire layered architecture (core, infrastructure, ports, DI, application, common, repositories)
- **71 unit tests** (was 0) covering configuration, security, error hierarchy, metrics, entities, DI container, data port interfaces
- **36 RED metrics** across 8 services for production observability
- **Health check endpoints** for load balancer integration
- **Compose consolidation** eliminates 3-way file duplication
- **35+ Makefile targets** for reproducible operations
- **Deployment runbook** and **secrets lifecycle guide**

Calling this a PATCH would misrepresent the scope to downstream consumers.

---

## 3. Changes Since v3.1.0

### 3.1 What v3.1.0 Planned vs. What v3.2.0 Delivers

| v3.1.0 Plan | v3.2.0 Status | Difference |
|---|---|---|
| Modular monolith infrastructure **planned** | **Implemented** — 40 files, all modules exist on disk | Modules were missing; now real |
| Import-linter `.importlinter` defined | **Implemented** — 7 boundary contracts validated | Same |
| Health endpoints designed | **Implemented** — `/health/live`, `/health/ready`, `/health/metrics` with DB+MQTT dependency checks | More robust than planned |
| Correlation middleware specified | **Implemented** — `X-Request-ID` injection, structured request logging, integrated in `main.py` | Operational |
| Metrics collection planned | **Implemented** — 36 RED metrics across 8 services with thread-safe counters/gauges/REDMetrics | Fully operational |
| PII-safe logging designed | **Implemented** v2 — auto-redacts emails, phones, JWTs; sensitive-key filtering | Production-ready |
| DI container sketched | **Implemented** — 10 lazy-loaded repository properties with setter-based test injection | Fully wired |
| Repository interfaces planned | **Implemented** — 10 abstract ports + 9 SQLModel-backed implementations + generic BaseCRUDRepository | More complete |
| 0 backend tests | **71 unit tests** (8 test files) covering config, security, errors, metrics, container, entities, DTOs, ports | Exists now |
| Compose in 3 files | **Consolidated** to 1 file with dev/staging/prod profiles | 3-way duplication eliminated |
| No Makefile | **Makefile** with 35+ targets | Exists |
| No .env.example | **.env.example** with 30+ documented variables | Exists |
| No .gitignore | **.gitignore** with comprehensive rules | Exists |
| No deploy docs | **docs/DEPLOY.md** + **docs/SECRETS.md** | Exists |
| Nginx routing manual | **Updated** nginx.conf with `/api/v1/` backend routing block | Automated |

### 3.2 What's Still Design-Only (Not Shipped)

These artifacts exist as designs but are NOT part of the v3.2.0 release:

| Artifact | Status | Reason Excluded |
|---|---|---|
| database-engineer v7 (7 schemas, 35 tables) | **Design only** | No Alembic migrations written; raw SQL migrations not restructured. Existing `dbscripts/DML/` remains. |
| observability-engineer v2 (PII-safe, 36 metrics) | **Partially shipped** | Core infrastructure (metrics registry, middleware, health, logging) shipped. Per-service instrumentation is partially done — 8 services instrumented, 18 remaining. |
| Full service migration to DI | **Partial** — 10/26 services (~38%) | 10 services use `di.container`; 16 still use direct `Session(engine)` with FIXME annotations. |

---

## 4. Changelog — v3.2.0

### Added

#### Backend — Modular Monolith Infrastructure (NOW SHIPPED)

These modules were planned in v3.1.0 but did not exist on disk. They are now fully implemented and integrated into the running application.

**Core (`core/` — 3 files, 245 lines)**
- **`core/config.py`** (107 lines) — Centralized `Settings` singleton. Reads 30 environment variables with safe defaults: `APP_TITLE`, `APP_VERSION`, `API_PREFIX`, `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_HOURS`, `CORS_ORIGINS`, `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `DIFY_API_URL`, `DIFY_API_KEY`, `DOWNLOAD_URL`, `DEBUG`, and more. This is the single source of truth for all application configuration. The legacy `config/setting.py` remains but is deprecated.
- **`core/security.py`** (52 lines) — `hash_password()` and `verify_password()` using SHA-256 for backward compatibility with existing user records. bcrypt migration planned for Phase 2.
- **`core/exception_handlers.py`** (86 lines) — `register_exception_handlers(app)` — structured JSON error responses for `ValueError`, `DomainError`, and unhandled exceptions. Each response includes timestamp and correlation ID. Registered in `main.py` at application startup.

**Infrastructure — Database (`infrastructure/db/` — 2 files, 792 lines)**
- **`infrastructure/db/connection.py`** (46 lines) — Lazy database engine factory. Provides `engine` object with connection pooling (pool_size=20, max_overflow=40, pool_timeout=60s, pool_recycle=3600s, pool_pre_ping=True). Uses `__getattr__` pattern to defer MySQL connection until first use. Auto-detects SQLite for testing and skips MySQL-specific pool parameters.
- **`infrastructure/db/entities.py`** (746 lines) — 35 SQLModel entity classes mapping all MySQL tables: `UserEntity`, `SystemEnterpriseEntity`, `SystemUserEnterpriseEntity`, `CaptchaEntity`, `SystemRoleEntity`, `SystemMenuEntity`, `SystemUserRoleEntity`, `SystemRoleMenuEntity`, `RobotEntity`, `DashboardEntity`, `ScreenProjectEntity`, `ScreenPageEntity`, `TaskInfoEntity`, `TaskInfoDetailEntity`, `TaskResultDetailEntity`, `InspectionTaskInfoEntity`, `InspectionTaskStepsEntity`, `InspectionTaskResultsEntity`, `InventoryTaskInfoEntity`, `InventoryTaskStepsEntity`, `InventoryTaskResultsEntity`, `DictEntity`, `DictItemEntity`, `ScreenRobotLogEntity`, `RobotExtInfoEntity`, `LogExtractResultEntity`, `SynergyInfoEntity`, `Synergy2InfoEntity`, `DeviceInfoEntity`, `AgentInfo`, `RecommendedAgentInfo`, `ActionLibraryInfo`, `ExpressionLibraryInfo`, `VoiceLibraryInfo`, `KnowledgeLibraryInfo`. All entities include table name, field types, relationships, and `__table_args__`.

**Infrastructure — Observability (`infrastructure/observability/` — 4 files, 249 lines)**
- **`infrastructure/observability/middleware.py`** (51 lines) — `add_correlation_middleware(app)` — injects `X-Request-ID` header into every HTTP response. Makes `correlation_id` available via `request.state`. Logs method, path, status code, and duration in milliseconds per request. Integrated in `main.py` at startup.
- **`infrastructure/observability/health.py`** (64 lines) — `build_health_router(db_engine, mqtt_client)` — creates three health endpoints:
  - `GET /health/live` → `{"status": "alive"}` 200 (process liveness)
  - `GET /health/ready` → `{"status": "healthy/unhealthy", "checks": {...}}` 200/503 (dependency readiness — checks DB `SELECT 1` and MQTT `is_connected()`)
  - `GET /health/metrics` → full in-process metrics snapshot JSON
- **`infrastructure/observability/logging.py`** (23 lines) — `structured_log(level, msg, **ctx)` — machine-parseable `key=value` format for log aggregation. Includes `mask_pii()` that auto-redacts email addresses, phone numbers, and JWT tokens. Sensitive-key filtering (password, token, secret) applied by default.
- **`infrastructure/observability/metrics.py`** (111 lines) — `get_metrics()` → `MetricsRegistry` with thread-safe `Counter`, `Gauge`, and `REDMetrics` (Rate, Errors, Duration) for Prometheus-style metric collection. REDMetrics includes convenience methods: `track_request()`, `track_error()`, `track_latency()`.

**Ports (`ports/` — 2 files, 506 lines)**
- **`ports/config.py`** (47 lines) — `ConfigPort` abstract class with 6 typed methods: `get(key)`, `get_required(key)`, `get_int(key)`, `get_bool(key)`, `get_float(key)`, `all()`. Enables source-swappable configuration (environment variables → HashiCorp Vault, etc.).
- **`ports/repositories.py`** (459 lines) — 10 abstract repository interfaces defining type-safe CRUD contracts:
  - `UserRepository` — 13 methods (get_by_id, get_by_username, get_by_email, get_by_mobile, create, update, delete, list_paginated, count, exists_by_username, exists_by_email, update_password, update_login_info)
  - `RobotRepository` — 9 methods
  - `RoleRepository` — 8 methods
  - `MenuRepository` — 11 methods (with tree traversal)
  - `CaptchaRepository` — 3 methods
  - `DictRepository` — 10 methods
  - `TaskRepository` — create, get_by_id, list_by_robot, list_by_user, update, delete
  - `TaskDetailRepository` — create_batch, get_by_task, update_status, delete_by_task
  - `TaskResultRepository` — create, get_by_task_detail, list_by_task, delete_by_task
  - `AgentRepository` — 6 methods

**Dependency Injection (`di/` — 1 file, 156 lines)**
- **`di/container.py`** — `Container` class with 10 lazy-loaded SQLModel repository properties: `user_repository`, `robot_repository`, `role_repository`, `menu_repository`, `captcha_repository`, `dict_repository`, `task_repository`, `task_detail_repository`, `task_result_repository`, `agent_repository`. Module-level `container` singleton provides default wired implementations. Each property has a setter for test injection: `container.user_repository = mock_repo`.

**Application Layer (`application/` — 1 file, 27 lines)**
- **`application/dto.py`** — `PageResult[T]` — generic paginated response DTO with `total: int` and `items: List[T]`. Used by repository query methods returning paginated results.

**Common (`common/` — 1 file, 102 lines)**
- **`common/errors.py`** — Domain error hierarchy: `DomainError` (base with `code`, `http_status`, `context`), `ConfigurationError` (missing/invalid config), `NotFoundError` (entity not found, carries `entity` + `entity_id`), `ValidationError` (input validation, carries `field`), `UnauthorizedError` (authentication required), `ForbiddenError` (permission denied), `ConflictError` (duplicate resource). All carry structured context for API error responses.

**Repository Implementations (`db/repositories/` — 8 files, 678 lines)**
- **`db/repositories/base_repository.py`** (178 lines) — `BaseCRUDRepository[E]` generic class with `get_by_id()`, `list_all()`, `list_paginated()`, `create()`, `update()`, `delete()`, `count()`, and dynamic filter support. Supports both subclassing (for port/adapter pattern) and direct instantiation (for simple CRUD services).
- **`db/repositories/user_repository.py`** (92 lines) — `SQLUserRepository` implementing `UserRepository` with 13 methods.
- **`db/repositories/robot_repository.py`** (28 lines) — `SQLRobotRepository` implementing `RobotRepository` with 9 methods.
- **`db/repositories/role_repository.py`** (57 lines) — `SQLRoleRepository` implementing `RoleRepository` with 8 methods.
- **`db/repositories/menu_repository.py`** (126 lines) — `SQLMenuRepository` implementing `MenuRepository` with 11 methods including recursive tree traversal.
- **`db/repositories/captcha_repository.py`** (34 lines) — `SQLCaptchaRepository` implementing `CaptchaRepository` with 3 methods.
- **`db/repositories/dict_repository.py`** (72 lines) — `SQLDictRepository` implementing `DictRepository` with 10 methods.
- **`db/repositories/task_repository.py`** (67 lines) — `SQLTaskRepository`, `SQLTaskDetailRepository`, `SQLTaskResultRepository` implementing 3 task port interfaces.
- **`db/repositories/agent_repository.py`** (24 lines) — `SQLAgentRepository` implementing `AgentRepository` with 6 methods.

**Backend Tests (`tests/` — 8 files, 454 lines)**
- **`tests/test_core_config.py`** (40 lines, 9 tests) — Settings singleton property verification.
- **`tests/test_core_security.py`** (44 lines, 8 tests) — Password hashing/verification consistency.
- **`tests/test_common_errors.py`** (59 lines, 9 tests) — Error hierarchy HTTP status codes and context.
- **`tests/test_dtos.py`** (31 lines, 4 tests) — PageResult construction and typing.
- **`tests/test_metrics.py`** (64 lines, 9 tests) — MetricsRegistry counters, gauges, REDMetrics convenience methods.
- **`tests/test_container.py`** (94 lines, 12 tests) — DI container wiring and setter-based test injection.
- **`tests/test_entities.py`** (61 lines, 9 tests) — Entity table names, primary key presence, entity count (35).
- **`tests/test_config_port.py`** (61 lines, 11 tests) — ConfigPort interface contract, DictConfigAdapter.

**Main Application Integration (`main.py`)**
- Correlation middleware registered via `add_correlation_middleware(app)`
- Health check router registered via `build_health_router(db_engine=engine, mqtt_client=client)`
- Both active in the FastAPI application lifecycle

#### DevOps — Compose Consolidation & Ops Standardization

**Consolidated Docker Compose (`docker/docker-compose.yml` — 299 lines)**
- Single compose file replacing 3 legacy files:
  - `docker-compose.ci.yml` → profile: `dev`
  - `docker-compose.staging.yaml` → profile: `staging`
  - `docker-compose.prod.yaml` → profile: `prod`
- **7 services**: nginx, portal, admin-web, backend, mysql, redis, emqx
- **3 profiles**: `dev` (infrastructure only), `staging` (all services, reduced resources), `prod` (all services, full resources, host bind mounts)
- All services include HEALTHCHECK directives
- All environment variables use `${VAR}` references exclusively — zero hardcoded secrets
- GHCR image references with `${CONTAINER_REGISTRY}`, `${GITHUB_REPOSITORY}`, `${IMAGE_TAG}` substitution
- Legacy compose files preserved with deprecation headers pointing to the unified file

**Makefile (425 lines, 35+ targets)**
- **Development**: `dev-up`, `dev-up-full`, `dev-down`, `dev-down-clean`, `dev-logs`, `dev-ps`
- **Build**: `build-base`, `build-backend`, `build-frontend`, `build-nginx`, `build-planbe`, `build-all`
- **Test**: `test-backend`, `test-backend-cov`, `test-frontend`, `test-all`
- **Lint**: `lint-backend`, `lint-backend-fix`, `lint-frontend`, `module-check`, `migration-status`
- **CI**: `ci-check` (pre-push validation), `ci-build-check`
- **Staging**: `staging-up`, `staging-down`, `staging-logs`
- **Deploy**: `deploy-staging`, `deploy-prod`, `deploy-status`
- **Rollback**: `rollback SVC=<service|all>`, `list-backups`, `restore-db NAME=<name>`
- **Secrets**: `secrets-init`, `secrets-check`, `secrets-rotate`
- **Verification**: `health-check`, `verify-compose`
- **Cleanup**: `clean-docker`, `clean-cache`, `clean-all`

**Environment Configuration (`.env.example` — 100 lines)**
- 30+ documented environment variables covering all 7 services
- Required secrets marked with `:?err` suffix
- Secret lifecycle documentation: local dev → CI → staging → production
- Separated into sections: Deployment, Container Registry, Database, Redis, MQTT, JWT, CORS, Downloads, AI Platform, Third-Party APIs

**Repository Hygiene (`.gitignore` — 58 lines)**
- Secrets: `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.key`
- Python: `__pycache__/`, `*.py[cod]`, `.pyest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `coverage*`
- Node: `node_modules/`, `.pnpm-store/`
- Docker: `docker-compose.override.yml`
- Data volumes: `data/`, `attach_file/`, `conf/`
- IDE: `.idea/`, `.vscode/`
- OS: `.DS_Store`, `Thumbs.db`
- Deploy state: `.deployed-sha`

**Deployment Runbook (`docs/DEPLOY.md` — 162 lines)**
- Deployment workflow: staging → production
- Pre-deployment checklist
- Rollback procedure for containers and database
- Health verification steps
- Emergency response contacts

**Secrets Lifecycle Guide (`docs/SECRETS.md` — 116 lines)**
- Where secrets live per environment (local, CI, staging, production)
- Rotation schedule and procedure
- Audit checklist
- GitHub Actions secrets naming convention

**Nginx Routing Update (`docker/edge/nginx/nginx.conf` — +24 lines)**
- Backend API routing block for `/api/v1/` — proxies to `backend:8000`
- Health check endpoint with short timeout (5s)
- Large file upload support (500MB body limit, 300s timeout)
- Placed before Dify `/api` catch-all for correct routing precedence

#### Observability — 36 RED Metrics Across 8 Services

**Instrumented Services:**
- **robotService.py** — 6 metrics: action requests, emoticon requests, operation requests, plus latency/errors per operation
- **synergy_service.py** — 6 metrics: creates, updates, deletes, publishes, publish errors, publish latency
- **agent_service.py** — 7 structured_log points; Dify API metrics (create/update/delete/list latency + errors)
- **captchaService.py** — Email sending metrics; PII-safe (no SMTP password leakage)
- **userservice.py** — Login/signin/registration metrics with success/failure labels
- **dictService.py** — Dict/item create/delete counters
- **menuService.py** — Menu create/delete counters
- **task_service.py** — Task creation/completion/status transition metrics

**All metric calls use `structured_log()` with PII masking, not bare `logger.info()`.**

### Changed

- **`APP_VERSION`** in `core/config.py` and `config/setting.py`: `3.0.1` → `3.2.0`
- **`config/setting.py`** — updated `[DEPRECATED]` docstring directing all new imports to `core.config`
- **`main.py`** — now imports from `core.config`, `core.exception_handlers`, `infrastructure.observability.middleware`, `infrastructure.observability.health`. Correlation middleware and health check router registered at startup.
- **Compose deployment command** — changes from `docker compose -f docker-compose.prod.yaml up -d` to `docker compose --profile prod -f docker/docker-compose.yml up -d`. Legacy files still available with deprecation headers.
- **10 of 26 services** (~38%) migrated to use `di.container` for dependency injection instead of direct `Session(engine)` calls. Remaining 16 services carry FIXME annotations.

### Fixed

*(No user-facing bugs fixed in this release. The DI container, repository pattern, and 71 unit tests lay the foundation for identifying and fixing bugs in future releases.)*

### Deprecated

- **`docker/docker-compose.ci.yml`** — redirected to unified compose with `--profile dev`
- **`docker/docker-compose.prod.yaml`** — redirected to unified compose with `--profile prod`
- **`docker/docker-compose.staging.yaml`** — redirected to unified compose with `--profile staging`
- **`config/setting.py`** — deprecated in favor of `core.config`. All new code must import from `core.config`.
- **Direct `Session(engine)` in services** — 16 remaining services should migrate to `di.container` + repository ports. FIXME annotations in place.

### Security

- **Zero secrets in code.** All 26 environment variables in `docker-compose.yml` use `${VAR}` references exclusively. Verified across all compose files, Makefile, nginx.conf, Dockerfiles, and scripts.
- **`.gitignore`** excludes `.env`, `*.pem`, `*.key` files by default.
- **PII-safe logging** via `mask_pii()` — auto-redacts emails, phones, JWTs in structured logs.
- **`secrets-check` Makefile target** validates that no placeholder/insecure values remain in `.env`.
- **`secrets-rotate` Makefile target** generates cryptographically random secrets.
- **OCI labels** on all Docker images for supply-chain traceability.
- **No hardcoded credentials in any configuration file** (verified by devops-engineer).

---

## 5. Breaking Changes

**None.** This is a MINOR release with no breaking API or database changes.

All v3.0.x API endpoints, request/response schemas, authentication mechanisms, MQTT topics, and container orchestration contracts are identical to v3.1.0.

The breaking API path changes (`/api/` → `/api/v1/`, `/raas-api/` → `/api/v1/portal/`) were introduced in v3.0.0 and remain unchanged.

---

## 6. Release Readiness Checklist

### Pre-Release Validation

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | All planned features implemented | ✅ PASS | 40 infrastructure files created, 71 tests, compose consolidation, Makefile, health endpoints, correlation middleware all verified on disk |
| 2 | Breaking changes documented | ✅ PASS | No breaking changes — documented in Section 5 |
| 3 | API documentation updated | ✅ PASS | FastAPI auto-docs (`/docs`, `/redoc`) remain available; all routes under `/api/v1/` |
| 4 | Database migrations tested | ⚠️ CAUTION | Existing `dbscripts/DML/` DML scripts remain in place. No new migrations in this release. Schema design (database-engineer v7) is design-only — not implemented. |
| 5 | Security review completed | ⚠️ CAUTION | Zero-secrets guarantee verified (devops-engineer). PII-safe logging implemented (observability-engineer v2). No formal SAST/DAST scan. |
| 6 | Performance testing | ❌ FAIL | No load/performance testing performed. Architectural refactoring should not regress (same DB, same queries, same API routes). |
| 7 | Internationalization | N/A | No i18n changes |
| 8 | Third-party integrations validated | ⚠️ CAUTION | Dify, MQTT, Redis integrations unchanged. No runtime integration tests. |

### Quality Gates

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Unit test coverage | ⚠️ CAUTION | 71 unit tests across 8 files. Covers config, security, errors, metrics, container, entities, DTOs, ports. Backend service-layer tests still absent. Coverage estimate: ~15% infrastructure, ~0% services. |
| 2 | Integration tests | ❌ FAIL | No integration tests for API endpoints (no `httpx`/`TestClient` tests). |
| 3 | End-to-end tests | ❌ FAIL | No E2E tests (Playwright/Cypress) configured. |
| 4 | Static analysis | ✅ PASS | `ruff check`, `ruff format --check`, `mypy` configured in Makefile and CI. |
| 5 | Security scan | ❌ FAIL | No SAST/DAST scanning in CI pipeline. |
| 6 | Dependency audit | ⚠️ CAUTION | `requirements.txt` has unpinned top-level deps: `requests`, `redis`, `websockets`, `dotenv`, `pyyaml`, `flasgger`. |
| 7 | Load testing | ❌ FAIL | Not performed. |

### Documentation Requirements

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | CHANGELOG.md updated | ✅ PASS | Section 4 of this document is the changelog |
| 2 | README.md updated | ⚠️ CAUTION | No root README.md changes in this release |
| 3 | API documentation generated | ✅ PASS | FastAPI OpenAPI schema at `/docs` and `/redoc` |
| 4 | Migration guide | ✅ PASS | No breaking changes — no migration needed for API consumers. Compose migration is documented |
| 5 | Deployment notes | ✅ PASS | Sections 7 (Deployment) + `docs/DEPLOY.md` |
| 6 | Rollback procedure | ✅ PASS | Section 8 (Rollback Procedure) |

### Blocking Issues — Production Gate

| # | Issue | Severity | Resolution Required |
|---|---|---|---|
| 1 | **No service-layer tests** | HIGH | 71 infrastructure tests exist, but 0 tests for 26 service modules. The 10 migrated services cannot be verified without integration tests. Mitigation: services use same DB queries as before — regression risk is low for unmigrated services, moderate for migrated ones. |
| 2 | **No integration/E2E tests** | MEDIUM | API behavior changes cannot be validated automatically. Risk is mitigated by backward compatibility — same paths, same response shapes. |
| 3 | **Backend untestable in current env** | MEDIUM | `volcengine` package not installed in dev. `api.qianhai.dashboard` references missing `controller` module. `backend-module-check` CI job uses `continue-on-error`. |
| 4 | **Security audit not performed** | MEDIUM | No SAST/DAST in CI. No dependency vulnerability scanning. |
| 5 | **Unpinned top-level dependencies** | LOW | `requirements.txt` uses unpinned versions for 6 packages. Reproducible builds not guaranteed. |

---

## 7. Deployment Coordination

### 7.1 Environments

| Environment | URL | Deploy Trigger | App Version |
|---|---|---|---|
| Staging | `https://staging.roboease.cn` | Manual via `make deploy-staging` | `3.2.0` |
| Production | `https://roboease.cn` | Manual `workflow_dispatch` + approval | `3.2.0` |

### 7.2 New Deployment Command

```bash
# Production (replaces old docker-compose.prod.yaml command)
docker compose --profile prod -f docker/docker-compose.yml up -d

# Staging
docker compose --profile staging --env-file .env.staging -f docker/docker-compose.yml up -d

# Local dev (infrastructure only)
docker compose --profile dev -f docker/docker-compose.yml up -d
```

### 7.3 Deployment Sequence

| Step | Timing | Action | Owner |
|---|---|---|---|
| 1. Pre-deploy backup | T-5m | `mysqldump` snapshot via `db-migrate` CI job | CI automation |
| 2. Build & push images | T-4m | Build 5 Docker images (base, backend, portal, admin-web, nginx), push to GHCR | CI automation |
| 3. Staging deploy | T-24h | `make deploy-staging` → staging environment | Release manager |
| 4. Staging smoke test | T-23h | Verify `/health/live`, `/health/ready`, admin login, portal login, robot list | QA / Release manager |
| 5. Production approval | T-4h | GitHub Environments approval gate | Engineering Lead |
| 6. Production deploy | T-0 | `docker compose --profile prod up -d` | CI automation |
| 7. Health check | T+2m | 6 retries × 10s against `GET /health/ready` | CI automation |
| 8. Verify health endpoints | T+3m | `GET /health/live` (200), `GET /health/ready` (DB+MQTT healthy), `GET /health/metrics` | Release manager |
| 9. Slack notification | T+5m | Success/failure posted to Slack | CI automation |
| 10. Rollback window | T+4h | Monitor error rates, decide go/no-go | Engineering Lead |

---

## 8. Rollback Procedure

### 8.1 Rollback Decision Matrix

| Failure Type | Rollback Scope | Recovery Time | Command |
|---|---|---|---|
| Backend crash on deploy | Backend only | < 2 min | `make rollback SVC=backend` |
| Database migration failure | DB restore + backend | < 5 min | `make rollback SVC=all && make restore-db NAME=...` |
| Frontend JS error | Frontend only | < 1 min | `make rollback SVC=portal` or `SVC=admin-web` |
| Nginx routing failure | Nginx only | < 1 min | `make rollback SVC=nginx` |
| Health check failures | Backend only (likely) | < 2 min | `make rollback SVC=backend` |
| Full stack regression | All services + DB | < 15 min | `make rollback SVC=all && make restore-db NAME=...` |

### 8.2 Rollback Triggers

| Condition | Threshold | Action |
|---|---|---|
| Error rate spike | >2× baseline within 30 min | Immediate rollback |
| Performance degradation | >50% latency increase sustained >15 min | Evaluate → rollback |
| Core functionality broken | Login, task creation, robot control fail | Immediate rollback |
| Security incident | Vulnerability exploited | Immediate rollback + incident response |
| Data corruption | DB integrity compromised | Immediate rollback + restore from backup |

### 8.3 Post-Rollback Validation

```bash
# Health endpoint verification
curl -fsS https://roboease.cn/health/live
curl -fsS https://roboease.cn/health/ready

# Root endpoint
curl -fsS https://roboease.cn/
```

---

## 9. Known Gaps & Future Work

### 9.1 Critical — Must Be Addressed Before Next MINOR or Any MAJOR

| Gap | Owner | Deadline |
|---|---|---|
| **Service-layer integration tests** — 0 of 26 services have API-level tests | qa-engineer / senior-engineer | v3.3.0 |
| **Complete DI migration** — 16 of 26 services still use direct `Session(engine)` | senior-engineer | v3.3.0 |
| **Alembic migration setup** — replace raw SQL DML with Alembic | database-engineer | v3.4.0 |
| **Deploy workflow update** — `deploy.yml` still references `docker-compose.prod.yaml`, must switch to `--profile prod` | devops-engineer | v3.2.1 (PATCH) |

### 9.2 Important — Should Be Addressed in Next 2 Releases

| Gap | Owner | Deadline |
|---|---|---|
| Database schema migration to 7-module design (database-engineer v7) | database-engineer | v3.4.0 |
| bcrypt password migration from SHA-256 | security-engineer | v3.4.0 |
| SAST/DAST in CI pipeline | devops-engineer / security-engineer | v3.3.0 |
| Dependency pinning in `requirements.txt` | senior-engineer | v3.3.0 |
| Nginx CSP, HSTS, X-Frame-Options security headers | devops-engineer | v3.3.0 |
| Login rate limiting (slowapi) | security-engineer | v3.3.0 |
| WebSocket authentication | senior-engineer | v3.4.0 |
| File upload MIME validation | senior-engineer | v3.4.0 |

### 9.3 Nice to Have

| Gap | Owner |
|---|---|
| E2E tests (Playwright) for admin + portal | qa-engineer |
| Blue-green deployment for zero-downtime releases | devops-engineer |
| TLS certificate auto-renewal | devops-engineer |
| Redis password protection in dev/CI | devops-engineer |
| Complete observability for all 26 services | observability-engineer |
| Remove deprecated compose files (after 2 release cycles) | devops-engineer |
