---
name: diagnose
description: Reproduce, isolate, and fix a reported failure through a deterministic feedback loop and ranked hypotheses, ending with a regression test that locks the fix.
---

## Purpose

Turn a bug report into a confirmed root cause and a durable fix. This skill is
disciplined debugging: build a repeatable way to trigger the failure, form
falsifiable hypotheses, test them with instrumentation, and prove the fix by
re-running the same loop. It distinguishes the underlying cause from its visible
symptom so the failure does not return in a new disguise.

## When to use

- A task contains a bug report, stack trace, or error description.
- Something is broken, throwing, hanging, or producing wrong output.
- A performance regression is reported and the cause is unknown.
- Tests pass but observed behavior contradicts the specification.
- You must confirm a fix rather than guess at one.

## Method

1. Build the feedback loop first. Find or write the smallest command that
   triggers the failure and runs without human intervention. If you cannot make
   the failure reproduce on demand, you cannot yet debug it — say so and stop.
2. Confirm you reproduced the reported bug, not a nearby failure that merely
   looks similar. Match the observed output to the report precisely.
3. Generate 3 to 5 ranked, falsifiable hypotheses about the cause. Rank by
   likelihood and by how cheaply each can be tested.
4. Instrument to test each hypothesis in rank order: add logging, assertions, or
   probes that will confirm or eliminate it. Let evidence, not intuition, decide.
5. Once a hypothesis is confirmed, trace from symptom to root cause. Ask why the
   faulty state was reachable, not just where it surfaced.
6. Apply the narrowest fix that addresses the root cause. Re-run the loop and
   confirm the original reproduction no longer triggers.
7. Write a regression test that fails without the fix and passes with it. If no
   correct test seam exists, document precisely why.
8. Remove every piece of debug instrumentation before finishing.

## Quality bar

- The feedback loop runs unattended and reliably triggers the failure.
- The reproduced bug is the reported bug, verified against its description.
- The winning hypothesis is stated explicitly, not summarized as "it was X".
- Root cause is separated from symptom in the writeup.
- A regression test locks the fix, or the absence of a seam is justified.
- All temporary debug output is stripped from the final code.

## Output

An inline-markdown analysis containing reproduction steps, the ranked
hypotheses with their outcomes, and the confirmed root cause; the fix applied as
a file change; and a regression test as a file. Evidence must show the loop
reproducing the failure, then re-running clean after the fix, with the test
passing.

## Anti-patterns

- Forming a hypothesis before you can reproduce the failure.
- Patching the symptom (silencing the error) instead of the cause.
- Declaring victory on one green run without re-confirming the original repro.
- Leaving print statements, temporary logging, or debug flags in the fix.
- Fixing a different, more interesting bug you noticed along the way.
