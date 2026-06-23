# Silicon Org Versioning and Continuity

Silicon Org evolves through code, graph weights, traces, and operating
principles. The goal of versioning is not only rollback. It is preventing
context loss after many iterations.

## Layers of Memory

| Layer | Purpose | File(s) |
|-------|---------|---------|
| Context Block | Preserves origin, invariants, and non-negotiables | `org/CONTEXT_BLOCK.md` |
| ADRs | Records durable architecture decisions | `docs/adr/*.md` |
| Changelog | Human release notes | `CHANGELOG.md` |
| Graph | Current organizational structure | `ontology/*.yaml` |
| Ledger | Task-level facts and experience | `traces/<task_id>/` |
| Learning indices | Cross-task role and relation signals | `traces/index_by_*.yaml` |

## Context Block Rule

Before a change touches runtime, graph, policy, ledger, model routing, or
learning, read `org/CONTEXT_BLOCK.md`.

When the core intent changes, update `org/CONTEXT_BLOCK.md` in the same commit
as the implementation. When the implementation changes but the intent does not,
do not rewrite the Context Block just to narrate the work. Roadmaps, agendas,
and implementation plans belong in ADRs, specs, changelogs, or planning docs,
not in the Context Block.

Every new task manifest records:

```yaml
context_block:
  ref: org/CONTEXT_BLOCK.md
  sha256: <digest-at-task-start>
```

This lets future analysis know which design intent governed a trace.

## ADR Rule

Use an ADR when a decision changes architectural direction or creates a
long-lived boundary. Examples:

- adopting LangGraph as an optional execution substrate
- changing the meaning of Graph, Policy, Ledger, Runtime, or Learning
- changing learning credit assignment
- introducing a new model routing policy

Do not use ADRs for tiny bug fixes.

## Release Rhythm

- Patch: fixes to ledger guards, docs correctness, or trace consistency.
- Minor: new runtime adapter, learning signal type, node, or relation type.
- Major: conceptual model changes that alter Graph/Policy/Ledger semantics.

## Merge Checklist

1. `python3 -m py_compile tools/*.py runtime/*.py learning/*.py`
2. YAML parse for `ontology/*.yaml` and trace indices.
3. `python tools/ledger.py context` prints a Context Block digest.
4. `python tools/audit.py` reports no orphan nodes, dead-head nodes, missing
   harnesses, missing skills, or loose required docs.
5. New task initialization writes `manifest.context_block`.
6. New handoffs include `deliverable` and valid `context_block.context_digest`.
7. New downstream handoffs are backed by a registered Context Compression Report.
8. Review whether `org/CONTEXT_BLOCK.md` or an ADR needs updating.
