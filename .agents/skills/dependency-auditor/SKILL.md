---
name: dependency-auditor
description: Evaluate each dependency as a trust decision across necessity, maintenance, and execution surface, including its transitive graph, and render a verdict.
---

## Purpose

Treat every dependency as a trust decision, not a convenience. Adding a package
pulls its entire transitive graph inside your trust boundary, along with whatever
it executes at install, build, and run time. This skill audits the direct
dependency and what it drags in, judging whether the value is worth the surface,
and returns a clear recommendation per package.

## When to use

- New dependencies are being added to the project.
- Existing dependencies are being updated or bumped.
- A release is being prepared and the supply chain is in scope.
- A security audit covers third-party packages.
- Lock file changes are significant or unexplained.

## Method

1. For each dependency under review, evaluate necessity: could this be
   implemented directly in fewer lines than the integration and maintenance cost?
   "It's useful" is not a justification.
2. Evaluate maintenance: check the last publish date, release cadence, open issue
   and PR counts, and any history of security incidents. Flag deprecated or
   abandoned packages regardless of whether the current version has a known CVE.
3. Evaluate surface: determine what the package actually executes at install
   time, build time, and runtime. Install-time scripts require explicit
   justification.
4. Inspect the transitive graph. Note the transitive dependency count for any
   significant addition — the direct package is only the entry point.
5. Verify CVE status against a specific source (npm audit, OSV, GitHub advisories,
   or equivalent). "No known vulnerabilities" must be a verified check with a
   named source, not an assumption.
6. Confirm the lock file is committed and consistent with the package manifest.
7. Render a per-dependency recommendation: APPROVE, APPROVE_WITH_NOTE, or REJECT,
   with the reasoning that produced it.

## Quality bar

- Every new dependency carries a stated justification beyond "it's useful".
- Transitive dependency count is noted for significant additions.
- CVE absence is verified against a named source, not merely asserted.
- Lock file is committed and consistent with the manifest.
- Install-time code execution is flagged and justified, or rejected.
- Deprecated packages are flagged even when the current version is clean.

## Output

An inline-markdown audit that, for each dependency, gives a necessity verdict,
maintenance status, CVE status with its source, transitive count, and a
recommendation of APPROVE, APPROVE_WITH_NOTE, or REJECT. Evidence must reference
the specific CVE check used and the last publish date plus open-issue count for
maintenance claims.

## Anti-patterns

- Auditing the direct package while ignoring its transitive graph.
- Reporting "no known vulnerabilities" without running an actual check.
- Accepting a heavy dependency for a task solvable in a few local lines.
- Overlooking install-time or build-time scripts as part of the surface.
- Leaving the lock file uncommitted or inconsistent with the manifest.
