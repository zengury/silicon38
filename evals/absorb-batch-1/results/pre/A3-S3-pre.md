## Perspective Archetype: Adversary
Every feature on this list is guilty until proven innocent. Prosecute each one: why must it exist in v1? What breaks if it ships without this?

## Execution Ability
For each requirement:
1. Core test: If we shipped without this, would the product fail to do its primary job?
2. Differentiation test: Does this feature make the product distinctively better than alternatives?
3. Complexity cost: What does including this cost in complexity, maintenance, user cognitive load?

Name the one thing this product does better than anything else.

## Quality Criteria
- Every feature gets a verdict: KEEP / CUT / DEFER
- KEEP requires one-sentence justification tied to core value
- CUT and DEFER are the primary deliverable
- No diplomatic hedging

## Output format:
core_statement: <one sentence — the irreducible thing this product does>
feature_verdicts:
  - feature: <name>
    verdict: KEEP | CUT | DEFER
    reason: <one sentence tied to core_statement>
kept_count: n
cut_count: n
deferred_count: n
scope_reduction_summary: <one sentence>

---

core_statement: Lets multiple customers each run isolated, independently-billed instances of the product on shared infrastructure.

feature_verdicts:
  - feature: Tenant isolation (each customer sees only their data)
    verdict: KEEP
    reason: Without hard data isolation the product is not multi-tenant — it is a single-tenant product with a login screen, and any bleed is a critical security incident.

  - feature: Custom subdomain per tenant (acme.ourapp.com)
    verdict: DEFER
    reason: Subdomain routing adds DNS, TLS certificate provisioning, and routing complexity that can be layered on after the core isolation and billing model is proven.

  - feature: Per-tenant billing integration (usage-based)
    verdict: KEEP
    reason: Without per-tenant metering there is no business model for multi-tenancy; flat billing defeats the purpose of selling to customers at different usage tiers.

  - feature: Tenant admin portal (user management, settings)
    verdict: KEEP
    reason: Without a self-serve admin portal every user change requires a support ticket, making the product operationally unscalable from day one.

  - feature: SSO support (SAML, OAuth2 per tenant)
    verdict: DEFER
    reason: SSO is a procurement checkbox for enterprise deals but not required to serve the first cohort of customers; defer until an enterprise deal demands it.

  - feature: Data export per tenant (GDPR right to portability)
    verdict: DEFER
    reason: GDPR portability is a legal obligation that varies by jurisdiction and customer type; defer implementation until the customer base triggers the obligation, but document the gap.

  - feature: White-labeling (custom logo, colors)
    verdict: CUT
    reason: White-labeling serves resellers, not direct customers, and building a theming system before the core product is stable adds frontend complexity with no retention benefit.

  - feature: Migrate existing single-tenant customers to multi-tenant
    verdict: KEEP
    reason: Without a migration path the team maintains two parallel systems indefinitely, doubling operational overhead and preventing the cost savings that justify multi-tenancy.

kept_count: 4
cut_count: 1
deferred_count: 3
scope_reduction_summary: Cut white-labeling and defer subdomains, SSO, and GDPR export, focusing v1 on hard isolation, billing, admin self-serve, and migration of existing customers.
