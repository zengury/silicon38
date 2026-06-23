## Plain-Language Explanation

This codebase has a problem: same code written in many places, modules do too many things, hard to change without breaking stuff. Hard to test. Slow to add features. Risk of bugs.

Goal: clean it up. Remove duplicate code. Make each module do one thing. Make it easy to test. Do it step by step, not all at once.

## Minimum Viable Version

1. Find duplicate code with a tool (like jscpd).
2. Pick one duplicate, extract to shared function.
3. Replace all copies with call to shared function.
4. Repeat.

That's it. No big redesign. No new architecture. Just remove duplication first.

## Complexity Assessment

**Justified complexity:**
- Using a duplication detection tool (saves time, catches what humans miss).
- Incremental refactoring (Strangler Fig) to avoid breaking everything at once.
- Keeping backward compatibility during transition.

**Unnecessary complexity:**
- Redefining module boundaries before removing duplication. Do duplication first, then see if modules still messy.
- Setting test coverage targets (70%) before knowing current state. Measure first, then set target.
- Writing detailed user stories for developers. The problem is clear: duplicate code, bad structure. Just fix it.
- Dependency graph documentation. Not needed for first pass.
- Linter/static analysis for structural issues. Add later if needed.

**Simpler approach:**
1. Run duplication tool, get report.
2. Fix duplicates one by one, each commit working.
3. After duplicates gone, assess module structure. If still bad, extract modules.
4. Add tests for new shared functions.

## Completion Report

what_was_done: Analyzed PRD for roboease refactoring. Identified minimum viable version (dedup only) and unnecessary complexity (premature module redesign, coverage targets, user stories, dependency docs).
key_decisions:
  - decision: Focus on duplication removal first, defer module restructuring.
    rationale: Duplication is the clearest problem; fixing it yields immediate benefit without risky redesign.
  - decision: Drop user stories and coverage targets from initial plan.
    rationale: Adds process overhead without clear value. Measure first, then set targets.
handoff_focus:
  - Run duplication detection tool on codebase.
  - Fix exact duplicates first.
  - After dedup, assess if module restructuring still needed.
open_questions:
  - What language(s) is the codebase? Affects tool choice.
  - Are there existing tests? If yes, what framework?
  - What is the current duplication percentage?
known_constraints:
  - No write access to codebase; analysis only.
  - Must respect existing ADRs.
confidence_differential: 0.9
dissent_if_alone: null
iteration_context: null