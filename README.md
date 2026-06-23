# Silicon Org

**Dynamic Workflow, with a harness.**

Coding agents like Claude Code converged on a pattern called **Dynamic
Workflow**: dynamically spin up role-scoped subagents — a reviewer, a
test-runner, an architect — to beat the three chronic failures of
single-context agents: lost task tracking, self-verification bias, and goal
drift.

The paradigm is right. But as practiced, it is **ephemeral** — every role is
re-invented per task, the todo list lives and dies inside one context window,
review happens only if the agent decides to bother, and nothing learned in one
run survives to the next.

Silicon Org keeps the paradigm and adds the missing layer:

| Dynamic Workflow improvises this per task | Silicon Org persists it |
|---|---|
| Role design (prompt-crafted on the spot) | **Role ontology** — 38 curated, versioned role definitions covering the ecosystem's observed role vocabulary |
| Task tracking (in-context todos) | **Ledger** — durable task facts + 6 convergence gates that define "done" outside any context window |
| Verification (optional self-check) | **Blocking `evaluates` edges** — the producer *cannot* settle until an independent reviewer role completes |
| Routing (re-decided cold each time) | **Learned weight matrix + Thompson Sampling** — every real trace improves the next activation decision |

> Statically curate what converges (role definitions).
> Dynamically decide what varies (role activation).
> Learn what improves (routing weights).

Agent-agnostic: Claude Code, Codex, Cursor, pi, or any coding agent becomes
the Runtime. Full doctrine: [`docs/DYNAMIC_WORKFLOW_HARNESS.md`](docs/DYNAMIC_WORKFLOW_HARNESS.md).

---

## Quick Start

```bash
git clone https://github.com/zengury/silicon38.git
cd silicon38
```

Then start your coding agent **in this directory**:

| Agent | Command |
|-------|---------|
| Claude Code | `claude` |
| Codex | `codex` |
| pi | `pi` |
| Cursor | Open this folder in Cursor |
| Any other | Just start it here |

**That's it.** No installation. No configuration. No API keys.
All 38 role skills are pre-packaged in `.agents/skills/`. The agent reads
`AGENTS.md` → `org/RUNTIME.md` and becomes the Runtime automatically.

LangGraph-native execution is an optional local OSS runtime dependency:

```bash
python -m pip install -e '.[langgraph-oss]'
python tools/langgraph_native_smoke.py
```

Run a local LangGraph-native task:

```bash
python tools/langgraph_run.py \
  --task-id task-local-demo \
  --description "Validate native LangGraph execution." \
  --max-role-executions 2 \
  --replace
```

By default this uses `semantic_command`, which calls the local `pi` CLI via
`tools/semantic_node_executor.py`. Set `SILICON_ORG_NODE_AGENT=codex` or
`SILICON_ORG_NODE_AGENT=claude` to use another installed local agent.
No LangGraph Platform, no LangSmith, no hosted tracing — local OSS only.

---

## How a task runs (DW vocabulary ↔ harness vocabulary)

You describe a task in natural language. The Runtime:

1. **Encodes** it — task type, entry roles, a fresh ledger (*DW: "plan the workflow"*)
2. **Activates roles dynamically** — typed edges propose candidates, policy
   decides legality, learned weights rank them (*DW: "spawn subagents"*)
3. **Fans out and pipelines** — independent roles run in parallel; handoffs
   carry digest-linked Context Compression Reports (*DW: "parallel + pipeline"*)
4. **Reviews structurally** — blocking evaluator roles (tdd, security-engineer,
   delivery-prover) must complete *after* their producers before anything
   settles (*DW: "verification subagent", but mandatory*)
5. **Converges on gates, not vibes** — six ledger-computed gates define done;
   delivery status is derived from them
6. **Learns** — quality signals update the weight matrix; the next task routes
   better

Mental model (five concepts, unchanged): **Graph** is law, **Ledger** is task
facts, **Policy** says what is legal now, **Runtime** executes it, **Learning**
updates the organization from real traces.
See [`docs/HARNESS_ENGINEERING.md`](docs/HARNESS_ENGINEERING.md).

---

## The role library

```
38 roles   ·   142 typed edges   ·   7 relation types   ·   38 pre-packaged skills
```

| Layer | Role | Agents |
|-------|------|--------|
| **Intake** | Understand & decompose | triage, zoom-out, caveman, grill-with-docs, to-prd, to-issues, prototype |
| **Architecture** | Design the system | architect, api-designer, database-engineer, improve-codebase-architecture |
| **Engineering** | Build it | senior-engineer, tdd, diagnose, refactor-specialist |
| **Operations** | Secure & deploy | devops-engineer, observability-engineer, performance-engineer, security-engineer |
| **Design** | Craft the interface | ux-researcher-designer, ui-design-system, apple-hig-expert, senior-frontend, epic-design |
| **Quality** | Review & challenge | code-reviewer, grill-me, dependency-auditor, technical-writer |
| **Release** | Ship it | release-manager, handoff |

The library is curated, not closed — adding a role is 4 files:

1. Skill: `.agents/skills/<role>/SKILL.md`
2. Harness profile: `org/registry/<role>.md` (follow `org/HARNESS.md`)
3. Ontology entry: `ontology/nodes.yaml`
4. Edges: `ontology/relations.yaml`

### Relation types

| Type | Meaning |
|------|---------|
| `triggers` | Completion creates an activation candidate |
| `may_trigger` | Conditional activation |
| `evaluates` | Reviews target's output; `blocking: required` makes it mandatory |
| `constrains` | Reduces target's design space |
| `supports` | Provides context to target |
| `complements` | Combined output > each alone |
| `augments` | Adds to target's output |

---

## Audit trail

Every task produces a complete, timestamped trail under `traces/<task_id>/`:

```
manifest.yaml          task index, outcome, artifact index
state.yaml             task facts used by Runtime and Policy
events.yaml            append-only event stream
artifacts/             all produced files + provenance sidecars
handoffs/              deliverable + compressed context-chain blocks
```

Every handoff is backed by a node-authored Context Compression Report —
sources read, retained decisions, constraints, assumptions, open questions,
omitted context, rationale, quality checks — digest-linked and
policy-validated. This is what "task tracking" means when it has to survive
context windows, process restarts, and handoffs between different LLMs.

---

## Why a harness, honestly

Multi-agent systems suffer organizational diseases — hidden information, peer
pressure convergence, bystander effects, invisible orchestrators
([`docs/ANALYSIS_AI_ORG_DISEASE.md`](docs/ANALYSIS_AI_ORG_DISEASE.md)). The
harness is the architectural defense: structured communication, visible power
structure, traceable decisions.

The cost is ceremony: ledger writes, context reports, gates. For a small task,
raw Dynamic Workflow is faster. The harness wins when tasks are **long,
multi-role, auditable, or repeated** — when persistence pays. That is the
honest boundary, and it is exactly the regime where ephemeral DW breaks down.

---

## Documentation

| Document | Content |
|----------|---------|
| [`docs/DYNAMIC_WORKFLOW_HARNESS.md`](docs/DYNAMIC_WORKFLOW_HARNESS.md) | Design doctrine — DW with a harness |
| [`docs/DW_PATTERNS_COOKBOOK.md`](docs/DW_PATTERNS_COOKBOOK.md) | The six DW patterns expressed as graph topologies |
| [`docs/DW_ROLE_SURVEY.md`](docs/DW_ROLE_SURVEY.md) | Ecosystem survey — why a curated role library covers the vocabulary |
| [`org/RUNTIME.md`](org/RUNTIME.md) | Runtime protocol — what your agent must follow |
| [`org/CONTEXT_BLOCK.md`](org/CONTEXT_BLOCK.md) | Continuity anchor — origin, invariants, non-negotiables |
| [`org/HARNESS.md`](org/HARNESS.md) | Agent harness specification |
| [`org/REGISTRY.md`](org/REGISTRY.md) | 38-role registry with selection guide |
| [`org/ENCODER.md`](org/ENCODER.md) | Task intake protocol |
| [`org/DECODER.md`](org/DECODER.md) | Synthesis and delivery protocol |
| [`docs/SPEC.md`](docs/SPEC.md) | Full technical specification |
| [`docs/HARNESS_ENGINEERING.md`](docs/HARNESS_ENGINEERING.md) | Graph / Ledger / Policy / Runtime / Learning |
| [`docs/LANGGRAPH_NATIVE_RUNTIME.md`](docs/LANGGRAPH_NATIVE_RUNTIME.md) | Native runtime contract |
| [`docs/VERSIONING.md`](docs/VERSIONING.md) | Continuity and versioning rules |
| [`docs/adr/0001-hybrid-langgraph-runtime-learning-kernel.md`](docs/adr/0001-hybrid-langgraph-runtime-learning-kernel.md) | ADR: LangGraph-native runtime |
| [`docs/silicon-org-visualizer.md`](docs/silicon-org-visualizer.md) | Local 3D visualizer demo |

---

## License

MIT — see [LICENSE](LICENSE)
