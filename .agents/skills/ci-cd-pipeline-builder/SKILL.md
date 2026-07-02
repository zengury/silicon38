---
name: ci-cd-pipeline-builder
description: Design and build reproducible, secure CI/CD pipelines, deployment configuration, and infrastructure-as-code with a defined rollback path — use whenever a pipeline, deployment, secrets flow, or release automation is in scope.
---

## Purpose

Treat infrastructure as code: every configuration decision carries a rationale, every secret has a lifecycle, and every pipeline step that can fail has a recovery path.
Build pipelines that are reproducible (the same commit yields the same artifact), visible (failures produce actionable output), and secure (secrets are never in code, logs, or artifacts).
The pipeline is the contract between a commit and a running system, so it must be trustworthy end to end.
Optimize for the operator who will one day debug a failed deploy at 3am: clarity and recoverability outrank cleverness.

## When to use

- A CI/CD pipeline needs to be created or modified.
- Deployment configuration is involved.
- Environment variables or secrets management is in scope.
- Containerization or infrastructure-as-code is required.
- Release automation or a repeatable build flow is needed.
- A build succeeds on one machine but fails in CI and reproducibility is suspect.
- A production service needs SLA hardening or a reliability review.

## Method

1. Establish the target: name the environment(s), the artifact produced, and the trigger events. Refuse to proceed if the target environment is unspecified — that is a blocker, not a guess.
2. Model the stages as a DAG: build, test, package, deploy. For each stage define inputs, outputs, and the single responsibility it owns.
3. Make it idempotent: running the pipeline twice on the same commit must not create duplicates or errors. Guard mutating steps with existence checks or declarative apply.
4. Wire secrets by reference only. Pull them from the platform's secret store at runtime; never embed them, even encrypted, and never echo them into logs. Document exactly which secrets are needed and where an operator sets them.
5. Design caching deliberately: the cache key must include every input that affects the cached output (lockfiles, tool versions, source hashes). A stale cache is a silent correctness bug.
6. Give every failing step a clear failure output that says what failed and why — exit codes, surfaced logs, named steps.
7. Define and document the rollback procedure: how to revert to the previous known-good artifact, and confirm the deploy mechanism supports it. Deployment must be reversible.
8. Apply infrastructure changes through code, not console clicks, so the state is auditable and reproducible.
9. When SLA hardening is requested, run the resilience pass: list the top failure modes, sketch one injection scenario each, and estimate MTTR; flag any MTTR that exceeds SLA tolerance.
10. When automation is being reviewed, run a toil inventory: flag any manual step consuming more than ~30 min/week as a backlog item — identify and record, do not auto-fix unless that is the goal.
11. Validate syntax before delivery (lint/dry-run the config) and confirm no secret appears in any tracked file.

## Quality bar

- Pipeline is idempotent: a second run produces no errors or duplicates.
- No secrets embedded in any configuration file — referenced, not stored.
- No secret is ever written to build logs or baked into an artifact.
- Every stage that can fail emits output identifying what failed and why.
- Cache keys include all inputs that affect the cached output.
- Each stage owns one responsibility and its inputs/outputs are explicit.
- Rollback procedure is defined and shown to be executable.
- All infrastructure changes flow through code, not manual operations.
- Configuration is syntactically valid and dry-run/lint clean.
- When required, failure inventory and MTTR estimates are recorded.

## Output

- A pipeline/deployment/IaC configuration file (CI config, Dockerfile, or IaC manifest).
- An inline markdown note covering what the pipeline does, the secrets required and where to set them, and the tested rollback procedure. If a resilience or toil pass ran, record its findings alongside the key decisions.

## Anti-patterns

- Embedding secrets in config "just for now," even base64'd or encrypted at rest.
- Cache keys that omit a real input, producing builds that pass locally and fail in CI.
- A deploy step with no rollback path, discovered only mid-incident.
- Silent failures: a stage that exits non-zero without saying which command or input broke.
- Manual console changes that leave the codified infrastructure state drifted and unreproducible.
- Automating away toil that was never measured, or leaving a 30-min/week manual step unflagged.
- A pipeline that mutates shared state without a guard, so a re-run corrupts or duplicates it.
