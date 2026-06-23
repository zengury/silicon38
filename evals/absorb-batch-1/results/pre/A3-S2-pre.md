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
