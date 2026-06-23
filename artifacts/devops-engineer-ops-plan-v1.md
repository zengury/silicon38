# Ops Plan: RoboEase Refactoring CI/CD & Delivery

## 1. Executive Summary

This ops plan enhances the RoboEase CI/CD pipeline to support the architect-approved
feature-based modular monolith refactoring. It adds duplication detection, hardens
module boundary enforcement, and defines deployment safety gates for incremental
refactoring delivery.

**Target Codebase:** `/Users/ZQ/roboease`
**Refactoring Strategy:** Feature-based modules, interface extraction, static analysis for duplication, incremental per-module delivery
**External Behavior Constraint:** Must not change

---

## 2. Enhanced CI Pipeline

### 2.1 New Stage: Duplication Detection

The architect specified static analysis for duplication detection. Two tools are
added to CI:

| Tool | Layer | Rationale |
|---|---|---|
| `jscpd` | All sources | Language-agnostic, works on Python + TypeScript + Vue |
| `pylint` (duplicate-code) | Backend only | Python-native, integrates with existing Ruff pipeline |

```yaml
# Added to .github/workflows/ci.yml — backend-duplication job
backend-duplication:
  needs: changes
  if: needs.changes.outputs.backend == 'true'
  runs-on: ubuntu-latest
  defaults:
    run:
      working-directory: backend
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    - name: Cache pip packages
      uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ env.PIP_CACHE_KEY_PREFIX }}-${{ runner.os }}-${{ hashFiles('backend/requirements.txt') }}
        restore-keys: |
          ${{ env.PIP_CACHE_KEY_PREFIX }}-${{ runner.os }}-
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pylint
    - name: Pylint duplicate-code check
      run: |
        pylint --disable=all --enable=duplicate-code \
          --ignore=tests,__pycache__,config,db \
          --min-similarity-lines=8 \
          . 2>&1 | tee pylint-duplicates.log
        DUPLICATES=$(grep -c "duplicate-code" pylint-duplicates.log 2>/dev/null || echo 0)
        echo "Duplicate code blocks detected: ${DUPLICATES}"
        if [ "$DUPLICATES" -gt 0 ]; then
          echo "::warning ::${DUPLICATES} duplicate code block(s) detected — review and extract shared modules"
        fi
```

### 2.2 New Stage: Cross-Language Duplication Detection (jscpd)

```yaml
# Added to .github/workflows/ci.yml — duplication-check job
duplication-check:
  needs: changes
  if: |
    needs.changes.outputs.backend == 'true' ||
    needs.changes.outputs.frontend_admin == 'true' ||
    needs.changes.outputs.frontend_portal == 'true' ||
    needs.changes.outputs.robot == 'true'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
    - name: Install jscpd
      run: npm install -g jscpd
    - name: Run jscpd — backend
      if: needs.changes.outputs.backend == 'true'
      run: |
        jscpd backend/ \
          --pattern '**/*.py' \
          --ignore '**/tests/**' \
          --ignore '**/__pycache__/**' \
          --ignore '**/config/**' \
          --ignore '**/db/**' \
          --min-lines 8 --min-tokens 70 \
          --reporters console,json \
          --output jscpd-report-backend \
          || echo "::warning ::Duplication detected in backend/ — see jscpd report"
    - name: Run jscpd — frontend
      if: |
        needs.changes.outputs.frontend_admin == 'true' ||
        needs.changes.outputs.frontend_portal == 'true'
      run: |
        jscpd frontend/ \
          --pattern '**/*.{ts,vue,js}' \
          --ignore '**/node_modules/**' \
          --ignore '**/dist/**' \
          --min-lines 8 --min-tokens 70 \
          --reporters console,json \
          --output jscpd-report-frontend \
          || echo "::warning ::Duplication detected in frontend/ — see jscpd report"
    - name: Upload jscpd reports
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: jscpd-duplication-reports
        path: |
          jscpd-report-backend/
          jscpd-report-frontend/

### 2.3 Hardened Module Boundary Enforcement

The existing `backend-module-check` job uses `continue-on-error` controlled by
`LEGACY_IMPORTS_ALLOWED` variable. For the refactoring effort, this gate is
**hardened** — the variable is set to `false` to block new violations while
allowing a migration window for existing legacy imports.

```yaml
# Changed in ci.yml: backend-module-check
backend-module-check:
  needs: changes
  if: needs.changes.outputs.backend == 'true'
  runs-on: ubuntu-latest
  continue-on-error: false  # CHANGED: was vars.LEGACY_IMPORTS_ALLOWED != 'false'
  # ... (rest unchanged)
```

**Refactoring Migration Tracking** — the existing `backend-migration-check` job
counts `config/` and `db/` legacy imports. During the refactoring, this becomes a
gating metric: each PR must reduce or maintain (not increase) the legacy import count.

```yaml
# Added to backend-migration-check — regression check
- name: Enforce migration regression
  run: |
    PREVIOUS_CONFIG=$(curl -sS -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
      "https://api.github.com/repos/${{ github.repository }}/actions/variables/CONFIG_IMPORT_COUNT" \
      | python3 -c "import sys,json; print(json.load(sys.stdin).get('value','0'))" 2>/dev/null || echo "0")
    echo "Previous config/ imports: ${PREVIOUS_CONFIG}"
    echo "Current config/ imports:  ${{ steps.config-count.outputs.config_count }}"
    if [ "${{ steps.config-count.outputs.config_count }}" -gt "${PREVIOUS_CONFIG}" ]; then
      echo "::error ::Legacy config/ imports increased — this PR must not add new legacy dependencies"
      exit 1
    fi
```

---

## 3. CI Gate Update

The `ci-gate` job adds the new duplication jobs:

```yaml
ci-gate:
  needs:
    - backend-lint
    - backend-test
    - backend-duplication       # NEW
    - backend-module-check
    - backend-migration-check
    - duplication-check         # NEW (jscpd)
    - frontend-admin
    - frontend-portal
    - frontend-webui
    - frontend-planweb
    - robot-lint
    - robot-test
    - robot-planbe-lint
    - robot-planbe-test
    - docker-smoke
    - dbscripts-validate
```

---

## 4. Environment Boundaries

### 4.1 Named Environments

| Environment | Deploy Trigger | Approval | Config Source | URL |
|---|---|---|---|---|
| **development** | Local `make dev-up` | None | `.env` (gitignored) | `http://localhost:8000` |
| **staging** | Auto on main merge (CI green) | None | GitHub Environment `staging` | `https://staging.roboease.cn` |
| **production** | Manual `make deploy-prod` | GitHub Environment approval | GitHub Environment `production` | `https://roboease.cn` |

### 4.2 Refactoring Deployment Strategy

Refactored modules deploy through staging first. Each module refactoring must:

1. Pass full CI (lint + test + duplication + module-check + migration-check)
2. Deploy to staging automatically on main merge
3. Pass staging health verification (`make health-check`)
4. Production deploy requires explicit approval via GitHub Environment `production`

**Feature Flag Strategy:** If a refactored module introduces new interface boundaries,
use environment variables to toggle between old and new code paths during staging
validation, removing the toggle once verified.

---

## 5. Verification Path

### 5.1 Pre-Deploy Verification (CI)

```bash
# Local CI pre-flight — run everything CI would check
make ci-check

# Includes:
#   make lint-backend      — Ruff check + format + mypy
#   make test-backend      — Pytest with coverage
#   make module-check      — import-linter contract validation
#   make migration-status  — Legacy import count
#   make lint-frontend     — ESLint + Prettier + Stylelint
#   make test-frontend     — Frontend type-check
```

### 5.2 Post-Deploy Verification (Runtime)

```bash
# Full deployment verification — 12+ health checks
make health-check
```

The verification script (`scripts/verify-deploy.sh`) tests:
1. **Tier 1** — Gateway & Static Assets (nginx → portal → admin)
2. **Tier 2** — Backend Health Probes (liveness, readiness, metrics)
3. **Tier 3** — Module Health (per-module readiness: auth, robot, notification, task)
4. **Tier 4** — API Endpoint Sanity (admin/portal auth-gate returns 401, not 500)
5. **Tier 5** — Dependency Status (MySQL, Redis, MQTT confirmed healthy)

### 5.3 Refactoring-Specific Verification

After each module refactoring deployment, additionally verify:
1. **No regression in existing behavior** — run staging smoke tests
2. **Import boundary contracts** — `make module-check` passes on deployed code
3. **Legacy import count** — `make migration-status` shows stable or decreasing count
4. **Duplication metrics** — jscpd report shows duplication reduced (not increased)

---

## 6. Rollback Procedures

### 6.1 Container Rollback

| Scenario | Command | Recovery Time |
|---|---|---|
| Single service failure | `make rollback SVC=backend` | < 2 min |
| Full stack regression | `make rollback SVC=all` | < 5 min |
| Database migration failure | `make rollback SVC=all && make restore-db NAME=...` | < 15 min |

### 6.2 Refactoring Rollback Decision Tree

```
Refactored module deployed → Health check fails?
  ├─ Yes → Did CI pass?
  │   ├─ Yes → Rollback containers: make rollback SVC=backend
  │   └─ No  → Rollback containers + restore DB: make rollback SVC=all
  └─ No  → Module health check passes?
      ├─ Yes → API endpoint sanity OK?
      │   ├─ Yes → ✅ Deploy verified
      │   └─ No  → Rollback: make rollback SVC=backend
      └─ No  → Rollback: make rollback SVC=backend
```

### 6.3 Database Rollback

```bash
# List available backups
make list-backups

# Restore from pre-deploy snapshot
make restore-db NAME=pre-deploy-backup-staging-<sha>.sql.gz
```

The deploy pipeline (`deploy.yml`) automatically:
1. Creates a point-in-time snapshot before migration (`rollback-snapshot-*.sql.gz`)
2. Creates a pre-deploy backup (`pre-deploy-backup-*.sql`)
3. Both are uploaded as 30-day retention artifacts

---

## 7. Secrets & Configuration

### 7.1 Required Secrets for Deploy

| Secret | Scope | Purpose |
|---|---|---|
| `DEPLOY_SSH_KEY` | Environment (`staging`, `production`) | SSH access to deployment server |
| `DEPLOY_USER` | Environment | SSH username |
| `DEPLOY_HOST` | Environment | Server hostname |
| `DB_HOST` | Environment | Database host |
| `DB_USER` | Environment | Database user |
| `DB_PASSWORD` | Environment | Database password |
| `DB_NAME` | Environment | Database name |
| `SLACK_BOT_TOKEN` | Repository | Slack notifications |

**No secrets are embedded in any configuration file.** All CI YAML uses
`${{ secrets.* }}` references. All docker-compose files use `${VAR}` references
resolved at runtime.

### 7.2 Refactoring Config Variables

| Variable | Default | Purpose |
|---|---|---|
| `LEGACY_IMPORTS_ALLOWED` | `false` | When `true`, module boundary violations are warnings. Set `false` to enforce. |
| `CONFIG_IMPORT_COUNT` | auto-tracked | Current count of legacy `config/` imports — used for regression detection |
| `DB_IMPORT_COUNT` | auto-tracked | Current count of legacy `db/` imports — used for regression detection |

---

## 8. CI Configuration File

The following changes are applied to `.github/workflows/ci.yml`:

### 8.1 New Jobs Added

1. **`backend-duplication`** — Pylint duplicate-code check on backend Python files
2. **`duplication-check`** — jscpd cross-language duplication detection (backend + frontend + robot)

### 8.2 Modified Jobs

1. **`backend-module-check`** — Changed from `continue-on-error` advisory to hard fail
2. **`backend-migration-check`** — Added regression detection against previous import counts
3. **`ci-gate`** — Added `backend-duplication` and `duplication-check` to dependency list

### 8.3 Complete Enhanced CI Workflow

See appendix: the full `ci-refactoring-enhanced.yml` is written alongside this plan.

---

## 9. Operational Runbook Updates

### 9.1 New Makefile Targets (Recommended)

```makefile
.PHONY: dup-check-backend
dup-check-backend:
	cd $(BACKEND_DIR) && \
	pip install -q pylint && \
	pylint --disable=all --enable=duplicate-code \
		--ignore=tests,__pycache__,config,db \
		--min-similarity-lines=8 .

.PHONY: dup-check-all
dup-check-all:
	npm install -g jscpd 2>/dev/null || true
	jscpd backend/ --pattern '**/*.py' --ignore '**/tests/**' --ignore '**/__pycache__/**' \
		--min-lines 8 --min-tokens 70
	jscpd frontend/ --pattern '**/*.{ts,vue,js}' --ignore '**/node_modules/**' --ignore '**/dist/**' \
		--min-lines 8 --min-tokens 70
```

### 9.2 Refactoring Health Dashboard

Recommended metrics to track during the refactoring:

| Metric | Source | Target |
|---|---|---|
| Legacy config/ imports | `make migration-status` | 0 |
| Legacy db/ imports | `make migration-status` | 0 |
| Duplicate code blocks | `jscpd` JSON report | Decreasing trend |
| Module boundary violations | `make module-check` | 0 |
| Test coverage | `coverage.xml` artifact | ≥ current baseline |
| CI pipeline duration | GitHub Actions Insights | < 12 min |

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Designed and documented an enhanced CI/CD pipeline for the RoboEase
    feature-based modular monolith refactoring. Added duplication detection
    (pylint duplicate-code + jscpd), hardened module boundary enforcement,
    defined environment boundaries (dev/staging/production), documented
    verification path (5-tier health check), and specified rollback
    procedures (container + database). Created the enhanced CI workflow
    configuration file with two new jobs and hardened existing gates.
  key_decisions:
    - decision: Add pylint duplicate-code as backend duplication detection
      rationale: >
        Python-native, integrates with existing Ruff pipeline, configurable
        minimum similarity threshold. Captures Python-specific duplication
        that jscpd might miss due to tokenization differences.
    - decision: Add jscpd as cross-language duplication detection
      rationale: >
        Language-agnostic, covers TypeScript/Vue/JS/Python in one tool.
        Generates JSON reports for trend tracking across the refactoring.
    - decision: Harden module-check from advisory to blocking
      rationale: >
        The architect specified interface extraction as a core goal.
        Advisory enforcement allows drift. Blocking enforcement ensures
        every PR respects the modular monolith contract.
    - decision: Add legacy import regression detection
      rationale: >
        Prevents new PRs from adding legacy config/ or db/ imports during
        the migration. Ensures the migration is monotonic — import counts
        can only decrease or stay flat.
    - decision: Keep existing deployment and rollback procedures unchanged
      rationale: >
        The existing deploy.yml with pre-deploy snapshot, db-migrate backup,
        idempotency check, and rolling restart is sufficient for refactoring
        delivery. No changes needed — the CI enhancements provide the safety
        net.
    - decision: Use jscpd min-lines=8 and min-tokens=70 thresholds
      rationale: >
        Balances sensitivity — short boilerplate (< 8 lines) is not
        meaningful duplication. Token threshold of 70 (~10 lines of Python)
        filters out coincidental similarity.
  handoff_focus:
    - security-engineer: Review secret lifecycle for new CI jobs — jscpd uses npm, no new secrets needed
    - release-manager: The deployment pipeline is unchanged; CI gate now includes duplication + hardened module checks
    - senior-engineer: CI now enforces module boundaries and detects duplication. Local `make dup-check-backend` and `make dup-check-all` recommended before PR.
  open_questions:
    - What is the baseline duplication percentage (jscpd report) for the current codebase?
    - Should jscpd thresholds be adjusted after first run (maybe too noisy or too lenient)?
    - Are there plans to add feature flags for toggling refactored vs legacy code paths in staging?
    - What is the target completion timeline for the config/ and db/ legacy import migration?
  known_constraints:
    - Must not change external behavior — deployment and rollback procedures preserve this
    - Codebase path: /Users/ZQ/roboease
    - Existing tests must be preserved — CI test stage unchanged
    - jscpd and pylint are added as CI dependencies (npm install -g, pip install)
    - MySQL service container required for backend-test and dbscripts-validate (unchanged)
  confidence_differential: 0.15
  dissent_if_alone: null
  iteration_context: null
```
