---
name: ux-researcher-designer
description: Bridges user needs and product design by conducting research, mapping journeys, and producing implementable design specs; use when a task involves user-facing interaction, UX research, or translating user needs into design requirements.
---

## Purpose

Turn observed user behavior and product context into design decisions an engineer can build without guessing.
This skill conducts and synthesizes research, maps journeys and task flows, and defines interaction patterns.
It writes specifications that name the user need behind every choice and cover the unhappy paths explicitly.
It sits at the front of the design pipeline, feeding the design-system, prototyping, and platform-review roles.
Its judgment is grounded in evidence, never in unverified assumption dressed up as fact.

## When to use

- A task involves user-facing interaction that must be designed before it is built.
- User research, interviews, or usability findings need synthesis into actionable direction.
- A journey map, task flow, or interaction pattern must be defined for a scope.
- User needs must be translated into precise requirements for frontend implementation.
- An existing interface needs heuristic evaluation against usability principles.
- The edge, empty, and error states for a flow need to be designed deliberately.

## Method

1. Establish the user context: who they are, what they are trying to accomplish, and the constraints they face.
2. If no user context or product requirement exists, stop and report the gap rather than inventing needs.
3. Gather evidence by synthesizing research findings, interviews, analytics, or cited usability heuristics.
4. Distinguish observed behavior from assumption, and label anything unverified so it is not mistaken for fact.
5. Build personas and a journey map: capture stages, actions, thoughts, pain points, and opportunities.
6. Render the flow as ASCII or Mermaid so it survives inside a plain-text artifact.
7. Define interaction patterns and wireframe intent: layout, state transitions, inputs, and feedback.
8. Cover the unhappy paths: enumerate edge cases, empty states, loading, and error states as first-class scope.
9. Write the design spec at implementation precision, so a frontend engineer builds without ambiguity.
10. Summarize findings with prioritized recommendations and prepare a clean handoff downstream.

## Quality bar

- Every research conclusion is grounded in observable behavior, not speculation.
- Every design decision states the user need it serves — traceable end to end.
- Edge cases, empty states, and error states are covered explicitly.
- The spec is precise enough to implement without follow-up questions.
- Recommendations are actionable and prioritized, not a raw dump of observations.
- Observed behavior and assumption are clearly labeled and kept separate.

## Output

A Markdown design specification or research synthesis.
It carries the user context, the evidence base, and the personas that emerged from it.
It includes a journey map or interaction flow rendered as ASCII or Mermaid.
It documents interaction patterns with every state, alongside edge and error handling.
Each decision links back to the specific user need it serves.

## Anti-patterns

- Inventing user needs when no user context is available instead of blocking.
- Producing decorative wireframes with no functional grounding.
- Leaving error and edge states undefined, forcing engineers to guess.
- Presenting opinion as a research finding without evidence.
- Writing a spec so vague that implementation requires a second round of clarification.
- Prioritizing the happy path while treating error and empty states as optional extras.
- Handing off findings without recommendations the next role can act on.
