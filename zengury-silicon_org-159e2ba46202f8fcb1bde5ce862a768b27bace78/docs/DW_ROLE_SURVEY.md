# Survey: How big is the ecosystem's subagent role vocabulary?

Date: 2026-06-10. Supporting evidence for
[`docs/DYNAMIC_WORKFLOW_HARNESS.md`](DYNAMIC_WORKFLOW_HARNESS.md) §5.

**Claim under test**: the set of distinct subagent roles the Claude Code
ecosystem actually uses is within 1–2 orders of magnitude of Silicon Org's 38
curated roles, and the recurring functional core is well under 100 — so a
curated library plus modest extension covers effectively the whole observed
vocabulary.

**Verdict: supported.**

---

## 1. Largest public agent collections

| Collection | Roles | Notes |
|---|---|---|
| [wshobson/agents](https://github.com/wshobson/agents) | **192** | Flagship collection (84 plugins, 192 agents, 156 skills); grew from ~48 mid-2025 |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | **~157** | 10 categories; largest: Language Specialists (31), Quality & Security (17), Infrastructure (16) |
| [0xfurai/claude-code-subagents](https://github.com/0xfurai/claude-code-subagents) | 100+ | Mostly per-technology experts |
| [dl-ezo/claude-code-sub-agents](https://github.com/dl-ezo/claude-code-sub-agents) | 35 | End-to-end dev automation |
| davepoon/claude-code-subagents-collection | ~36 | |
| lst97, iannuttall and similar personal collections | 10–35 each | |
| Directories ([aitmpl.com](https://www.aitmpl.com/), subagents.cc, subagents.app) | — | Aggregators; "1000+" counts are all component types with heavy re-hosting overlap |

The biggest single collection is ~200 roles. Naively summing the top
collections gives ~600–700 names **before** dedup; every one of them ships a
code-reviewer, security-auditor, python-pro, etc. The deduplicated distinct
named-role set across the public ecosystem plausibly lands in the high
hundreds to low thousands — within 2 orders of magnitude of 38, arguably
within 1 for the meaningful set.

## 2. The recurring functional core: ~25–40 archetypes

Anthropic ships only **3 built-in subagent types** (Explore, Plan,
general-purpose — [official docs](https://code.claude.com/docs/en/sub-agents)).
Community collections converge on roughly:

- **Quality/verification**: code-reviewer, security-auditor, test-automator,
  debugger, performance-engineer, qa-expert
- **Build**: frontend/backend/fullstack developer, api-designer, architect,
  mobile-developer
- **Infra/ops**: devops-engineer, k8s/terraform specialist, database-admin,
  incident-responder, SRE
- **Data/AI**: data-engineer, data-scientist, ml-engineer, llm-architect,
  prompt-engineer
- **Docs/DX**: documentation-engineer, technical-writer, refactoring/legacy-modernizer
- **Meta**: workflow-orchestrator, multi-agent-coordinator, context-manager
- **Business edge**: product-manager, business-analyst

The bulk of every collection beyond this is the **same archetype parameterized
by technology stack** (python-pro, rust-engineer, typescript-pro… = one
archetype × N stacks). Collapsing those, the genuinely distinct core is well
under 100.

Silicon Org's 38 nodes already cover the engineering-relevant majority of this
core; the gaps are mostly stack-parameterized variants — which the harness
treats as profile/model routing (`org/models.local.yaml`), not as new roles.

## 3. Dynamic Workflow is an official Anthropic feature

Not just a community concept: shipped in Claude Code v2.1.154+
([announcement](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code),
[docs](https://code.claude.com/docs/en/workflows)). A dynamic workflow is a
JavaScript script Claude writes, orchestrating temporary subagents in a
background runtime (up to 16 concurrent, 1,000 agents per run).

- **3 primitives**: `agent()` (spawn role-scoped subagent), `parallel()`
  (concurrent with barrier), `pipeline()` (streaming stages)
- **3 target failures**: self-verification bias, goal drift across
  compaction, task tracking / context degradation
- **6 patterns**: classify-and-act, fan-out-and-synthesize, adversarial
  verification, generate-and-filter, tournament, quarantine
- The workflow roles are **task-shaped, not new archetypes**: generator /
  verifier / judge / classifier / synthesizer / researcher — about a
  half-dozen functional roles instantiated thousands of times.

## 4. Implications for Silicon Org

1. **The curated-library bet is sound.** The role vocabulary converges; a
   38-node ontology with cheap extension (4 files/role) covers the observed
   core. "Dynamic role creation" in the wild is overwhelmingly re-derivation
   of the same archetypes.
2. **Our differentiation is exactly what DW lacks.** DW's own docs frame its
   three target failures; the harness answers each structurally (ledger +
   gates, blocking `evaluates` edges, Context Block) and adds the layer DW
   has no equivalent of: cross-task learning over routing weights.
3. **Vocabulary bridge is straightforward.** `agent()` ↔ node activation,
   `parallel()` ↔ LangGraph fan-out over candidates, `pipeline()` ↔ typed
   handoffs with context blocks. All six DW patterns are expressible as graph
   topologies — adversarial verification is literally our `evaluates` +
   `blocking: required` edge.

## Caveat

Private `.claude/agents/` definitions are unobservable and hyper-specific
per-project roles could push raw *name* counts higher — but those collapse
onto the same archetypes, so the claim about distinct *roles* stands.

Key sources: [wshobson/agents](https://github.com/wshobson/agents) ·
[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) ·
[0xfurai/claude-code-subagents](https://github.com/0xfurai/claude-code-subagents) ·
[subagents docs](https://code.claude.com/docs/en/sub-agents) ·
[workflows docs](https://code.claude.com/docs/en/workflows) ·
[Anthropic blog](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code) ·
[36kr team interview](https://36kr.com/p/3839611362658569)
