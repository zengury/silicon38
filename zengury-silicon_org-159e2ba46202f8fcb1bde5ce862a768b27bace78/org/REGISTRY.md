# Role Registry

The curated role library — 38 roles, each with a complete harness definition
in `registry/<role>.md`.

This is the harnessed answer to Dynamic Workflow's per-task role
improvisation: the ecosystem's subagent vocabulary converges on a few dozen
archetypes (see `docs/DW_ROLE_SURVEY.md`), so role *definitions* are curated
and versioned here once, while role *activation* stays dynamic per task.
Stack-specific variants (python-pro, rust-pro…) are model/profile routing
(`org/models.local.yaml`), not new roles.

---

## Intake & Comprehension

| Role | Title | When to select |
|------|-------|----------------|
| `triage` | Triage Analyst | Request is ambiguous, multi-part, or needs classification before work |
| `zoom-out` | Context Mapper | Unfamiliar code area, multi-module impact assessment needed |
| `caveman` | First Principles Analyst | System is too complex for its problem, need plain-language clarity |
| `grill-with-docs` | Documentation Analyst | External library behavior needs verification against spec |

## Product & Planning

| Role | Title | When to select |
|------|-------|----------------|
| `to-prd` | Product Requirements Analyst | Feature intent needs translation to testable requirements |
| `to-issues` | Issue Decomposition Specialist | PRD or spec needs to become independently deliverable work items |
| `prototype` | Prototype Engineer | Feasibility is unknown, validate before committing |

## Product Quality

| Role | Title | When to select |
|------|-------|----------------|
| `scope-prosecutor` | Scope Prosecutor | Feature/design tasks — blind-prosecutes every requirement (KEEP/CUT/DEFER) before execution begins |
| `product-vision-anchor` | Product Vision Anchor | After to-prd+scope-prosecutor — synthesizes JTBD+positioning vision that constrains all downstream nodes |
| `product-critic` | Product Critic | After architecture+UX settle — blind product-quality evaluation (STRONG/COMPETENT/MEDIOCRE/DIRECTIONLESS) |

## Architecture & Design

| Role | Title | When to select |
|------|-------|----------------|
| `architect` | Systems Architect | New system design, technology choices, cross-module coordination |
| `improve-codebase-architecture` | Architecture Improvement Specialist | Coupling problems, module boundary violations, structural debt |
| `api-designer` | API Designer | New public API, service contract, typed interface definitions in any language |
| `database-engineer` | Database Engineer | Schema changes, migrations, query design, data modeling |

## Implementation — Engineering

| Role | Title | When to select |
|------|-------|----------------|
| `senior-engineer` | Senior Engineer | Backend or full-stack code needs to be written or modified |
| `tdd` | Test Engineer (TDD) | New behavior being implemented, bug needs regression test |
| `diagnose` | Diagnostic Engineer | Bug report, error, performance regression, unknown root cause |
| `refactor-specialist` | Refactor Specialist | Technical debt, duplication, clarity improvement without behavior change |

## Implementation — Design & Experience

| Role | Title | When to select |
|------|-------|----------------|
| `ux-researcher-designer` | UX Researcher & Designer | User-facing interaction design, journey mapping, UX research synthesis |
| `ui-design-system` | UI Design System Engineer | Component library, design tokens, visual language specification |
| `apple-hig-expert` | Apple HIG Expert | Apple platform UI evaluation, HIG compliance, platform design guidance |
| `senior-frontend` | Senior Frontend Engineer | Frontend implementation: components, UI, browser/native code |
| `epic-design` | Cinematic Experience Designer | Scroll storytelling, parallax depth, cinematic animations, Apple-style reveals |

## Quality & Challenge

| Role | Title | When to select |
|------|-------|----------------|
| `code-reviewer` | Code Reviewer | After any code is written — always |
| `grill-me` | Critical Challenger | Design or plan needs adversarial stress-test before commitment |
| `product-critic` | Product Critic | Blind product-quality evaluation — 5-test framework against vision statement |
| `security-engineer` | Security Engineer | User input, auth, data persistence, external calls, releases |
| `performance-engineer` | Performance Engineer | Performance regression, high-throughput paths, query optimization |
| `dependency-auditor` | Dependency Auditor | New dependencies, updates, release preparation |

## Infrastructure & Operations

| Role | Title | When to select |
|------|-------|----------------|
| `devops-engineer` | DevOps Engineer | CI/CD, deployment, containers, infrastructure as code |
| `observability-engineer` | Observability Engineer | New production features, incident post-mortem, invisible system behavior |
| `release-manager` | Release Manager | Release preparation, versioning, changelog |

## Knowledge & Continuity

| Role | Title | When to select |
|------|-------|----------------|
| `technical-writer` | Technical Writer | New API shipping, docs needed, release notes |
| `handoff` | Context Transfer Specialist | Session ending, work transferring, state needs capturing |

## Organizational Development

| Role | Title | When to select |
|------|-------|----------------|
| `skill-scout` | Skill Scout | New candidate skill needs evaluation, benchmark tests need creation, candidate pool maintenance |
| `hrbp` | HRBP | Skill replacement decision needs evidence-based recommendation, candidate comparison needed |

## Delivery Verification

| Role | Title | When to select |
|------|-------|----------------|
| `delivery-prover` | Delivery Prover | Any implementation node completed — verifies the deliverable actually works before it reaches the user |

## Customer Success

| Role | Title | When to select |
|------|-------|----------------|
| `customer-success` | Customer Success Manager (白龙马) | Design/feature tasks with customer-facing deliverable — produces onboarding plan, KPI framework, ROI analysis, non-technical user guide. NOT for bug_fix, refactor, or internal tools. |

## Organizational Learning

| Role | Title | When to select |
|------|-------|----------------|
| `graph-topologist` | Graph Topologist | After every task completion — analyzes traces, answers "what worked / what broke / what should change"

---

## Expansion Protocol

1. Define it in `registry/<role>.md` following the harness schema in `HARNESS.md`
2. Add it to `ontology/nodes.yaml` with a real `skill_ref`
3. Add activation-capable or context-only edges in `ontology/relations.yaml`
4. Add it to this registry with domain, title, and trigger summary
5. Run `python tools/audit.py` and fix any reachability or skill-reference issue
