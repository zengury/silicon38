---
name: senior-backend
description: Implement backend features to specification and design contracts that are impossible to misuse, clearing a specification gate and a minimalism gate before writing code — use when code must be written or an API surface defined.
---

## Purpose

Mastery of this skill produces backend code that does exactly what the
specification says and API contracts that make wrong usage fail to compile. It
serves two closely joined jobs: implementing features against an architecture
decision, contract, and test suite; and designing the interfaces and service
boundaries those features expose. The output is readable by the next engineer
with no context from this conversation — names reveal intent, structure reveals
relationships — and it is done when the specified behavior exists and passes,
not when the code is theoretically elegant.

## When to use

- Code needs to be written or modified, or a feature implemented or changed.
- A task requires reading and modifying multiple files coherently.
- A new public API is being created or an existing one changed.
- A service boundary or a contract between components must be specified.

## Method

1. Specification gate. Before writing any code, confirm a formal spec exists:
   expected inputs, expected outputs, edge cases handled, edge cases explicitly
   out of scope, and the acceptance criterion that proves it works. If none
   exists, write one first and record it in key decisions. Proceed only when the
   spec could be handed to an engineer who never saw this conversation.
2. Minimalism gate. Walk six questions in order and stop at the first whose
   answer eliminates new code: Is it necessary by the spec or merely assumed?
   Does the standard library already do it? Can a native language feature
   replace a dependency? Does something in this codebase already do it? What is
   the simplest interface — fewest parameters, narrowest types, shortest honest
   name? Would the system still serve the real need if this code were deleted?
   Only write code that clears all six.
3. When designing an interface, name every element from the caller's
   perspective, express the contract in the project's native language (detect it
   from the workspace — Pydantic for FastAPI, TypeScript for Node, Go structs
   for Go), make nullable, optional, and required fields explicit, type error
   conditions rather than passing strings, scope inputs to what the function
   needs, and state a versioning strategy with no unjustified breaking changes.
4. If the interface target is an AI agent over MCP, apply the agent rules
   instead: verb-noun deterministic tools, stable read-only resource URIs,
   parameterized and tested prompts, one transport in v1, at most twenty tools
   per server, and JSON Schema with explicit required fields. If the consumer is
   ambiguous, ask before designing.
5. Implement to the spec and the contract. Do not invent requirements or
   over-engineer. Put error handling at real system boundaries — user input,
   external calls — not defensively throughout.
6. Run the tests and the linter. The work is done when the specified behavior
   exists, the suite is green, and there are no compile or lint errors.

## Quality bar

- Code does exactly what the specification says, no more.
- All tests provided by the test engineer pass; no lint or type errors.
- No dead code, commented-out blocks, or TODO stubs in the final output.
- Naming is precise: a function is named for what it actually does.
- Contracts are in the project's native language with every field's intent
  stated and error conditions typed rather than stringly-typed.
- Public APIs state a versioning strategy; breaking changes are justified.

## Output

For implementation: code files satisfying the specification, with a readable,
logically grouped diff. For interface design: an API surface definition in the
project's language plus a rationale document covering design decisions, a
breaking-change assessment, and a usage example demonstrating correct use.

## Anti-patterns

- Writing code before a spec exists, producing plausible but mis-specified
  behavior ("confident drift").
- Skipping the minimalism gate and reinventing what the stdlib or codebase has.
- Naming from the implementer's viewpoint instead of the caller's.
- Scattering defensive error handling everywhere instead of at real boundaries.
- Shipping breaking API changes without explicit justification or versioning.
