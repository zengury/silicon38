# RoboEase — DevOps Operations Plan v9: Resource Governance & Environment Hardening

**Producer:** devops-engineer
**Task ID:** task-20260530T130959Z-ee6d83ff
**Artifact Ref:** artifacts/devops-engineer-ops-plan-v9.md
**Previous Plan:** artifacts/devops-engineer-ops-plan-v8.md
**Artifact Type:** ops-plan

---

## 1. Executive Summary

This v9 ops plan addresses **operational gaps** not covered by v8's CI/CD governance focus:

1. **Resource governance** — every service in `docker-compose.prod.yaml` gets memory/CPU limits and reservations to prevent noisy-neighbor degradation.
2. **Environment boundary hardening** — explicit environment names (`dev`, `staging`, `production`) with isolated compose files and network segments.
3. **Reproducible operations** — `Makefile` with 35 targets covering build, test, deploy, rollback, secret rotation, and module validation.
4. **Verification path** — explicit end-to-end health verification through the API → gateway → module → infrastructure chain.
5. **Nginx routing hardening** — modular route prefixes aligned with ADR module boundaries.

### v9 Changes Applied

| File | Change | Rationale |
|---|---|---|
| `docker/docker-compose.prod.yaml` | Added `deploy.resources` (limits + reservations) to all 7 services | Prevents resource starvation |
| `docker/docker-compose.prod.yaml` | Added `deploy.restart_policy` with backoff window | Prevents restart storms; max 3 restarts per 60s window |
| `docker/docker-compose.prod.yaml` | Added `DEPLOY_ENV` env var to all services | Explicit environment tagging for observability |
| `docker/docker-compose.ci.yml` | Added resource limits and Redis maxmemory | Prevents CI runner exhaustion |
| `Makefile` | **Created** — 35 targets | Single entry-point for all ops workflows |
| `docker/docker-compose.staging.yaml` | **Created** — staging-specific override | Isolates staging from production |
| `scripts/verify-deploy.sh` | **Created** | End-to-end health verification across 5 tiers |

---

## 2. Environment Boundaries

| Environment | Compose File | Network | Purpose | Data Persistence |
|---|---|---|---|---|
| **dev** | `docker-compose.ci.yml` | `raas-ci-net` | Local development, CI testing | Ephemeral |
| **staging** | `docker-compose.prod.yaml` + `docker-compose.staging.yaml` | `raas-staging-net` | Pre-prod validation, UAT | Named volumes (`staging-` prefix) |
| **production** | `docker-compose.prod.yaml` | `raas-prod-net` | Live traffic | Bind mounts (`/opt/roboease/data/`) |

Promotion flow: `dev → staging (auto on main) → production (manual dispatch + approval)`

---

## 3. Resource Governance

### Production Resource Allocation

| Service | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation |
|---|---|---|---|---|
| nginx | 1.0 | 256M | 0.25 | 64M |
| portal | 0.5 | 128M | 0.1 | 32M |
| admin-web | 0.5 | 128M | 0.1 | 32M |
| backend | 2.0 | 512M | 0.5 | 256M |
| mysql | 2.0 | 1G | 0.5 | 512M |
| redis | 0.5 | 256M | 0.1 | 64M |
| emqx | 1.0 | 512M | 0.25 | 128M |

All services use restart policy: `on-failure`, 5s delay, max 3 attempts per 60s window.

### CI Test Infrastructure Limits

| Service | Memory Limit | CPU Limit |
|---|---|---|
| mysql (CI) | 512M | 1.0 |
| redis (CI) | 128M | 0.5 |
| emqx (CI) | 256M | 0.5 |

---

## 4. Reproducible Operations (Makefile)

35 targets organized into categories:

- **Local Development** (6): `dev-infra-up`, `dev-infra-down`, `dev-infra-logs`, `dev-backend`, `dev-admin`, `dev-portal`
- **Build** (7): `build-base`, `build-backend`, `build-admin`, `build-portal`, `build-nginx`, `build-frontend`, `build-all`
- **Test** (4): `test-backend`, `test-backend-cov`, `test-frontend`, `test-all`
- **Lint & Quality** (5): `lint-backend`, `lint-backend-fix`, `lint-frontend`, `module-check`, `migration-status`
- **CI Pre-flight** (2): `ci-check`, `ci-build-check`
- **Deployment** (5): `deploy-trigger-staging`, `deploy-trigger-production`, `deploy-status`, `deploy-logs`, `deploy-local`
- **Rollback** (4): `rollback`, `rollback-all`, `rollback-db`, `list-backups`
- **Secrets** (3): `secrets-rotate`, `secrets-check`, `secrets-audit`
- **Cleanup** (3): `clean-docker`, `clean-artifacts`, `clean-all`
- **Observability** (4): `health-check`, `health-check-local`, `metrics-snapshot`, `logs-errors`

---

## 5. Verification Path

`scripts/verify-deploy.sh` tests 12 checks across 5 tiers:

1. **Tier 1 — Gateway & Static Assets**: nginx root, portal/admin SPA responses
2. **Tier 2 — Backend Health Probes**: `/health/live`, `/health/ready`, `/health/metrics`
3. **Tier 3 — Module Health**: per-module health endpoints (auth, robot, notification, task)
4. **Tier 4 — API Endpoint Sanity**: admin/portal endpoints return 401 (auth required), not 500
5. **Tier 5 — Dependency Status**: DB, Redis, MQTT reachability via health response

---

## 6. Secrets Lifecycle Management

| Category | Storage | Rotation |
|---|---|---|
| Infrastructure (`MYSQL_ROOT_PASSWORD`, `REDIS_PASSWORD`) | `.env` + GitHub Environment Secrets | Quarterly |
| Application (`JWT_SECRET_KEY`, API keys) | `.env` + GitHub Environment Secrets | Quarterly/per-provider |
| Deployment (`DEPLOY_SSH_KEY`, `SLACK_BOT_TOKEN`) | GitHub Secrets only | Annually |
| TLS (SSL certs) | Server filesystem | Per CA expiry |

`make secrets-rotate` generates cryptographically random values. `make secrets-check` validates non-empty, non-default, minimum-length requirements. `make secrets-audit` checks file permissions and detects weak patterns.

---

## 7. Rollback Procedure

### Service Rollback
```bash
./scripts/rollback.sh backend           # auto-detects previous tag
./scripts/rollback.sh backend abc1234   # specific SHA
```

Steps: backup container state → resolve/pull target image → create override → force-recreate → health check → record SHA.

### Rollback Decision Matrix

| Failure Type | Rollback Scope | Recovery Time |
|---|---|---|
| Backend crash on deploy | Backend only | < 2 min |
| Database migration failure | DB restore + backend | < 5 min |
| Frontend JS error | Frontend only | < 1 min |
| Full stack regression | All services + DB restore | < 15 min |

---

## 8. CI Pipeline Hardening

- **Module boundary enforcement**: Advisory during refactoring (`LEGACY_IMPORTS_ALLOWED=true`). Set to `false` when modules exist.
- **Legacy migration tracking**: Counts `config/` and `db/` imports (target: 0)
- **Resource validation** (new): Validates all services have resource limits and reservations ≤ limits

---

## 9. Observability Integration

Health endpoints (once `infrastructure/observability/` is created):
- `GET /api/v1/health/live` — liveness
- `GET /api/v1/health/ready` — dependency readiness (DB, Redis, MQTT)
- `GET /api/v1/health/metrics` — Prometheus metrics
- `GET /api/v1/health/modules/{name}` — per-module health

Alert thresholds: backend p95 > 500ms (warn) / > 2s (critical), 5xx rate > 1% (warn) / > 5% (critical), DB pool > 70% (warn) / > 90% (critical).
