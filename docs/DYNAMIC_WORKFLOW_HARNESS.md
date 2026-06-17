# Dynamic Workflow, with a Harness

**Design doctrine for Silicon Org v2 positioning.**
Status: draft on branch `claude/dynamic-workflow-with-harness`.

---

## 1. The concept we are landing

"Dynamic Workflow" (DW) is an official Claude Code feature (v2.1.154+,
[announcement](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code),
[docs](https://code.claude.com/docs/en/workflows)): instead of a static,
pre-wired pipeline, Claude writes an orchestration script that **constructs
subagents on the fly** — a reviewer here, a test-runner there — to solve three
chronic failures of single-context agents:

1. **Lost task tracking** — long tasks outgrow one context window;
   intermediate results degrade.
2. **Self-verification bias** — the model favors its own outputs; the author
   of code is the worst judge of it.
3. **Goal drift** — constraints get lost across compaction; without an
   external anchor, the objective mutates mid-task.

DW's answer is three orchestration primitives — **`agent()`** (a role-scoped
subagent), **`parallel()`** (fan-out with a barrier), **`pipeline()`**
(streaming sequenced stages) — combined into six recurring patterns
(classify-and-act, fan-out-and-synthesize, adversarial verification,
generate-and-filter, tournament, quarantine).

DW is the right paradigm. But as practiced today it is **ephemeral**: every
role is re-invented per task, every todo list lives in one context, every
verification is ad hoc, and nothing learned in one run survives to the next.

**Silicon Org is Dynamic Workflow with a harness.** Same paradigm — dynamic
role activation, parallel fan-out, pipelined handoffs — but the four things DW
re-does from scratch every time are persisted into infrastructure:

| What DW improvises per task | What the harness persists |
|---|---|
| Role design (prompt-crafted on the spot) | **Role ontology** — a curated, versioned library of role definitions (`ontology/nodes.yaml`, `org/registry/`) |
| Task tracking (in-context todo list) | **Ledger** — durable, auditable task facts with convergence gates (`traces/<task_id>/`) |
| Verification (agent decides to self-check) | **Typed `evaluates` edges with `blocking: required`** — review is structural, not optional |
| Routing (which role next? re-decided cold) | **Learned weight matrix + Thompson Sampling** — every real trace updates activation priors |

The one-line claim: **DW proved that dynamically orchestrated, role-scoped
subagents are the right shape. The harness makes that shape durable,
auditable, and self-improving.**

---

## 2. Why a fixed role library is not a regression from "dynamic"

The instinctive objection: "DW creates roles dynamically; a 38-node ontology
is static." This conflates two different things being dynamic:

- **Role *definitions*** — what a "code reviewer" is, what it must produce,
  what it is allowed to see. DW re-generates these per task. Empirically the
  ecosystem's role vocabulary is small and convergent (see §5): community
  collections cluster in the dozens-to-low-hundreds, and the recurring core is
  a few dozen archetypes. A curated library can cover effectively all of it
  with modest extensions. Re-inventing these per task adds variance, not
  capability.
- **Role *activation*** — which roles run, in what order, with what handoffs,
  for *this* task. This is where dynamism pays, and this is exactly what the
  harness keeps dynamic: activation candidates are computed per task from
  typed edges, decided by policy, and the weights behind those decisions are
  learned from real outcomes.

So the design rule is:

> **Statically curate what converges (role definitions). Dynamically decide
> what varies (role activation). Learn what improves (routing weights).**

DW with ephemeral roles is a special case of this system where the library is
empty and the learning rate is zero.

---

## 3. Mapping DW's three components onto the harness

| DW primitive | Harness primitive | What the harness adds |
|---|---|---|
| **`agent()`** (role-scoped subagent) | Node = skill (`.agents/skills/`) + harness profile (`org/registry/`) + ontology entry | Role contract is versioned and reviewed once, reused everywhere; output must be a registered artifact with provenance |
| **`parallel()`** | LangGraph fan-out over activation candidates (`runtime/langgraph_native.py`) | Fan-out is bounded by typed edges and policy legality, not by the orchestrator's mood; concurrent ledger writes are serialized and auditable |
| **`pipeline()`** | Typed handoffs with Context Compression Reports | Each hop carries a digest-linked context block; the pipeline's shape is recorded and becomes training signal |

All six DW patterns are expressible as graph topologies. Adversarial
verification is literally our `evaluates` + `blocking: required` edge;
classify-and-act is the Encoder + entry-node selection; fan-out-and-synthesize
is parallel activation + Decoder synthesis. The difference is that in DW the
pattern lives in a throwaway script; here it lives in the graph and its
outcomes feed the weight matrix.

And DW's three target failures, structurally:

| DW failure mode | Harness defense | Mechanism |
|---|---|---|
| Lost task tracking | Ledger + convergence gates | `state.yaml` survives process death; six gates (`tools/ledger.py: CONVERGENCE_KEYS`) define "done" independently of any context window |
| Self-verification bias | Blocking evaluator edges | `evaluates` + `blocking: required` (tdd→senior-engineer, security-engineer→senior-engineer, delivery-prover→…) — the producer **cannot** settle until an independent role completes after it |
| Goal drift | Context Block + Encoder contract | `org/CONTEXT_BLOCK.md` digest is recorded in every manifest; task intent is a ledger fact, not a memory |

Plus one thing DW does not have at all:

| Beyond DW | Mechanism |
|---|---|
| **Cross-task learning** | Every delivery emits quality signals (`learning/signals.py`); Thompson Sampling updates edge weights (`tools/thompson_policy.py`); the org's routing gets better with use |

---

## 4. What changes in the project's self-description

The five-concept core (Graph / Ledger / Policy / Runtime / Learning,
`docs/HARNESS_ENGINEERING.md`) is unchanged — it *is* the harness. What
changes is the framing layer above it:

1. **README leads with the DW claim**, not with "38 agents". The agent count
   is evidence, not the headline.
2. **Vocabulary bridge**: docs consistently translate DW terms ↔ harness
   terms (subagent ↔ node, fan-out ↔ parallel activation, handoff ↔ typed
   handoff with context block, todo list ↔ ledger + gates).
3. **The 38 nodes are presented as a *coverage* result**: the curated library
   covers the ecosystem's observed role vocabulary; extension is open and
   cheap (4 files per role).
4. **Honest boundary**: the harness costs ceremony (ledger writes, context
   reports, gates). For small tasks raw DW is faster. The harness wins when
   tasks are long, multi-role, auditable, or repeated — i.e., when persistence
   pays.

## 5. Evidence: how big is the ecosystem's role vocabulary?

Surveyed 2026-06-10 — full data and sources in
[`docs/DW_ROLE_SURVEY.md`](DW_ROLE_SURVEY.md). Summary:

- The largest public agent collection ([wshobson/agents](https://github.com/wshobson/agents))
  has **192** roles; the top collections sum to <700 names before dedup, with
  massive overlap. The deduplicated public vocabulary is high hundreds to low
  thousands — within 1–2 orders of magnitude of our 38.
- The recurring functional core is **~25–40 archetypes** (reviewer, auditor,
  tester, debugger, architect, frontend/backend, devops, data/ML, docs,
  orchestrator…). Most apparent diversity is one archetype × technology stack
  (python-pro, rust-pro…), which the harness handles as model/profile routing,
  not as new roles.
- Anthropic's own taxonomy is smaller still: 3 built-in subagent types, and
  DW's six patterns are built from ~6 task-shaped functional roles (generator
  / verifier / judge / classifier / synthesizer / researcher).

**Conclusion: the curated-library bet is sound.** Role definitions converge;
re-inventing them per task adds variance, not capability. A 38-node ontology
with cheap extension covers the observed engineering core.

---

## 6. Open-source narrative (for launch)

**Headline**: *Dynamic Workflow, with a harness — persistent roles, durable
task state, structural review, and routing that learns.*

**Elevator paragraph**: Claude Code's Dynamic Workflow showed that the right
way to run hard coding tasks is to dynamically orchestrate role-scoped
subagents. Silicon Org keeps that paradigm and adds the missing layer: a
versioned role ontology instead of per-task prompt improvisation, a ledger
with convergence gates instead of an in-context todo list, blocking evaluator
edges instead of optional self-review, and a Thompson-Sampling-weighted graph
that learns from every real trace. It runs agent-agnostic (Claude Code, Codex,
pi, Cursor) with a LangGraph-native local kernel and zero hosted dependencies.

**Who it attracts**:
- *Harness engineers* — people who think in gates, ledgers, and provenance.
- *Multi-agent researchers* — real traces + learning loop = a live testbed
  (MAST-style failure taxonomy already integrated).
- *Coding-agent power users* — those whose DW usage has outgrown one context
  window and want continuity across sessions and tasks.

**Flagship examples to publish**:
1. A long refactor run twice — ephemeral DW vs harnessed DW —
   showing convergence gates, blocking review, and the learned weight delta.
2. "Add a role in 4 files" — extending the library live, demonstrating the
   curated-library-is-open point.
3. A failure post-mortem read straight from the ledger — the audit trail as a
   first-class product.
