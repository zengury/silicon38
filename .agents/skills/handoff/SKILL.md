---
name: handoff
description: Capture in-progress work for a fresh context (session handoff) or synthesize settled terminal artifacts into one coherent deliverable (task decoder).
---

## Purpose

Preserve continuity across a boundary. This skill operates in two modes: a
session handoff that lets a new instance resume work without losing ground, and
a task decoder that assembles finished artifacts into a single usable
deliverable. In both, nothing implicit may stay implicit — a receiver who must
re-derive what was already known, or re-read prior conversation to understand, is
the sign of a failed handoff.

## When to use

- A session is ending and work must continue in a new context (Mode A).
- A task is being transferred between agents or sessions (Mode A).
- The state of complex in-progress work must be captured before a break (Mode A).
- The task graph has reached the settled state and needs final assembly (Mode B).

## Method

1. Choose the mode. Session handoff (Mode A) is for continuity of unfinished
   work; task decoder (Mode B) fires only when the runtime reports the task graph
   as settled.
2. Mode A — capture the full picture: task description, what is completed, what is
   in progress with what remains, and the decisions made.
3. Mode A — record each decision with its rationale and the alternatives
   rejected, not just the choice. Distinguish blockers (external obstacles) from
   choices (deliberate directions).
4. Mode A — state the next concrete action as something executable: "the next
   step is X", never "continue the work". List every artifact produced with its
   location.
5. Mode A — assume zero context carries over and make all implicit knowledge
   explicit before finishing.
6. Mode B — verify the task graph state is settled; if it is not, do not fire.
   Collect all approved artifacts from the registry.
7. Mode B — check for conflicts between artifacts and resolve or surface them.
   Assemble a coherent whole, not a concatenation: primary deliverable first,
   supporting material after.
8. Mode B — surface every open question from handoff records, write the outcome,
   and update the weight-learning indices. Mark the outcome partial if anything
   required is missing — never success.

## Quality bar

- Mode A: decisions include rationale and rejected alternatives.
- Mode A: partial outputs are labeled partial with what remains.
- Mode A: the next action is specific and executable, not "continue".
- Mode A: nothing requires reading prior conversation to understand.
- Mode B: no draft or under-review artifact enters the deliverable.
- Mode B: conflicts are documented and resolved; open questions are surfaced.

## Output

Mode A produces a handoff document capturing task, completed work, in-progress
items with what remains, decisions with rationale and rejected alternatives,
blockers, open questions, a specific next action, and artifact locations. Mode B
produces the assembled final deliverable plus an updated manifest recording the
outcome status.

## Anti-patterns

- Listing decisions as bare choices with no rationale or rejected alternatives.
- A next action of "continue the work" that requires prior context to act on.
- Assuming the receiver can read the previous conversation to fill gaps.
- Concatenating artifacts instead of synthesizing a coherent whole.
- Marking an outcome success while a required artifact is still missing.
