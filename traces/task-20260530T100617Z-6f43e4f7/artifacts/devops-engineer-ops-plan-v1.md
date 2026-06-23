# RoboEase — DevOps Operations Plan v7: Modular Monolith Refactoring

## 1. Executive Summary

This v7 ops plan aligns the CI/CD pipeline infrastructure with the architect's ADR for **Modular Monolith** refactoring. The key addition is **module boundary enforcement** in CI — preventing regressions into tight coupling during the refactoring — plus enhanced secret management, deployment verification, and rollback hardening.

### v7 Changes (from v6)

| File | Change | Rationale |
|---|---|---|
| `.github/workflows/ci.yml` | Added `backend-module-check` job with import-linter | Enforces `core → api → services → infrastructure` dependency rules from ADR |
| `backend/.importlinter` (new) | Import-linter contracts for all module boundaries | Prevents cross-boundary imports (e.g., `api` importing directly from `infrastructure`) |
| `backend/ruff.toml` (new) | Ruff config with module-boundary lint rules | Prevents cross-boundary imports with isort and per-file-ignores for legacy modules |
| `.github/workflows/ci.yml` | Added `backend-migration-check` job | Validates legacy `config/` → `core/` and `db/` → `infrastructure/` migration progress |
| `.github/workflows/deploy.yml` | Added `rollback-snapshot` step in db-migrate | Takes timestamped DB snapshot before each migration for point-in-time recovery |
| `scripts/rollback.sh` | Enhanced with snapshot-based restore | Point-in-time recovery from timestamped snapshots |
| `Makefile` | Added `check-modules`, `check-migration` targets | Local pre-push validation of module boundaries |

### Architecture Alignment

The ADR defines this module structure and dependency graph:

```
core/          ← No business logic; configuration, settings, DI
  ↓ (can depend on)
api/           ← Thin route handlers; delegates to services
  ↓
services/      ← Business logic; orchestrates infrastructure
  ↓
infrastructure/ ← DB entities, MQTT, Redis, external APIs
schemas/       ← Pydantic models (leaf — depends on nothing internal)
```

**Forbidden patterns:**
- `api/` importing directly from `infrastructure/` (must go through `services/`)
- `infrastructure/` importing from `services/` or `api/` (circular)
- Any module importing from `config/` (legacy — use `core/` instead)
- Any module importing from `db/database.py` directly (legacy re-exports — use `infrastructure/`)

---

## 2. CI/CD Pipeline Architecture (Post-Refactoring)

### 2.1 Enhanced CI Pipeline (`ci.yml`) — 14 Jobs

```
push/PR (main, develop)
  │
  ├── changes (dorny/paths-filter@v3)
  │
  ├── backend-lint              [ruff + mypy]
  ├── backend-module-check  ★   [import-linter: enforce ADR boundaries]
  ├── backend-migration-check★  [verify legacy imports decreasing]
  ├── backend-test              [pytest + MySQL/Redis services]
  ├── dbscripts-validate        [MySQL syntax check]
  ├── frontend-admin            [pnpm → vue-tsc → lint → build]
  ├── frontend-portal           [pnpm → vue-tsc → lint → build]
  ├── frontend-webui            [pnpm → build]
  ├── frontend-planweb          [pnpm → vue-tsc → build]
  ├── robot-lint                [ruff entire robot/]
  ├── robot-test                [pytest agent + modules]
  ├── robot-planbe-lint         [ruff planbe]
  ├── robot-planbe-test         [pytest planbe]
  ├── docker-smoke              [build 6 images — validates all contexts]
  └── ci-gate                   [aggregate results]
```

**★ = New in v7**

### 2.2 Enhanced Deploy Pipeline (`deploy.yml`)

```
trigger: workflow_run (main CI pass) OR workflow_dispatch
  │
  ├── deploy-gate               [set env + SHA]
  ├── build-push                [push 6 images to GHCR]
  ├── approve-production        [manual gate for production]
  ├── preflight-check           [idempotency: skip if SHA already deployed]
  ├── db-migrate                [snapshot★ → backup → apply DML → verify]
  ├── deploy                    [pull → restart → health check → Slack]
  └── skip-notify               [already-deployed notification]
```

**★ = Enhanced in v7 with snapshot-based recovery**

---

## 3. New CI Jobs: Module Boundary Enforcement

### 3.1 `backend-module-check` — Import Linter

Runs `lint-imports --config backend/.importlinter` against the backend codebase. Fails the build if any forbidden cross-boundary imports are detected. Uses pip caching for fast execution.

**Contracts enforced:**
- `api/` must not import from `infrastructure/`, `config/`, or `db/`
- `services/` must not import from `api/`, `config/`, or `db/`
- `infrastructure/` must not import from `services/`, `api/`, `config/`, or `db/`
- `core/` must not import from `api/`, `services/`, or `infrastructure/`
- `schemas/` must not import from `services/` or `infrastructure/`
- All modules: use `core/` instead of `config/` (legacy)
- All modules: use `infrastructure/` instead of `db/` (legacy re-exports)

### 3.2 `backend-migration-check` — Legacy Migration Progress

Counts remaining imports from `config/` and `db/` across the backend. Always passes (monitoring check) but blocks when `LEGACY_IMPORTS_ALLOWED=false` (CI/staging/production). Outputs counts at `>50` (warning), `>0` (notice), or `0` (success).

---

## 4. Module Boundary Configuration Files (Delivered)

### 4.1 `backend/.importlinter` — Created

Contains 8 import-linter contracts with explicit `source_modules`, `forbidden_modules`, `ignore_imports`, and `message` fields. Validated via `configparser` — 8 sections parse successfully.

### 4.2 `backend/ruff.toml` — Created

Ruff config with `target-version = py313`, lint rules (`E,W,F,I,N,B,C4,SIM,TCH,RUF`), per-file ignores for legacy modules (`config/*.py`, `db/database.py`), isort configuration with `known-first-party = ["core", "api", "services", "infrastructure", "schemas"]`. Validated via `tomllib`.

---

## 5. Environment Boundaries

| Environment | Purpose | Trigger | Image Source | Compose File | Module Boundary Gate |
|---|---|---|---|---|---|
| **development** | Local dev, hot-reload | `make dev` | Local `docker build` | `docker/edge/docker-compose.yaml` | Warning only |
| **ci** | Automated test infra | PR/push CI | Service containers | `docker/docker-compose.ci.yml` | Hard gate (block) |
| **staging** | Integration + pre-prod | CI pass on `main` | `ghcr.io/.../<sha>`, `:staging` | `docker/docker-compose.prod.yaml` | Hard gate |
| **production** | Live customer-facing | `workflow_dispatch` | `ghcr.io/.../<sha>` | `docker/docker-compose.prod.yaml` | Hard gate |

### `LEGACY_IMPORTS_ALLOWED` Toggle

| Environment | Value | Behavior |
|---|---|---|
| development | `true` | Warnings only; migration in progress |
| ci / staging / production | `false` | Hard gate — blocks on legacy imports |

---

## 6. Secrets Management

### 6.1 Required Secrets — Where to Set Them

All secrets are **referenced, never embedded**. Each has a single source of truth and a clear lifecycle.

| Secret | Source | Set In | Rotation | Fallback |
|---|---|---|---|---|
| `JWT_SECRET_KEY` | `openssl rand -hex 32` | Host `.env` → Docker compose env | 90 days | None (required) |
| `JWT_ALGORITHM` | Static (`HS256`) | `.env.example` (public) | N/A | `HS256` |
| `MYSQL_ROOT_PASSWORD` | `openssl rand -hex 16` | Host `.env` → Docker compose env | 90 days | None (required, `:?err`) |
| `REDIS_PASSWORD` | `openssl rand -hex 16` | Host `.env` → Docker compose env | 90 days | Empty string (dev only) |
| `MQTT_PASSWORD` | `openssl rand -hex 16` | Host `.env` → Docker compose env | 90 days | Empty string |
| `OPENAI_API_KEY` | OpenAI dashboard | Host `.env` → Backend container env | Per provider policy | None (AI features unavailable) |
| `VOLCENGINE_ACCESS_KEY` | Volcengine console | Host `.env` → Backend container env | Per provider policy | None |
| `VOLCENGINE_SECRET_KEY` | Volcengine console | Host `.env` → Backend container env | Per provider policy | None |
| `DIFY_API_KEY` | Dify admin panel | Host `.env` → Backend container env | Per provider policy | None |
| `GITHUB_TOKEN` | GitHub auto-provisioned | `${{ secrets.GITHUB_TOKEN }}` in CI | Auto-rotated by GitHub | N/A |
| `DEPLOY_SSH_KEY` | `ssh-keygen -t ed25519` | GitHub Secrets → CI deploy job | 180 days | None (deploy blocked) |
| `SLACK_BOT_TOKEN` | Slack app dashboard | GitHub Secrets → CI notify job | Per Slack policy | None (notifications silent) |

### 6.2 No Secrets In (Verified)

- ✅ **No Dockerfiles** — All values are `ARG` or `ENV` with defaults referencing env vars
- ✅ **No docker-compose files** — All `${VAR:?err}` syntax references host `.env`
- ✅ **No application code** — All values from `os.environ.get()` or Pydantic `Settings`
- ✅ **No build artifacts** — `.dockerignore` excludes `.env`, `.gitignore` excludes `.env`
- ✅ **No logs** — Backend uses `loguru` with `LOG_LEVEL` filtering; no secret values in log format

---

## 7. Deployment Procedure

### 7.1 Development Deployment (Local)

```bash
cp .env.example .env && chmod 600 .env
make ci-check          # lint + type-check + module boundary check
make dev              # docker compose -f docker/edge/docker-compose.yaml up -d
```

### 7.2 Staging Deploy (Automatic on `main` push)

1. CI passes on `main` → triggers `deploy.yml`
2. `build-push` builds and pushes 6 images with tag `:staging` and `:<sha>`
3. `preflight-check` verifies commit not already deployed (idempotency)
4. `db-migrate`: snapshot → backup → apply DML → verify
5. `deploy`: pull → restart → health check (6 attempts, 10s intervals) → record SHA
6. Slack notification

### 7.3 Production Deploy (Manual with Approval Gate)

1. GitHub → Actions → Deploy → Run workflow → `environment=production`
2. `build-push` → **manual approval gate** (GitHub Environment `production`)
3. Same flow as staging: preflight → db-migrate → deploy → health check → Slack

---

## 8. Rollback Procedure

### 8.1 Service Rollback

```bash
ssh deploy@<host>
cd /opt/roboease
./scripts/rollback.sh backend              # Auto-detects previous tag
./scripts/rollback.sh backend abc1234      # Specific SHA tag
./scripts/rollback.sh all                  # All services
./scripts/rollback.sh planbe               # Planning backend
```

### 8.2 Database Rollback

```bash
./scripts/rollback.sh --list-backups
./scripts/rollback.sh --restore-db snapshot-20260530-120000.sql.gz
./scripts/rollback.sh --restore-db pre-deploy-backup-abc1234.sql.gz
./scripts/rollback.sh all --restore-db snapshot-20260530-120000.sql.gz  # Full recovery
```

### 8.3 Rollback Safety Guarantees

| Guarantee | Mechanism |
|---|---|
| Container state preserved | Docker inspect snapshot saved before rollback |
| Database safety copy | `mysqldump` with `--single-transaction` before restore |
| Interactive confirmation | Required for DB restore (`Type 'yes' to continue`) |
| Health check after rollback | 6 attempts, 5s interval, must reach `healthy` |
| Deployed SHA tracking | `.deployed-sha` updated on every deploy/rollback |
| Old images retained | `docker image prune --filter "until=72h"` keeps last 3 days |
| Override cleanup | Rollback override files auto-deleted after success |

---

## 9. Container Image Inventory

| Image | Source | Dockerfile | Build Context | Health Check |
|---|---|---|---|---|
| `roboease-python-base` | `backend/requirements.txt` | `docker/base/python-base/DOCKERFILE` | `.` | N/A (base) |
| `roboease-backend` | `backend/` | `docker/edge/backend/DOCKERFILE` | `backend` | `urllib` → `:8000` |
| `roboease-nginx` | `docker/edge/nginx/` | `docker/edge/nginx/DOCKERFILE` | `docker/edge/nginx` | `wget` → `:80` |
| `roboease-portal` | `frontend/portal/` | `docker/cloud/web/DOCKERFILE` | `.` (repo root) | `wget` → `:8081` |
| `roboease-admin-web` | `frontend/admin/` | `docker/edge/web/DOCKERFILE` | `.` (repo root) | `wget` → `:8080` |
| `roboease-planbe` | `robot/planning/backend/` | `docker/robot/planning-backend/DOCKERFILE` | `robot/planning/backend` | `curl` → `:8100` |

### Build Dependency Graph

```
roboease-python-base  ← base layer with pip deps
         ↓
roboease-backend      ← extends python-base

roboease-portal | roboease-admin-web | roboease-nginx | roboease-planbe  ← all parallel
```

---

## 10. Verification Paths

### 10.1 Pre-Push (Local)

```bash
make ci-check          # lint + type-check + module boundary check
make check-modules     # import-linter only
make check-migration   # legacy import counts
make build-base && make build-backend && make build-admin && make build-portal && make build-nginx && make build-planbe
```

### 10.2 CI Verification Gates

| Gate | Check | Pass Criteria |
|---|---|---|
| `backend-module-check` ★ | import-linter enforces ADR boundaries | Zero forbidden imports |
| `backend-migration-check` ★ | Legacy import count trending down | Block only if `LEGACY_IMPORTS_ALLOWED=false` |
| `backend-lint` | ruff check + format + mypy | Zero errors |
| `backend-test` | pytest against MySQL/Redis services | All tests pass |
| `frontend-admin` | vue-tsc + lint + build | All pass |
| `frontend-portal` | vue-tsc + lint + build | All pass |
| `docker-smoke` | Build all 6 images | All build successfully |
| `ci-gate` | Aggregate all job results | All succeeded or skipped |

### 10.3 Deploy Verification

```bash
ssh deploy@<host>
cd /opt/roboease
docker compose -f docker-compose.prod.yaml ps    # All "healthy"
cat .deployed-sha                                  # Current commit
curl -fsS -o /dev/null -w "%{http_code}" https://roboease.cn/      # 200
curl -fsS -o /dev/null -w "%{http_code}" https://admin.roboease.cn/ # 200
```

---

## 11. Makefile Additions (v7)

```makefile
.PHONY: check-modules
check-modules: ## Check module boundaries with import-linter (ADR enforcement)
	cd backend && pip install -q import-linter && lint-imports --config .importlinter

.PHONY: check-migration
check-migration: ## Count remaining legacy imports (config/, db/)
	@echo "config/ imports: $$(grep -rn 'from config\.' backend/ | grep -v 'config/setting.py' | grep -v 'config/dbconfig.py' | wc -l)"
	@echo "db/ imports:     $$(grep -rn 'from db\.' backend/ | wc -l)"

.PHONY: ci-check
ci-check: lint type-check check-modules ## Run checks that match CI before pushing (expanded v7)
```

---

## 12. Known Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| Legacy `config/` modules still referenced | Migration must be gradual | `LEGACY_IMPORTS_ALLOWED=true` in dev; migration track job in CI |
| `db/database.py` backward-compat re-exports | Can't remove until all consumers migrated | `.importlinter` allows `db.database → infrastructure` imports |
| Team size < 10 developers | Limited capacity for parallel migration | Modular monolith avoids distributed complexity |
| Robot hardware tests impossible in CI | Robot agent tests limited to unit tests | Pytest + mock services cover agent logic; hardware tests on edge devices |
| `web_ui` uses yarn, CI expects pnpm | CI fails if web_ui changes trigger paths-filter | Pending migration to pnpm or dual-package-manager CI path |
| GHCR as sole container registry | No multi-cloud registry redundancy | GHCR has 99.9% SLA; acceptable for current scale |

---

## 13. File Inventory (v7)

| File | Status | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | **Enhanced (v7)** | Added `backend-module-check`, `backend-migration-check` |
| `.github/workflows/deploy.yml` | **Enhanced (v7)** | Added `rollback-snapshot` to `db-migrate` |
| `backend/.importlinter` | **New (v7)** | ADR module boundary contracts (validated: 8 sections) |
| `backend/ruff.toml` | **New (v7)** | Ruff config with isort rules (validated: valid TOML) |
| `Makefile` | **Enhanced (v7)** | Added `check-modules`, `check-migration`; expanded `ci-check` |
| `scripts/rollback.sh` | **Enhanced (v7)** | Snapshot-based restore support |
| `artifacts/devops-engineer-ops-plan-v7.md` | **New (v7)** | This document |
| `docker/docker-compose.prod.yaml` | Stable (v4) | Prod: GHCR images with healthchecks |
| `docker/docker-compose.ci.yml` | Stable (v3) | CI infra: MySQL + Redis + EMQX |
| `docker/edge/docker-compose.yaml` | Fixed (v5) | Dev: Redis added, naming aligned |
| All Dockerfiles (8 files) | Stable | Multi-stage builds with healthchecks |
| `docker/deploy-build.sh` | Fixed (v5) | Image names aligned |
| `.env.example` | Created (v4) | Complete env template |

---

## 14. Completion Report

```yaml
what_was_done: >
  Designed enhanced CI/CD pipeline for RoboEase Modular Monolith refactoring.
  Added module boundary enforcement via import-linter (.importlinter with 8 contracts),
  legacy migration tracking job, snapshot-based rollback, and comprehensive deployment
  documentation. Created backend/.importlinter (validated: 8 sections) and backend/ruff.toml
  (validated: valid TOML). All pipeline stages are idempotent, all secrets are referenced
  not embedded, and rollback procedures are fully defined with safety guarantees.
key_decisions:
  - decision: Add import-linter to CI for ADR module boundary enforcement
    rationale: >
      The architect's ADR mandates strict module boundaries (core → api → services →
      infrastructure). Without automated enforcement, the modular monolith will
      degrade into a tightly-coupled ball of mud. Import-linter provides deterministic,
      version-controlled contracts that fail the build on violations.
  - decision: Add legacy migration tracking job (non-blocking initially)
    rationale: >
      The config/ → core/ and db/ → infrastructure/ migration must be gradual.
      A tracking job with LEGACY_IMPORTS_ALLOWED toggle lets teams see progress
      without blocking development. The toggle flips to false in CI/staging once
      migration is complete.
  - decision: Add snapshot-based database recovery to deploy pipeline
    rationale: >
      The existing pre-deploy backup covers the "before migration" state, but without
      timestamped snapshots, point-in-time recovery is impossible. Snapshots are
      cheap (gzipped SQL dumps) and provide a clear recovery target for each deployment.
  - decision: Keep single docker-compose deployment (no Kubernetes)
    rationale: >
      The architect's ADR confirms Modular Monolith for team size < 10. Kubernetes
      would add operational complexity without clear benefit. Docker Compose provides
      sufficient orchestration for the current scale.
handoff_focus:
  - security-engineer: Review secret management — all secrets are referenced, verify lifecycle and rotation compliance.
  - release-manager: Validate rollback procedure, snapshot recovery, and deploy gate approvals.
  - senior-engineer: Implement .importlinter contracts; ensure module structure matches ADR before CI gates activate.
  - qa-engineer: Verify module boundary checks don't produce false positives; ensure migration tracking is accurate.
open_questions:
  - Are there any cross-boundary imports that are intentional and need contract exceptions?
  - What is the target date for setting LEGACY_IMPORTS_ALLOWED=false in CI?
  - Should we add Dependabot or Renovate for automated dependency updates?
  - Should we move web_ui from yarn to pnpm to unify package managers?
  - Where are the robot hardware dependencies for edge deployment?
known_constraints:
  - Legacy config modules need gradual migration; cannot block deployment.
  - Team size < 10 limits operational complexity we can absorb.
  - Robot hardware tests cannot run in CI; limited to unit tests.
  - GHCR is the sole container registry; no multi-cloud redundancy.
  - web_ui uses yarn while other frontends use pnpm — needs resolution.
confidence_differential: 0.85
dissent_if_alone: null
iteration_context: >
  v7 builds on v6's build context fixes. The existing pipeline is mature and
  well-structured — this iteration adds governance (module boundaries) and
  safety (snapshot recovery) for the architect's refactoring initiative.
```