---
name: compliance-auditor
description: Audit a system against the privacy and regulatory frameworks that actually apply (GDPR, CCPA, HIPAA, SOC 2), producing scoped, article-level findings and a data inventory — use when PII, health, or financial data is handled or a launch is being prepared.
---

## Purpose

Answer a different question than the security auditor: not "can this be exploited?" but "does this system satisfy its legal obligations to the people whose data it processes?"
These audits are orthogonal — a system can be fully hardened yet non-compliant, or fully compliant yet exploitable.
This skill owns the legal-regulatory half: map the system to the frameworks its data and jurisdictions trigger, and evaluate the concrete obligations each one creates.
Evaluate the specific articles and sections that this system actually triggers, never the regulation in the abstract.

## When to use

- The product handles PII, health data, or financial data.
- A security audit has completed and the regulatory half is still open.
- A release is being prepared for production launch.
- The task explicitly mentions GDPR, HIPAA, CCPA, or SOC 2.
- The system operates across jurisdictions whose obligations must be reconciled.

## Method

1. Determine scope first: declare which regulations apply and why, based on the data types handled and the jurisdictions of operation. List frameworks that do NOT apply with a one-line exclusion reason. If jurisdiction or covered-entity status is unknown, treat scoping as blocked.
2. Build the PII/PHI inventory: for each data entry record data type, storage location, retention period, and deletion mechanism (or "NONE — GAP").
3. For GDPR, check the triggered articles: Article 6 lawful basis per data category; Articles 13/14 privacy-notice disclosures; Article 17 exercisable deletion mechanism; Article 30 record of processing activities; Article 33 sub-72-hour breach notification path; Article 35 whether a DPIA is required.
4. For CCPA, verify a "Do Not Sell/Share" mechanism where applicable, the data inventory coverage under § 1798.100(a), opt-out honored within 15 business days, and privacy-policy disclosures of categories, purposes, and consumer rights.
5. For HIPAA (only when the operator is a covered entity or business associate), evaluate the Technical Safeguards under 45 CFR § 164.312 (access control, audit controls, transmission security), the PHI inventory, BAAs for all PHI-processing vendors, and the minimum-necessary standard.
6. For SOC 2, map against the applicable Trust Service Criteria and flag missing or untested controls as readiness risk, not legal violation.
7. Write each finding as concrete and located: cite the specific article or section, the requirement, a status of PASS / GAP / LAUNCH_BLOCKER, and the evidence. PASS findings must cite the mechanism that satisfies the requirement; GAP findings must state what is absent and where.
8. State the breach-notification procedure: whether it exists, its timeline, and the responsible party.
9. Derive the overall verdict from the findings — COMPLIANT, GAPS_REQUIRE_FIX, or LAUNCH_BLOCKER — never assert it independently.

## Quality bar

- Each regulation in scope is explicitly justified; out-of-scope ones carry a one-line exclusion reason.
- Every gap is a concrete, located finding, not "consider adding X."
- PASS findings cite the exact mechanism satisfying the requirement.
- Every finding carries a status of PASS, GAP, or LAUNCH_BLOCKER.
- The PII/PHI inventory states data type, storage, retention, and deletion mechanism per entry.
- Breach-notification procedure is stated with timeline and responsible party.
- Every finding references a specific article or section.
- No "you should consider" language anywhere in the report.
- The verdict is derived from the findings, not asserted separately.

## Output

- A compliance report containing:
  - Frameworks in scope, each with a one-line applicability rationale.
  - Frameworks out of scope, each with a one-line exclusion rationale.
  - The PII/PHI inventory: data type, storage location, retention period, and deletion mechanism per entry.
  - Per-framework findings tagged PASS, GAP, or LAUNCH_BLOCKER, each citing an article or section with evidence.
  - The breach-notification procedure: whether it exists, its timeline, and the responsible party.
  - The overall verdict: COMPLIANT, GAPS_REQUIRE_FIX, or LAUNCH_BLOCKER.

## Anti-patterns

- Auditing frameworks in the abstract instead of the specific articles the system triggers.
- "You should consider" language instead of a definite met/not-met obligation.
- Reporting only gaps and staying silent on passes, leaving no evidence of coverage.
- Conflating exploitability with compliance — that is the security auditor's job.
- Asserting a verdict that the individual findings do not support.
- Auditing a framework that does not apply, or failing to say why an excluded one is out of scope.
- An inventory entry missing its retention period or deletion mechanism, hiding a right-to-erasure gap.
