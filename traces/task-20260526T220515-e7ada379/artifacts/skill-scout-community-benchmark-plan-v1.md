# Skill Scout Community Candidate Benchmark Plan

Date: 2026-05-27
Evaluator: Skill Scout screen, prepared for HRBP review
Scope: all 35 current nodes in `ontology/nodes.yaml`
Graph state checked: `python3 tools/audit.py` -> VALID

## Status Boundary

This is not a replacement decision.

This report is a source-screen and benchmark plan. It maps each Silicon Org
role to high-star community candidate skills and scores readiness against the
role benchmarks in `.agents/skills/skill-scout/benchmark-catalog.md`.

HRBP must not approve replacement from this report alone because candidate
sample_count is still 0. The next required step is to run at least two benchmark
tasks per replacement candidate and then submit those scored outputs to HRBP.

## Source Pool

| Source | Stars | License | Notes |
|---|---:|---|---|
| `JuliusBrussee/caveman` | 65061 | MIT | Best community source for caveman compression, but not first-principles role analysis. |
| `OthmanAdi/planning-with-files` | 22126 | MIT | Excellent persistent planning/context memory; useful adjunct for handoff/planning, not a direct role replacement. |
| `alirezarezvani/claude-skills` | 16242 | MIT | Broadest high-quality engineering/product/business skill library. Many current strong nodes already align here. |
| `ComposioHQ/awesome-codex-skills` | 11830 | unspecified in API | Strong tool-integration skills for web testing, CI, issue triage, deploy, observability integrations. |
| `trailofbits/skills` | 5407 | CC-BY-SA-4.0 | Strong security, supply-chain, audit, differential-review, workflow-skill-design skills. License must be checked before vendoring. |
| `Dimillian/Skills` | 3571 | MIT | Strong multi-agent review, refactor orchestration, SwiftUI/frontend performance, project skill audit. |
| `lackeyjb/playwright-skill` | 2675 | MIT | Strong browser automation / smoke-test candidate for delivery-prover. |
| `daymade/claude-code-skills` | 1114 | MIT | Strong QA, deep research, promptfoo evaluation, UI designer, fact checking. |
| `bergside/awesome-design-skills` | 978 | MIT | Design style catalog; useful supplement for design taste, not a design-system replacement by itself. |
| `Kappaemme-git/codex-complexity-optimizer` | 848 | MIT | Focused algorithmic complexity/performance optimization skill. |
| `mxyhi/ok-skills` | 366 | Apache-2.0 | Some current local skills are close to this source; useful for TDD/diagnose/frontend. Thin for grill-me. |

## Scoring Rubric

Scores are readiness estimates for entering benchmark, not final performance
scores. Use the same 0.0-1.0 scale as Skill Scout.

| Dimension | Weight | Meaning |
|---|---:|---|
| Semantic fit | 0.35 | Candidate performs the role's actual job, not merely a neighboring task. |
| Method depth | 0.25 | Candidate has a repeatable workflow, not only a prompt fragment. |
| Output contract | 0.20 | Candidate names concrete artifacts, formats, evidence, and quality bars. |
| Source quality | 0.10 | Community adoption, maintenance, license clarity, and provenance. |
| Integration risk | 0.10 | Lower risk means easier to adapt without violating Graph/Policy/Ledger/Context Block intent. |

## Priority Findings

1. `observability-engineer`, `performance-engineer`, and
   `dependency-auditor` have clear high-star replacements in
   `alirezarezvani/claude-skills`; these should enter benchmark first.
2. `delivery-prover` has strong external candidates from Playwright and
   webapp-testing sources; benchmark should test actual runtime proof, not
   prose quality.
3. `technical-writer` still has no exact high-star, general technical-writing
   skill match. Current candidates are adjacent: content writer, fact checker,
   QMS document controller. Recruit more before replacement.
4. `graph-topologist` candidates are partial. Trail of Bits Trailmark skills
   reason about code graphs, not Silicon Org trace learning. Current local
   graph-topologist remains necessary until a trace-retrospective benchmark is
   run.
5. `caveman` community source is excellent for token compression, but the
   Silicon node is titled "First Principles Analyst". That role definition and
   skill are semantically misaligned. Either rename/scope the node to
   compression, or recruit a true first-principles simplifier.
6. `grill-me` community candidates exist and are stronger than the original
   thin skill. Use `challenge`, `stress-test`, and `adversarial-reviewer` as
   candidates; benchmark must test adversarial plan/design review rather than
   code review only.
7. `handoff` has a strong community candidate, but Silicon handoff requires
   digest-linked context-chain semantics. Benchmark must test `deliverable` +
   `context_block` + source/omission quality, not generic session summary.

## Full Node Candidate Map

| Role | Current status | Best candidate(s) | Readiness | Benchmark action |
|---|---|---|---:|---|
| `triage` | Adequate | current; Composio `issue-triage` only tracker-specific | 0.78 | Keep current in pool; benchmark against ambiguous request and multi-concern split. |
| `zoom-out` | Improved locally, still needs external benchmark | alirez `codebase-onboarding`, `code-tour`; ToB `audit-context-building` | 0.72 | Run unknown-codebase mapping benchmark; require boundary map, data-flow, hidden coupling, confidence labels. |
| `caveman` | Semantics mismatch | Julius `caveman`; Julius `caveman-compress`; current | 0.54 | Decide role: compression node or first-principles analyst. Benchmark cannot be fair until role title/output is clarified. |
| `grill-with-docs` | Strong | current; daymade `deep-research`; daymade `fact-checker` | 0.80 | Keep current; optional benchmark on external library verification. |
| `to-prd` | Adequate | alirez `product-manager`, `agile-product-owner`, `code-to-prd`; current | 0.82 | Benchmark on feature intent -> testable PRD and contradictory requirements. |
| `to-issues` | Adequate | current; alirez `agile-product-owner`; Othman `planning-with-files` adjunct | 0.76 | Benchmark vertical-slice decomposition and dependency DAG. |
| `prototype` | Weak | lackey `playwright-skill`; Composio `webapp-testing`; mxyhi frontend skill | 0.55 | Recruit more. Existing candidates prove UI/runtime behavior but do not define throwaway prototype strategy. |
| `architect` | Strong | alirez `senior-architect` | 0.88 | Keep. Benchmark periodically on ADR quality and architecture review. |
| `api-designer` | Strong | alirez `api-design-reviewer`; alirez `api-test-suite-builder` adjunct | 0.84 | Keep. Benchmark OpenAPI contract completeness and version/error strategy. |
| `database-engineer` | Strong | alirez `database-designer` | 0.82 | Keep. Benchmark DDL/index/migration rollback design. |
| `senior-engineer` | Strong | alirez `senior-backend`; alirez `cs-backend-engineer` optional | 0.85 | Keep. Benchmark implementation fidelity to ADR/API spec. |
| `tdd` | Adequate | current; mxyhi `tdd`; ToB property-based testing/mutation testing adjunct | 0.76 | Benchmark behavior-focused tests, not implementation-detail tests. |
| `diagnose` | Adequate | Dimillian `bug-hunt-swarm`; mxyhi `diagnose`/`systematic-debugging`; Composio `sentry-triage` adjunct | 0.80 | Benchmark regression investigation with hypothesis/proof chain. |
| `refactor-specialist` | Replacement candidate exists but needs benchmark | Dimillian `orchestrate-batch-refactor`; Dimillian `review-and-simplify-changes`; Kappa `complexity-optimizer`; Ousterhout local candidate | 0.74 | Run behavior-preserving refactor benchmark; require tests unchanged and explicit invariants. |
| `improve-codebase-architecture` | Strong | current; Kappa `complexity-optimizer`; Trailmark structural adjunct | 0.82 | Keep. Benchmark coupling analysis and migration path. |
| `devops-engineer` | Adequate | alirez `ci-cd-pipeline-builder`; Composio `deploy-pipeline`; daymade `terraform-skill` | 0.78 | Benchmark CI/CD from scratch with rollback/secrets/notification. |
| `observability-engineer` | Critical local skill | alirez `observability-designer`; Composio `datadog-logs`; Composio `sentry-triage` | 0.86 | High-priority benchmark. Require SLI/SLO, golden signals, actionable alerts, dashboard/runbook. |
| `performance-engineer` | Critical local skill | alirez `performance-profiler`; Kappa `complexity-optimizer`; Dimillian performance skills for platform-specific cases | 0.88 | High-priority benchmark. Require measured baseline, bottleneck proof, before/after plan. |
| `security-engineer` | Strong | alirez `senior-security`; ToB `differential-review`; ToB testing handbook adjuncts | 0.87 | Keep. Benchmark STRIDE threat model and mitigations. |
| `ux-researcher-designer` | Strong | alirez `ux-researcher-designer`; daymade `product-analysis` adjunct | 0.84 | Keep. Benchmark journey synthesis from interviews. |
| `ui-design-system` | Thin local copy of strong upstream | alirez full `ui-design-system`; bergside design-style catalog adjunct; daymade `ui-designer` adjunct | 0.82 | Benchmark token architecture and component-state spec. Candidate should likely be upstream full skill, not current 51-line local copy. |
| `apple-hig-expert` | Adequate | current/alirez `apple-hig-expert`; Dimillian `swiftui-liquid-glass`, `swiftui-ui-patterns` adjunct | 0.78 | Keep; benchmark HIG citation accuracy and platform-specific fixes. |
| `senior-frontend` | Strong | alirez `senior-frontend`; mxyhi frontend skill; Dimillian React/SwiftUI performance adjuncts | 0.86 | Keep. Benchmark implementation from tokens/spec with accessibility and performance checks. |
| `epic-design` | Strong local specialization | current; bergside `immersive`, `premium`, `storytelling` adjuncts; daymade `ui-designer` adjunct | 0.80 | Keep. Benchmark scrollytelling output with visual/performance proof. |
| `skill-scout` | Local-specialized | current; ToB `designing-workflow-skills`; ToB `skill-improver`; Dimillian `project-skill-audit` | 0.70 | Keep local for Silicon role; benchmark source-screen + benchmark-design quality. |
| `hrbp` | Local-specialized | current; alirez `chro-advisor`, `culture-architect` only adjacent | 0.72 | Keep local. Benchmark talent recommendation from scored results with sample-size discipline. |
| `delivery-prover` | New local skill, external candidates strong | lackey `playwright-skill`; Composio `webapp-testing`; daymade `qa-expert` | 0.84 | High-priority benchmark. Require actual app start, smoke test, logs/screenshots, reproducible failure. |
| `customer-success` | Adequate but should benchmark | alirez `customer-success-manager`; Composio `support-ticket-triage` adjunct | 0.86 | Benchmark onboarding/KPI/ROI/nontechnical guide from product deliverable. |
| `graph-topologist` | Local-specialized, external candidates partial | ToB `graph-evolution`; ToB `trailmark-structural`; Dimillian `project-skill-audit` | 0.62 | Recruit more or keep local. Benchmark trace retrospective with evidence-backed graph-change proposals. |
| `code-reviewer` | Strong | alirez `code-reviewer`; ToB `differential-review`; Dimillian `review-swarm` | 0.86 | Keep or benchmark against review-swarm/differential-review for higher bug find rate. |
| `grill-me` | Original was critical; community replacements exist | alirez `challenge`; alirez `stress-test`; alirez `adversarial-reviewer` | 0.74 | Benchmark plan/design adversarial review. Avoid code-review-only candidate unless role is narrowed. |
| `dependency-auditor` | Critical local skill | alirez `dependency-auditor`; ToB `supply-chain-risk-auditor` | 0.87 | High-priority benchmark. Combine CVE/license/version drift from alirez with takeover/maintainer risk from ToB. |
| `technical-writer` | Critical; no exact high-star match | Composio `content-research-writer`; daymade `fact-checker`; alirez `quality-documentation-manager` | 0.58 | Recruit more. Existing candidates are adjacent and must not be installed as-is. |
| `release-manager` | Strong | alirez `release-manager`; Composio `changelog-generator`; Dimillian `app-store-changelog` | 0.86 | Keep. Benchmark release plan from changelist with rollback and user-facing changelog. |
| `handoff` | Original critical; community candidate strong but incomplete for Silicon | alirez `handoff`; Othman `planning-with-files`; current Silicon context-chain skill | 0.78 | Benchmark context compression from long trace, requiring deliverable + digest-linked context block + omissions. |

## Benchmark Execution Queue

### Wave 1 — Immediate Replacement Risk

Run these first because current local skills are thin or known critical:

1. `observability-engineer`
   - Candidates: current, alirez `observability-designer`, Composio `datadog-logs`+`sentry-triage` combined.
   - Benchmarks: monitoring setup for a service; noisy-alert remediation.
   - Pass threshold: overall >= 0.78, actionability >= 0.80.

2. `performance-engineer`
   - Candidates: current, alirez `performance-profiler`, Kappa `complexity-optimizer`.
   - Benchmarks: bottleneck identification; code hotspot complexity report.
   - Pass threshold: overall >= 0.80, measurement discipline >= 0.85.

3. `dependency-auditor`
   - Candidates: current, alirez `dependency-auditor`, ToB `supply-chain-risk-auditor`.
   - Benchmarks: dependency risk assessment from package manifests; suspicious maintainer/takeover scenario.
   - Pass threshold: overall >= 0.80, CVE/license/transitive coverage >= 0.80.

4. `technical-writer`
   - Candidates: current, Composio `content-research-writer`, daymade `fact-checker`, alirez `quality-documentation-manager`.
   - Benchmarks: API docs from code; factual correction of stale docs.
   - Expected outcome: likely "recruit more", not replacement.

### Wave 2 — Semantics Must Be Resolved

1. `caveman`
   - Blocking issue: role title says First Principles Analyst; skill source says token compression.
   - Decision required before benchmark: rename/scope to compression, or recruit first-principles simplifier.

2. `handoff`
   - Blocking issue: generic session handoff is not enough.
   - Must benchmark Silicon-specific context chain and `context_compression_report` consumption.

3. `graph-topologist`
   - Blocking issue: external candidates analyze code graphs, not Silicon task traces.
   - Must benchmark trace retrospectives before any replacement.

4. `prototype`
   - Blocking issue: candidates test web apps but do not define prototype strategy.
   - Recruit more from prototyping/product-validation skill sources.

### Wave 3 — Strong Skills, Periodic Benchmark

Run lower priority comparative benchmarks for:
`architect`, `api-designer`, `database-engineer`, `senior-engineer`,
`security-engineer`, `senior-frontend`, `release-manager`, `code-reviewer`,
`ux-researcher-designer`, `ui-design-system`, `epic-design`.

## HRBP Handoff

HRBP should receive this report with the following explicit decision limits:

```yaml
recommendation_scope:
  allowed:
    - approve benchmark execution order
    - flag roles needing recruiting
    - reject auto-replacement due to sample_count=0
  not_allowed:
    - approve replacing skill_ref now
    - treat GitHub stars as output quality
    - accept adjacent skills for exact roles without benchmark evidence
minimum_evidence_for_replacement:
  sample_count_per_candidate: 2
  dimensions_required:
    - output_quality
    - constraint_compliance
    - efficiency
    - consistency
    - role_semantic_fit
  design_roles_extra:
    - soul_compatibility
```

## Known Repo Issues Noted During This Review

1. `org/REGISTRY.md` says "30 agents" while `ontology/nodes.yaml` contains
   35 nodes. This must be corrected before using Registry as an authority.
2. `tools/audit.py` currently treats meta nodes and terminal roles as special
   cases. That can be correct, but the exception list itself needs policy
   justification so "no orphan nodes" does not become silently weakened.
3. Some current `skill_ref` changes in the worktree point at newly added local
   skills. Those must be considered provisional until benchmark + HRBP review.
4. `caveman` is not orphaned. Current graph count: incoming 0, outgoing 6,
   activation-capable outgoing 3.
