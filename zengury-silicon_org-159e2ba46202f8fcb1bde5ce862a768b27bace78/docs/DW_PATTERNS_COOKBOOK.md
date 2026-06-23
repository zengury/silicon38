# Dynamic Workflow Patterns — the Silicon Org Cookbook

Claude Code's [Dynamic Workflow](https://code.claude.com/docs/en/workflows)
ships six recurring orchestration patterns. Every one of them is expressible
as a Silicon Org graph topology — with the difference that in DW the pattern
lives in a throwaway JavaScript script, while here it lives in typed edges,
survives the run in the ledger, and feeds the weight matrix.

This cookbook shows each pattern twice: the DW shape, and the harnessed shape.

---

## 1. Classify-and-act (分类并执行)

**DW shape**: a classifier `agent()` inspects each item and routes it to a
matching handler agent.

**Harnessed shape**: this is the **Encoder + entry-node selection**. Task
intake (`org/ENCODER.md`) classifies the task type; `ontology/nodes.yaml`
entry-node declarations plus learned weights pick the entry roles
(`triage` for ambiguous work, `diagnose` for bug reports, `to-prd` for
feature intent…).

```yaml
# ontology/nodes.yaml (excerpt)
triage:
  entry_node: true        # ambiguous / multi-part requests land here
diagnose:
  entry_node: true        # defect reports land here
```

What the harness adds: the classification decision is a ledger fact
(`manifest.yaml: task_type`), and entry-selection accuracy is learnable —
mis-routed tasks produce weaker quality signals on those entry edges.

## 2. Fan-out-and-synthesize (分发并汇总)

**DW shape**: `parallel()` over N subtasks with clean contexts, then a
synthesizer agent merges results.

**Harnessed shape**: **parallel candidate activation + the Decoder**. When
multiple activation candidates are legal simultaneously, the LangGraph kernel
(`runtime/langgraph_native.py`) fans them out; each role gets a clean context
built from digest-linked handoffs, not a shared scratchpad. The Decoder
(`org/DECODER.md`) is the synthesis step — it runs only after convergence
gates pass, collects terminal artifacts, and checks them for conflicts.

What the harness adds: fan-out width is bounded by graph legality, every
branch's contribution is a registered artifact with provenance, and synthesis
cannot run early (`NEVER synthesize before convergence`).

## 3. Adversarial verification (对抗性验证)

**DW shape**: each generator's output is checked by an independent skeptic
agent.

**Harnessed shape**: this is literally one edge:

```yaml
# ontology/relations.yaml (excerpt)
- from: security-engineer
  to: senior-engineer
  type: evaluates
  weights:
    blocking: required
```

`blocking: required` means the producer **cannot settle** until the evaluator
completes *after* it — enforced by the `all_blocking_evals_resolved`
convergence gate (`tools/ledger.py`), not by the orchestrator remembering to
check. Current required evaluator edges: tdd→senior-engineer,
security-engineer→senior-engineer, release-manager→{dependency-auditor,
devops-engineer}, delivery-prover→{senior-engineer, senior-frontend,
prototype}.

What the harness adds: verification is structural and non-optional. The
artifact approval lifecycle (draft → approved) is keyed to the same edges —
an artifact with a required evaluator stays unapproved until that evaluator
completes.

## 4. Generate-and-filter (生成并筛选)

**DW shape**: overgenerate ideas with several agents, then filter/dedup by
criteria.

**Harnessed shape**: **candidate activation + policy decision**. Completed
roles propose activation candidates along `triggers` / `may_trigger` edges —
that is generation. Policy (`tools/policy.py`) plus the Thompson-sampled
weight matrix filter them: low-probability edges are dropped, undecided
candidates must receive an explicit activate/skip/defer decision before the
`no_undecided_activation_candidates` gate passes.

What the harness adds: the filter criteria are learned, not improvised — each
delivered task updates edge weights, so the generator/filter loop improves
across tasks instead of resetting.

## 5. Tournament (锦标赛)

**DW shape**: N agents attempt the same task; pairwise judging selects a
winner.

**Harnessed shape**: the closest current equivalents are **A/B policy runs**
(same task, different routing policy — e.g. Thompson vs. symbolist, compared
across traces) and blind quality evaluation roles (`product-critic` rates
outputs STRONG/COMPETENT/MEDIOCRE/DIRECTIONLESS without seeing who produced
them). A first-class N-way tournament (N parallel instantiations of one role,
judged by an evaluator edge) is expressible in the model — one role, N
iterations, an `evaluates` edge as judge — but is not yet packaged as a
runtime mode. **Open contribution surface.**

## 6. Quarantine (隔离)

**DW shape**: agents that read untrusted content are barred from
high-privilege operations; dedicated action agents act on their findings.

**Harnessed shape**: **layered entry control + typed information flow**.
Layer 2/3 roles can never be entry nodes (`NEVER mark Layer 2 or Layer 3
roles as entry nodes`) — raw task input only enters through intake roles.
Non-activation edges (`supports`, `constrains`, `complements`, `augments`)
carry information without granting execution. Handoffs carry compressed,
digest-validated context blocks rather than raw upstream context.

What the harness adds: information flow and privilege are visible in the
graph (no invisible orchestrator), and every handoff's content provenance is
auditable after the fact. Hard sandboxing of role processes is the runtime's
responsibility and is an open hardening area.

---

## The meta-point

| | DW script | Silicon Org graph |
|---|---|---|
| Where the pattern lives | throwaway JS, regenerated per task | typed edges, versioned in `ontology/` |
| After the run | gone | trace + quality signals → weight update |
| Verification | agent decides to check | gate refuses to settle without it |
| Tracking | script variables, one process | ledger, survives restarts and agent swaps |

If you use these six patterns daily and are tired of re-prompting them into
existence, the harness is the persistence layer you are missing. Start with
[`README.md`](../README.md) Quick Start, then
[`DYNAMIC_WORKFLOW_HARNESS.md`](DYNAMIC_WORKFLOW_HARNESS.md) for the doctrine.
