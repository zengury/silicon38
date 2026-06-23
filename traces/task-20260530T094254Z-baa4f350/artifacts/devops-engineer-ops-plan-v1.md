# RoboEase — DevOps Operations Plan v6

## 1. Executive Summary

This v6 ops plan performs a targeted refactor of the CI/CD pipeline infrastructure, fixing **build context misconfigurations** that would cause Docker image builds for the frontend services (portal, admin-web) to fail in both CI and deploy pipelines. The root cause is that the multi-stage Dockerfiles for frontend services require the repository root as build context (to resolve the pnpm workspace, lockfile, and shared workspace dependency `@roboease/shared`), but the pipeline configurations were using the individual frontend directory paths instead.

### v6 Changes Applied

| File | Change | Impact |
|---|---|---|
| `.github/workflows/deploy.yml` | Fixed `build-push` matrix: portal/admin-web `context: .` with `build_args: APP_DIR=...` | **CRITICAL** — deploy would fail for portal and admin-web images |
| `.github/workflows/ci.yml` | Added portal + admin-web to `docker-smoke` matrix; fixed contexts | **HIGH** — CI smoke test now validates all 6 images |
| `Makefile` | Fixed `build-admin` and `build-portal` targets: context `.` with `--build-arg APP_DIR=...` | **MEDIUM** — local Docker builds now match CI behavior |

### v5-v6 Cumulative Status

| Severity | Gap (from v5) | v6 Status |
|---|---|---|
| 🔴 **CRITICAL** | `pnpm-lock.yaml` files missing from frontend projects | **RESOLVED** — root `pnpm-lock.yaml` exists; pnpm workspaces use a single lockfile |
| 🔴 **HIGH** | Frontend Docker build contexts broken (portal, admin-web) | **FIXED in v6** |
| 🟡 **MEDIUM** | Docker smoke missing portal/admin-web | **FIXED in v6** |
| 🟡 **MEDIUM** | Makefile build targets wrong contexts | **FIXED in v6** |
| 🟡 **MEDIUM** | `web_ui` uses yarn but CI expects pnpm | **PENDING** — needs investigation of `robot/agent/web_ui/` |
| 🟡 **MEDIUM** | Backend source not in workspace | **PENDING** — blocked on upstream source availability |
| 🟢 **LOW** | Deprecated `version: '3.8'` in compose files | **PENDING** — cosmetic, remove when touching those files |

---

## 2. Root Cause Analysis: Build Context Mismatch

### The Problem

The multi-stage Dockerfiles for portal (`docker/cloud/web/DOCKERFILE`) and admin-web (`docker/edge/web/DOCKERFILE`) share an identical build pattern requiring repository root context for pnpm workspace resolution:

```dockerfile
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./      # FROM ROOT
COPY frontend/shared/package.json frontend/shared/tsconfig.json frontend/shared/  # FROM ROOT
COPY frontend/shared/src/ frontend/shared/src/               # FROM ROOT
```

### The Fix

Set the Docker build context to `.` (repository root) and pass `APP_DIR` as a build argument:

```bash
# Correct
docker build --build-arg APP_DIR=frontend/portal -f docker/cloud/web/DOCKERFILE .

# Wrong (would fail with "COPY failed: file not found in build context")
docker build -f docker/cloud/web/DOCKERFILE frontend/portal
```

### Affected Configurations

| Location | Before (v5) | After (v6) |
|---|---|---|
| `deploy.yml build-push portal` | `context: frontend/portal` | `context: .` with `build_args: APP_DIR=frontend/portal` |
| `deploy.yml build-push admin-web` | `context: frontend/admin` | `context: .` with `build_args: APP_DIR=frontend/admin` |
| `ci.yml docker-smoke` | Missing portal + admin-web | Added both with correct contexts |
| `Makefile build-admin` | `docker build ... frontend/admin` | `docker build --build-arg APP_DIR=frontend/admin ... .` |
| `Makefile build-portal` | `docker build ... frontend/portal` | `docker build --build-arg APP_DIR=frontend/portal ... .` |

---

## 3. CI/CD Pipeline Architecture (Post-Fix)

### 3.1 CI Pipeline (`ci.yml`) — 13 Jobs (unchanged topology, fixed docker-smoke)

```
push/PR (main, develop)
  ├── changes (dorny/paths-filter@v3)
  ├── backend-lint          [ruff + mypy]
  ├── backend-test          [pytest + MySQL/Redis services]
  ├── dbscripts-validate    [MySQL syntax check]
  ├── frontend-admin        [pnpm → vue-tsc → lint → build]
  ├── frontend-portal       [pnpm → vue-tsc → lint → build]
  ├── frontend-webui        [pnpm → build]
  ├── frontend-planweb      [pnpm → vue-tsc → build]
  ├── robot-lint            [ruff entire robot/]
  ├── robot-test            [pytest agent + modules]
  ├── robot-planbe-lint     [ruff planbe]
  ├── robot-planbe-test     [pytest planbe]
  ├── docker-smoke          [build 6 images — NOW INCLUDES portal + admin-web]
  └── ci-gate               [aggregate results]
```

### 3.2 Deploy Pipeline (`deploy.yml`) — 7 Jobs (fixed build contexts)

- `deploy-gate` → `build-push` (6 images, corrected contexts) → `approve-production` (manual for prod) → `preflight-check` (idempotency) → `db-migrate` → `deploy` → `skip-notify`

### 3.3 Container Image Build Matrix (Fixed)

| Image | Context | Dockerfile | Build Args |
|---|---|---|---|
| `roboease-python-base` | `.` | `docker/base/python-base/DOCKERFILE` | `PIP_INDEX_URL` |
| `roboease-backend` | `backend` | `docker/edge/backend/DOCKERFILE` | `PIP_INDEX_URL` |
| `roboease-nginx` | `docker/edge/nginx` | `docker/edge/nginx/DOCKERFILE` | `PIP_INDEX_URL` |
| `roboease-portal` | `.` **(fixed)** | `docker/cloud/web/DOCKERFILE` | `PIP_INDEX_URL`, `APP_DIR=frontend/portal` |
| `roboease-admin-web` | `.` **(fixed)** | `docker/edge/web/DOCKERFILE` | `PIP_INDEX_URL`, `APP_DIR=frontend/admin` |
| `roboease-planbe` | `robot/planning/backend` | `docker/robot/planning-backend/DOCKERFILE` | `PIP_INDEX_URL` |

---

## 4. Environment Boundaries (unchanged from v5)

| Environment | Purpose | Trigger | Image Source | Compose File |
|---|---|---|---|---|
| **development** | Local dev, hot-reload | `make dev` | Local `docker build` | `docker/edge/docker-compose.yaml` |
| **ci** | Automated test infra | CI workflow | Service containers | `docker/docker-compose.ci.yml` |
| **staging** | Integration + pre-prod | CI pass on `main` | `ghcr.io/.../<sha>`, `:staging` | `docker/docker-compose.prod.yaml` |
| **production** | Live customer-facing | `workflow_dispatch` | `ghcr.io/.../<sha>` | `docker/docker-compose.prod.yaml` |

---

## 5. Secrets Management

All secrets are **referenced, not embedded**:
- **GitHub Actions**: `${{ secrets.DEPLOY_SSH_KEY }}`, `${{ secrets.GITHUB_TOKEN }}`
- **Docker Compose**: `${MYSQL_ROOT_PASSWORD:?err}` — reads from host `.env`, fails clearly if missing
- **Container env**: Populated by docker-compose `environment:` block from host `.env`

**No secrets appear in any Dockerfile, YAML config, build artifact, or log.**

### Required Secrets (Set in GitHub Secrets, Not in Code)

| Secret | Where Set | Purpose |
|---|---|---|
| `DEPLOY_SSH_KEY` | GitHub Secrets | SSH deploy access |
| `GITHUB_TOKEN` | Auto-provisioned | GHCR push + checkout |
| `SLACK_BOT_TOKEN` | GitHub Secrets | Deploy notifications |
| `DB_PASSWORD` | GitHub Secrets | Backend DB connection (for migration job) |
| `DB_HOST`, `DB_USER`, `DB_NAME` | GitHub Secrets | DB migration target |
| `DEPLOY_USER`, `DEPLOY_HOST` | GitHub Secrets | Deploy target |

### Environment Variables (Per-Server `.env`, Not in Git)

| Variable | Location | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | Server `.env` (chmod 600) | Token signing |
| `MYSQL_ROOT_PASSWORD` | Server `.env` | Database admin |
| `REDIS_PASSWORD` | Server `.env` | Redis auth |
| `MQTT_PASSWORD` | Server `.env` | EMQX auth |
| `OPENAI_API_KEY` | Server `.env` | LLM provider |

---

## 6. Rollback Procedure

```bash
# Single service (auto-detects previous tag)
ssh deploy@<host> && cd /opt/roboease
./scripts/rollback.sh backend
./scripts/rollback.sh backend abc1234      # Specific SHA tag
./scripts/rollback.sh all                  # All services

# Database
./scripts/rollback.sh --list-backups
./scripts/rollback.sh --restore-db pre-deploy-backup-abc1234.sql.gz
```

**Safety guarantees:** Pre-rollback container state backup, pre-restore DB safety backup, interactive confirmation for DB restore, health check after service rollback, deployed SHA tracking for idempotency.

---

## 7. Verification Paths

### 7.1 Local Pre-Push Verification

```bash
make ci-check          # lint + type-check all components
make build             # build ALL 6 Docker images (NOW FIXED)
make dev               # start full dev stack
```

### 7.2 CI Docker Smoke (Now 6 Images)

The `docker-smoke` job validates all 6 images build: python-base, backend, nginx, portal **(new)**, admin-web **(new)**, planning-backend.

### 7.3 Deploy Verification

```bash
ssh deploy@<host> && cd /opt/roboease
docker compose -f docker-compose.prod.yaml ps    # All "healthy"
curl -fsS -o /dev/null -w "%{http_code}" https://roboease.cn/      # 200
curl -fsS -o /dev/null -w "%{http_code}" https://admin.roboease.cn/ # 200
```

---

## 8. Remaining Gaps

| # | Gap | Severity | Owner |
|---|---|---|---|
| 1 | `robot/agent/web_ui/` uses yarn; CI expects pnpm | 🟡 MEDIUM | Frontend team |
| 2 | Backend source not in workspace | 🟡 MEDIUM | Runtime/team |
| 3 | Robot planning backend has no tests | 🟡 MEDIUM | qa-engineer |
| 4 | Deprecated `version: '3.8'` in compose files | 🟢 LOW | DevOps |
| 5 | No container orchestration beyond docker compose | 🟡 MEDIUM | Architect |
| 6 | No automated secrets rotation schedule | 🟡 MEDIUM | Release-manager |
| 7 | Robot hardware cannot be tested in CI | 🟢 LOW | Robot team |

---

## 9. File Inventory (v6 Cumulative)

| File | v6 Status | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | **FIXED (v6)** | Added portal + admin-web to docker-smoke, fixed build contexts |
| `.github/workflows/deploy.yml` | **FIXED (v6)** | Fixed portal + admin-web build contexts and build-args |
| `Makefile` | **FIXED (v6)** | Fixed build-admin + build-portal targets |
| `docker/docker-compose.prod.yaml` | Stable (v4) | Prod: GHCR images with healthchecks |
| `docker/docker-compose.ci.yml` | Stable (v3) | CI infra: MySQL + Redis + EMQX |
| `docker/edge/docker-compose.yaml` | Fixed (v5) | Dev: Redis added, naming aligned |
| `docker/base/python-base/DOCKERFILE` | Stable (v3) | Python 3.13 base |
| `docker/edge/backend/DOCKERFILE` | Stable (v3) | Backend from python-base |
| `docker/edge/web/DOCKERFILE` | Stable (v3) | Admin web multi-stage |
| `docker/cloud/web/DOCKERFILE` | Stable (v2) | Portal multi-stage |
| `docker/edge/nginx/DOCKERFILE` | Stable (v4) | Nginx with healthcheck |
| `docker/edge/nginx/nginx.conf` | Fixed (v4) | Removed hardcoded IP |
| `docker/robot/planning-backend/DOCKERFILE` | Stable (v2) | PlanBE |
| `docker/deploy-build.sh` | Fixed (v5) | Image names aligned |
| `scripts/rollback.sh` | Created (v4) | Container + DB rollback |
| `.gitignore` | Created (v4) | Comprehensive gitignore |
| `.dockerignore` | Created (v4) | Comprehensive dockerignore |
| `.env.example` | Created (v4) | Complete env template |
| `package.json` | Exists | Workspace root package |
| `pnpm-workspace.yaml` | Exists | pnpm workspace config |
| `pnpm-lock.yaml` | Exists | Root workspace lockfile |
