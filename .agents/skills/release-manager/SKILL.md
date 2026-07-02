---
name: release-manager
description: Prepare a release as a contract with users — strict semantic versioning, an accurate user-facing changelog, defined SLOs, and a completed readiness checklist.
---

## Purpose

Treat a release as a commitment. Everything in it ships, everything shipped must
be documented, and everything documented must be accurate. The release artifact
is a contract with downstream consumers. This skill decides a correct version
number, writes a truthful changelog, verifies service-level objectives, and runs
the readiness checklist before any tag is created.

## When to use

- A release is being prepared or cut.
- A version bump is needed and the increment must be justified.
- A changelog needs to be written or reconciled against the diff.
- A deployment to production is in scope.

## Method

1. Decide the version by strict semantic versioning. A patch that breaks a public
   API is a major release; a major that adds only internal changes is a lie.
   Justify the increment from the actual changes, not from how big it feels.
2. Run the SLO definition gate before any production launch. For every
   user-facing dependency in the release, confirm availability, latency (p95
   budget), and error-rate objectives exist. If they do not, write them and
   record the decision; if the team has deliberately chosen not to, document that
   explicitly — silence is not acceptable.
3. Confirm SLOs have alerting thresholds and that the metrics they depend on are
   actually instrumented. SLOs without alerting are decorative.
4. Write the changelog from the user's perspective, covering every user-visible
   change. Reconcile it against the actual diff so no shipped change is missing
   and no listed change is fabricated.
5. Place breaking changes in a dedicated, prominent section — never buried in a
   flat list.
6. Complete the release checklist before tagging: tests green, security audit
   done, changelog written, docs updated.
7. Define the rollback procedure before the release ships, not after an incident
   begins.

## Quality bar

- Version number follows semantic versioning strictly and is justified.
- Changelog covers every user-visible change, written from the user's view.
- No change in the release is absent from the changelog, and none is fabricated.
- Breaking changes appear in a dedicated, prominent section.
- The checklist is completed — tests, security audit, changelog, docs — before tagging.
- SLOs are defined (or explicitly waived) and a rollback procedure exists.

## Output

A changelog entry for the release as a file, plus an inline-markdown release
readiness checklist showing pass or fail for each item. Evidence requires that
every checklist item is explicitly addressed rather than assumed, and that the
changelog has been reviewed against the actual diff.

## Anti-patterns

- Picking a version number by feel instead of by semantic-versioning rules.
- A changelog written from the implementer's view ("Refactored...") not the user's.
- Shipping changes that never make it into the changelog.
- Tagging a release before the checklist and security audit are complete.
- Treating SLOs as decoration with no alerting or instrumentation behind them.
