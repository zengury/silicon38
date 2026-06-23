# ADR 0002 — Silicon Org Operator (Deferred)

**Status**: DEFERRED — archived for future consideration  
**Date**: 2026-06-23  
**Decision**: Do not build the Operator now. ROI is too low at current scale.

## Context

Silicon Org runs locally via `semantic_command` runner (local CLI subprocess).
There is no scheduled execution, no webhook trigger, and no cloud runtime.
PRD was drafted (see below) but deprioritized.

## Decision

Defer the Operator until one or more of the following conditions is met:
- The org is running > 20 automated tasks per week
- Multiple team members need shared trace access without manual git pull
- A recurring task (HRBP daily, graph-topologist weekly) has proven value
  over ≥ 4 manual runs

Until then: run recurring tasks manually on demand.

## PRD Summary (archived)

### What it would be
A lightweight cloud service (Fly.io / Railway) providing:
1. **SDK Runner** (`runner_mode: sdk_runner`) — calls Anthropic/DeepSeek API
   directly via SDK; no local CLI dependency; tool_use for structured output
2. **Scheduler** — reads `org/schedule.yaml` (declarative cron config)
3. **HTTP trigger** — `POST /trigger` for webhook-based task launch
4. **Git committer** — auto-commits trace results back to repo after each run
5. **GitHub App** (v1.5) — PR-triggered code-review + security runs

### Key open questions at time of deferral
- Q1: Which model for Operator runs? (haiku vs follow models.local.yaml)
- Q2: How to implement `web_search: true` for HRBP? (Tavily / Brave API / skip v1)
- Q3: Interactive override support during runs?
- Q4: Single-repo vs multi-repo?

### Estimated effort when ready to build
- M0 SDK Runner: 1-2 days
- M1 Local scheduling validation: 1 day
- M2 Operator container: 2-3 days
- M3 Fly.io deploy: 1 day
- M4 GitHub webhook: 2 days
- Total: ~7-9 days

### Why deferred
Investment/return ratio too low at current stage. Manual periodic runs cover
the need. Revisit when recurring tasks have demonstrated value over multiple
manual runs.
