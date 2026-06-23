# Architecture Decision Record: RoboEase Refactor

## Context
RoboEase is a robot-as-a-service (RaaS) platform with a Vue 3 frontend (portal + admin), a FastAPI backend, and Docker-based deployment for edge and cloud environments. The workspace contains frontend source code, Docker configuration, and deployment scripts, but the backend source code is absent. The system uses MySQL, EMQX, Redis, and Minio as external dependencies. The task is to optimize and refactor the codebase.

## Decision
Adopt a **Modular Monolith** architecture with clear bounded contexts, retaining the existing deployment topology but introducing strict module boundaries within the backend (once source is available) and improving frontend code organization. The architecture will be documented via ADRs, and the frontend will be refactored to reduce duplication and improve maintainability.

## Rationale
- The team size is small (likely <10 developers), making a modular monolith the appropriate starting point.
- The existing deployment topology (nginx → portal + backend) is simple and works; splitting into microservices would add unnecessary complexity.
- The backend source is missing, so we cannot refactor it now; we focus on what is present: frontend and Docker configuration.
- The frontend has two SPAs (portal and admin) with overlapping concerns (e.g., API calls, auth). Refactoring shared logic into a common library reduces duplication.
- The Docker setup is functional but can be optimized for build speed and consistency.

## Alternatives Considered
1. **Microservices**: Rejected because the team size and current complexity do not justify the operational overhead. The existing monolith can be modularized incrementally.
2. **Full rewrite**: Rejected due to high risk and cost; incremental refactoring is safer.
3. **Do nothing**: Rejected because the codebase has duplication and unclear boundaries that hinder maintainability.

## Consequences
- Positive: Clearer module boundaries, reduced duplication, faster builds, easier onboarding.
- Negative: Requires discipline to maintain boundaries; backend refactoring is deferred until source is available.
- Risk: The missing backend source may contain architectural decisions that conflict with our assumptions.

## Downstream Constraints
- Backend source must be located and integrated before backend refactoring can proceed.
- Any shared frontend library must be versioned and published to avoid divergence.
- Docker images must be rebuilt after frontend changes; CI/CD pipeline should be established.

## Data Flows (Refined)
- User → Portal → Backend (REST API) → MySQL/EMQX/Redis/Minio
- Admin → Admin Panel → Backend (REST API + WebSocket) → MySQL/EMQX
- Robot → EMQX → Backend → MySQL/Redis

## Failure Modes
- Backend unavailable: Frontend should show error states gracefully.
- EMQX down: Robot commands and telemetry will fail; backend should queue or retry.
- MySQL down: Backend should return 503 and retry.
- Redis down: Cache misses; system degrades but remains functional.

## Implementation Plan (Incremental)
1. Extract shared frontend utilities (API client, auth, types) into a common package.
2. Refactor portal and admin to use the shared package.
3. Optimize Docker builds by using multi-stage builds and layer caching.
4. Add health checks and readiness probes to all services.
5. Document API contracts (OpenAPI) once backend source is available.

---

## Completion Report

```yaml
completion_report:
  what_was_done: Created architecture decision record for RoboEase refactor, focusing on frontend modularization and Docker optimization. Documented tradeoffs, failure modes, and incremental implementation plan.
  key_decisions:
    - decision: Adopt Modular Monolith architecture
      rationale: Team size and complexity do not warrant microservices; incremental modularization is safer.
    - decision: Extract shared frontend library from portal and admin
      rationale: Reduces duplication and improves maintainability.
    - decision: Defer backend refactoring until source is available
      rationale: Backend source is not in workspace; assumptions need validation.
  handoff_focus:
    - senior-engineer: Implement frontend shared library extraction and refactoring
    - api-designer: Define API contracts for backend endpoints
    - database-engineer: Review data models for consistency
  open_questions:
    - Where is the backend source code located?
    - What is the authentication/authorization mechanism?
    - Is there an existing CI/CD pipeline?
  known_constraints:
    - Backend source code is not present in workspace
    - Only Dockerfile and docker-compose references available for backend
    - Frontend code has significant duplication between portal and admin
  confidence_differential: 0.7
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - zoom-out-context-map-v1
    handoffs_read:
      - handoffs/zoom-out→architect-20260530-092751.yaml
  retained_context:
    decisions:
      - Map focuses on high-level module structure and deployment topology
      - Backend source not present in workspace; only Dockerfile and docker-compose references used
    constraints:
      - Only workspace files under /Users/ZQ/roboease are available
      - Backend implementation code is not included in the workspace
    assumptions:
      - Backend is a FastAPI application based on Dockerfile and docker-compose references
      - EMQX is used for MQTT messaging to robots
      - MySQL is the primary database
      - Redis is used for caching
      - Minio is used for object storage
    open_questions:
      - Where is the backend source code?
      - What are the exact API endpoints and data models?
      - How is authentication/authorization implemented?
      - What is the robot-side software architecture?
      - Is there a CI/CD pipeline?
      - What is the Dify AI Platform integration scope?
  omitted_context:
    - Detailed file listings for frontend admin (300+ files truncated)
    - Artifact files in /Users/ZQ/roboease/artifacts/ (release reports, plans) - not relevant for architecture decisions
  compression_rationale:
    method: Selective inclusion based on relevance to architecture decisions. Retained high-level module structure, deployment topology, and key assumptions. Omitted detailed frontend component trees and artifact files as they are not needed for architectural decision-making.
    loss_notes: []
  quality_checks:
    - name: All upstream decisions and constraints are captured
      passed: true
    - name: Assumptions are explicitly documented with risk
      passed: true
    - name: Open questions are carried forward
      passed: true
```