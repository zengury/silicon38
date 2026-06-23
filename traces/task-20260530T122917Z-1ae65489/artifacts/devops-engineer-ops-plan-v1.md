# RoboEase — DevOps Operations Plan v8: Refactored CI/CD with Module Governance

## 1. Executive Summary

This v8 ops plan documents the **current state** of the RoboEase CI/CD pipeline infrastructure
and adds **module boundary governance** and **snapshot-based recovery** to align with the
architect's ADR for Modular Monolith refactoring.

### v8 Changes Applied

| File | Change | Rationale |
|---|---|---|
| `.github/workflows/ci.yml` | Added `backend-module-check` job (import-linter) | Enforces ADR module boundaries |
| `.github/workflows/ci.yml` | Added `backend-migration-check` job | Tracks legacy config/ → core/ migration progress |
| `.github/workflows/ci.yml` | Updated `ci-gate` with advisory severity for new jobs | Non-blocking during refactoring |
| `.github/workflows/deploy.yml` | Added `rollback-snapshot` step to `db-migrate` | Gzipped snapshot with 30-day retention |
| `Makefile` | **Created** — 30+ targets | Local dev, CI pre-flight, module checks, deployment |
| `.env.example` | Added `LEGACY_IMPORTS_ALLOWED` documentation | Governance toggle for CI enforcement |

## 2. CI/CD Pipeline Architecture

### 2.1 CI Pipeline — 16 Jobs (2 new in v8)

```
push/PR (main, develop)
  ├── changes (dorny/paths-filter@v3)
  ├── backend-lint              [ruff + mypy]
  ├── backend-test              [pytest + MySQL/Redis services]
  ├── backend-module-check  ★   [import-linter: ADR boundary contracts]
  ├── backend-migration-check★  [legacy import tracking]
  ├── dbscripts-validate        [MySQL syntax check]
  ├── frontend-admin            [pnpm → vue-tsc → lint → build]
  ├── frontend-portal           [pnpm → vue-tsc → lint → build]
  ├── frontend-webui            [pnpm → build]
  ├── frontend-planweb          [pnpm → vue-tsc → build]
  ├── robot-lint                [ruff entire robot/]
  ├── robot-test                [pytest agent + modules]
  ├── robot-planbe-lint         [ruff planbe]
  ├── robot-planbe-test         [pytest planbe]
  ├── docker-smoke              [build 6 images]
  └── ci-gate                   [aggregate results — 14 checks + 2 advisory]
```

### 2.2 Deploy Pipeline — 7 Jobs (enhanced db-migrate)

```
trigger: workflow_run (main CI) OR workflow_dispatch
  ├── deploy-gate               [set env + SHA]
  ├── build-push                [6 images to GHCR]
  ├── approve-production        [manual gate for production]
  ├── preflight-check           [idempotency: skip if SHA deployed]
  ├── db-migrate                [snapshot★ → backup → apply DML → upload]
  ├── deploy                    [pull → restart → health check → Slack]
  └── skip-notify               [already-deployed]
```

## 3. Module Boundary Governance

### `backend-module-check` — Import Linter

Uses `import-linter` with `continue-on-error` controlled by `vars.LEGACY_IMPORTS_ALLOWED`.
When absent or `true`, violations produce warnings. When `false`, they block CI.

The `.importlinter` contracts enforce:
- `api/` must not import from `infrastructure/`, `config/`, `db/`
- `services/` must not import from `api/`, `config/`, `db/`
- `infrastructure/` must not import from `services/`, `api/`
- `core/` must not import from business modules
- `schemas/` must pull in no business logic

### `backend-migration-check` — Legacy Tracking

Counts remaining `from config.` and `from db.` imports across the backend.
Excludes self-references. Outputs structured counts via `$GITHUB_OUTPUT`.

## 4. Snapshot-Based Database Recovery

### db-migrate Enhancement

The deploy pipeline now creates a **timestamped, gzipped snapshot** before any migration:

```yaml
- name: Snapshot database (point-in-time recovery anchor)
  run: |
    SNAPSHOT_FILE="rollback-snapshot-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).sql.gz"
    mysqldump ... | gzip > "${SNAPSHOT_FILE}"
- name: Upload rollback snapshot artifact
  uses: actions/upload-artifact@v4
  with:
    name: rollback-snapshot-staging
    retention-days: 30
```

**Recovery**: Download from GitHub Actions artifact → `gunzip -c snapshot.sql.gz | docker exec -i roboease-mysql mysql ...`

## 5. Rollback Procedures

- **Container rollback**: `./scripts/rollback.sh <service> [tag]` or `./scripts/rollback.sh all`
- **DB rollback**: `./scripts/rollback.sh --restore-db <snapshot-name>`
- **Full DR**: Stop services → restore DB from snapshot → restart with tagged images → health check

## 6. Environment Boundaries

| Environment | Method | Image Source | Compose File | Approval |
|---|---|---|---|---|
| Development | `make dev` | Local builds | `docker/edge/docker-compose.yaml` | None |
| CI | `make ci-infra-up` | Docker Hub | `docker/docker-compose.ci.yml` | N/A |
| Staging | Auto on main CI pass | GHCR `:staging` | `docker/docker-compose.prod.yaml` | None |
| Production | Manual + approval | GHCR `:production` | `docker/docker-compose.prod.yaml` | Manual gate |

## 7. Secret Management

All secrets are referenced via `${{ secrets.* }}` in CI or read from `.env` on the deploy host.
No secrets are embedded in any configuration file.

**Required GitHub Secrets**: `DEPLOY_SSH_KEY`, `DEPLOY_USER`, `DEPLOY_HOST`, `DB_*`, `SLACK_BOT_TOKEN`

**Optional GitHub Variables**: `PIP_INDEX_URL`, `DEPLOY_URL`, `HEALTH_CHECK_URL`, `SLACK_CHANNEL`, `LEGACY_IMPORTS_ALLOWED`

**Lifecycle**: `make secrets-rotate` local; Update in GitHub Settings → Secrets → Actions for CI.

## 8. Verification Paths

- **Pre-push**: `make ci-check` (lint + type-check + module checks)
- **CI**: 16 jobs with aggregated gate — advisory checks for module boundaries
- **Deploy**: `docker compose ps` health, `.deployed-sha` check, HTTP health check
- **Modules**: `make check-modules` + `make check-migration`

## 9. Container Image Inventory

| Image | Context | Dockerfile | Build Args |
|---|---|---|---|
| python-base | `.` | `docker/base/python-base/DOCKERFILE` | `PIP_INDEX_URL` |
| backend | `backend/` | `docker/edge/backend/DOCKERFILE` | `BASE_IMAGE`, `PIP_INDEX_URL` |
| nginx | `docker/edge/nginx` | `docker/edge/nginx/DOCKERFILE` | — |
| portal | `.` | `docker/cloud/web/DOCKERFILE` | `APP_DIR=frontend/portal` |
| admin-web | `.` | `docker/edge/web/DOCKERFILE` | `APP_DIR=frontend/admin` |
| planbe | `robot/planning/backend` | `docker/robot/planning-backend/DOCKERFILE` | `PIP_INDEX_URL` |

## 10. Known Constraints

| Constraint | Mitigation |
|---|---|
| `core/`, `infrastructure/`, `schemas/` dirs don't exist | `continue-on-error` until refactoring complete |
| Legacy `config/` + `db/` still in use | Gradual migration; tracking job reports progress |
| Team < 10 | Modular monolith avoids distributed complexity |
| Robot hardware tests impossible in CI | Unit tests + mock services |
| GHCR sole registry | 99.9% SLA; acceptable for current scale |
| Single deploy host | Acceptable for team size; can add HA later |

## 11. Pipeline Quality Assessment

| Criterion | Status | Evidence |
|---|---|---|
| Idempotent | ✅ | ci-gate with `if: always()`; preflight idempotency check |
| No secrets in configs | ✅ | All refs via `${{ secrets.* }}` or `${{ vars.* }}` |
| Clear failure output | ✅ | Each step echos; ci-gate reports per-job status |
| Correct caching | ✅ | pip keyed on requirements.txt hash; pnpm on lockfile hash |
| Reversible deployment | ✅ | rollback.sh with per-service + DB restore + snapshot |
| Infrastructure as code | ✅ | All via docker-compose YAML + Dockerfiles |
| Syntactically valid | ✅ | All YAML validated with yaml.safe_load |

## 12. Completion Report

```yaml
what_was_done: >
  Produced v8 ops plan for RoboEase CI/CD pipeline. Added module boundary governance
  (import-linter CI check, legacy migration tracking) and snapshot-based database
  recovery for deployments. Created Makefile with 30+ targets. Updated CI and deploy
  pipeline YAML with new jobs and enhanced db-migrate. Updated .env.example with
  LEGACY_IMPORTS_ALLOWED documentation. All YAML validated, no hardcoded secrets.

key_decisions:
  - decision: Add import-linter CI job with continue-on-error during refactoring
    rationale: ADR mandates strict boundaries but refactoring is in progress.
  - decision: Add legacy migration tracking as advisory job
    rationale: Gradual migration of config/ → core/ and db/ → infrastructure/.
  - decision: Add snapshot-based DB recovery to deploy pipeline
    rationale: 30-day artifact retention enables point-in-time recovery.
  - decision: Create comprehensive Makefile
    rationale: Unifies dev-X, reduces onboarding friction.
  - decision: Keep Docker Compose (no Kubernetes)
    rationale: Team < 10, modular monolith — K8s is overkill.

handoff_focus:
  - security-engineer: Review secret management lifecycle and rotation.
  - release-manager: Validate rollback + snapshot recovery.
  - senior-engineer: Create core/, infrastructure/, schemas/ per ADR.
  - qa-engineer: Verify module boundary checks accuracy.

open_questions:
  - Target date for LEGACY_IMPORTS_ALLOWED=false?
  - Any intentional cross-boundary imports needing contract exceptions?
  - Dependabot/Renovate for dependency updates?
  - web_ui yarn → pnpm migration plan?
  - Robot hardware dependency paths for edge deployment?

known_constraints:
  - core/, infrastructure/, schemas/ don't exist yet
  - Legacy config/ and db/ modules still in use
  - Team < 10 limits operational complexity
  - Robot hardware tests can't run in CI
  - GHCR sole registry; single deploy host

confidence_differential: 0.88
dissent_if_alone: null
iteration_context: >
  v8 builds on v6's mature pipeline and v7's planned governance features.
  Implements CI/CD enforcement of those features and adds snapshot recovery.
  Pipeline is production-ready for modular monolith with gradual ADR migration.
```