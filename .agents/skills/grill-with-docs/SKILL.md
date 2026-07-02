---
name: grill-with-docs
description: Read external documentation with compiler-like precision to surface constraints, contradictions with actual behavior, and version differences — every finding cited to a specific section.
---

## Purpose

Mastery of this skill produces citation-backed findings that reconcile real behavior with official documentation.
You read docs the way a compiler reads code: precisely, completely, without assumption.
You find the constraint buried in a footnote.
You find the behavior that is correct per spec but surprising in practice.
You find the version difference that explains an inconsistency.
You do not use documentation to confirm what is already believed — you use it to discover what is not yet known.

## When to use

- An external library or framework is central to the task.
- Existing behavior appears to conflict with the documentation.
- API usage needs to be verified against the official specification.
- The task involves a technology whose edge cases materially matter.
- An inconsistency might be explained by a version or configuration difference.

## Method

1. Fix the documentation scope: the exact library, framework, and version in question.
2. Confirm the documentation version matches the runtime version in use.
3. Read the relevant sections completely, including footnotes, notes, and caveats.
4. Assume nothing that is not written.
5. For each finding, quote the specific section first, then comment.
6. Cite the section precisely — never "according to the docs" without a locator.
7. Compare documented behavior against actual code behavior.
8. Where they diverge, state both sides exactly: what the doc says versus what the code does, with a reference to each.
9. Flag version differences whenever doc and runtime versions disagree, noting which behavior applies.
10. Label undocumented behavior explicitly — it is a finding to verify, not a fact to rely on.
11. Hand findings to the receiving engineer, or to a diagnostician if documented behavior explains a bug.

## Quality bar

- Every finding cites a specific section of documentation, not a vague gesture at it.
- Contradictions state what the doc says versus what the code does, with references to both.
- Version differences are flagged whenever doc and runtime versions diverge.
- Undocumented behavior is labeled as undocumented, never asserted as fact.
- No interpretation runs beyond what is written: quote first, then comment.

## Output

An inline-markdown artifact in three sections.
Findings: each a claim plus its documentation reference plus its implication.
Contradictions: each pairing the code behavior, the documented behavior, and references to both the code location and the doc section.
Version notes: differences between documented and runtime versions.
Every claim is traceable to a citation.

## Anti-patterns

- Citing "the docs" without a specific section locator.
- Reading documentation to confirm a prior belief rather than to discover the unknown.
- Presenting undocumented behavior as if it were specified.
- Ignoring the gap between the documentation version and the runtime version.
- Interpreting or paraphrasing beyond what the text actually states.
