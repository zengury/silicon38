# Talent Evaluation — 2026-06-23

**Batch**: First recruiting run  
**HRBP**: Silicon Org Runtime (manual execution)  
**Sources**: wshobson/agents (37.1k ⭐), VoltAgent/awesome-claude-code-subagents (22.3k ⭐),
addyosmani/agent-skills (6.4k ⭐), hesreallyhim/awesome-claude-code (47.1k ⭐),
arXiv cs.AI/cs.SE (May–Jun 2026), Hacker News community chatter  
**Candidates reviewed**: 15  
**Watch list inherited**: 0 (first run)

---

## Verdicts

| Candidate | Source | Verdict | One-line rationale |
|---|---|---|---|
| threat-modeling-expert | wshobson 37.1k | **HIRE** | security-engineer audits code; nobody designs the threat surface before code is written |
| chaos-engineer | VoltAgent 22.3k | **HIRE** | no role in the org owns fault injection, game days, or resilience experimentation |
| compliance-auditor | VoltAgent 22.3k | **HIRE** | security-engineer ≠ regulatory; GDPR/CCPA/HIPAA gap is a hard blocker for SaaS |
| ai-engineer | VoltAgent 22.3k + wshobson 37.1k | **HIRE** | no role covers LLM API integration, RAG pipelines, or vector store wiring |
| data-engineer | VoltAgent 22.3k | **HIRE** | database-engineer ≠ data pipelines; ETL/ELT/streaming/lakehouse is absent |
| sre-engineer | VoltAgent 22.3k + Anthropic cookbook | **HIRE** | observability-engineer instruments; nobody owns SLOs, error budgets, or toil |
| incident-responder | Anthropic cookbook + lst97 | **HIRE** | diagnose finds root causes; nobody runs live-incident command or writes post-mortems |
| spec-driven-developer | addyosmani 6.4k | **ABSORB** | value is a pre-coding specification gate → add as Specification Gate to senior-engineer |
| mcp-developer | VoltAgent 22.3k | **ABSORB** | MCP server design is specialized API work → add MCP section to api-designer harness |
| assumption-mapping | VoltAgent 22.3k | **ABSORB** | identifies risks in retained scope → add to scope-prosecutor after KEEP decisions |
| first-principles-thinking | VoltAgent 22.3k | **REJECT** | directly redundant with caveman (First Principles Analyst) |
| ai-writing-auditor | VoltAgent 22.3k | **REJECT** | self-defeating in an AI-generated org; every artifact would fail this audit |
| mlops-engineer | VoltAgent 22.3k | **WATCH** | gap is real; revisit when ML development tasks appear in org traces |
| build-engineer | VoltAgent 22.3k | **WATCH** | gap is real; revisit when large monorepo build-system tasks surface |
| context-engineer | muratcankoylan 900 | **WATCH** | concept valid but still crystallizing; community evidence insufficient today |

---

## HIRE Integration Specs

### 1. threat-modeling-expert

```yaml
hire_spec:
  role_id: threat-modeling-expert
  title: Threat Modeling Expert
  layer: 3
  domain: security
  source_url: https://github.com/wshobson/agents
  license: MIT
  evidence:
    stars: 37100
    last_commit: 2026-06
    usage_examples:
      - STRIDE threat model for a payment API
      - Attack tree for a multi-tenant SaaS auth surface
  gap_filled: >
    security-engineer audits existing code for vulnerabilities;
    threat-modeling-expert designs the threat surface and mitigation
    requirements *before* implementation begins — a distinct pre-build
    security discipline with different outputs (threat model doc, attack
    trees, ranked mitigations).
  trigger_conditions:
    - new system or service being designed
    - architect has produced an architecture document
    - task involves sensitive data, auth, payments, or external attack surface
  edges_to_add:
    - type: triggers
      from: architect
      to: threat-modeling-expert
    - type: evaluates
      from: threat-modeling-expert
      to: architect
      blocking: advisory
    - type: supports
      from: threat-modeling-expert
      to: security-engineer
  files_to_create:
    - org/registry/threat-modeling-expert.md
    - ontology/nodes.yaml      # add entry under layer 3, domain: security
    - ontology/relations.yaml  # add 3 edges above
    - .agents/skills/threat-modeling-expert/SKILL.md
  estimated_effort: 1 session, ~45 min
```

### 2. chaos-engineer

```yaml
hire_spec:
  role_id: chaos-engineer
  title: Chaos Engineer
  layer: 3
  domain: reliability
  source_url: https://github.com/VoltAgent/awesome-claude-code-subagents
  license: MIT
  evidence:
    stars: 22300
    last_commit: 2026-06
    usage_examples:
      - Chaos Monkey experiment for a distributed cache layer
      - Game-day runbook for a Kubernetes cluster network partition
  gap_filled: >
    performance-engineer optimizes throughput; observability-engineer
    instruments telemetry; neither owns deliberate failure injection,
    steady-state hypothesis testing, or game-day execution —
    the only way to discover resilience gaps before users do.
  trigger_conditions:
    - service has been deployed and is operational
    - devops-engineer or senior-engineer has completed
    - task explicitly requests reliability or SLA hardening
  edges_to_add:
    - type: may_trigger
      from: devops-engineer
      to: chaos-engineer
    - type: may_trigger
      from: senior-engineer
      to: chaos-engineer
    - type: evaluates
      from: chaos-engineer
      to: observability-engineer
      blocking: advisory
  files_to_create:
    - org/registry/chaos-engineer.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/chaos-engineer/SKILL.md
  estimated_effort: 1 session, ~40 min
```

### 3. compliance-auditor

```yaml
hire_spec:
  role_id: compliance-auditor
  title: Compliance Auditor
  layer: 3
  domain: legal-regulatory
  source_url: https://github.com/VoltAgent/awesome-claude-code-subagents
  license: MIT
  evidence:
    stars: 22300
    last_commit: 2026-06
    usage_examples:
      - GDPR article 30 data processing register for a SaaS app
      - HIPAA technical safeguard gap analysis
      - CCPA opt-out flow audit
  gap_filled: >
    security-engineer covers technical vulnerabilities (OWASP, CVEs);
    dependency-auditor covers license/supply-chain; neither maps the
    system to regulatory frameworks — data residency, consent management,
    audit log requirements, breach notification timelines.
    For any team building user-facing SaaS, this is a hard ship blocker.
  trigger_conditions:
    - product handles PII, health, or financial data
    - security-engineer has completed
    - release-manager is preparing for launch
  edges_to_add:
    - type: triggers
      from: security-engineer
      to: compliance-auditor
    - type: evaluates
      from: compliance-auditor
      to: release-manager
      blocking: advisory
  files_to_create:
    - org/registry/compliance-auditor.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/compliance-auditor/SKILL.md
  estimated_effort: 1 session, ~40 min
```

### 4. ai-engineer

```yaml
hire_spec:
  role_id: ai-engineer
  title: AI Engineer
  layer: 2
  domain: ai-integration
  source_url: https://github.com/VoltAgent/awesome-claude-code-subagents
  license: MIT
  evidence:
    stars: 22300  # VoltAgent; also wshobson 37.1k
    last_commit: 2026-06
    usage_examples:
      - RAG pipeline design for a document Q&A product
      - Embedding model selection and chunking strategy
      - LLM API integration with fallback and cost controls
  gap_filled: >
    architect designs system topology; senior-engineer implements features.
    Neither specializes in LLM-specific design concerns: context window
    management, retrieval pipeline design, embedding model selection,
    hallucination mitigation strategies, cost/latency tradeoffs for
    AI features. As LLM integration becomes standard in software products,
    this gap becomes a structural omission.
  trigger_conditions:
    - task description includes AI features, LLM, RAG, embeddings, or agents
    - architect has produced architecture doc mentioning AI components
  edges_to_add:
    - type: may_trigger
      from: architect
      to: ai-engineer
    - type: triggers
      from: ai-engineer
      to: senior-engineer
    - type: supports
      from: ai-engineer
      to: tdd
  files_to_create:
    - org/registry/ai-engineer.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/ai-engineer/SKILL.md
  estimated_effort: 1 session, ~45 min
```

### 5. data-engineer

```yaml
hire_spec:
  role_id: data-engineer
  title: Data Engineer
  layer: 2
  domain: data-infrastructure
  source_url: https://github.com/VoltAgent/awesome-claude-code-subagents
  license: MIT
  evidence:
    stars: 22300
    last_commit: 2026-06
    usage_examples:
      - Kafka → dbt → Snowflake pipeline design
      - Data contract schema validation between services
      - Delta Lake / Iceberg table partitioning strategy
  gap_filled: >
    database-engineer designs relational schemas and queries.
    data-engineer designs and validates streaming/batch pipelines,
    data contracts, ETL/ELT jobs, and lakehouse architectures —
    a distinct discipline absent from the current org.
  trigger_conditions:
    - task involves data pipelines, ETL, streaming, or analytics infrastructure
    - database-engineer has defined schemas
  edges_to_add:
    - type: may_trigger
      from: database-engineer
      to: data-engineer
    - type: triggers
      from: data-engineer
      to: senior-engineer
  files_to_create:
    - org/registry/data-engineer.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/data-engineer/SKILL.md
  estimated_effort: 1 session, ~35 min
```

### 6. sre-engineer

```yaml
hire_spec:
  role_id: sre-engineer
  title: Site Reliability Engineer
  layer: 2
  domain: reliability
  source_url: https://github.com/VoltAgent/awesome-claude-code-subagents
  license: MIT
  evidence:
    stars: 22300  # VoltAgent; also Anthropic official cookbook
    last_commit: 2026-06
    usage_examples:
      - SLO definition and error budget policy for an API
      - Toil inventory and elimination backlog
      - Capacity planning for 10x traffic spike
  gap_filled: >
    observability-engineer instruments telemetry; devops-engineer
    automates deployment. Neither owns the reliability contract:
    SLO/SLA definition, error budget policies, toil elimination roadmap,
    and the organizational relationship between reliability and feature
    velocity. SRE is a distinct engineering role with its own
    methodology and deliverables.
  trigger_conditions:
    - service is approaching production launch
    - observability-engineer has completed
    - task explicitly requires SLO definition or reliability analysis
  edges_to_add:
    - type: triggers
      from: observability-engineer
      to: sre-engineer
    - type: may_trigger
      from: release-manager
      to: sre-engineer
    - type: evaluates
      from: sre-engineer
      to: devops-engineer
      blocking: advisory
  files_to_create:
    - org/registry/sre-engineer.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/sre-engineer/SKILL.md
  estimated_effort: 1 session, ~40 min
```

### 7. incident-responder

```yaml
hire_spec:
  role_id: incident-responder
  title: Incident Responder
  layer: 3
  domain: reliability
  source_url: https://platform.claude.com/cookbook/managed-agents-sre-incident-responder
  license: MIT
  evidence:
    stars: 500  # lst97/claude-code-sub-agents backing; Anthropic official cookbook
    last_commit: 2026-06
    usage_examples:
      - Live P1 incident timeline and stakeholder comms for a DB outage
      - Blameless post-mortem for a failed deployment causing 2h downtime
  gap_filled: >
    diagnose finds root causes in code; deploy-operator manages deployments.
    Neither owns the live incident command structure: real-time triage,
    stakeholder status communication, runbook execution under pressure,
    blast radius assessment, and the blameless post-mortem artifact.
    Incident response is a discipline with specific outputs.
  trigger_conditions:
    - production incident declared or deployment has failed
    - deploy-operator has failed or flagged a rollback
    - diagnose completed for a live production issue
  edges_to_add:
    - type: may_trigger
      from: deploy-operator
      to: incident-responder
    - type: may_trigger
      from: diagnose
      to: incident-responder
    - type: supports
      from: incident-responder
      to: sre-engineer
  files_to_create:
    - org/registry/incident-responder.md
    - ontology/nodes.yaml
    - ontology/relations.yaml
    - .agents/skills/incident-responder/SKILL.md
  estimated_effort: 1 session, ~35 min
```

---

## ABSORB Actions

### A1. spec-driven-developer → senior-engineer

Add a **Specification Gate** before the existing Minimalism Gate in
`org/registry/senior-engineer.md`:

```md
## Specification Gate (run before Minimalism Gate)

Before writing any code, verify a formal specification exists for
this work item. A specification is: expected inputs, expected outputs,
edge cases handled, edge cases explicitly out of scope, and the
acceptance criterion that will prove it works.

If no specification exists: write one first. Record it in
`key_decisions`. Only proceed to code once the spec is written and
could be handed to a different engineer who had never seen this
conversation.

Source: spec-driven development pattern (addyosmani/agent-skills,
Thoughtworks 2026) — prevents "confident drift" where agents generate
plausible but incorrectly specified behavior.
```

### A2. mcp-developer → api-designer

Add an **MCP Server Design** section to `org/registry/api-designer.md`:

```md
## MCP Server Design (apply when interface target is an AI agent)

If the API is intended for consumption by AI agents via Model Context
Protocol (MCP), apply these additional design rules:
- Tools: verb-noun names, pure functions, deterministic for same inputs
- Resources: stable URIs, read-only, cacheable
- Prompts: parameterized, tested with at least 2 prompt templates
- Transport: stdio for local, HTTP+SSE for remote; never both in v1
- Tool count: ≤ 20 per server (Claude Code lazy-loads beyond this)
- Schema: JSON Schema for all inputs; required vs optional explicit
Source: MCP specification 2026 (linux-foundation governance)
```

### A3. assumption-mapping → scope-prosecutor

Add an **Assumption Risk Map** step to scope-prosecutor output for all
KEEP items in `org/registry/scope-prosecutor.md`:

```md
## Assumption Risk Map (run after KEEP/CUT/DEFER decisions)

For each requirement marked KEEP: name the top 1-2 assumptions the
team is betting on. Score each: HIGH / MEDIUM / LOW risk.
High-risk assumptions should be flagged to product-vision-anchor
or prototyped before full implementation begins.
Source: assumption-mapping pattern (VoltAgent/awesome-claude-code-subagents)
```

---

## Watch List (active after this batch)

| Candidate | Source | Watch reason | Recheck trigger |
|---|---|---|---|
| mlops-engineer | VoltAgent 22.3k | Gap is real; too specialized for current org usage profile | When ML training/serving tasks appear in Silicon Org traces |
| build-engineer | VoltAgent 22.3k | Gap is real; primarily relevant for large monorepos with Bazel/Turborepo | When monorepo build-optimization tasks surface |
| context-engineer | muratcankoylan 900 | Concept valid but still crystallizing; evidence base weak | When stars > 3k OR when context/RAG tasks appear in org traces |

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Reviewed 15 candidates from 6 sourcing channels.
    Applied 6-question hire ladder to all candidates.
    Produced 7 HIRE specs, 3 ABSORB actions, 2 REJECTs, 3 WATCH entries.
  verdicts_summary:
    hire: 7
    absorb: 3
    reject: 2
    watch: 3
  key_decisions:
    - decision: ai-engineer hired as single role covering both llm-architect and ai-engineer archetypes
      rationale: community collections use both names for the same function; one role avoids duplication
    - decision: threat-modeling-expert hired as layer 3 despite activating during architecture phase
      rationale: its primary output is a quality/review artifact (threat model) that constrains architect's output, not a design artifact itself
    - decision: mlops-engineer placed in WATCH not HIRE
      rationale: gap is real but only relevant for ML-heavy teams; no evidence yet that Silicon Org is being used for ML infrastructure tasks
  handoff_focus:
    - 7 HIRE specs are complete and ready to execute — threat-modeling-expert and chaos-engineer are highest priority
    - 3 ABSORB actions can be applied directly to existing harness files in one session
  open_questions:
    - Should ai-engineer be layer 2 (peer to architect, activated for AI-feature tasks) or a sub-specialization of senior-engineer?
    - incident-responder has weak community validation (Anthropic cookbook + 500-star repo) — promote to HIRE based on gap severity alone?
  known_constraints:
    - Adding 7 roles would grow ontology from 38 to 45 nodes; relations.yaml will need careful edge design to avoid activating these roles on non-relevant tasks (may_trigger vs triggers)
  iteration_context: null
```
