# RoboEase — DevOps Operations Plan v10: Compose Consolidation & Ops Standardization

**Producer:** devops-engineer
**Task ID:** task-20260530T143742Z-b85bb72b
**Artifact Ref:** artifacts/devops-engineer-ops-plan-v10.md

---

## 1. Executive Summary

Executed architect Decision 4: consolidated `docker-compose.ci.yml`, `docker-compose.prod.yaml`, and `docker-compose.staging.yaml` (collectively ~600 lines with heavy duplication) into a single `docker/docker-compose.yml` (299 lines) with three profiles: `dev`, `staging`, `prod`. Delivered a `Makefile` (425 lines, 35+ targets) replacing ad-hoc `deploy-build.sh`. Created `.env.example`, `.gitignore`, deployment runbook (`docs/DEPLOY.md`), and secrets lifecycle guide (`docs/SECRETS.md`). Updated nginx.conf with backend API routing for the modular monolith.

**Critical finding**: `backend/core/`, `infrastructure/`, `ports/`, `schemas/` directories do not exist on disk. `main.py` imports from these nonexistent modules. Backend cannot start in any environment until the senior engineer creates them. CI module boundary checks remain advisory.

### Files Written

| File | Action | Lines |
|---|---|---|
| `docker/docker-compose.yml` | Created (consolidated) | 299 |
| `Makefile` | Created | 425 |
| `.env.example` | Created | 86 |
| `.gitignore` | Created | 56 |
| `docs/DEPLOY.md` | Created | 145 |
| `docs/SECRETS.md` | Created | 118 |
| `docker/docker-compose.ci.yml` | Deprecation header added | — |
| `docker/docker-compose.prod.yaml` | Deprecation header added | — |
| `docker/docker-compose.staging.yaml` | Deprecation header added | — |
| `docker/edge/nginx/nginx.conf` | Backend API routing block added | +24 |

### Profile Architecture

```
┌── dev (CI + local) ──────────────┐
│  mysql:3306  redis:6379  emqx:1883│  infrastructure only
│  Network: raas-prod-net           │  ephemeral volumes
└──────────────────────────────────┘
┌── staging ──────────────────────┐
│  nginx + portal + admin-web      │  all services
│  backend + mysql + redis + emqx  │  persistent volumes (staging- prefix)
│  ports offset via .env.staging   │  reduced resources
└─────────────────────────────────┘
┌── prod ─────────────────────────┐
│  nginx + portal + admin-web      │  all services
│  backend + mysql + redis + emqx  │  host bind mounts
│  80/443/8443 exposed              │  full resource allocation
└─────────────────────────────────┘
```

### Key Makefile Targets

```bash
make dev-up              # Start dev infra (mysql, redis, emqx)
make dev-down            # Stop dev infra
make build-all           # Build all 5 Docker images
make test-backend        # pytest with coverage
make test-frontend       # ESLint + Prettier + Stylelint + type-check
make ci-check            # Full CI pre-flight (lint + test + module-check)
make deploy-staging      # Trigger staging deploy via GitHub Actions
make deploy-prod         # Trigger production deploy (approval-required)
make rollback SVC=all    # Rollback all services
make restore-db NAME=... # Restore database from backup
make secrets-init        # Create .env from .env.example
make secrets-check       # Verify no insecure/default secrets
make secrets-rotate      # Generate cryptographically random secrets
make health-check        # End-to-end deployment verification (12 checks)
make clean-all           # Full cleanup (containers, images, volumes, caches)
```

### Zero-Secrets Guarantee

All 7 services in `docker-compose.yml` use `${VAR}` or `${VAR:-default}` references exclusively. No literal passwords, API keys, or tokens appear in any file:
- Compose file: 26 environment variables, all `${VAR}` references
- nginx.conf: no credentials
- Makefile: no embedded values
- All DOCKERFILEs: no secrets in any layer
- Scripts: read from container environment at runtime only

### Known Gaps

1. **Backend unstartable**: `core/`, `infrastructure/`, `ports/`, `schemas/` modules missing
2. **CI gates advisory**: `backend-module-check` and `backend-migration-check` use `continue-on-error` until modules exist
3. **No Alembic**: raw SQL migrations in `dbscripts/DML/` — Alembic planned but not implemented
4. **Deploy workflow needs updating**: `deploy.yml` still references `docker-compose.prod.yaml` — must switch to `--profile prod`

### Rollback Decision Matrix

| Failure | Scope | Recovery Time |
|---|---|---|
| Backend crash | Backend only | < 2 min |
| DB migration failure | DB restore + backend | < 5 min |
| Frontend JS error | Frontend only | < 1 min |
| Full stack regression | All + DB | < 15 min |

---

## Completion Report

```yaml
completion_report:
  what_was_done: |
    Consolidated 3 docker-compose files into a single file with dev/staging/prod
    profiles. Created Makefile with 35+ reproducible operations targets. Created
    .env.example, .gitignore, deployment runbook, and secrets lifecycle guide.
    Updated nginx.conf with backend API routing. Discovered and documented the
    critical gap: backend cannot start because core/, infrastructure/, ports/,
    schemas/ modules do not exist yet.
  key_decisions:
    - decision: Merge 3 compose files into one with profiles
      rationale: Architect Decision 4 required this. Eliminates ~300 lines of
        duplication, ensures consistency, provides single file to audit.
    - decision: Mark CI module boundary checks as advisory until core/ exists
      rationale: main.py imports from nonexistent modules; blocking CI would
        halt all development. Gated by LEGACY_IMPORTS_ALLOWED GitHub variable.
    - decision: Keep MySQL, Redis, EMQX in all profiles (shared infrastructure)
      rationale: Needed in every environment; avoids duplication.
    - decision: Use .env files for per-environment config instead of override files
      rationale: Profiles handle service inclusion; .env handles values. More
        maintainable than 180+ line staging override files.
    - decision: Backend NOT in dev profile
      rationale: Cannot start until modules exist. Developers run manually.
  handoff_focus:
    - senior-engineer: Create backend/core/, infrastructure/, ports/, schemas/
      modules. See §11.1 of ops plan for exact import list needed.
    - security-engineer: Review .env.example; audit zero-secrets guarantee.
    - release-manager: Update deploy.yml to use --profile prod; test rollback.
  open_questions:
    - When will core/, infrastructure/, ports/, schemas/ modules be implemented?
    - Should staging run on same host as production or separate?
    - What is the TLS certificate renewal strategy?
    - Should Redis have a password in CI/dev for security parity?
  known_constraints:
    - Backend cannot start until core/, infrastructure/ modules exist.
    - Single-host Docker Compose; no Kubernetes.
    - Robot-side services run on edge devices with separate deploy infrastructure.
    - Raw SQL migrations; Alembic planned but not implemented.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: |
    v10 executes architect Decision 4 (compose consolidation) with actual
    implementations. Critical finding: backend module extraction must happen
    before any environment can deploy the backend.
```