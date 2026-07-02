---
name: caveman
description: Strip a system down to first principles and explain it in plain language, exposing which complexity is genuinely necessary and which is self-inflicted.
---

## Purpose

Mastery of this skill produces a jargon-free explanation that reveals what a system actually does.
It also delivers a judgment on which of the system's complexity is justified.
You describe the thing as if to someone who has never seen software.
This is not because they are unintelligent — stripping abstraction exposes what is truly happening.
Every abstraction hides something; your job is to find what is hidden and ask whether hiding it earned its keep.
When a system cannot be described simply, its complexity is real.
When it can, the implementation's complexity is usually unnecessary.

## When to use

- A solution looks too complex for the problem it solves.
- Accumulated abstraction is obscuring what is actually happening.
- The request is "explain this simply."
- A design review needs a first-principles challenge before it is approved.
- A team suspects it has built more machinery than the problem demands.

## Method

1. Identify the subject precisely. If it is not specified enough to explain, stop and say so.
2. Describe what the system does in plain language.
3. Introduce no term without an immediate plain-language definition.
4. Name every abstraction you encounter and state its purpose in one sentence.
5. For each abstraction, answer the "so what": why does it exist, and what changes without it?
6. Derive the minimum viable version by asking "what is the least that would actually work here?"
7. Describe that minimum concretely; it must be genuinely simpler than what exists.
8. Sort the complexity into two piles: justified (the problem demands it) and unnecessary (the implementation invented it).
9. Guard accuracy throughout — do not oversimplify to the point of being wrong.
10. If unnecessary complexity is found, flag it for a refactor specialist or architect, with the minimum viable version as the target.

## Quality bar

- The explanation uses no jargon without an immediate plain-language definition.
- Every abstraction is named with its purpose stated in one sentence.
- The "so what" is answered for each element: why it matters, what changes without it.
- A minimum viable version is stated and is actually simpler than what exists.
- Accuracy is preserved — the explanation survives both a non-engineer's understanding and an engineer's scrutiny.

## Output

An inline-markdown artifact in three parts.
First, a plain-language explanation of the system.
Second, the minimum viable version that would still do the job.
Third, an assessment separating justified complexity from unnecessary complexity.
The explanation passes the "would a non-engineer understand this" test while remaining technically correct.

## Anti-patterns

- Hiding behind jargon or restating the code in slightly different technical words.
- Declaring complexity "necessary" without testing whether a simpler version would work.
- Oversimplifying until the explanation is no longer true.
- Describing abstractions without answering why they exist.
- Proposing a "minimal" version that is not actually simpler than the original.
