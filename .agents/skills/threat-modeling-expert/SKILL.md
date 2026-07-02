---
name: threat-modeling-expert
description: Produce a design-level threat model from an architecture document using STRIDE over trust boundaries, with scored threats, attack trees, and mitigations expressed as design constraints — use when a new system is being designed, not for implementation-time review.
---

## Purpose

Model the threat surface of a system before implementation begins.
The input is an architecture document; the output is a design-constraint document — not a vulnerability report and not a code review.
Working at the design level keeps findings addressable: the architect can still change data flows, split trust zones, add authentication boundaries, or re-route sensitive data.
Once code ships, that window closes, so the analysis earns its value by arriving early and staying grounded in the actual design.

## When to use

- A new system or service is being designed, not just a feature.
- An architect has produced an architecture document to analyze.
- The task involves authentication, payment flows, multi-tenant data isolation, external API exposure, or PII handling.
- An explicit security-design requirement is present in the task.
- A design review needs a structured threat pass before implementation is greenlit.

## Method

1. Establish scope from the architecture doc: name the systems, the trust boundaries, and the data flows to be analyzed. If the doc is absent or too abstract to identify boundaries, treat it as a blocker.
2. Enumerate every trust boundary, not just components. A component safe within its zone can be catastrophically exposed at the boundary — that is where attackers think.
3. Apply STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege) to each boundary and flow. Build a table of component/boundary versus threat category.
4. Ground every threat in a concrete element of the architecture: a named service, a stated data flow, or a boundary that was drawn or notably not drawn. If it cannot be grounded, it is speculation and does not belong.
5. Score each threat: likelihood (1–5) × impact (1–5) = priority (1–25), with brief justifying reasoning for the numbers.
6. For every threat scored HIGH (priority ≥ 15) or CRITICAL (priority = 25), build an attack tree with at least two levels of decomposition, naming concrete attack steps rather than abstract categories.
7. Write mitigations as design decisions that constrain what gets built — reference the STRIDE category each addresses. Anything that can only be fixed at implementation time is out of scope and belongs to the security-engineer.
8. Rank the mitigation requirements so the architect knows what must change first.
9. Render a verdict: CLEAN, THREATS_WITH_MITIGATIONS, or CRITICAL_REDESIGN_REQUIRED. A clean model is valid — if the architecture is well-bounded, say so and explain which boundaries were checked and why they hold.

## Quality bar

- STRIDE covers every trust boundary, not just components in isolation.
- Each threat carries a likelihood × impact = priority score with reasoning.
- Attack trees exist for every HIGH/CRITICAL threat, each with ≥2 levels of decomposition.
- Attack-tree steps name concrete attacker actions, not abstract categories.
- Every mitigation references the STRIDE category it addresses and is a design decision, not a code comment.
- No finding that can only be addressed at implementation time.
- Every finding references a named element from the architecture doc.
- Mitigation requirements are ranked so the architect knows what to change first.
- A clean verdict states which boundaries were checked.

## Output

- A threat-model document with these sections:
  - Scope: the systems, trust boundaries, and data flows analyzed.
  - STRIDE table: component/boundary × threat category, with likelihood, impact, and priority score.
  - Attack trees: one per HIGH/CRITICAL threat, each at least two levels deep with concrete steps.
  - Mitigation requirements: a ranked list where each entry states the STRIDE category, the threat, and the design constraint that addresses it.
  - Verdict: CLEAN, THREATS_WITH_MITIGATIONS, or CRITICAL_REDESIGN_REQUIRED.

## Anti-patterns

- Analyzing components in isolation and skipping the boundaries between them.
- Listing theoretical threats untraceable to any element of the architecture.
- Writing mitigations as implementation to-dos instead of design constraints.
- Omitting attack trees for high-priority threats, leaving them unexplored.
- Padding the model with low-value findings instead of declaring a well-bounded design clean.
- Assigning priority scores with no reasoning, making the ranking impossible to trust.
- Handing the architect a to-do list for engineers instead of constraints on the design itself.
