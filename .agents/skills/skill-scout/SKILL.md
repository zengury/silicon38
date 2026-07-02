---
name: skill-scout
description: Evaluates candidate skills against reproducible role benchmarks and presents evidence-based comparison reports for a human to decide; use when a role's candidate pool, benchmarks, or skill comparisons need work.
---

## Purpose

Make every other role more capable by ensuring the skills that fill them are the best available.
This skill maintains the candidate pool for each role and designs benchmark test cases.
It runs candidates through those benchmarks and collects multi-dimensional scores.
It presents evidence to a human, who makes the final call.
It never auto-replaces a deployed skill — it recommends, and the human decides.

## When to use

- A new candidate skill must be evaluated for a role.
- A role's benchmark test cases need to be created or updated.
- The candidate pool for a role needs maintenance of scores, samples, and history.
- A user asks for a comparison of skill candidates.
- A role has no active candidates and the gap must be flagged for recruiting.

## Method

1. Understand the role's core competency from its definition.
2. If the definition is too vague to design a fair benchmark, block and report it.
3. Design benchmark tasks that test the role's OUTPUT quality, not its process.
4. Fix the inputs, evaluation dimensions, and scoring rubric so the benchmark is reproducible by anyone.
5. Confirm candidates exist; if none are available to evaluate, block rather than proceed.
6. If an existing skill's output format is incompatible with the rubric, flag that as a blocker.
7. Run each candidate against the benchmark and collect multi-dimensional scores.
8. Never collapse a candidate to a single number; record per-dimension results.
9. Require at least two to three completed runs before recommending any replacement.
10. Record confidence intervals, sample counts, and known biases for each result.
11. Score soul compatibility for design-class roles and omit it for non-design roles.
12. Update the candidate pool, then produce a comparison report as a recommendation, not a decision.

## Quality bar

- Every benchmark tests output quality, not process.
- Every benchmark is reproducible: same inputs, same rubric, same scorers.
- Comparison reports include raw scores, confidence intervals, sample counts, and known biases.
- No replacement is recommended without at least two to three completed runs.
- Soul compatibility is scored for design-class roles and only those.
- Scores are multi-dimensional, never a single aggregate number.

## Output

Two Markdown artifacts.
The first is a benchmark definition for the target role.
It contains the task description, input artifacts, evaluation dimensions, rubric, and passing threshold.
The second is a candidate evaluation report comparing skills on that benchmark.
It carries per-dimension scores, confidence, and an explicit recommendation that stops short of deciding.

## Anti-patterns

- Auto-replacing a deployed skill instead of presenting evidence for a human.
- Reducing a candidate to a single aggregate score.
- Recommending replacement on a single run with no confidence interval.
- Benchmarking a role's process instead of the quality of its output.
- Writing an irreproducible benchmark whose inputs or rubric are undocumented.
- Scoring soul compatibility for non-design roles where it does not apply.
- Presenting a recommendation as if it were the final hiring decision.
