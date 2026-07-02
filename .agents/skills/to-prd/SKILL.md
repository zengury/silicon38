---
name: to-prd
description: Translate a feature idea or stakeholder request into an implementable product requirements document where every requirement is testable, essential-or-not, and scoped with explicit boundaries.
---

## Purpose

Mastery of this skill produces a specification an engineer can implement without a follow-up conversation.
You close the gap between what someone wants and what can be built.
That gap is usually about clarity, not capability.
A PRD is not a wish list.
Every requirement is either essential — the feature fails without it — or explicitly labeled non-essential.
Nothing exists in the document merely because it seemed reasonable at the time.

## When to use

- A feature idea needs to be translated into engineering requirements.
- A stakeholder request must be decomposed into concrete deliverables.
- The scope of a feature is being defined.
- The question is "what exactly should this do?"
- An engineer needs a spec precise enough to build from without asking questions.

## Method

1. Capture intent. Read the request and any context; identify the core value the feature must deliver.
2. If intent is too ambiguous to specify, get clarification before writing.
3. Do not encode guesses as requirements — a requirement that needs clarification is not finished.
4. Enumerate functional requirements, each written so it is testable.
5. Prefer "user can filter by date" over "intuitive interface"; the first is a requirement, the second is not.
6. Mark each requirement essential or non-essential, where essential means the feature fails without it.
7. Label everything else explicitly as future scope or nice-to-have.
8. State non-functional requirements with thresholds: "loads in under 2 seconds on a 4G connection," not "loads fast."
9. Draw the scope boundary by listing what the feature explicitly does NOT do.
10. Define success criteria: measurable signals that show the feature is working correctly.
11. Record remaining open questions; if any are blockers, escalate before finalizing.

## Quality bar

- Every requirement is testable — a specific, verifiable behavior, not a quality adjective.
- Non-functional requirements carry concrete thresholds.
- Out-of-scope items are listed and non-empty; nothing is infinitely scoped.
- Success criteria are defined and measurable.
- No requirement needs clarification to implement — clarity was resolved beforehand.
- Each requirement's essential/non-essential status is explicit.

## Output

A written PRD document, self-contained and ready to hand to issue decomposition or architecture.
It contains an overview.
It contains a requirements list where each entry has an id, a description, an essential flag, and a testable criterion.
It contains an out-of-scope list, a success-criteria list, and an open-questions list.

## Anti-patterns

- Writing aspirational or vague requirements that cannot be tested.
- Padding the document with requirements that merely "seem reasonable."
- Leaving out-of-scope empty, implying the feature does everything.
- Stating non-functional requirements without measurable thresholds.
- Encoding unresolved ambiguity as requirements instead of clarifying first.
