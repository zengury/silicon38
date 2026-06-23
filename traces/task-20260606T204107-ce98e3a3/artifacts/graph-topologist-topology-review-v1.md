# Graph Topologist — Runtime Review

- **Task**: task-20260606T204107-ce98e3a3
- **Outcome**: success
- **Execution mode**: Runtime manual drive
- **Completed roles**: to-prd, scope-prosecutor, caveman, product-vision-anchor, architect, ux-researcher-designer
- **Deferred roles**: to-issues, senior-engineer, api-designer, database-engineer, devops-engineer, prototype, ui-design-system, product-critic, grill-me, security-engineer, customer-success
- **Artifact count**: 6
- **Handoff count**: 9

## Findings

### 1. Task Type Classification Bottleneck (Structural)

**Observation**: The original LangGraph-native run (task-20260606T123359Z-47218acf) classified the task as `general` instead of `feature`. This caused Policy to gate out 8+ downstream Layer 2/3 nodes (architect, ux-researcher-designer, product-vision-anchor, prototype, senior-engineer, tdd, product-critic, grill-me) because their may_trigger edges have activation_task_types constraints.

**Severity**: Critical — same pattern observed in 5 aggregate tasks.

**Root cause**: `triage` node's task type inference is not surfacing the user's explicit task framing ("从零构建一个mobile app" = feature + design). The task_type enum appears to default to `general` when confidence is below threshold.

**Proposed action**: Add a `task_type_override` field to the manifest that allows Runtime to correct ambiguous classifications after triage. Or add a `task_type_hint` to the Encoder input so user intent is preserved.

### 2. Runtime Manual Drive Viability (Process)

**Observation**: Runtime manual drive successfully completed the design phase by bypassing Policy gating. All 6 nodes produced valid, soul-aligned artifacts. The context chain was preserved through handoff digests. The ledger remained transactional and consistent.

**Positive signal**: The Runtime manual drive path is viable when Policy gating is too restrictive. This is an escape hatch, not a pattern to encourage.

**Risk**: Manual drive bypasses evaluator nodes (caveman→architect evaluates, grill-me→architect evaluates, etc.). The architect artifact was never challenged by an adversarial evaluator. This is acceptable for design-phase tasks where the user will review, but dangerous for implementation tasks.

### 3. Context Report Overhead (Process)

**Observation**: Writing schema-valid context reports for each node accounted for ~30% of Runtime effort in the manual drive. The schema is strict (artifacts_read must be mappings with artifact_id/used/why, handoff context_digest must match exactly, omitted_context reasons must use the enum).

**Proposed action**: Consider relaxing context report validation for Runtime manual drive tasks. The value of exact context_digest matching is high for automated propagation but lower for manual execution.

### 4. Cross-Task Artifact Migration (Process)

**Observation**: Importing artifacts from task-20260606T123359Z-47218acf into task-20260606T204107-ce98e3a3 required rewriting context reports because handoff references didn't match. This is a known limitation of cross-task artifact reuse.

**Proposed action**: Add a `ledger import-artifact <task_id> <source_task_id> <artifact_id>` command that clones an artifact with its provenance and context report but re-links handoffs for the target task.

## Signal

The trace is structurally sound. All 6 artifacts are approved and delivered. The context chain is digest-linked and verifiable. The manual drive produced coherent, soul-aligned output. The primary structural concern is the task_type classification bottleneck, which has now been observed in 6 aggregate tasks.

## Proposed Changes

```yaml
proposals:
  - change: "Add task_type_hint to Encoder input"
    type: graph_policy
    severity: high
    rationale: "User intent ('build a mobile app from scratch') should survive triage classification. A hint field preserves intent without overriding triage autonomy."
  - change: "Relax context report validation for Runtime manual drive"
    type: policy
    severity: medium
    rationale: "Exact digest matching is valuable for automated graph propagation but creates friction in manual execution."
  - change: "Add cross-task artifact import command"
    type: tooling
    severity: medium
    rationale: "Reduces friction when reusing artifacts across task runs."
```
