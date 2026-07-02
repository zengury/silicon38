---
name: prototype
description: Build the minimum throwaway artifact that answers one specific feasibility question, then report the finding — use when the question is "would this work?" not "build this."
---

## Purpose

Mastery of this skill produces a fast, disposable artifact that reduces
uncertainty about a single unknown. The prototype exists to answer a question,
not to impress or to ship. A good prototype converts a vague "maybe" into a
grounded "proceed," "pivot," or "investigate further," and it does so with the
least code that can honestly settle the question.

## When to use

- Solution feasibility is unknown and needs a concrete test.
- A new technology, library, or approach must be validated before commitment.
- The user experience of an idea needs to be felt before it is committed to.
- The real question is "would this work?" rather than "build this."
- A decision downstream is blocked on evidence that only a spike can provide.

## Method

1. State the one question. Write it as a single sentence at the top of the
   work: what specific uncertainty will this prototype resolve? If you cannot
   name it precisely, stop — the task is not yet ready for a prototype.
2. Identify the shortest path to evidence. Ask what is the minimum that could
   possibly answer the question. Everything beyond that path is waste that
   makes the question harder to answer.
3. Build only the demo path. Hardcode inputs, stub external systems, skip error
   handling beyond what the demonstration requires. Speed of learning beats
   completeness.
4. Label every shortcut inline. Each hack carries a comment in the form "this
   is hardcoded because we are testing X, not Y," so no reader mistakes the
   spike for production code.
5. Run it end-to-end on the demo path. A prototype that does not reliably
   execute the one path it exists to show has failed at its only job.
6. Read the result as a direct answer. Translate what you observed into a
   finding that speaks to the stated question, not to tangential impressions.
7. Write the "what this does NOT tell us" section. Name every dimension the
   prototype deliberately left untested so no one over-reads the result.
8. Recommend a next step: proceed, pivot, or investigate further, with the
   evidence that supports it.

## Quality bar

- The prototype answers exactly one specific question, stated upfront.
- Every shortcut is labeled with what it trades away and why it is acceptable.
- The demo path runs reliably end-to-end; the finding is reproducible.
- Output includes an explicit "what this prototype does NOT tell us" section.
- The finding is a direct answer to the stated question, not a status update.
- The prototype is never merged to main as production code without an explicit,
  separately scoped upgrade.

## Output

A runnable code artifact with shortcuts clearly labeled inline, plus an inline
analysis block containing: the question answered, the finding the prototype
revealed, an explicit list of what the prototype does not tell us, and a
recommended next step of proceed, pivot, or investigate further.

## Anti-patterns

- Polishing the prototype into production quality, adding features and error
  handling that the question never required.
- Leaving shortcuts unlabeled so a reader mistakes the spike for real code.
- Reporting an impression of the technology instead of a direct answer to the
  stated question.
- Omitting the "does not tell us" boundary, letting others over-generalize a
  narrow result.
- Starting to build before the question is specific enough to answer.
