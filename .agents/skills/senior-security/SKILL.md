---
name: senior-security
description: Audit code for real, exploitable vulnerabilities with an attacker's mindset and render a clear verdict with ranked, located, remediable findings — use when auth, user input, external calls, data persistence, dependencies, or a release are in scope.
---

## Purpose

Audit for exploitability, not for compliance checkboxes.
Adopt the attacker's mindset: for every input path ask what happens if this is malicious; for every data store ask what happens if an unauthorized party reads it; for every dependency ask what it actually executes.
Trust nothing that crosses the process boundary. OWASP Top 10 is the floor, not the ceiling.
The value of the report is its precision: a located, reachable finding an engineer can fix, or an honest clean verdict that names what was checked.

## When to use

- Authentication or authorization logic is involved.
- User input is processed anywhere in the flow.
- External API calls are made.
- Data is persisted or transmitted.
- Dependencies are added or updated.
- Secrets, tokens, or credentials are handled.
- A release is being prepared.

## Method

1. Define scope precisely: which files, entry points, data flows, and dependencies are in bounds. A clean verdict later must state exactly what was checked.
2. Map the trust boundaries and the paths where untrusted data enters the process.
3. Walk each input path adversarially: injection (SQL, command, template), deserialization, path traversal, SSRF, and missing validation. Ask what a hostile input does at each hop.
4. Examine authentication and authorization: broken access control, missing checks, privilege escalation, insecure session handling, and IDOR on every object reference.
5. Inspect data at rest and in transit: encryption, secret handling, and exposure of sensitive fields in logs or responses.
6. Audit dependencies including transitive ones: known CVEs, unexpected execution, and supply-chain risk — not just the direct manifest.
7. For each real issue, record the vulnerability class, the specific location (file and line), the concrete exploitability condition, and the remediation.
8. Rank findings by exploitability, not theoretical severity. Suppress false positives — a clean report is a valid result, and padding it to look thorough is a failure.
9. Render a verdict: CLEAN, FINDINGS_REQUIRE_FIX, or CRITICAL_BLOCKER. If CLEAN, explicitly state what was checked.
10. Optionally provide remediation patches for confirmed vulnerabilities. If runtime confirmation or dependency source is unavailable, flag that as a constraint rather than asserting exploitability.

## Quality bar

- Every finding states vulnerability class, specific location, exploitability condition, and remediation.
- Findings are ranked by exploitability, not by theoretical severity.
- No false positives padded in to appear thorough; a clean report is acceptable.
- Dependency audit covers transitive dependencies, not just direct ones.
- No "you should consider" findings — either it is a vulnerability or it is not.
- A clean verdict enumerates exactly what was checked.
- Each finding names the trust boundary the malicious input crosses.
- Remediations are concrete and specific to the located issue, not generic advice.

## Output

- An inline markdown analysis listing findings as {vulnerability, location, exploitability, remediation} and an explicit verdict: CLEAN, FINDINGS_REQUIRE_FIX, or CRITICAL_BLOCKER.
- Findings ordered by exploitability so the reader addresses the reachable risks first.
- Optionally, remediation patch files for identified vulnerabilities.

## Anti-patterns

- Auditing for compliance checkboxes instead of actual exploitability.
- Reporting theoretical findings with no concrete exploit path to inflate the count.
- Ranking by CVSS abstraction while ignoring whether the path is reachable here.
- Auditing only direct dependencies and missing the transitive supply chain.
- Vague "consider hardening" advice that neither confirms nor denies a vulnerability.
- Claiming exploitability without a concrete condition, or asserting it when runtime confirmation was impossible.
- A finding with no file/line location, forcing the reader to hunt for what you meant.
