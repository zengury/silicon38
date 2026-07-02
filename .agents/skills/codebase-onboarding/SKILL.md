---
name: codebase-onboarding
description: Map an unfamiliar area of a codebase into a verified module map, call graph, and data-flow summary using the codebase's own vocabulary, sized to the task at hand.
---

## Purpose

Mastery of this skill produces cartography, not opinion.
You map the territory before any agent navigates it.
The output is a compact, accurate picture of how the area in question connects to the rest of the system.
You use the codebase's real module names and domain terms rather than imposing external naming.
The map orients downstream agents — architects, engineers, reviewers — so they plan changes with an accurate model.
What to do with the map is decided by whoever receives it; your job is the map itself.

## When to use

- An unfamiliar area of the codebase is involved in the task.
- A change touches multiple modules and their relationships are not obvious.
- An impact assessment of a proposed change is needed.
- The question is "how does X fit into the bigger picture?"
- A downstream agent needs orientation before safely making edits.

## Method

1. Establish the task scope. Identify the specific area to map; resist mapping the whole system.
2. Keep the map small enough to be useful — only what the task actually requires.
3. Locate the relevant modules by reading source, following imports, and tracing entry points.
4. Confirm every module you name actually exists in the codebase.
5. For each module, state its responsibility in exactly one sentence.
6. Use the codebase's own terminology, not generic descriptions.
7. Build the call graph: record who calls whom, directionally and completely for the scope.
8. Verify each edge by reading actual imports and calls — never infer a relationship you have not seen.
9. Trace the data flow: what data enters, how it is transformed, and where it exits.
10. Label external dependencies explicitly — third-party APIs, databases, other services.
11. Trim the map to the task's needs, then hand it to the receiving agents.

## Quality bar

- The map uses the codebase's actual module names and domain terms.
- Every module listed has a one-sentence responsibility.
- Call relationships are directional and complete for the relevant scope.
- External dependencies are explicitly labeled as external.
- Every relationship was verified by reading real imports or calls, not inferred.
- The map is scoped to the task — no irrelevant breadth.

## Output

An inline-markdown map in three parts.
A module map lists each module with its one-sentence responsibility.
A call graph records directional relationships within scope.
A data-flow summary describes inputs, transformations, and outputs.
External dependencies are flagged distinctly, and every element traces to something read in the codebase.

## Anti-patterns

- Imposing external or generic naming instead of the codebase's own vocabulary.
- Inferring call relationships from names rather than verifying them in source.
- Mapping the whole system when only one area is in scope.
- Listing a module without stating its responsibility.
- Blurring the line between internal modules and external services.
