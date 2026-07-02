---
name: observability-designer
description: Instrument code with structured logging, metrics, and traces so production behavior is visible — use when shipping a feature, running a post-mortem, or when system behavior in production is unclear.
---

## Purpose

A system you cannot observe is a system you cannot operate. Design observability as a first-class feature rather than a retrofit.
Every production code path must be able to answer three questions: how will you know when this is broken, how will you know when this is slow, and how will you know who used it.
Prefer structured logs over string logs, metrics over log parsing, and traces over metrics when distributed causality matters.
The goal is that an on-call engineer can diagnose an incident from signals alone, without attaching a debugger to production.

## When to use

- A new feature is being shipped to production.
- An incident post-mortem is in scope and gaps in visibility surfaced.
- Logging, monitoring, or tracing is explicitly requested.
- System behavior in production is unclear or invisible.
- A distributed request path crosses services and cannot currently be traced end to end.

## Method

1. Confirm the monitoring platform and the data classification of anything logged. If the platform is unspecified or the PII status of in-scope data is unknown, treat that as a blocker.
2. Enumerate the code paths in scope. For each, decide the observable signal: a log, a metric, a trace span, or a combination.
3. Instrument error conditions with structured log entries: a level, a human message, and machine-readable context as fields — never string-interpolate values that should be queryable.
4. Set log levels with meaning: DEBUG is local-only detail, INFO is operational signal, WARN is a recoverable anomaly, ERROR requires human attention. Do not inflate or deflate severity.
5. Classify and mask PII before it reaches any sink. No personal data lands in logs without explicit classification and masking.
6. Define metrics with alert thresholds, not just collection. A metric nobody alerts on is a dashboard decoration; state the healthy range and the trigger point.
7. Propagate correlation IDs across service boundaries so a single request can be traced end to end.
8. Guard logging in hot paths: no unbounded logging inside tight loops — add rate limiting or sampling.
9. For each signal, write down what healthy versus unhealthy looks like so an on-call engineer can act without reverse-engineering the code.
10. Add cardinality discipline to metric labels: avoid unbounded label values (user IDs, request IDs) that explode time-series storage.
11. Produce the observability guide describing what is observable, which alerts to configure, and the healthy/unhealthy signatures.

## Quality bar

- Every error condition emits a log with level, message, and structured context.
- No PII in log output without explicit classification and masking.
- Metrics carry defined alert thresholds, not bare collection.
- Log levels are meaningful and consistently applied.
- No unrate-limited logging inside tight loops.
- Correlation IDs exist for request tracing across service boundaries.
- Every new code path has at least one observable signal.
- Each signal has a documented healthy-versus-unhealthy signature.
- The observability guide names the alerts to configure and their thresholds.

## Output

- Instrumented code carrying logging, metrics, and/or tracing.
- An inline markdown observability guide: what is observable, which alerts to configure with their thresholds, and what a healthy versus unhealthy signal looks like for each path.
- Where relevant, the correlation-ID propagation scheme and the metric label conventions used.

## Anti-patterns

- String-interpolated log messages that cannot be filtered or aggregated as fields.
- Collecting a metric with no alert threshold, so a regression is only visible in hindsight.
- Logging raw PII because classification was skipped.
- Chatty logs inside a hot loop that drown the signal and inflate cost.
- Instrumenting only the happy path, leaving failures silent in production.
- Emitting signals with no documented healthy range, so nobody knows when to act.
- Breaking the correlation ID chain at a service hop, making distributed traces useless.
