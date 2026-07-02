---
name: content-research-writer
description: Produce documentation for a reader without your context — READMEs, API docs, changelogs, and guides — with runnable examples and user-visible framing.
---

## Purpose

Write documentation that transfers information to a reader who lacks your
context. That reader is uninformed, not unintelligent; the goal is to inform
them, not to display mastery of the subject. Good documentation answers, in
order: what is this, when do I use it, how do I use it, and what can go wrong.
Every example must run exactly as written.

## When to use

- A new API or interface is being shipped.
- Release notes or changelog entries are required.
- Developer onboarding materials need updating.
- A feature is complete but undocumented.
- Documentation is explicitly requested.

## Method

1. Identify the reader and their starting context. Write for someone who has not
   seen the implementation and does not share your assumptions.
2. Structure the document to answer the four questions in order: what it is, when
   to use it, how to use it, what can go wrong. Resist turning it into a disguised
   implementation walkthrough.
3. State prerequisites before they are needed, not discovered mid-example. The
   reader should never hit a step that assumes setup you never mentioned.
4. Cover the happy path completely before addressing edge cases. A reader needs
   the main flow working before they care about corner cases.
5. Write every code example so it runs as-is, then actually run it and confirm it
   produces the stated output.
6. Define jargon at first use. If a term needs the reader to already know it, the
   documentation is only true under unstated conditions — rewrite it.
7. For changelog entries, describe user-visible impact from the user's
   perspective: "Users can now..." rather than "Refactored...".
8. Verify the document covers the complete specified scope or API surface.

## Quality bar

- Every code example is runnable and correct as written, and has been run.
- Prerequisites appear before they are needed.
- The happy path is covered fully before edge cases.
- No statement is true only under unstated conditions.
- Changelog entries describe user-visible impact, not internal churn.
- No jargon is used without a definition at first use.

## Output

A documentation artifact in the format the task calls for — README, API
reference, changelog, or guide — written as a file. Evidence requires that every
code example has been executed and produces its stated output, and that the
document covers the complete specified scope.

## Anti-patterns

- Writing an implementation walkthrough disguised as user documentation.
- Shipping examples that were never actually run.
- Introducing setup steps mid-example that should have been prerequisites.
- Changelog entries framed as internal refactors instead of user impact.
- Using undefined jargon that assumes the reader already knows the domain.
