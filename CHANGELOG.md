# Changelog

## v0.6.0 — 2026-06-10

**"Dynamic Workflow, with a harness."** First public-launch release.

### Positioning

- Repositioned the project around Claude Code's official Dynamic Workflow
  feature: Silicon Org is its persistence layer — curated role ontology,
  durable ledger with convergence gates, structural blocking review, and
  routing weights learned from real traces.
- New doctrine: `docs/DYNAMIC_WORKFLOW_HARNESS.md` (design rule: statically
  curate role definitions, dynamically decide role activation, learn routing
  weights).
- New evidence base: `docs/DW_ROLE_SURVEY.md` — cited ecosystem survey
  showing the subagent role vocabulary converges (~25–40 core archetypes;
  largest public collection 192 roles).
- New cookbook: `docs/DW_PATTERNS_COOKBOOK.md` — all six DW patterns
  (classify-and-act, fan-out-and-synthesize, adversarial verification,
  generate-and-filter, tournament, quarantine) expressed as graph topologies.
- README rewritten to lead with the DW claim; `AGENTS.md`, `CLAUDE.md`,
  `org/REGISTRY.md`, `docs/USAGE.md` aligned to the same vocabulary.

### Runtime correctness (merged on main during this line)

- `convergence_policy_node` now derives delivery status from real convergence
  gates — `success` is reachable, `failed` is detected, and `partial` carries
  unmet-gate diagnostics (PR #2).
- Artifact approval lifecycle implemented: artifacts move draft → approved
  once their producer and any required blocking evaluators complete, so the
  `all_artifacts_resolved` gate can settle (PR #3).

## v0.5.0-dev — 2026-05-26

Development line for hybrid runtime and learning kernel.

### Runtime

- Added `runtime/langgraph_adapter.py` as a dependency-optional LangGraph OSS
  execution adapter.
- Kept Silicon Org Graph, Policy, Ledger, and Learning as the core ownership
  boundary. LangGraph is execution substrate only.
- Split graph-legality checks into `tools/policy.py`; `tools/ledger.py` remains
  the durable write surface.

### Continuity

- Added `org/CONTEXT_BLOCK.md` as the origin and intent anchor.
- New task manifests record the Context Block reference and SHA-256 digest.
- Added `docs/VERSIONING.md` for continuity, ADR, and merge-check rules.
- Restored two-part handoff semantics: each downstream handoff now carries a
  direct `deliverable` plus a digest-linked compressed `context_block`.

### Learning

- Added `learning/signals.py` and `learning/weight_update.py`.
- `ledger weights` now records structured signal value, confidence, source,
  and detail for role and relation indices.

### Architecture

- Added ADR 0001 for the hybrid LangGraph runtime and learning kernel.
- Restored `caveman` activation-capable outbound edges based on observed trace
  usage.
- Current graph: 30 agent nodes, 112 typed weighted edges, 7 relation types.
- Added local backing skills for refactor-specialist, observability-engineer,
  performance-engineer, dependency-auditor, and technical-writer.

## v0.1.0 — 2026-05-23

Initial release of Silicon Org.

### Organization

- **30 agent nodes** across 3 layers
- Typed weighted edge graph
- Packaged community skills for the initial role set

### Node Registry

**Layer 1 — Intake & Understanding (7)**
triage · zoom-out · caveman · grill-with-docs · to-prd · to-issues · prototype

**Layer 2 — Architecture (4)**
architect · api-designer · database-engineer · improve-codebase-architecture

**Layer 2 — Engineering (4)**
senior-engineer · tdd · diagnose · refactor-specialist

**Layer 2 — Operations (4)**
devops-engineer · observability-engineer · performance-engineer · security-engineer

**Layer 2 — Design & Experience (5)**
ux-researcher-designer · ui-design-system · apple-hig-expert · senior-frontend · epic-design

**Layer 3 — Quality & Output (6)**
code-reviewer · grill-me · dependency-auditor · technical-writer · release-manager · handoff

### Architecture

- Encoder–Decoder architecture: task intake, graph propagation, terminal synthesis
- Actor model: nodes self-navigate via the ontology graph
- Multi-dimensional edge weights: each relation type has its own weight space
- Weight learning via EMA (α=0.05)
- Full audit trail: timestamped artifacts, provenance sidecars, handoff records
