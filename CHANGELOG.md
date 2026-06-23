# Changelog

## v0.7.0 — 2026-06-23

### Harness Improvements — Absorb Batch 1

Three behavioral upgrades shipped to existing role harnesses, sourced from the
first HRBP recruiting run. Each was evaluated with a pre/post measurement:
3 scenarios per harness, 6-point rubric, baseline run before editing.

---

#### Specification Gate — `senior-engineer`

`senior-engineer` now requires a formal specification before writing any code.

**The gap**: the role previously ran the Minimalism Gate and then implemented,
resolving ambiguous requirements through silent inference. The role's quality
criterion "Code does exactly what the specification says" assumed a spec existed.
It rarely did.

**What changed**: a Specification Gate runs before the Minimalism Gate. A
specification must name: expected inputs, expected outputs, edge cases in scope,
edge cases explicitly out of scope, and a falsifiable acceptance criterion. If no
spec exists, the role writes one before proceeding — recorded as a named artifact
in `key_decisions`.

**Measured delta**: 1/6 → 6/6 across 3 scenarios. Pre-absorb: role noted "no
spec provided" in completion_report open_questions — post-hoc, not as a gate.
Post-absorb: spec is written first and constrains the Minimalism Gate; tests map
1:1 to acceptance criterion clauses.

Source: spec-driven development pattern (addyosmani/agent-skills, 6.4k ⭐)

---

#### MCP Server Design — `api-designer`

`api-designer` now produces MCP-native schemas when the consumer is an AI agent.

**The gap**: the role designed contracts regardless of who would consume them.
When the consumer was an AI agent (Claude Code, an MCP client), the output
required manual translation — wrong primitive types, no transport selection,
no tool-count constraint, no JSON Schema.

**What changed**: an MCP Server Design section activates when the task mentions
"AI agent," "Claude," or "MCP" as the consumer. Rules: verb-noun tool names,
read-only stable-URI resources, ≤20 tools per server, JSON Schema with explicit
`required` arrays, transport selection (stdio for local, HTTP+SSE for remote;
never both in v1). Ambiguous callers trigger a clarifying question rather than
an assumption.

**Measured delta**: 0/6 → 6/6 across 3 scenarios. Ambiguous-caller scenario
(S3) showed emergent behavior: role detects ambiguity, asks, provides both design
paths with a conditional recommendation.

Source: MCP specification 2026 (linux-foundation governance)

---

#### Assumption Risk Map — `scope-prosecutor`

`scope-prosecutor` now surfaces the hidden bets inside every KEEP decision.

**The gap**: KEEP decisions embedded assumptions about external facts that were
invisible in one-sentence justifications — infrastructure capacity, DB schema
compatibility, LLM latency — and only surfaced as blocked work in sprint 3.

**What changed**: after the verdict table, an Assumption Risk Map runs for every
KEEP item. Each KEEP gets 1–2 named assumptions scored HIGH/MEDIUM/LOW. HIGH
assumptions must be flagged to `product-vision-anchor` or marked "prototype
before implementation sprint." Assumption risk is distinguished from
implementation complexity.

**Measured delta**: 0/6 → 6/6 across 3 scenarios. Pre-absorb: "review latency
< 30 seconds" KEEP with no flag on the LLM inference assumption; "migrate
existing customers" KEEP with no flag on DB schema compatibility. Post-absorb:
both surface as HIGH risk with explicit next actions.

Source: assumption-mapping pattern (VoltAgent/awesome-claude-code-subagents, 22.3k ⭐)

---

### HRBP Recruiting — First Batch (2026-06-23)

First run of the autonomous HRBP recruiting harness. 15 candidates screened
from 6 sourcing channels (wshobson 37.1k⭐, VoltAgent 22.3k⭐, addyosmani 6.4k⭐,
arXiv cs.AI/cs.SE, HN community):

| Verdict | Count |
|---|---|
| HIRE (full integration spec ready to execute) | 7 |
| ABSORB (3 applied this batch, above) | 3 |
| REJECT | 2 |
| WATCH (recheck triggers set) | 3 |

7 HIRE specs (threat-modeling-expert, chaos-engineer, compliance-auditor,
ai-engineer, data-engineer, sre-engineer, incident-responder) fully written
and ready for future sessions. Watch list written to
`traces/index_hrbp_watchlist.yaml`.

---

### Eval Framework

First measurement infrastructure for harness changes. `evals/absorb-batch-1/`
contains 9 pre-absorb baselines + 9 post-absorb runs across the 3 absorb
targets, with a 6-point rubric per eval and a `results/scores.yaml` record.
Future harness changes run against this framework before shipping.

---

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

### Harness Improvements

#### Minimalism Gate — `senior-engineer`

`senior-engineer` now runs a six-question decision ladder before writing any code.

**The gap**: implementation roles trend toward over-engineering — adding utility
functions, new dependencies, and abstraction layers the task never required.
"Do not over-engineer" was a principle with no structural enforcement.

**What changed**: a Minimalism Gate runs before implementation. Six questions
in order; stop at the first that eliminates the need to write code:

1. **Necessary?** Is this in the spec, or assumed?
2. **Standard library?** Does the language stdlib already do this?
3. **Native capability?** Can a built-in language feature replace this?
4. **Existing utility?** Does something in this codebase already do it?
5. **Simplest interface?** Fewest parameters, narrowest types, shortest name?
6. **Deletion test?** If deleted tomorrow, would the system still work for the stated need?

Source: Ponytail minimalism pattern (33.5k ⭐) — absorbed, not hired.

---

#### Minimalism Gate — `refactor-specialist`

`refactor-specialist` now runs a refactor-specific decision ladder before each move.

**The gap**: refactors drift toward extraction and abstraction rather than
deletion. The urge to create a well-named helper is strong; each move makes
the codebase larger, not smaller.

**What changed**: six questions tuned for refactoring, distinct from the
implementation variant:

1. **Necessary?** Does this duplication actually cause harm?
2. **Deletion first?** Can the problem be solved by *deleting* code?
3. **Inline over extract?** Is a well-named local variable clearer than a new function?
4. **Existing abstraction?** Does a construct in this codebase already express this?
5. **Smallest step?** Is there a smaller move that resolves the same problem?
6. **Deletion test?** If this abstraction were deleted, would a future engineer recreate it — or just use the concrete form?

Core rule: a refactor that makes code smaller is strictly better than one that
makes it larger. If the deletion test answer is "they'd delete it again" — don't
create the abstraction.

Source: Ponytail minimalism pattern (33.5k ⭐) — adapted with refactor-specific
framing (deletion-first, inline-over-extract) distinct from the implementation variant.

---

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
