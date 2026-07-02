---
name: playwright-skill
description: Prove a deliverable actually runs by launching it, exercising the happy path plus a key edge case, and capturing reproducible evidence with a pass/fail verdict — use to verify any artifact that claims to be runnable before it reaches its consumer.
---

## Purpose

Answer one binary question: does it actually work?
Organizations produce artifacts that claim to be runnable — web apps, scripts, services, APIs — and this skill verifies that claim before the artifact reaches its consumer.
It does not review code quality or architecture; it proves that a real user can use the thing.
When the deliverable fails, it does not fix it — it reports what broke, with evidence.
The method is tool-agnostic: launch the deliverable however it actually runs, drive it, and observe real results rather than trusting the claim.

## When to use

- An implementation node has completed and claims a runnable or functional deliverable.
- A deliverable is described as "runnable," "working," or "functional" and that claim is unverified.
- The task produced something a user is meant to use — a feature, a bug fix, or a design artifact.
- A deliverable is about to reach its consumer and no one has exercised it end to end yet.

## Method

1. Identify the deliverable and how it is meant to be started: dev server, CLI entry point, API endpoint, or built binary. If it cannot be started at all (missing dependencies, broken build, required credentials or external services unavailable), report BLOCKED with the reason.
2. Launch it in a clean, reproducible way and record the exact commands used so anyone can repeat them.
3. Exercise the happy path — the primary thing the deliverable is supposed to do — and observe the real result, not just that the process started.
4. Exercise at least one key edge case or failure-adjacent input (empty input, invalid argument, boundary value, an error route) to confirm behavior under stress, not only under ideal conditions.
5. Match observation to expectation for each step: for web, confirm the page renders and check the console for errors; for CLI, verify exit codes and output; for APIs, confirm responses match the stated contract.
6. Capture observable evidence for every step: logs, screenshots of failure states, exit codes, response bodies. Evidence for a pass is as valuable as evidence for a failure.
7. Time-box each step: if a verification step exceeds roughly 30 seconds, record a timeout and move on rather than hanging the whole run.
8. Distinguish "works correctly" from "works but has visual or contract defects" — both are failures, at different severities.
9. Render the overall verdict — PASS, FAIL_WITH_ISSUES, or BLOCKED — justified by the individual step results, and include reproduction steps for every failure.

## Quality bar

- Every verification is reproducible: the report's steps yield the same result for anyone.
- Failure reports include what was expected, what happened, the exact error message, and a screenshot or log excerpt.
- Both a happy path and at least one edge or error case were exercised.
- The skill proves existence of behavior, not absence of bugs; it does not fix the deliverable.
- Steps are time-bounded; a stuck step becomes a reported timeout, not a hang.
- Visual or contract defects are reported as failures, distinct from a hard break.
- The report covers what WAS verified, not just what failed — a pass is evidence too.
- The overall verdict is justified by the individual step outcomes.

## Output

- A verification report containing:
  - The deliverable ID and the exact commands used to launch and drive it.
  - The test steps executed, with pass/fail recorded per step.
  - Evidence per step: logs, screenshots, exit codes, or response bodies.
  - Reproduction instructions for every failure.
  - An overall verdict: PASS, FAIL_WITH_ISSUES, or BLOCKED, justified by the individual step results.

## Anti-patterns

- Declaring a pass because the process started, without exercising what it actually does.
- Testing only the happy path and never a single edge or error case.
- Reporting a failure with no error text, screenshot, or reproduction steps.
- Slipping into fixing the deliverable instead of reporting the defect and its evidence.
- Letting one step hang indefinitely instead of timing it out and continuing.
- Drifting into a code-quality or architecture review, which is a different role's job.
- Recording steps so vaguely that no one else could reproduce the same result.
