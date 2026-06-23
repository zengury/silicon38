# Scope Prosecution — AI-Powered Code Review (POST-ABSORB)

## Perspective Archetype: Adversary
Every feature on this list is guilty until proven innocent. Prosecute each one.

---

## Verdict Table

core_statement: Automatically reviews every pull request for bugs and security issues before a human spends time on it.

feature_verdicts:
  - feature: Automatic code review triggered on every PR
    verdict: KEEP
    reason: This is the product — without automatic triggering, developers must opt in manually and the core promise of consistent gatekeeping disappears.

  - feature: Language-specific analysis (Python, TypeScript, Go)
    verdict: KEEP
    reason: Generic analysis produces false positives that erode trust; language-aware rules are the minimum bar for the review to be actionable rather than noise.

  - feature: Security vulnerability detection
    verdict: KEEP
    reason: Security findings are the highest-stakes output and the primary reason a team would tolerate any friction from an automated reviewer.

  - feature: Style and convention enforcement
    verdict: CUT
    reason: Linters and formatters already solve this; shipping style enforcement in v1 invites bikeshedding debates that bury the security signal and positions the product as a fancy linter.

  - feature: Natural language explanation of findings
    verdict: KEEP
    reason: Without readable explanations, findings are lookup codes that junior developers ignore; explanation converts a flag into actionable guidance.

  - feature: One-click suggested fixes
    verdict: DEFER
    reason: Generating safe, context-correct patches requires a reliability bar the product has not yet earned; shipping broken fixes destroys trust faster than shipping no fixes.

  - feature: Integration with GitHub, GitLab, and Bitbucket
    verdict: DEFER
    reason: GitHub accounts for the majority of addressable teams; adding GitLab and Bitbucket in v1 triples the integration surface without tripling the user base.

  - feature: Review latency < 30 seconds per PR
    verdict: KEEP
    reason: Reviews that arrive after a developer has moved on to the next task are ignored; sub-30-second latency is the threshold between a blocking gate and an afterthought.

kept_count: 5
cut_count: 1
deferred_count: 2
scope_reduction_summary: Cut style enforcement entirely and defer multi-platform integrations and auto-fix, reducing v1 to a fast, security-focused GitHub reviewer with readable findings.

---

## Assumption Risk Map

### KEEP 1 — Automatic code review triggered on every PR

**Assumption A:** The GitHub webhook and API quota limits will not throttle the product under real team usage volumes.
Risk: MEDIUM
Rationale: GitHub secondary rate limits apply to API calls per repository per hour. A team with many simultaneous PRs (e.g., a monorepo with feature branches) could exhaust webhook delivery or status-check API quotas. The team is betting that GitHub's limits are well above the usage patterns of early customers.

**Assumption B:** Teams will accept a required GitHub App installation with the necessary permissions scope without escalating to a security review that blocks adoption.
Risk: MEDIUM
Rationale: Write permissions to post PR comments and set commit statuses are required. Enterprise security teams often quarantine any new GitHub App pending review — this is an adoption friction assumption, not an engineering one.

---

### KEEP 2 — Language-specific analysis (Python, TypeScript, Go)

**Assumption A:** Three languages are sufficient to cover the majority of the addressable v1 customer base without requiring immediate expansion.
Risk: MEDIUM
Rationale: The team is betting that customers who use Java, Rust, Ruby, or C# will wait for language support rather than choosing a competitor. If even one enterprise pilot customer requires a fourth language, the assumption breaks and scope expands mid-sprint.

**Assumption B:** AST parsing and static analysis libraries for all three languages are maintained, stable, and license-compatible with the product's distribution model.
Risk: LOW
Rationale: Tree-sitter and language-specific AST tooling are mature; this is a verifiable pre-implementation check rather than an ongoing operational bet.

---

### KEEP 3 — Security vulnerability detection

**Assumption A:** The security rule set (whether LLM-generated or static) has a false-positive rate low enough that developers do not train themselves to dismiss findings.
Risk: HIGH
Rationale: This is the central trust bet for the entire product. If the security detector fires on non-issues — common patterns mistaken for vulnerabilities, over-eager SQL injection flags on parameterized queries — developers will learn to ignore all output within weeks. The team has no empirical false-positive rate data before shipping; they are betting their rule quality is good enough on day one.
Flag: **Prototype before implementation sprint.** Run the security detector against 20–30 real public PRs from open-source repos with known histories. Measure false-positive rate before committing to the detection approach. If FPR exceeds 15%, route to product-vision-anchor to decide whether to narrow scope to a smaller, higher-confidence rule set.

---

### KEEP 4 — Natural language explanation of findings

**Assumption A:** LLM inference is available as a cost-effective API dependency that the team does not need to self-host.
Risk: MEDIUM
Rationale: Natural language explanations at scale require either an LLM API call per finding or a large self-hosted model. The team is betting that per-call LLM API costs remain within margins at the expected findings-per-PR volume. At high PR velocity this can become a significant variable cost that is invisible in initial pricing models.

**Assumption B:** LLM-generated explanations are accurate enough that they describe the actual finding rather than hallucinating plausible-sounding but incorrect guidance.
Risk: HIGH
Rationale: If the explanation is generated from the finding code snippet and rule label, the LLM may produce confident, well-formatted explanations that are factually wrong about the specific vulnerability — for example, correctly identifying a potential injection point but misstating the remediation. Developers will follow LLM-generated remediation advice; incorrect advice causes harm.
Flag: **Prototype before implementation sprint.** Evaluate explanation accuracy against a set of known vulnerabilities with ground-truth remediation. If accuracy is below acceptable threshold, route to product-vision-anchor to decide between static templated explanations (lower quality, higher reliability) versus LLM-generated explanations.

---

### KEEP 5 — Review latency < 30 seconds per PR

**Assumption A:** LLM inference latency for the analysis payload (full diff + context) fits within the 30-second budget under p95 load, not just median.
Risk: HIGH
Rationale: This is the most consequential invisible architectural bet in the entire requirements list. A 30-second SLA for a full PR review means each step — webhook receipt, diff retrieval, static analysis, LLM inference, posting results — must complete in sequence well under 30 seconds. LLM inference alone for a large diff (1,000+ line changes) can exceed 20 seconds at p95 on shared inference infrastructure. The team is betting on a latency profile they have not measured under realistic load.
Flag: **Prototype before implementation sprint.** Benchmark the full pipeline (diff fetch + analysis + LLM explanation generation + GitHub comment post) against PRs of varying sizes (small: <50 lines, medium: 200–500 lines, large: 1,000+ lines). If p95 latency for medium PRs exceeds 25 seconds, route to product-vision-anchor: either raise the SLA, constrain analysis to diffs below a size threshold, or accept that large PRs will breach the SLA and communicate this to customers.

**Assumption B:** GitHub webhook delivery is reliable enough that the 30-second clock starts close to the actual PR open event rather than minutes later due to delivery delays.
Risk: MEDIUM
Rationale: GitHub webhook delivery is not guaranteed to be instantaneous; under platform load, delivery can lag by 30–90 seconds. The team's 30-second latency requirement may be measured from webhook receipt, which is not the same as latency perceived by the developer. This should be clarified in the SLA definition before customer commitments are made.
