---
name: senior-architect
description: Design systems from constraints by naming the load-bearing decisions and recording them with rationale and rejected alternatives — use when a new system or subsystem, technology choice, or cross-module boundary needs design.
---

## Purpose

Mastery of this skill produces an architecture that engineers can implement
without ambiguity and future architects can understand without archaeology.
The core output is a set of load-bearing decisions — the choices that, once
made, determine ten others downstream — each stated explicitly, justified, and
kept reversible where possible. Good architecture is derived from the real
constraints of this codebase, this team, and this task, not from preference or
theoretical future needs.

## When to use

- A new system or significant subsystem is being designed.
- Technology choices need to be made and their consequences reasoned about.
- An existing architecture is under question or strain.
- A feature requires cross-module coordination or new service boundaries.
- The task involves data flow design or defining where components meet.

## Method

1. Extract the constraints. Enumerate the real limits — performance, team
   skills, existing systems, deadlines, data volumes — before proposing any
   structure. Design from these, not from preference.
2. Identify the load-bearing decisions. Find the few choices that constrain the
   most downstream work. These deserve the most rigor; everything else can
   follow cheaply once they are settled.
3. Decide each one explicitly, and for each record context, the decision, the
   rationale, the alternatives considered, why the rejected ones were rejected,
   and the consequences accepted.
4. Map the data flows. For each significant piece of data, state where it
   originates, how it transforms, and where it terminates. Ambiguous data flow
   is an unfinished design.
5. Define boundaries and contracts. Specify module boundaries, interfaces, and
   data models precisely enough that downstream engineers implement without
   guessing.
6. Enumerate failure modes. For each component, state what happens when it is
   unavailable or degraded. A design without failure modes is optimistic
   fiction.
7. Check incrementality. Confirm the design can be built in independently
   deployable steps, with no "build the whole thing first" dependency.
8. Resist speculative generality. Do not optimize for future requirements that
   were not stated. Keep decisions reversible so the future can decide itself.

## Quality bar

- Every structural decision has a stated rationale, not "best practice."
- Alternatives considered are documented, including the rejected ones and why.
- The design can be implemented incrementally, with no big-bang dependency.
- Data flows are explicit from origin through transform to termination.
- Failure modes are identified for each component.
- The design does not optimize for unstated theoretical future requirements.

## Output

An architecture decision record in inline Markdown covering context, decision,
rationale, alternatives rejected, and consequences. Where applicable, add
schema files: data models, interface contracts, or module boundary definitions
that downstream agents can implement against directly. The alternatives section
is never empty.

## Anti-patterns

- Justifying decisions with "best practice" instead of the concrete constraint.
- Designing in the abstract, detached from this codebase and this task.
- Optimizing for speculative future requirements that were never stated.
- Leaving data flow or failure behavior implicit for the implementer to invent.
- Producing a monolithic design that must be built whole before it delivers.
