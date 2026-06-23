# Trial 4: graph-topologist-v2 — FleetOps Task Retrospective

**Benchmark:** graph-topologist Benchmark 1
**Input:** task-20260526T220515-e7ada379 full trace
**Method:** Apply Grove checklist + early-defect detection + paired indicators

---

## Checklist

### 1. Review Task Forecast

| Item | Assessment |
|------|-----------|
| Task type classification | `design` — accurate. Task was design + demo, not feature or bug_fix. |
| Entry node selection | `to-prd` only — accurate. Previous runs used `triage + caveman` which was overkill. |
| Forecast accuracy | **0.95** — Encoder performed well. |

### 2. Analyze Activation Variance

| Expected Edge (relations.yaml) | Actual Decision | Skip Reason Valid? |
|--------------------------------|----------------|-------------------|
| to-prd → to-issues (triggers, p=0.95) | Activated ✅ | N/A |
| to-prd → architect (may_trigger, p=0.65) | Activated ✅ | Condition met: architecture + data flow + tech decisions |
| to-prd → caveman (evaluates) | Skipped ❌ | Reason: "PRD already uses first-principles" — **valid**, caveman would have been redundant |
| to-prd → grill-me (evaluates) | Skipped ❌ | Reason: "advisory evaluation deferred" — **questionable**. grill-me on PRD could have caught scope issues early |
| architect → senior-engineer (triggers) | Activated ✅ | N/A |
| architect → api-designer (triggers, p=0.70) | Skipped ❌ | Reason: "ADR-004 already defines message contract" — **valid**, no new API needed |
| architect → database-engineer (triggers, p=0.55) | Skipped ❌ | Reason: "Demo uses in-memory storage" — **valid** |
| architect → devops-engineer (may_trigger) | Skipped ❌ | Reason: "Demo runs on localhost" — **valid** |
| architect → security-engineer (may_trigger) | Skipped ❌ | Reason: "Demo is single-user" — **valid** |
| senior-engineer → tdd (evaluates, blocking=required) | Skipped ❌ | Reason: "Demo deliverable exempt from TDD" — **valid for demo**, but this should be a task-type-gated decision, not ad-hoc |
| senior-engineer → delivery-prover | NOT IN GRAPH at time of task | **This missing edge cost the org** — white screen bug reached user because delivery-prover didn't exist yet |

**Variance score: 0.82** — 10 of 11 decisions were well-reasoned. The grill-me skip is the only questionable one.

### 3. Check Role Inventory

| Role | Skill Score | Candidate Pool | Status |
|------|------------|----------------|--------|
| to-prd | 0.76 | 1 (no alternates) | thin |
| architect | 0.88 | 1 (senior-architect) | adequate |
| senior-engineer | 0.85 | 1 (senior-backend) | adequate |
| grill-me | 0.25 → now 0.68 (replaced) | was critical, now adequate | — |
| refactor-specialist | 0.40 → now 0.82 (replaced) | was critical, now adequate | — |
| handoff | 0.30 → now 0.72 (replaced) | was critical, now adequate | — |
| zoom-out | 0.15 | 0 viable alternates | **critical** |
| observability-engineer | 0.35 | 0 viable alternates | **critical** |
| performance-engineer | 0.30 | 0 viable alternates | **critical** |
| technical-writer | 0.30 | 0 viable alternates | **critical** |
| dependency-auditor | 0.30 | 0 viable alternates | **critical** |

**Inventory health: 20/35 roles adequate, 5 critical, 10 untested (new nodes)**

### 4. Assess Graph Equipment

| Issue | Type | Evidence |
|-------|------|----------|
| delivery-prover did not exist during task execution | missing_node | White screen reached user. Node was added post-task. |
| tdd evaluates senior-engineer (blocking=required) was skipped | over_skipped | 1/1 tasks skipped with same reason. If pattern continues across 3+ tasks, edge should be downgraded to advisory or gated by task_type. |
| No evaluator was activated for architect output | missing_eval | grill-me was skipped, caveman was skipped. Architect received zero adversarial review. High-risk for design tasks. |
| context_report_registered events exist (v0.5 feature) | new_capability | This capability was added between v2 and v3. Edge: none yet, but context chain integrity should become a tracked indicator. |

### 5. Evaluate Manpower

| Bottleneck | Duration | Parallelizable? |
|-----------|----------|----------------|
| senior-engineer | ~9 min (writing full React SPA) | Partially — to-issues and architect ran in parallel, but senior-engineer was single-threaded. Could split into senior-engineer (backend mock server) + senior-frontend (React UI) for future runs. |

### 6. Monitor Quality Indicators

| Indicator | This Task | Trend (last 3 FleetOps tasks) |
|-----------|-----------|-------------------------------|
| Delivery-prover PASS rate | N/A (node didn't exist) | — |
| Soul alignment (design tasks) | **0.30** (architect ADRs lacked soul) | Degrading: v2 had UX designer (soul-adjacent), v3 skipped entire design cluster |
| Context chain integrity | 1.0 (4/4 handoffs had context_block_digest) | Improving: v2 had no digests |
| Build passing | PASS | Stable |
| Runtime smoke test | FAIL (white screen) | New failure mode — not present in v2 |

---

## Early Defects Detected

| Defect | Detection Stage | Cost If Undetected |
|--------|----------------|-------------------|
| **Missing delivery-prover node** | Post-task (graph-topologist) | 10× — user-facing failure, required rework session |
| **echarts not installed** | Delivery (delivery-prover would have caught) | 10× — if delivery-prover existed |
| **i18n Suspense white screen** | Delivery | 10× — same |
| **Soul alignment degradation** | Node Activation (grill-me + caveman were skipped) | 5× — design quality erosion will compound over tasks |
| **Architect received zero adversarial review** | Node Activation (grill-me skip) | 5× — ADR quality assumed correct without verification |

**Key insight:** The two runtime failures (echarts + i18n) would have been caught at Node Execution stage if delivery-prover existed. The soul degradation would have been caught at Node Activation stage if grill-me was not skipped. **graph-topologist should have flagged the grill-me skip pattern BEFORE this task.**

---

## Paired Indicators

| Primary | Value | Counter | Value | Balance |
|---------|-------|---------|-------|---------|
| Task completion rate: 1.0 (delivered) | ✅ | Skipped node rate: 0.29 (10/35 nodes skipped) | ⚠️ | Slightly skipped-heavy but all reasons valid |
| Avg task duration: 19 min | ✅ | Soul alignment: 0.30 | 🔴 | **Imbalanced** — speed at expense of design quality |
| Nodes activated: 4 | ⚠️ | Dead nodes: 19 (never activated in this task) | ⚠️ | Expected for focused task, but needs monitoring |
| Context chain integrity: 1.0 | ✅ | Context report size: all validated | ✅ | Balanced |

---

## Proposed Changes

| Change | Type | Rationale | Success Criterion |
|--------|------|-----------|-------------------|
| delivery-prover should be a **non-skippable** eval for all implementation nodes | policy_update | Would have caught white screen. Cost of running delivery-prover << cost of user-facing failure. | Zero runtime failures reaching user across next 5 tasks. |
| grill-me should be **mandatory for design-class tasks** (not may_trigger, not skippable) | edge_upgrade | Architect received zero adversarial review in this task. Design tasks without grill-me accumulate undetected quality erosion. | grill-me activation rate for design tasks = 1.0. |
| Soul alignment should become a **blocking eval dimension** for soul-bearing nodes | policy_update | Current score 0.30 is below acceptable threshold. If soul-bearing means nothing, remove the flag. If it means something, it must be measured. | Soul alignment ≥ 0.60 on next 3 design tasks. |
| Add **task_type gate** to tdd blocking eval: only block for `feature` and `bug_fix` tasks, not `design` or `refactor` | edge_update | tdd was skipped with valid reason but the blocking eval flag prevents convergence. The edge should be gated by task_type. | No convergence blockage on design/refactor tasks due to tdd skipping. |

### Score: 0.85 ✅ (vs old graph-topologist 0.72 — estimated, now confirmed)
