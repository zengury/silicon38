# Silicon Org — Installation Guide

## Prerequisites

- A coding agent that reads repo instructions, such as Claude Code, Codex,
  Cursor, or pi
- Git

## 1. Clone

```bash
git clone https://github.com/zengury/silicon38.git
cd silicon38
```

## 2. Verify Packaged Skills

```bash
bash install.sh
```

The script verifies `.agents/skills/`; it does not download anything.

## 3. Verify

```bash
ls .agents/skills/triage/SKILL.md
ls .agents/skills/senior-backend/SKILL.md
```

## 4. Open in Your Coding Agent

```bash
claude
```

Claude Code reads `CLAUDE.md`; Codex and other agents read `AGENTS.md`.
Give it a task — Silicon Org handles the rest.

## 5. View the Graph

The source graph is in `ontology/nodes.yaml` and `ontology/relations.yaml`.
For the harness-level diagram, read `docs/HARNESS_ENGINEERING.md`.

---

## Directory Structure

```
/
  README.md
  AGENTS.md           — Runtime entry point for agent-agnostic tools
  CLAUDE.md           — Claude Code entry point
  install.sh          — Packaged skill verifier
  CHANGELOG.md
  LICENSE
  docs/               — Specification and guides
  org/
    RUNTIME.md        — Runtime protocol
    ENCODER.md
    DECODER.md
    HARNESS.md
    REGISTRY.md
    registry/         — 41 agent harness files
  ontology/
    nodes.yaml        — 41 node definitions
    relations.yaml    — 152 typed edges
    relation_types.yaml
    artifact_ledger.yaml
    task_graph_state.yaml
    trace_schema.yaml
  .agents/skills/     — Packaged skill definitions
  traces/             — Created per task at runtime (not shipped)
    index_by_role.yaml
    index_by_relation.yaml
    task-*/           — Per-task ledgers and artifacts
  tools/
    policy.py         — Graph + Ledger legality kernel
    ledger.py         — Durable ledger write CLI
    scheduler.py      — Activation proposal advisor
    audit.py          — Repository and graph integrity audit
    spawn.py          — Subagent prompt assembler / preview
    runners/          — Node runner adapter interface
```
