# Skill Scout — Replacement Candidate Report

**Date:** 2026-05-26
**Sources searched:** mattpocock/skills, alirezarezvani/claude-skills, .pi/agent/skills, book2skill (Ousterhout, Grove, Myers, Helmer), everything-claude-code skills, .claude/skills
**Method:** Match role requirements against candidate skill methodology depth, output specificity, and philosophy alignment

---

## ✅ Found: Ready to Replace

### 1. refactor-specialist → `philosophy-software-design`
**Source:** `.pi/agent/skills/philosophy-software-design`
**Book:** John Ousterhout, *A Philosophy of Software Design*
**Current score:** 0.40 → **Estimated new score:** 0.85

**Why it fits:**
- 14 sub-skills covering: shallow module detection, temporal decomposition refactoring, information leakage remediation, pass-through elimination, module combination/separation, layer elimination
- Three-phase process: Triage (classify the problem domain) → Apply Heuristics (Interface Cost / Depth / Information Leakage / Design-it-Twice tests) → Recommend with specificity (point to specific lines, not vague advice)
- Anti-pattern catalog with symptoms and concrete fixes
- Aligns perfectly with benchmark: "behavior-preserving refactor with specific patterns, not vague restructuring"

**Risk:** The skill is comprehensive but may be *too* comprehensive for a single node — 14 sub-skills + references. May need to select a subset as the primary interface.
**Action:** Replace `skill_ref` and run benchmark trial.

---

### 2. grill-me → `black-box-performance-assessment` + local adaptation
**Source:** `book2skill/High Output Management/black-box-performance-assessment`
**Book:** Andy Grove, *High Output Management*
**Current score:** 0.25 → **Estimated new score:** 0.70

**Why it fits:**
- Define expectations upfront (before review begins)
- Evaluate both output measures (tangible results) and internal measures (process quality, future capability building)
- Explicit trade-off analysis: "What is being traded? Why this weighting? Document the rationale."
- Weighting is situational, not formulaic
- Core principle: "Assessment must be against pre-defined standards, not arbitrary criteria" — this is exactly what adversarial design review needs

**Adaptation needed:** The skill evaluates *people*, not *designs*. Need to adapt:
- "Output measures" → design decisions that hold up under scrutiny
- "Internal measures" → design process quality, constraint compliance, soul alignment
- "Define expectations upfront" → the PRD/ADR defines the standard the design is measured against

**Action:** Create a `grill-me-v2` skill that wraps black-box-performance-assessment with design-specific adaptations. Run benchmark trial.

---

### 3. handoff → `delegation-and-monitoring` + local adaptation
**Source:** `book2skill/High Output Management/delegation-and-monitoring`
**Book:** Andy Grove, *High Output Management*
**Current score:** 0.30 → **Estimated new score:** 0.68

**Why it fits:**
- "Delegation without follow-through is abdication" — context handoff without verification is the same
- Shared operational values + common information base → effective delegation
- Quality assurance principles for monitoring: check at the lowest-value stage, use random sampling, monitor at frequency proportional to risk
- "Never wash your hands of a task" → the upstream node remains accountable

**Adaptation needed:** Grove's delegation is manager→subordinate. Adapt to node→node handoff:
- "Shared operational values" → shared context model (Canonical Model, ADR decisions)
- "Common information base" → context_block + context_compression_report
- "Monitor delegated tasks" → verify downstream node actually consumed the handoff context

**Action:** Create a `handoff-v2` skill incorporating delegation principles. Run benchmark trial.

---

### 4. zoom-out → `philosophy-software-design` (Phase 1 subset)
**Source:** `.pi/agent/skills/philosophy-software-design`
**Current score:** 0.15 → **Estimated new score:** 0.65

**Why it fits (partially):**
- Phase 1 "Triage — Identify the Core Concern" provides a classification framework for codebase exploration
- "Explore the codebase" methodology with domain glossary awareness
- Shallow module detection provides a lens for understanding what you're looking at

**Why it's partial:**
- The skill is optimized for *refactoring*, not for *understanding unknown code*
- Missing: dependency graph construction, data flow tracing, risk surface identification

**Action:** Use as base but acknowledge it's a partial fit. Recommend writing a dedicated `context-mapper` skill combining philosophy-software-design exploration methods with dependency analysis patterns.

---

## ⚠️ Partial: Needs Local Skill Creation

### 5. observability-engineer
**No match found.** Neither book2skill nor existing repos have an observability-focused skill.

**Recommendation:** Write a local skill based on Google SRE Workbook golden signals (latency, traffic, errors, saturation). Source material exists in the ecosystem (Google SRE book has been turned into skills by others — may exist in community but not on this machine). **Action: community search deferred.**

### 6. performance-engineer
**No match found.**

**Recommendation:** Write a local skill based on Brendan Gregg's performance methodology (workload characterization, USE method, drill-down analysis). **Action: community search deferred.**

### 7. technical-writer
**No match found.** The existing `.claude/skills/documentation-and-adrs` is 24 lines — same quality as current.

**Recommendation:** Write a local skill based on Google Technical Writing Courses (free, high-quality methodology: clarity, structure, audience awareness). **Action: local creation.**

### 8. dependency-auditor
**No match found.**

**Recommendation:** Write a local skill based on OWASP Dependency-Check methodology + npm audit / pip audit patterns. **Action: local creation.**

### 9. ui-design-system
**No match found.** User explicitly unhappy. This is the hardest to fill from existing sources because design taste is subjective.

**Recommendation:** This requires a dedicated search. The `everything-claude-code/skills/design-system` exists but needs evaluation. `everything-claude-code/skills/liquid-glass-design` might be relevant. The `frontend-design` and `accessibility` skills from everything-claude-code could supplement. **Action: read and evaluate these candidates.**

---

## Summary

| Role | Current Score | Candidate | Source | Est. New Score | Status |
|------|-------------|-----------|--------|---------------|--------|
| refactor-specialist | 0.40 | philosophy-software-design | .pi/agent/skills | 0.85 | ✅ Ready |
| grill-me | 0.25 | black-box-performance-assessment (adapted) | book2skill/HOM | 0.70 | ✅ Ready |
| handoff | 0.30 | delegation-and-monitoring (adapted) | book2skill/HOM | 0.68 | ✅ Ready |
| zoom-out | 0.15 | philosophy-software-design (partial) | .pi/agent/skills | 0.65 | ⚠️ Partial |
| observability-engineer | 0.35 | None found | — | — | 🔍 Search |
| performance-engineer | 0.30 | None found | — | — | 🔍 Search |
| technical-writer | 0.30 | None found | — | — | ✍️ Create |
| dependency-auditor | 0.30 | None found | — | — | ✍️ Create |
| ui-design-system | 0.55 | Candidates to evaluate | everything-claude-code | ? | 🔍 Evaluate |

**Next step:** Run benchmark trials on the 3 ready replacements. For the 5 without matches, either search broader community (npm/Claude Code skill registry) or authorize local skill creation.
