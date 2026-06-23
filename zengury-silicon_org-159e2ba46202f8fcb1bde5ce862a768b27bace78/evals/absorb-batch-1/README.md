# Eval Suite: Absorb Batch 1

**Purpose**: Measure the behavioral delta introduced by three ABSORB actions
from the 2026-06-23 HRBP recruiting run, before and after each change is
applied to the target harness.

**Absorb actions under test**:

| ID | Source candidate | Target harness | Constraint added |
|---|---|---|---|
| A1 | spec-driven-developer | `senior-engineer` | Specification Gate |
| A2 | mcp-developer | `api-designer` | MCP Server Design section |
| A3 | assumption-mapping | `scope-prosecutor` | Assumption Risk Map |

---

## How to run an eval

Each eval file contains 3 task scenarios. For each scenario:

1. **Pre-absorb run**: Submit the task input to the target role *before* editing
   the harness file. Record the full output in `results/pre/<eval-id>-<n>.md`.
2. **Apply absorb**: Edit the harness file as specified in the ABSORB action.
3. **Post-absorb run**: Submit the same task input to the target role *after*
   the edit. Record output in `results/post/<eval-id>-<n>.md`.
4. **Score**: Apply the rubric in the eval file to both outputs. One point per
   criterion met. Record in `results/scores.yaml`.

**Scoring threshold**: A successful absorb requires ≥ 4/6 rubric criteria to
flip from FAIL → PASS on at least 2 of the 3 scenarios.

---

## Scoring record

```yaml
# results/scores.yaml (fill in after running)
absorb_batch: 1
run_date: null
scorer: null

A1_spec_gate:
  pre_scores:  [null, null, null]   # score per scenario
  post_scores: [null, null, null]
  delta: null
  verdict: null  # IMPROVED | NO_CHANGE | REGRESSION

A2_mcp_design:
  pre_scores:  [null, null, null]
  post_scores: [null, null, null]
  delta: null
  verdict: null

A3_assumption_map:
  pre_scores:  [null, null, null]
  post_scores: [null, null, null]
  delta: null
  verdict: null
```

---

## Baseline snapshot dates

- `senior-engineer.md` read: 2026-06-23 (pre-absorb, has Minimalism Gate, no Specification Gate)
- `api-designer.md` read: 2026-06-23 (pre-absorb, no MCP section)
- `scope-prosecutor.md` read: 2026-06-23 (pre-absorb, no assumption mapping)
