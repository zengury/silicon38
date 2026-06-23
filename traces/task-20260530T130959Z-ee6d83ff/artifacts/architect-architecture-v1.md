# Architecture Decision Record: RoboEase Refactor

## Context
The RoboEase codebase is a multi-module system for robot management. The current architecture has evolved organically, leading to:
- Mixed concerns in backend services (e.g., business logic in controllers)
- Tight coupling between frontend and backend via REST APIs
- Undefined service boundaries between robot-side services (star_walker, planning-backend) and the main backend
- Lack of clear data ownership and flow documentation
- No explicit authentication/authorization pattern documented
- Deployment complexity with multiple Docker compose files

The refactor aims to improve maintainability, scalability, and clarity without a full rewrite.

## Decision
Adopt a **Modular Monolith** architecture for the backend, with clear bounded contexts, and maintain the existing frontend separation (portal and admin). The robot-side services remain separate microservices due to their distinct deployment lifecycle.

### Key Architectural Decisions

1. **Backend Modularization**: Organize the FastAPI backend into domain modules (e.g., auth, robot, user, notification) with explicit interfaces. Each module owns its data access, business logic, and API routes.
2. **API Gateway Pattern**: Introduce a lightweight API gateway (or use Nginx) to route requests to appropriate backend modules and handle cross-cutting concerns (auth, rate limiting).
3. **Authentication Service**: Extract authentication into a dedicated module with JWT-based tokens, supporting both portal and admin frontends.
4. **Event Bus for Internal Communication**: Use Redis pub/sub or an in-process event bus for asynchronous communication between modules (e.g., robot status changes trigger notifications).
5. **Database per Module**: Each backend module gets its own schema/database (or at least separate table namespaces) to enforce bounded context. Use SQLModel for ORM.
6. **Robot-Side Services**: Keep star_walker and planning-backend as separate microservices communicating via MQTT and REST APIs. Define clear contracts.
7. **Shared Library**: Extract common utilities (DTOs, error handling, logging) into a shared Python package (`@roboease/shared` already exists for frontend; create `shared/` for backend).
8. **Configuration Management**: Centralize configuration using environment variables and a config module, replacing scattered `.env` files.

## Rationale
- **Modular Monolith** avoids the operational overhead of microservices while enforcing separation of concerns. It allows future extraction to microservices if needed.
- **API Gateway** simplifies client interaction and centralizes auth, reducing duplication.
- **Event Bus** decouples modules, improving testability and resilience.
- **Database per Module** prevents accidental cross-module coupling and enables independent scaling.
- **Shared Library** reduces code duplication and ensures consistent error handling.

## Alternatives Considered
1. **Full Microservices**: Rejected due to team size (small) and operational complexity. The current deployment (Docker Compose) is not suited for a full microservice mesh.
2. **Monolith without modularization**: Rejected because it perpetuates the current issues of mixed concerns and tight coupling.
3. **Serverless**: Rejected due to stateful robot communication (WebSockets, MQTT) and long-running SSH sessions.
4. **GraphQL**: Rejected for now; REST is simpler and sufficient for current use cases. Could be added later for complex queries.

## Consequences
- **Positive**: Clearer code organization, easier onboarding, improved testability, and reduced merge conflicts.
- **Negative**: Initial refactoring effort; need to migrate existing code to new module structure. Potential performance overhead from event bus.
- **Risks**: Breaking changes to API contracts; need to coordinate frontend updates. Robot-side service integration may require contract negotiation.

## Implementation Plan (Incremental)
1. Create shared library (`backend/shared/`) with common models, exceptions, and utilities.
2. Define module boundaries and create directory structure (`backend/modules/auth/`, `backend/modules/robot/`, etc.).
3. Extract authentication module first (most cross-cutting).
4. Migrate robot management module.
5. Add event bus for robot status changes.
6. Update deployment configuration to support new module structure.
7. Update frontend API calls if endpoints change.

## Data Flows
- **User Authentication**: Portal/Admin → API Gateway → Auth Module → JWT issued → subsequent requests include token.
- **Robot Control**: Admin → API Gateway → Robot Module → MQTT → Robot Device → status updates via MQTT → Event Bus → Notification Module.
- **Data Management**: Admin → API Gateway → respective module → database.

## Failure Modes
- **Auth Module Down**: All authenticated requests fail. Mitigation: redundant instances, caching of public keys.
- **MQTT Broker Down**: Robot communication fails. Mitigation: retry queue, fallback to polling.
- **Database Unavailable**: Module-specific failures. Mitigation: connection pooling, read replicas.

## Tradeoffs
- **Consistency vs. Availability**: Event bus introduces eventual consistency for non-critical updates. Critical operations (e.g., robot emergency stop) use synchronous calls.
- **Module Granularity**: Too many modules increase complexity; too few defeat the purpose. Aim for 5-7 modules initially.

## Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for RoboEase refactor, including modular monolith backend, API gateway, event bus, and module boundaries.
  key_decisions:
    - decision: Adopt modular monolith for backend
      rationale: Balances maintainability with operational simplicity; allows future extraction.
    - decision: Extract authentication into dedicated module
      rationale: Cross-cutting concern used by all frontends; centralizes security.
    - decision: Use event bus for async communication
      rationale: Decouples modules; enables future scalability.
    - decision: Database per module
      rationale: Enforces bounded context; prevents accidental coupling.
  handoff_focus:
    - senior-engineer: Implement shared library and auth module first.
    - api-designer: Define REST API contracts for each module.
    - database-engineer: Design database schemas per module.
  open_questions:
    - What is the exact event bus technology? (Redis pub/sub vs in-process)
    - Should the API gateway be a separate service or part of Nginx?
    - What is the migration strategy for existing data?
  known_constraints:
    - Team size is small; avoid over-engineering.
    - Existing deployment uses Docker Compose; must remain compatible.
    - Robot-side services are separate and cannot be merged.
  confidence_differential: 0.8
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
      - handoffs/zoom-out→architect-20260530-131015.yaml
  retained_context:
    decisions:
      - statement: Map focuses on top-level module structure and external dependencies.
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Adopt modular monolith for backend.
        source: architect
        impact: Shapes all backend refactoring.
      - statement: Extract authentication into dedicated module.
        source: architect
        impact: First module to implement.
      - statement: Use event bus for async communication.
        source: architect
        impact: Decouples modules.
      - statement: Database per module.
        source: architect
        impact: Enforces bounded context.
    constraints:
      - statement: Only files listed in workspace code were available; backend source not fully explored.
        source: semantic_node_executor
        impact: Constrains downstream node execution.
      - statement: Team size is small; avoid over-engineering.
        source: architect
        impact: Design must be pragmatic.
      - statement: Existing deployment uses Docker Compose; must remain compatible.
        source: architect
        impact: Deployment changes must be incremental.
      - statement: Robot-side services are separate and cannot be merged.
        source: architect
        impact: They remain microservices.
    assumptions:
      - statement: Backend is a single Python FastAPI service based on requirements.txt.
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: Admin panel is based on vue3-element-admin template.
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: Event bus can be implemented with Redis pub/sub.
        source: architect
        risk: May need evaluation.
    open_questions:
      - statement: What is the exact backend module structure?
        source: semantic_node_executor
        owner: runtime
      - statement: What are the robot-side services (star_walker, planning-backend)?
        source: semantic_node_executor
        owner: runtime
      - statement: What is the authentication flow?
        source: semantic_node_executor
        owner: runtime
      - statement: What is the database schema?
        source: semantic_node_executor
        owner: runtime
      - statement: What is the deployment environment?
        source: semantic_node_executor
        owner: runtime
      - statement: What is the exact event bus technology? (Redis pub/sub vs in-process)
        source: architect
        owner: runtime
      - statement: Should the API gateway be a separate service or part of Nginx?
        source: architect
        owner: runtime
      - statement: What is the migration strategy for existing data?
        source: architect
        owner: runtime
  omitted_context:
    - source: Detailed file listings beyond key files.
      reason: background_only
    - source: Artifact planning documents (not code).
      reason: background_only
    - source: Frontend component details.
      reason: not relevant to architecture decisions
  compression_rationale:
    method: Top-down structural mapping; only included modules with clear responsibilities and verified relationships.
    loss_notes:
      - Backend internal modules not enumerated due to limited file access.
      - Robot-side services not explored.
  quality_checks:
    - name: Module existence verified
      passed: true
    - name: Relationships verified by imports/configs
      passed: true
    - name: Domain vocabulary used
      passed: true
    - name: Decision record complete
      passed: true
    - name: Alternatives documented
      passed: true
    - name: Tradeoffs documented
      passed: true
```