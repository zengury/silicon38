# Skill Scout — Full Organization Benchmark Report

**Date:** 2026-05-26
**Methodology:** Resume review (SKILL.md depth + benchmark dimension alignment)
**Confidence:** Medium for strong skills (read full content) / Low for thin skills (limited methodology to assess)
**Recommendation:** Thin skills (<50 lines) need full benchmark runs with candidate alternatives before scoring is reliable

---

## Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Methodology depth** | 0.30 | Does the skill provide a process, not just a description? Can a node follow it step-by-step? |
| **Output specificity** | 0.35 | Does the skill specify what artifact to produce, in what format, with what quality bar? |
| **Philosophy/Principles** | 0.15 | Does the skill have explicit principles that guide judgment, or is it pure instruction? |
| **Soul compatibility** | 0.20 | (Design roles only) Does the skill's philosophy align with Kahn's three-room principles? |

Scores: 0.0-1.0. Below 0.40 = critical (needs immediate replacement). 0.40-0.60 = weak (candidate search active). 0.60-0.80 = adequate. 0.80+ = strong.

---

## Layer 1 — Intake & Understanding

### triage — `mattpocock/skills`
**Score: 0.78** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | State machine with clear transitions. Gather→Recommend→Reproduce→Grill→Apply pipeline. |
| Output | 0.80 | Agent brief format, triage notes template, label application spec. |
| Philosophy | 0.65 | "Every issue carries exactly one category + one state role" — clear principle but limited to issue management. |
| Soul | N/A | Not a design role. |

**Verdict:** Solid process skill. No replacement urgency. Would benefit from adding "when to escalate to human" decision tree.

---

### zoom-out — `mattpocock/skills`
**Score: 0.15** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.10 | One prompt fragment: "Go up a layer of abstraction." No process. |
| Output | 0.05 | No output format defined. |
| Philosophy | 0.30 | Implicit principle (abstraction helps) but no methodology to achieve it. |
| Soul | N/A | |

**Verdict:** This is not a skill — it's a one-line instruction. 7 lines total. `disable-model-invocation: true` suggests it was never meant to be a standalone skill. **Immediate replacement needed.** Candidate search: "context-mapper", "system-boundary-analyst", or write a local skill that provides actual module mapping methodology.

---

### caveman — `mattpocock/skills`
**Score: 0.72** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.65 | Clear rules: drop articles/filler/pleasantries, keep technical terms. Auto-clarity exception. |
| Output | 0.70 | Pattern: `[thing] [action] [reason]. [next step].` Examples provided. |
| Philosophy | 0.85 | Strong principle: "All technical substance stay. Only fluff die." Own identity. |
| Soul | N/A | User explicitly removed from soul carriers — caveman has its own strong principles. |

**Verdict:** Does one thing well. Narrow scope but well-defined. Keep.

---

### grill-with-docs — `mattpocock/skills`
**Score: 0.80** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | Challenge→Sharpen→Cross-reference→Update loop. One question at a time discipline. |
| Output | 0.80 | CONTEXT.md updates, ADRs (gated by 3-condition test), inline decisions. |
| Philosophy | 0.75 | "Glossary is the source of truth. ADRs only when hard to reverse + surprising + real trade-off." |
| Soul | N/A | |

**Verdict:** Strong. Has sub-files (CONTEXT-FORMAT.md, ADR-FORMAT.md) that provide additional depth. Keep.

---

### to-prd — `mattpocock/skills`
**Score: 0.76** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.75 | Explore→Sketch modules→Write PRD pipeline. Template provided. |
| Output | 0.85 | Structured template: Problem/Solution/User Stories/Implementation Decisions/Testing/Out of Scope. |
| Philosophy | 0.65 | "Do NOT interview the user — synthesize what you already know." Practical but limits quality in ambiguous cases. |
| Soul | N/A | |

**Verdict:** Proven across 4+ task runs. Template is good. Weakness: no guidance on resolving contradictory requirements. Keep.

---

### to-issues — `mattpocock/skills`
**Score: 0.74** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.75 | Tracer-bullet vertical slices. HITL vs AFK classification. |
| Output | 0.80 | Issue template with acceptance criteria + blocked-by. |
| Philosophy | 0.60 | "Prefer AFK over HITL" is the only explicit principle. |
| Soul | N/A | |

**Verdict:** Works. Proven in FleetOps. Vertical slice discipline is correct. Keep.

---

### prototype — `mattpocock/skills`
**Score: 0.65** ⚠️ Weak

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.70 | Two-branch routing (logic vs UI). Has sub-files LOGIC.md + UI.md. |
| Output | 0.55 | "Throwaway code" is the output. Capture is brief. |
| Philosophy | 0.70 | "Throwaway from day one." "One command to run." "Delete or absorb when done." Good principles. |
| Soul | 0.60 | Prototype mindset aligns with Kahn's "begin in the unmeasurable" — but skill doesn't make this connection. |

**Verdict:** Good principles but thin on output specificity. Sub-files (LOGIC.md, UI.md) provide depth. Adequate for now but could be replaced by a more structured prototyping framework.

---

## Layer 2 — Architecture & Engineering

### architect — `senior-architect` from `alirezarezvani/claude-skills`
**Score: 0.88** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.90 | ADR format, decision workflows (database selection, pattern selection, monolith vs microservices). |
| Output | 0.90 | Structured ADR with context/decision/rationale/alternatives/consequences. Diagram generation (Mermaid/PlantUML/ASCII). |
| Philosophy | 0.85 | "Design from constraints, not preferences." "Every structural decision has a stated rationale." |
| Soul | 0.85 | Kimbell-aligned: "Design backward from arrival, not forward from what you hold" maps to the constraints-driven approach. |

**Verdict:** Proven across 3 FleetOps runs producing 8 ADRs. Strongest architect skill in the pool. Keep.

---

### api-designer — `api-design-reviewer` from `alirezarezvani/claude-skills`
**Score: 0.82** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | Linting, breaking-change detection, design scorecards, OpenAPI generation. |
| Output | 0.85 | Route handlers, validation middleware, TypeScript types, OpenAPI specs. |
| Philosophy | 0.75 | "Catches inconsistent conventions, missing versioning, and design smells before APIs ship." |
| Soul | N/A | |

**Verdict:** Comprehensive. Good tooling. Keep.

---

### database-engineer — `database-designer` from `alirezarezvani/claude-skills`
**Score: 0.78** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.80 | Schema design, migration workflows, index strategies, SQL vs NoSQL decision guides. |
| Output | 0.80 | DDL, migration files, optimization suggestions. |
| Philosophy | 0.70 | Decision matrices for technology choices. |
| Soul | N/A | |

**Verdict:** Solid. Keep.

---

### senior-engineer — `senior-backend` from `alirezarezvani/claude-skills`
**Score: 0.85** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.90 | API scaffolder, database migration tool, load tester. Forcing-question library (7 questions). |
| Output | 0.85 | Route handlers, migrations, performance reports. |
| Philosophy | 0.80 | Karpathy discipline: 4 assumptions must be surfaced before scaffolding. "No SLO = no reliability work." |
| Soul | N/A | |

**Verdict:** Strongest engineering skill. 467 lines. Forcing-question library is excellent discipline. Keep.

---

### tdd — `mattpocock/skills`
**Score: 0.70** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.75 | Red-green-refactor loop. |
| Output | 0.70 | Test suite. |
| Philosophy | 0.65 | Standard TDD principles. |
| Soul | N/A | |

**Verdict:** Functional. 109 lines. Does the basics. Could be improved with property-based testing or mutation testing guidance. Keep for now.

---

### diagnose — `mattpocock/skills`
**Score: 0.72** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.80 | Reproduce→Minimise→Hypothesise→Instrument→Fix→Regression-test loop. |
| Output | 0.70 | Root cause + fix + regression test. |
| Philosophy | 0.60 | Disciplined debugging but no explicit principles beyond the loop. |
| Soul | N/A | |

**Verdict:** Solid debugging discipline. Keep.

---

### refactor-specialist — `local/silicon-org`
**Score: 0.40** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.45 | 5-step method exists but is skeletal. |
| Output | 0.35 | "Refactor summary + files changed + behavior-preservation evidence" — vague. |
| Philosophy | 0.40 | "Treat existing behavior as a contract" — correct but undeveloped. |
| Soul | N/A | |

**Verdict:** 25 lines. Too thin for a role that requires deep code understanding. **Replacement needed.** Candidates: "refactoring-catalog" (Martin Fowler patterns), "code-smell-detector", or write a local skill with specific refactoring patterns.

---

### improve-codebase-architecture — `mattpocock/skills`
**Score: 0.82** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | Explore→Present→Grilling loop. Deletion test. Depth/leverage/locality framework. |
| Output | 0.85 | Self-contained HTML report with before/after diagrams. |
| Philosophy | 0.80 | Strong glossary: module, interface, implementation, depth, seam, adapter, leverage, locality. Based on Ousterhout's Philosophy of Software Design. |
| Soul | N/A | |

**Verdict:** Surprisingly strong despite 81 lines — sub-files (LANGUAGE.md, HTML-REPORT.md, INTERFACE-DESIGN.md) provide depth. Keep.

---

### devops-engineer — `ci-cd-pipeline-builder` from `alirezarezvani/claude-skills`
**Score: 0.65** ⚠️ Weak

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.70 | Pipeline generation from detected stack signals. |
| Output | 0.65 | Pipeline config files. |
| Philosophy | 0.55 | "Fast baseline generation, repeatable checks." Pragmatic but thin. |
| Soul | N/A | |

**Verdict:** 147 lines. Functional but light on deployment strategy, environment management, rollback patterns. **Candidate search recommended.**

---

### observability-engineer — `local/silicon-org`
**Score: 0.35** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.40 | 5-step method exists. |
| Output | 0.30 | "Observability plan or patch" — no format. |
| Philosophy | 0.35 | "Prefer low-cardinality metrics" — one good principle but no depth. |
| Soul | N/A | |

**Verdict:** 24 lines. Too thin. **Replacement needed.** Candidates: "observability-designer" (if exists in ecosystem), or write a local skill based on Google SRE Workbook golden signals.

---

### performance-engineer — `local/silicon-org`
**Score: 0.30** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.35 | Minimal. |
| Output | 0.25 | Vague. |
| Philosophy | 0.30 | Minimal. |
| Soul | N/A | |

**Verdict:** 26 lines. **Replacement needed.** Same urgency as observability-engineer.

---

### security-engineer — `senior-security` from `alirezarezvani/claude-skills`
**Score: 0.84** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | STRIDE analysis, OWASP guidance, cryptography patterns, security scanning. |
| Output | 0.85 | Threat models, vulnerability assessments, hardening guides. |
| Philosophy | 0.80 | Defense in depth. Principle of least privilege. |
| Soul | N/A | |

**Verdict:** 444 lines. Comprehensive. Keep.

---

## Layer 2 — Design & Experience

### ux-researcher-designer — from `alirezarezvani/claude-skills`
**Score: 0.80** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | 4 workflows: persona generation, journey mapping, usability testing, research synthesis. |
| Output | 0.80 | Persona cards, journey maps, test plans, synthesis reports. |
| Philosophy | 0.75 | Data-driven personas. Journey stages with pain points. |
| Soul | 0.75 | Journey mapping aligns with Kimbell's "design backward from arrival" — the journey IS the light path. |

**Verdict:** 419 lines. Comprehensive. Keep but examine whether output has enough "style" for the user's taste.

---

### ui-design-system — from `alirezarezvani/claude-skills`
**Score: 0.55** ⚠️ Weak

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.60 | Token architecture, component specification, accessibility compliance. |
| Output | 0.55 | Design tokens + component specs. But no visual examples or style guidance. |
| Philosophy | 0.50 | "Every token has a semantic name" — correct but no design philosophy. |
| Soul | 0.50 | No Kahn alignment. "Walls two feet thick" should translate to "component depth" but skill doesn't make the connection. |

**Verdict:** 51 lines. The user explicitly said they're unhappy with UI design skills. **Candidate search active.** Potential replacements: "design-system-architect", "visual-language-designer", "design-tokens-framework".

---

### apple-hig-expert — from `alirezarezvani/claude-skills`
**Score: 0.68** ⚠️ Weak

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.70 | HIG compliance review, platform-specific guidance. |
| Output | 0.70 | Non-compliance list with HIG references. |
| Philosophy | 0.65 | Apple HIG as doctrine. Narrow but well-defined. |
| Soul | N/A | User removed from soul carriers — Apple-specific, not Kahn. |

**Verdict:** 90 lines. Narrow scope but well-defined within that scope. Adequate for its specific purpose. Keep.

---

### senior-frontend — from `alirezarezvani/claude-skills`
**Score: 0.82** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | React/Next.js patterns, performance optimization, bundle analysis, accessibility. |
| Output | 0.85 | Components, pages, optimized builds. |
| Philosophy | 0.75 | "Build for the user, not the developer." Accessibility-first. |
| Soul | 0.75 | Esherick-aligned: interface faces both ways — outward (user) and inward (data). |

**Verdict:** 572 lines. Strongest frontend skill. Keep.

---

### epic-design — from `alirezarezvani/claude-skills`
**Score: 0.78** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | 45+ techniques across 8 categories. Inspects→Judges→Plans→Codes workflow. |
| Output | 0.80 | Cinematic websites with scroll effects, parallax, animations. |
| Philosophy | 0.75 | "Make it feel alive." "Premium without WebGL." |
| Soul | 0.70 | Salk-aligned in theory ("the emptiness is what tells the person it matters") but skill leans toward maximalism, not subtraction. Tension with Kahn. |

**Verdict:** 353 lines. Technically strong but philosophically at odds with Kahn's subtraction principle. Keep for now but monitor soul alignment.

---

### customer-success — `zengury/teamup` (Bailongma)
**Score: 0.72** ✅ Adequate (new)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.75 | 30/60/90 milestones, KPI framework, ROI calculation. |
| Output | 0.80 | Customer success plan, KPI framework, onboarding guide, ROI calc. |
| Philosophy | 0.70 | "Speak business, not code." "Service first." Bailongma identity — strong narrative but light on methodology. |
| Soul | N/A | |

**Verdict:** New. Based on solid Bailongma character from teamup. Adequate for now. Monitor first 3 task runs.

---

## Layer 3 — Quality & Output

### delivery-prover — `local/silicon-org` (new)
**Score: 0.65** ⚠️ Weak (new, untested)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.70 | Protocol for web/CLI/API verification. Time-bounded steps. |
| Output | 0.70 | Structured PASS/FAIL/BLOCKED report with reproduction steps. |
| Philosophy | 0.55 | "Does not fix — reports." Clean separation of concerns but untested. |
| Soul | N/A | |

**Verdict:** New. Written today. Methodology is sound on paper but has never been executed. **Needs 3 trial runs** before score is reliable.

---

### code-reviewer — from `alirezarezvani/claude-skills`
**Score: 0.78** ✅ Adequate

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.80 | SOLID analysis, code smells, complexity scoring, review checklists. |
| Output | 0.80 | Review reports with severity ratings. |
| Philosophy | 0.70 | "Review for risk, not style." |
| Soul | N/A | |

**Verdict:** 220 lines. Solid. Keep.

---

### grill-me — `mattpocock/skills`
**Score: 0.25** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.20 | "Interview me relentlessly" — 3 sentences. No framework for adversarial questioning. |
| Output | 0.15 | No output format defined. |
| Philosophy | 0.40 | Implicit: adversarial review is valuable. But no methodology to execute it. |
| Soul | 0.30 | Soul-bearing role with no soul methodology. |

**Verdict:** 10 lines. This is a prompt fragment, not a skill. For a role that is supposed to be the org's strongest critic, this is unacceptable. **Immediate replacement needed.** Candidates: "adversarial-reviewer", "devils-advocate", "design-critic", or write a local skill with structured questioning frameworks (e.g., "5 Whys", "pre-mortem", "assumption inversion").

---

### dependency-auditor — `local/silicon-org`
**Score: 0.30** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.30 | Minimal. |
| Output | 0.25 | Vague. |
| Philosophy | 0.35 | Minimal. |
| Soul | N/A | |

**Verdict:** 25 lines. **Replacement needed.** Should cover supply-chain risk, license compliance, version drift, CVE scanning. Current skill is a placeholder.

---

### technical-writer — `local/silicon-org`
**Score: 0.30** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.30 | Minimal. |
| Output | 0.25 | Vague. |
| Philosophy | 0.35 | Minimal. |
| Soul | N/A | |

**Verdict:** 24 lines. **Replacement needed.** Should cover API docs, user guides, release notes, architectural decision records. Current skill is a placeholder.

---

### release-manager — from `alirezarezvani/claude-skills`
**Score: 0.80** ✅ Strong

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.85 | Release planning, changelog management, deployment coordination, versioning. |
| Output | 0.80 | Release plans, changelogs, deployment checklists. |
| Philosophy | 0.75 | "Coordinate deployments, not just tag versions." |
| Soul | N/A | |

**Verdict:** 489 lines. Surprisingly comprehensive. Keep.

---

### handoff — `mattpocock/skills`
**Score: 0.30** 🔴 Critical

| Dimension | Score | Notes |
|-----------|-------|-------|
| Methodology | 0.25 | "Write a handoff document" — no structure. |
| Output | 0.30 | "Save to temp directory" — no format. |
| Philosophy | 0.35 | "Don't duplicate content already captured." Correct but thin. |
| Soul | N/A | |

**Verdict:** 15 lines. For a role responsible for context continuity between sessions, this is critically thin. **Immediate replacement needed.** The org's context compression report format is more sophisticated than this skill.

---

## Meta Nodes

### skill-scout — `local/silicon-org` (new)
**Score: 0.70** ⚠️ Adequate (new, untested)

**Verdict:** New. Benchmark catalog exists (this document is its output). Methodology defined. Needs execution trials.

### hrbp — `zengury/hr-assistant` (new)
**Score: 0.75** ⚠️ Adequate (new, untested)

**Verdict:** New. Based on Andy Grove principles via hr-assistant repo (287 management skills). Strong foundation. Needs trial runs.

### graph-topologist — `local/silicon-org` (new)
**Score: 0.72** ⚠️ Adequate (new, untested)

**Verdict:** New. Methodology extracted from FleetOps retrospectives. Pattern detection framework is sound. Needs trial runs.

---

## Summary

| Grade | Count | Roles |
|-------|-------|-------|
| 🔴 Critical (<0.40) | 6 | zoom-out, refactor-specialist, observability-engineer, performance-engineer, grill-me, dependency-auditor, technical-writer, handoff |
| ⚠️ Weak (0.40-0.60) | 2 | ui-design-system, apple-hig-expert |
| ✅ Adequate (0.60-0.80) | 18 | triage, caveman, grill-with-docs, to-prd, to-issues, prototype, database-engineer, tdd, diagnose, devops-engineer, epic-design, customer-success, delivery-prover, code-reviewer, skill-scout, hrbp, graph-topologist, release-manager |
| ✅ Strong (0.80+) | 8 | architect, api-designer, senior-engineer, improve-codebase-architecture, security-engineer, ux-researcher-designer, senior-frontend |

### Immediate Replacement Queue (ordered by urgency)

1. **grill-me** (0.25) — 10 lines. Soul-bearing critic with no methodology.
2. **zoom-out** (0.15) — 7 lines. Not a real skill.
3. **handoff** (0.30) — 15 lines. Context continuity depends on this.
4. **technical-writer** (0.30) — 24 lines. Documentation quality gate.
5. **dependency-auditor** (0.30) — 25 lines. Supply chain risk.
6. **performance-engineer** (0.30) — 26 lines. Performance analysis.
7. **observability-engineer** (0.35) — 24 lines. Production visibility.
8. **refactor-specialist** (0.40) — 25 lines. Code health.

### Candidate Search Active (user dissatisfaction)

9. **ui-design-system** (0.55) — User explicitly unhappy. Need design philosophy depth.
