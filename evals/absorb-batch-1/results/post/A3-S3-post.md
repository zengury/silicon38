# Scope Prosecution — Multi-Tenant SaaS (POST-ABSORB)

## Perspective Archetype: Adversary
Every feature on this list is guilty until proven innocent. Prosecute each one.

---

## Verdict Table

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

---

## Assumption Risk Map

### KEEP 1 — Tenant isolation (each customer sees only their data)

**Assumption A:** Row-level security (or equivalent schema-level isolation) is sufficient to guarantee isolation without requiring a separate database per tenant.
Risk: HIGH
Rationale: Tenant isolation implemented via a `tenant_id` column and application-layer filtering is fundamentally different from physical isolation. Every future query, ORM relationship, background job, cache key, and report must correctly scope to the tenant. A single missing WHERE clause is a data-breach incident. The team is betting that disciplined application-layer enforcement is enough — which requires consistent, auditable patterns across every data access path, including third-party libraries and internal tooling.
Flag: **Route to product-vision-anchor.** Decide upfront on the isolation model: shared schema (highest risk, lowest cost), schema-per-tenant (medium risk, moderate cost), or DB-per-tenant (lowest risk, highest cost). This decision cannot be reversed cheaply after customers are onboarded. If shared schema is chosen, mandate a security audit of every data access path before launch.

**Assumption B:** Infrastructure-level isolation (network, storage, compute) is not required by the initial customer base's compliance requirements.
Risk: MEDIUM
Rationale: Customers in regulated industries (healthcare, financial services) may contractually require compute-level isolation, not just data-level isolation. If any of the existing single-tenant customers being migrated operate under such requirements, the migration breaks immediately.

---

### KEEP 2 — Per-tenant billing integration (usage-based)

**Assumption A:** The usage metric chosen for billing (seats, API calls, storage, etc.) can be reliably instrumented before the migration sprint, not after.
Risk: HIGH
Rationale: Usage-based billing requires metering infrastructure — counters, aggregation pipelines, audit trails — that must exist before customers are billed. The team is betting that the right usage signal is already knowable and instrumentable. If the metric is poorly chosen (e.g., billing on API calls that are inconsistently triggered across features), customers will dispute invoices immediately, and retroactive re-billing is legally and operationally hazardous.
Flag: **Route to product-vision-anchor.** Define and lock the billing metric before any billing integration work begins. Validate it against the existing customer base's usage patterns (even if single-tenant). Do not start billing integration work until the metric is signed off.

**Assumption B:** The chosen billing provider (Stripe, Lago, etc.) supports usage-based metering at the granularity the product requires without custom aggregation logic.
Risk: MEDIUM
Rationale: Billing APIs differ significantly in their metering granularity, idempotency guarantees, and invoice timing. Discovering mid-integration that the provider requires a custom aggregation job adds 2–4 weeks of unplanned work at a blocking point in the roadmap.

---

### KEEP 3 — Tenant admin portal (user management, settings)

**Assumption A:** The admin portal's scope (add/remove users, set roles, configure settings) is stable enough to build before knowing what enterprise customers will actually need to manage.
Risk: MEDIUM
Rationale: Admin portals have a well-known scope creep pattern — every enterprise pilot customer arrives with a list of settings they need exposed. The team is betting that a thin v1 portal (user CRUD + basic settings) will be sufficient for onboarding without requiring custom configuration for each new customer.

**Assumption B:** The admin portal does not require audit logging of admin actions for the initial customer base.
Risk: MEDIUM
Rationale: Many regulated customers require a full audit log of who changed what and when in the admin portal, even at v1. If the first enterprise customer requires audit logging and it was not built in, retrofitting it requires touching every admin action endpoint — a non-trivial rework that delays the customer go-live.

---

### KEEP 4 — Migrate existing single-tenant customers to multi-tenant

**Assumption A:** The existing single-tenant data schema is compatible with the multi-tenant schema without a destructive transformation.
Risk: HIGH
Rationale: This is the highest-risk assumption in the entire S3 requirements list, and it is invisible in the verdict table alone. Single-tenant databases frequently have implicit assumptions baked in — no `tenant_id` columns, global sequences, hardcoded configuration in schema, foreign keys that span what will become tenant boundaries. A migration that requires restructuring these schemas is not a data migration; it is a schema redesign under production data. If any existing customer has a data volume or schema deviation that breaks the migration script, the team faces either a data loss event or an indefinite freeze on the migration.
Flag: **Prototype before implementation sprint.** Run the migration script against a sanitized copy of the largest and most complex existing customer's database before committing to the migration architecture. Any schema incompatibility discovered at this stage is a blocker that must be routed to product-vision-anchor — it may require a longer migration window, a dual-write period, or a customer-by-customer manual migration rather than an automated batch.

**Assumption B:** Existing customers will accept a migration window (downtime or read-only period) without it triggering contract breach or churn.
Risk: MEDIUM
Rationale: Migrating a live customer to a new data architecture requires either a maintenance window or a complex zero-downtime dual-write strategy. The team is betting that customer SLAs and contracts permit a planned migration window. Any customer with an uptime SLA clause that the migration would violate requires individual negotiation before the migration is scheduled.
