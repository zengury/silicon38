# Silicon Org — Usage Guide

## Starting a Task

```bash
claude
```

Give your coding agent a task in natural language:

```
Add rate limiting to the authentication API endpoint
```

```
The search results return in wrong order when sorting by date.
```

```
We need a user settings page: email, password, notification preferences.
```

No need to specify agents — this is Dynamic Workflow with a harness. The
Runtime reads the task, selects entry roles from the curated ontology, and
propagates through the graph: parallel fan-out where edges allow it, pipelined
handoffs with compressed context, blocking review before anything settles.
See [`DW_PATTERNS_COOKBOOK.md`](DW_PATTERNS_COOKBOOK.md) for how the six
Dynamic Workflow patterns map onto this graph.

For the system design behind this process, including graph diagrams and the
runtime guardrails that constrain model execution, read
[`HARNESS_ENGINEERING.md`](HARNESS_ENGINEERING.md).

---

## What Happens

**Phase 0 — Encoder**: identifies task type, selects entry nodes, creates `traces/<task_id>/`

**Phase 1 — Graph Propagation**: Layer 1 understands → Layer 2 implements → Layer 3 reviews

**Phase 2 — Convergence**: checks settled nodes, resolved artifacts, blocking reviews, and activation candidates

**Phase 3 — Decoder**: collects approved artifacts, assembles coherent deliverable

---

## Reading the Audit Trail

```bash
# List recent tasks
ls -lt traces/ | head -10

# Task manifest
cat traces/<task_id>/manifest.yaml

# Event timeline
cat traces/<task_id>/events.yaml

# Decision provenance
cat traces/<task_id>/artifacts/architect-analysis-v1.provenance.yaml

# Context compression report
cat traces/<task_id>/artifacts/architect-context-report-v1.yaml

# Handoff note
cat "traces/<task_id>/handoffs/senior-engineer→code-reviewer-*.yaml"

# Diff code iterations
diff traces/<task_id>/artifacts/senior-engineer-code-v1.ts \
     traces/<task_id>/artifacts/senior-engineer-code-v2.ts
```

Each handoff contains the producer's `deliverable` and a compressed
`context_block` with prior block digests, inherited artifact refs, and the
producer's retained decisions, constraints, assumptions, open questions, and
omissions.

---

## Graph Visualization

The graph source lives in `ontology/nodes.yaml` and
`ontology/relations.yaml`. For an at-a-glance diagram of the current harness
design, read [`HARNESS_ENGINEERING.md`](HARNESS_ENGINEERING.md).

---

## Extending the Organization

```bash
# 1. Add or vendor a backing skill under .agents/skills/<new-role>/SKILL.md

# 2. Write the harness
cp org/registry/senior-engineer.md org/registry/<new-role>.md
# Edit following org/HARNESS.md schema

# 3. Add to nodes.yaml, relations.yaml, REGISTRY.md
```

Rules: new roles are additive unless an ADR justifies a graph correction;
backing skill required; must be reachable from Layer 1.
