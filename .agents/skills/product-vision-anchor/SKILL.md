---
name: product-vision-anchor
description: Synthesize analyzed requirements and a scope verdict into a single falsifiable product vision statement that every downstream node can test its output against.
---

## Purpose

Mastery of this skill produces a durable strategic constraint, not a marketing tagline.
You take the product requirements and the scope verdict and distill them into one precise sentence.
That sentence must be precise enough that any downstream node can test its output against it.
The test returns a yes-or-no answer on whether the output serves the vision.
The statement becomes a hard constraint on architecture, UX, and creative direction.
It anchors the whole team to a shared understanding of what the product is for.

## When to use

- Requirements have been analyzed and scope has been challenged.
- The team is about to begin execution and needs a shared vision constraint.
- Product direction must be established before architecture and design begin.
- Downstream nodes need a single test to check their work against.

## Method

1. Gather the inputs: analyzed requirements from to-prd and the scope verdict from the scope prosecutor.
2. If the scope verdict is not yet available, the work is blocked.
3. Apply the Jobs-to-be-Done lens, starting with the functional job — the task the user literally accomplishes.
4. Name the emotional job: how the user wants to feel while doing it.
5. Name the social job: how the user wants to be perceived by others.
6. Layer in positioning: against which competitive alternatives does this product win, and on what axis?
7. Consider differentiated value, target segment, market category, and relevant trends.
8. Write the vision statement in the form "[Target user] who [specific situation] uses this product to [functional job] so they feel [emotional job], unlike [alternative] which [fails to do X]."
9. Name a specific target user and situation — never "users" or "people."
10. Name the alternative being beaten so differentiation is explicit.
11. Define out-of-scope-forever: what this product will explicitly never do.
12. Write the vision test: the yes/no questions a node asks to check whether its output serves the user, reinforces the emotional promise, and avoids the forbidden scope.
13. Ban abstract filler — "seamless," "intuitive," "powerful" are not allowed.

## Quality bar

- The vision statement is falsifiable: a node's output can be tested against it.
- It names a specific target user and situation, not a generic audience.
- It names the alternative being beaten, making differentiation explicit.
- It is stable — it should not need to change as implementation proceeds.
- It contains no abstract filler adjectives.
- Out-of-scope-forever is defined.

## Output

An inline-markdown vision statement package that travels as a hard constraint downstream.
It contains the one-sentence vision statement in JTBD-plus-positioning form.
It names the target user, the primary functional job, and the emotional promise.
It names the alternative being beaten and why, plus out-of-scope-forever.
It ends with a vision test that downstream nodes apply to their own output.

## Anti-patterns

- Writing a marketing tagline instead of a testable strategic constraint.
- Naming a generic audience ("users," "people") rather than a specific user and situation.
- Omitting the alternative being beaten, leaving differentiation implicit.
- Leaning on filler adjectives like "seamless" or "powerful."
- Producing a vision so vague that no node can get a yes/no answer from it.
