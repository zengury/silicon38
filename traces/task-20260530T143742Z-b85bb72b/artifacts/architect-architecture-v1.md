# Architecture Decision Record: RoboEase Refactoring

## Context
The RoboEase codebase is a monorepo with pnpm workspaces, containing a Vue 3 frontend (portal and admin), a Python FastAPI backend, Docker deployment configurations, and various artifacts. The task is to optimize and refactor the codebase for improved maintainability, performance, and clarity. Key observations from the context map:
- Frontend: portal (public-facing) and admin (internal dashboard) both use Vue 3 + Element Plus, with shared workspace package `@roboease/shared`.
- Backend: FastAPI with SQLModel, Redis, MQTT, WebSocket, OpenAI, Volcengine.
- Docker: multiple environments (base, edge, cloud, robot) with docker-compose files.
- Artifacts: historical plans and designs from previous agent runs.
- Unknowns: exact database schema, WebSocket details, authentication mechanism, test coverage.

## Decision 1: Adopt Modular Monolith with Clear Service Boundaries
**Decision:** Keep the backend as a single deployable unit (modular monolith) but enforce strict module boundaries using FastAPI's `APIRouter` and dependency injection. Do not extract microservices at this stage.

**Rationale:** The team size is small (likely <10 developers), domain boundaries are still evolving, and operational complexity should be minimized. A modular monolith allows rapid iteration while providing clear separation of concerns. Future extraction to microservices is possible if scaling needs arise.

**Alternatives Considered:**
- Full microservices: rejected due to increased operational overhead, unclear domain boundaries, and small team.
- Serverless: rejected due to stateful robot communication (WebSocket/MQTT) and long-running processes.

**Consequences:**
- Positive: simpler deployment, easier debugging, faster development.
- Negative: eventual need for disciplined module boundaries to avoid tight coupling.

## Decision 2: Standardize API Layer with Versioned Endpoints
**Decision:** Implement API versioning (e.g., `/api/v1/...`) for all backend endpoints. Use FastAPI's `APIRouter` with a prefix.

**Rationale:** The codebase lacks explicit versioning, which will cause breaking changes as the API evolves. Versioning provides backward compatibility and clear migration paths.

**Alternatives Considered:**
- No versioning: rejected due to risk of breaking existing clients.
- Header-based versioning: rejected for simplicity; URL-based is more visible and easier to debug.

**Consequences:**
- Positive: clear API contract evolution.
- Negative: requires updating all frontend API calls to include version prefix.

## Decision 3: Replace Mock Data with Real API Calls in Admin Frontend
**Decision:** Remove mock data files (`mock/*.mock.ts`) from the admin frontend and implement real API calls using Axios with proper error handling and loading states.

**Rationale:** Mock data is useful for development but creates a false sense of functionality. Real API calls ensure the frontend is tested against actual backend behavior.

**Alternatives Considered:**
- Keep mock data for development: rejected because it leads to integration issues and untested error paths.
- Use MSW (Mock Service Worker): rejected for simplicity; direct API calls with environment-based mocking is sufficient.

**Consequences:**
- Positive: frontend is always tested against real backend.
- Negative: requires backend to be running during development; can be mitigated with Docker Compose.

## Decision 4: Consolidate Docker Compose Files
**Decision:** Merge `docker-compose.ci.yml`, `docker-compose.prod.yaml`, and `docker-compose.staging.yaml` into a single `docker-compose.yml` with multiple profiles (e.g., `--profile ci`, `--profile prod`, `--profile staging`).

**Rationale:** The current three files have significant duplication. Using Docker Compose profiles reduces duplication and ensures consistency across environments.

**Alternatives Considered:**
- Keep separate files: rejected due to maintenance overhead and drift between environments.
- Use environment variables only: rejected because profiles provide cleaner separation.

**Consequences:**
- Positive: single source of truth for service definitions.
- Negative: requires updating CI/CD pipelines to use profiles.

## Decision 5: Implement Centralized Configuration Management
**Decision:** Use a single configuration module in the backend (e.g., `backend/app/core/config.py`) that loads settings from environment variables with sensible defaults. Avoid hardcoded values across the codebase.

**Rationale:** The current codebase likely has scattered configuration (database URLs, API keys, etc.). Centralizing configuration improves security, testability, and deployment flexibility.

**Alternatives Considered:**
- Keep as-is: rejected due to security risks and maintenance burden.
- Use a config file: rejected because environment variables are more secure for secrets.

**Consequences:**
- Positive: easier to manage secrets, support multiple environments.
- Negative: requires refactoring all modules that currently use hardcoded values.

## Decision 6: Add Comprehensive Logging and Error Handling
**Decision:** Implement structured logging using `loguru` (already in requirements) across the backend. Add consistent error handling with custom exception classes and FastAPI exception handlers.

**Rationale:** The codebase lacks observability. Structured logging and error handling are essential for debugging and monitoring.

**Alternatives Considered:**
- Use standard logging: rejected because loguru provides better formatting and performance.
- No changes: rejected due to poor debuggability.

**Consequences:**
- Positive: improved observability and faster issue resolution.
- Negative: requires updating all backend modules to use the new logging pattern.

## Decision 7: Establish Database Migration Strategy
**Decision:** Use Alembic (with SQLModel support) for database migrations. Create an initial migration that captures the current schema, then use migrations for all future schema changes.

**Rationale:** The current schema is unknown and likely managed manually. Alembic provides version-controlled, repeatable migrations.

**Alternatives Considered:**
- SQLModel's built-in `create_all`: rejected because it doesn't support incremental migrations.
- Manual SQL scripts: rejected due to lack of versioning and rollback support.

**Consequences:**
- Positive: safe schema evolution, team collaboration.
- Negative: requires initial effort to generate the first migration.

## Decision 8: Implement Authentication and Authorization Middleware
**Decision:** Use JWT-based authentication with refresh tokens. Implement role-based access control (RBAC) using FastAPI dependencies.

**Rationale:** The authentication mechanism is unknown but critical for security. JWT is stateless and suitable for REST APIs. RBAC aligns with the admin dashboard's role management.

**Alternatives Considered:**
- Session-based auth: rejected due to scalability concerns.
- OAuth2: rejected for simplicity; can be added later if needed.

**Consequences:**
- Positive: secure, scalable authentication.
- Negative: requires implementing token refresh and revocation logic.

## Decision 9: Standardize Frontend State Management
**Decision:** Use Pinia (Vue 3's official state management) for shared state across frontend apps. Avoid prop drilling and event bus patterns.

**Rationale:** The current state management approach is unclear. Pinia provides a clean, TypeScript-friendly solution.

**Alternatives Considered:**
- Vuex: deprecated in favor of Pinia.
- Reactive composables: sufficient for simple state but not for complex cross-component state.

**Consequences:**
- Positive: predictable state management, easier testing.
- Negative: learning curve for developers unfamiliar with Pinia.

## Decision 10: Add Unit and Integration Tests
**Decision:** Set up pytest for backend tests and Vitest for frontend tests. Write tests for critical paths (authentication, robot control, API endpoints).

**Rationale:** The codebase has no tests (based on unknowns). Tests are essential for refactoring safely.

**Alternatives Considered:**
- No tests: rejected due to high risk of regressions.
- Only integration tests: rejected because unit tests provide faster feedback.

**Consequences:**
- Positive: increased confidence in refactoring, better code quality.
- Negative: initial time investment to set up test infrastructure.

## Tradeoffs Summary
- Modular monolith vs microservices: chose monolith for simplicity now, with clear boundaries for future extraction.
- Mock data vs real API: chose real API for reliability, accepting development dependency on backend.
- Multiple docker-compose files vs profiles: chose profiles for reduced duplication.
- Centralized config vs scattered: chose centralized for security and maintainability.
- Logging vs none: chose logging for observability.
- Alembic vs manual: chose Alembic for safe migrations.
- JWT vs sessions: chose JWT for scalability.
- Pinia vs alternatives: chose Pinia for modernity and TypeScript support.
- Tests vs no tests: chose tests for quality assurance.

## Downstream Constraints
- Senior engineer: must implement modular monolith with APIRouter, API versioning, centralized config, logging, error handling, JWT auth, and Alembic migrations.
- API designer: must design versioned REST API with consistent error responses.
- Database engineer: must create Alembic initial migration and define schema models.
- Frontend developer: must replace mock data with real API calls, adopt Pinia, and update API calls to versioned endpoints.
- DevOps engineer: must consolidate docker-compose files into profiles and update CI/CD.

## Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for RoboEase refactoring, including 10 key decisions covering modular monolith, API versioning, mock data removal, Docker consolidation, centralized config, logging, database migrations, authentication, state management, and testing.
  key_decisions:
    - decision: Adopt modular monolith with clear service boundaries
      rationale: Small team, evolving domain, minimize operational complexity.
    - decision: Standardize API layer with versioned endpoints
      rationale: Backward compatibility and clear evolution.
    - decision: Replace mock data with real API calls in admin frontend
      rationale: Ensure frontend is tested against real backend.
    - decision: Consolidate Docker Compose files into profiles
      rationale: Reduce duplication and ensure consistency.
    - decision: Implement centralized configuration management
      rationale: Security, testability, deployment flexibility.
    - decision: Add comprehensive logging and error handling
      rationale: Observability and debugging.
    - decision: Establish database migration strategy with Alembic
      rationale: Safe schema evolution.
    - decision: Implement JWT-based authentication with RBAC
      rationale: Secure, scalable authentication.
    - decision: Standardize frontend state management with Pinia
      rationale: Predictable state management.
    - decision: Add unit and integration tests
      rationale: Confidence in refactoring.
  handoff_focus:
    - "Implement modular monolith with APIRouter and dependency injection"
    - "Add API versioning prefix to all endpoints"
    - "Remove mock data and implement real API calls in admin"
    - "Consolidate docker-compose files into profiles"
    - "Create centralized config module in backend"
    - "Set up structured logging with loguru"
    - "Create Alembic initial migration"
    - "Implement JWT auth with refresh tokens and RBAC"
    - "Set up Pinia stores for shared state"
    - "Set up pytest and Vitest test frameworks"
  open_questions:
    - "What is the exact database schema and ORM model structure?"
    - "How are WebSocket connections managed for real-time robot updates?"
    - "What is the current authentication mechanism?"
    - "Are there any existing tests?"
  known_constraints:
    - "Cannot access robot-side code without additional permissions."
    - "Some backend modules may be large; detailed analysis may require multiple iterations."
  confidence_differential: 0.75
  dissent_if_alone: null
  iteration_context: null
```
