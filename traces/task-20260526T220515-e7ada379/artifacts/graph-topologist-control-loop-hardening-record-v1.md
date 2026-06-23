# Graph Topologist Development Record — Control Loop Hardening

Date: 2026-05-27
Task context: harden Silicon Org after graph-topologist diagnostics exposed drift between Graph, Policy, Ledger, Runtime, and Learning.

## Purpose

This record preserves the engineering reasoning behind the control-loop fixes.
The goal is not to make the graph look busy. The goal is to make Silicon Org
respond flexibly to task shape while learning safely from its own traces.

## Multi-Dimensional Diagnosis

### 1. Policy Dimension

Finding: Policy already blocks illegal activation through context-only edges,
but it was incomplete in three places:

- post-delivery `meta: true` nodes had no legal activation path;
- `carries_soul` was a node attribute but not a handoff legality condition;
- context reports checked shape but not whether cited handoff digests were real.

Decision: strengthen Policy around source integrity and meta activation, but do
not let Learning mutate Policy automatically.

### 2. Ledger Dimension

Finding: Ledger recorded many facts, but quality and skip semantics were too
weak. A task could be marked success with Runtime self-scored quality, and skip
events did not carry a cost model.

Decision: make success delivery depend on convergence gates, cap unverified
quality, and add `skip_cost` so repeated or high-cost skips become learning
signals.

### 3. Runtime Dimension

Finding: Runtime optimized for fast completion. That is useful, but dangerous
when quality gates become cheap to skip. The prior docs also instructed
post-delivery meta activation in a way the Ledger would reject.

Decision: document meta activation as a post-delivery Policy exception, preserve
`delivered` task status during meta node execution, and require detailed reasons
for skip/defer activation decisions.

### 4. Learning Dimension

Finding: Learning was mostly an index writer. It observed outcomes but did not
produce reviewable proposals for Policy or Runtime changes.

Decision: add `index_learning_proposals.yaml`. Proposals are machine-readable
evidence, not automatic graph edits. This closes part of the feedback loop
without letting a bad retrospective corrupt the graph.

### 5. Trace Evidence Dimension

Finding: The recent graph-topologist report had useful instincts but mixed
correct and incorrect claims. It correctly spotted quality-gate drift and
unused v0.5 meta nodes. It incorrectly said the design cluster had never been
activated across all traces.

Decision: future graph-topologist output must cite trace evidence and separate
global history from recent-task behavior. Low activation is not itself waste;
the defect is "should have activated but did not" or "skipped without adequate
cost/evidence."

### 6. Skill/Topology Dimension

Finding: `graph-topologist` had been pointed at a community project-skill-audit
skill. That skill audits local skills and sessions; it does not own trace
topology, relation activation, or convergence analysis.

Decision: restore `graph-topologist` to the local Silicon Org trace/topology
skill. Community skill audit remains useful to `skill-scout`, not as the
organization's learning topologist.

### 7. Documentation Dimension

Finding: Core docs still said "30 agents" while the graph had 35 nodes. Some
docs claimed behavior the code did not enforce.

Decision: update boot, runtime, decoder, spec, trace schema, and context block
so the written operating system matches executable behavior.

## Changes Made

- Policy now rejects soul-bearing handoffs without `soul_ref: org/soul.md`.
- Policy validates context-report source refs against registered artifacts and
  exact upstream handoff `context_digest` values.
- Policy allows post-delivery activation for `meta: true` nodes after
  `task_completed`.
- Node completion requires both a registered artifact and Context Compression
  Report.
- Ledger preserves `delivered` task status while post-delivery meta nodes run.
- Ledger rejects success delivery when any convergence gate is false.
- Ledger quality signal uses delivery-prover when available, caps unverified
  success, and subtracts skip penalties.
- Ledger rejects skipping required blocking evaluators after their producer has
  completed.
- Ledger records `skip_cost` and requires detailed justification for repeated
  role skips.
- Ledger requires concrete reasons for skip/defer activation decisions.
- Learning writes `index_learning_proposals.yaml` with non-auto-applied review
  proposals for verification gaps, convergence gate breaches, and high-cost
  skips.
- Audit counts linked skill method files, so multi-file skills like `prototype`
  are not falsely classified as skeletons.
- `graph-topologist` skill reference was restored to the local trace-analysis
  skill.

## What Was Intentionally Not Changed

- Learning does not automatically edit `ontology/relations.yaml`. A proposal
  must be reviewed before becoming law.
- Unused edges were not downgraded blindly. A rarely used specialist edge can
  be healthy reserve capacity.
- Existing invalid historical traces were not rewritten. New validation now
  detects their defects; rewriting history would hide the learning signal.

## Verification

Commands run:

- `python3 -m py_compile tools/policy.py tools/ledger.py tools/scheduler.py tools/audit.py learning/*.py`
- `python3 tools/audit.py`
- `git diff --check`
- Direct negative checks:
  - required evaluator skip is rejected;
  - skip/defer activation decision with too-short reason is rejected;
  - old prose context digests are detected as digest mismatches;
  - delivery quality is reduced by skip penalties;
  - learning proposals include verification gaps, convergence breaches, and
    high-cost skips.

Expected historical validation result:

- `task-20260526T220515-e7ada379` remains invalid under the stronger validator
  because it contains real old defects: missing `soul_ref`, prose digests in
  context reports, and unresolved delivery-prover/customer-success candidates.

## Residual Risks

- Skip-cost thresholds are conservative priors and should be tuned after 10-20
  new traces.
- Learning proposals need a review workflow: proposed -> accepted/rejected ->
  policy patch -> audit.
- `delivery-prover` still needs routine activation in real implementation
  tasks; the graph edge exists, but only future traces can prove Runtime follows
  it.
- Graph-topologist quality must be benchmarked against evidence discipline:
  every systemic claim needs trace refs and enough samples.

## Next Review Questions

1. Should `index_learning_proposals.yaml` be promoted into its own Ledger schema?
2. Should graph-topologist proposals require HRBP/skill-scout review before
   policy patches?
3. Should repeated advisory evaluator skips lower quality more aggressively for
   design and architecture task types?
4. Should trace validation be run before `ledger weights` so learning never
   indexes invalid traces as success?
