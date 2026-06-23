# HRBP Handoff — Skill Replacement Decision Gate

Date: 2026-05-27
Input report: `artifacts/skill-scout-community-benchmark-plan-v1.md`
Prepared by: Skill Scout

## Recommendation

Recommendation: Run more benchmarks.
Confidence: High for this recommendation.

HRBP must not recommend replacement yet because no candidate has completed the
required benchmark sample count. Current report is a sourcing and readiness
screen only.

## Decision Required From Human

Approve benchmark execution order, not replacements.

Suggested order:

1. `observability-engineer`
2. `performance-engineer`
3. `dependency-auditor`
4. `delivery-prover`
5. `technical-writer`
6. `handoff`
7. `grill-me`
8. `zoom-out`
9. `graph-topologist`
10. `caveman`

## What We Gain If We Follow This Path

- Replacement decisions become evidence-based instead of taste-based.
- High-risk thin skills are tested first.
- Community popularity is used only for sourcing, not as a proxy for quality.
- Silicon-specific requirements stay protected: graph legality, ledger truth,
  digest-linked context blocks, and soul compatibility for design roles.

## What We Lose

- Slower replacement speed.
- Some obvious-looking candidates cannot be adopted immediately.
- Roles with semantic mismatch (`caveman`, `technical-writer`,
  `graph-topologist`, `prototype`) require more recruiting or role-definition
  correction before selection.

## HRBP Blocking Rules

```yaml
replacement_decision:
  blocked_until:
    - sample_count_per_candidate >= 2
    - benchmark task matches actual role output
    - all dimensions scored
    - evaluator calibration stated
    - tradeoffs explicitly documented
  reject_if:
    - candidate only matches adjacent work
    - source stars are used as output score
    - local adaptation is installed without benchmark evidence
    - context-chain requirements are omitted for handoff/context roles
```

## Role-Specific HRBP Notes

### Immediate Benchmark Candidates

`observability-engineer`
- Likely front-runner: alirez `observability-designer`.
- Why: full SLI/SLO, golden signals, alert, runbook methodology.
- Risk: may need Silicon output contract added after benchmark.

`performance-engineer`
- Likely front-runner: alirez `performance-profiler`.
- Strong alternative: Kappa `complexity-optimizer`.
- Risk: one is profiling/bottleneck oriented; the other is algorithmic/code-hotspot oriented. They may be complementary rather than substitutes.

`dependency-auditor`
- Likely front-runner: alirez `dependency-auditor`.
- Strong supplement: Trail of Bits `supply-chain-risk-auditor`.
- Risk: ToB explicitly excludes license compliance; alirez covers more breadth.

`delivery-prover`
- Candidate pool is strong: lackey Playwright, Composio webapp-testing, daymade QA.
- Benchmark must prove actual runtime behavior with evidence.

### Needs Recruiting Or Role Clarification

`technical-writer`
- No exact high-star candidate found.
- Current candidates are adjacent: content writer, fact-checker, regulated document controller.
- HRBP should recommend recruit more, not force-fit.

`caveman`
- Community skill is excellent for compression.
- Silicon node title says First Principles Analyst.
- HRBP should ask for role definition correction before benchmark.

`graph-topologist`
- External candidates analyze code graphs or project skill histories.
- Silicon role analyzes task traces and graph topology learning.
- HRBP should keep local candidate unless benchmark proves trace-retrospective capability.

`prototype`
- External candidates verify/build web behavior but do not define prototype philosophy.
- Recruit product-validation/prototyping candidates.

## Final HRBP Position

Recommendation: Neither replace nor keep permanently yet.
Decision required: Run Wave 1 benchmarks, then HRBP evaluation.
