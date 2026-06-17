# Decoder — Synthesis Protocol

The Decoder fires when the Task Graph State reaches `settled`.
It does not fire before. It does not wait for manual instruction.
`ledger deliver ... success` enforces the same gates; a successful delivery is
rejected if any gate below is false.

---

## Trigger Condition

```yaml
convergence:
  all_non_loop_nodes_settled: true
  all_loops_resolved: true
  all_blocking_evals_resolved: true
  all_joins_passed: true
  all_artifacts_resolved: true
  no_undecided_activation_candidates: true
```

All must be true. Not before.

---

## Step 1 — Identify What Was Produced

From `artifact_registry`, collect all artifacts with `status: approved`.
Identify terminal nodes (completed but triggered nothing further).

## Step 2 — Check for Conflicts

For each pair of approved artifacts:
- Does the security review flag issues the code claims are resolved?
- Does the architecture decision contradict the API contract?
- If conflict: document explicitly, state resolution, or surface to user.

## Step 3 — Assemble the Deliverable

1. **Primary deliverable** — code, architecture, spec (whatever the task required)
2. **Supporting artifacts** — in logical dependency order
3. **Quality signals** — review outcomes summarized, not copied in full
4. **Open items** — unresolved open_questions from handoff records
5. **Artifact index** — all produced files with status and location

## Step 4 — Write Manifest Outcome

```yaml
timestamp_end: <now>
terminal_nodes: [<roles>]
outcome:
  status: success | partial | failed
  decoder_notes: >
    <One paragraph. What was produced. Key decisions. Deferred items. Quality signal.>
  quality_signal:
    source: delivery-prover | runtime_decoder_unverified | runtime_decoder
    value: 0.0-1.0
    detail: >
      Runtime cannot self-award full confidence. A success without an approved
      delivery-prover artifact is capped as runtime_decoder_unverified.
      Skip costs lower the value even when delivery proof exists.
```

## Step 5 — Update Weight Learning Indices

The Decoder does not edit index files directly. After `ledger deliver` writes
`manifest.outcome`, run:

```bash
python tools/ledger.py weights "$TASK_ID"
```

This appends conservative role and relation signals to
`traces/index_by_role.yaml` and `traces/index_by_relation.yaml`, and appends
non-auto-applied review proposals to `traces/index_learning_proposals.yaml`.

## Step 6 — Deliver to User

- What was produced and where it lives
- What remains open
- What quality signals are pending
- Whether the task is complete or partial
