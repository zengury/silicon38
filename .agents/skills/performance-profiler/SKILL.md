---
name: performance-profiler
description: Diagnose and fix performance problems by measuring first, locating the real bottleneck with profiler data, and proving improvement with a comparative measurement — use for regressions, latency-sensitive paths, or query optimization.
---

## Purpose

Measure first, hypothesize second, fix third. Never optimize without a baseline, and never claim an improvement without a comparative measurement taken the same way.
Performance intuition is unreliable; profiler data is not. Target the actual bottleneck rather than the most interesting optimization.
A 10x win in a path that is 1% of runtime is noise, while a 10% win in the critical path is the work.
Discipline about method is what separates a real speedup from a plausible-sounding story.

## When to use

- A performance regression is reported.
- The task touches high-throughput or latency-sensitive paths.
- Database queries are being designed or changed.
- Significant data volume is involved.
- An explicit performance requirement or budget is stated.
- Resource use (CPU, memory, I/O) is growing and the cause is unclear.

## Method

1. Reproduce the scenario with a representative dataset and workload. If the dataset or environment needed to reproduce the issue is unavailable, treat it as a blocker rather than guessing.
2. Establish a baseline: run the workload and record concrete numbers (latency percentiles, throughput, query time, memory) under a fixed methodology you can repeat exactly.
3. Profile to locate the bottleneck. Let the profiler or measurement data point to the hot path — do not infer it by reading code and picking the part that looks slow.
4. Confirm the bottleneck is on the critical path and accounts for a meaningful share of runtime. Discard tempting-but-irrelevant optimizations.
5. Form one hypothesis about the cause and the smallest change that would address it. For database work, capture the query plan before and after.
6. Apply the change while preserving correctness and maintainability. If the fix trades away either, get explicit user sign-off first.
7. Re-measure using the identical methodology as the baseline. Compute the real, quantified delta — never estimate the improvement.
8. If the improvement is insufficient, iterate: re-profile, since fixing the top bottleneck usually reveals the next one. Repeat until the target is met or diminishing returns are clear.
9. Report baseline, bottleneck evidence, the change, and the post-change measurement side by side so the gain is verifiable.

## Quality bar

- Baseline measurement established before any change.
- Bottleneck identified by profiler or measurement data, not by reading code.
- Optimization addresses the actual bottleneck, not a nearby one.
- The bottleneck is confirmed to sit on the critical path, not an incidental branch.
- Improvement measured after the change with the same methodology as the baseline.
- No optimization sacrificing correctness or maintainability without explicit sign-off.
- Query plans included for database-related optimizations.
- Both baseline and post-optimization numbers are present and real.
- The reported delta is computed from measurements, never estimated.

## Output

- An inline markdown analysis: baseline measurement, bottleneck identification with evidence, the optimization approach, and the result measurement with the quantified delta.
- The measurement methodology stated explicitly enough to be re-run and reproduce the baseline.
- Optionally, the optimized implementation as a file when a code change was made. Include before/after query plans for database changes.

## Anti-patterns

- Optimizing from intuition or a code read without ever profiling.
- Reporting an estimated or projected speedup instead of a measured one.
- Polishing a path that is a negligible fraction of total runtime.
- Changing baseline conditions between measurements so the comparison is meaningless.
- Sacrificing correctness or readability for speed without user agreement.
- Stopping after the first fix without re-profiling to see whether the bottleneck simply moved.
- Skipping the query plan on a database change, so the real cost driver stays hidden.
- Measuring against a toy dataset that does not exhibit the production bottleneck.
- Declaring victory without confirming the change actually met the stated budget or target.
