# Architecture Decision Record: RoboEase Refactor

## Context
The RoboEase codebase is a robot-as-a-service (RAAS) management platform. The zoom-out node identified the high-level module map. The task is to optimize and refactor the codebase. Key observations:
- Backend uses FastAPI with SQLModel, but has legacy config modules (`backend/config/`, `backend/db/`) that duplicate functionality in `backend/core/config/` and `backend/infrastructure/db/`.
- Two frontends (admin and portal) share no code; both are Vue 3 + TypeScript + Vite.
- Docker setup has edge and cloud profiles, but the cloud profile is incomplete (only web Dockerfile).
- Robot communication uses MQTT and WebSocket, but protocol details are not fully documented.
- External API clients (OpenAI, Volcengine) are in `infrastructure/external/`.
- No CI/CD pipeline visible.
- Testing strategy is absent.

## Decision: Modular Monolith with Clear Boundaries
We will maintain a modular monolith architecture for the backend, with strict separation between core, infrastructure, domain, and API layers. This avoids premature microservices complexity while enabling future extraction if needed.

## Rationale
- Team size is small (likely <10 developers).
- Domain boundaries are still evolving (robot management, task execution, AI integration).
- Rapid iteration is prioritized.
- Operational complexity is minimized.
- Shared database is acceptable.

## Alternatives Considered
1. **Microservices**: Rejected due to team size, unclear domain boundaries, and increased operational overhead.
2. **Serverless**: Rejected because robot communication requires persistent connections (WebSocket, MQTT).
3. **Event-Driven Architecture**: Rejected for now; can be introduced later if needed.

## Consequences
- Backend remains a single deployable unit.
- Clear layer boundaries prevent cross-layer coupling.
- Future extraction of services (e.g., AI service) is possible by moving domain logic to separate services.
- Shared database requires careful schema management.

## Load-Bearing Decisions

### Decision 1: Consolidate Backend Configuration
- **Decision**: Remove legacy `backend/config/` and `backend/db/` modules. All configuration goes through `core.config.Settings`. Database entities and connection go through `infrastructure.db`.
- **Rationale**: Eliminates duplication and confusion. New code should import from `core.config` and `infrastructure.db`.
- **Alternatives**: Keep legacy modules as backward-compat wrappers (current state). Rejected because it perpetuates confusion.
- **Consequences**: Requires updating imports across the codebase. Backward-compat re-exports in `backend/db/database.py` can be deprecated with a warning.

### Decision 2: Standardize API Versioning
- **Decision**: All API endpoints are under `/api/v1/`. Use FastAPI's APIRouter with prefix.
- **Rationale**: Clear versioning allows backward-compatible changes.
- **Alternatives**: No versioning (rejected for future-proofing).
- **Consequences**: New versions can be added as `/api/v2/`.

### Decision 3: Use SQLModel for ORM
- **Decision**: Continue using SQLModel (which combines SQLAlchemy and Pydantic).
- **Rationale**: Already in use; reduces boilerplate by defining models once.
- **Alternatives**: Raw SQLAlchemy (more verbose), Django ORM (different stack).
- **Consequences**: Must stay within SQLModel's capabilities; complex queries may need raw SQL.

### Decision 4: Separate Domain Logic from Infrastructure
- **Decision**: Business logic lives in `domain/` services. Infrastructure (DB, external APIs) lives in `infrastructure/`. API layer (`api/`) only handles HTTP concerns.
- **Rationale**: Testability, maintainability, and future extraction.
- **Alternatives**: Mixed layers (current state in some places).
- **Consequences**: Requires refactoring existing code that mixes concerns.

### Decision 5: Shared Frontend Components
- **Decision**: Extract common UI components (icons, utilities, styles) into a shared package under `frontend/shared/`. Both admin and portal import from it.
- **Rationale**: Reduces duplication; consistent look and feel.
- **Alternatives**: Keep separate (current state). Rejected due to duplication.
- **Consequences**: Requires setting up a monorepo tool (pnpm workspaces already in use).

### Decision 6: Docker Profile Completion
- **Decision**: Complete the cloud Docker profile with backend and nginx services, similar to edge profile. Use environment-specific overrides.
- **Rationale**: Enables production deployment.
- **Alternatives**: Single Docker Compose file with profiles (rejected for clarity).
- **Consequences**: Two compose files to maintain, but they share base images.

### Decision 7: Robot Communication Protocol Documentation
- **Decision**: Document MQTT topics and WebSocket message formats in `docs/robot-communication.md`.
- **Rationale**: Essential for debugging and future development.
- **Alternatives**: Keep tribal knowledge (rejected).
- **Consequences**: Requires reading existing code to extract protocol details.

## Data Flows

### User Authentication
```
Frontend -> POST /api/v1/auth/login -> Backend validates credentials -> Returns JWT -> Subsequent requests include Bearer token -> Backend validates via dependency
```

### Robot Management
```
Admin creates robot -> POST /api/v1/robots -> Backend stores in MySQL -> Robot connects via MQTT -> Backend updates robot status -> Frontend polls or WebSocket push
```

### Task Execution
```
User submits task -> POST /api/v1/tasks -> Backend dispatches via MQTT -> Robot executes -> Robot reports status via WebSocket -> Backend updates task state
```

### External AI
```
Backend receives AI request -> Calls OpenAI/Volcengine API -> Returns response -> Optionally caches in Redis
```

## Failure Modes
- **MySQL down**: Backend fails to start or returns 500 on DB operations. Need health checks and connection retry.
- **Redis down**: Caching disabled; authentication may fail if session store is Redis. Fallback to DB.
- **MQTT broker down**: Robot communication fails. Backend should queue commands and retry.
- **External API down**: AI features degrade. Backend should return cached responses or error gracefully.

## Downstream Constraints
- **Senior Engineer**: Must implement refactoring of backend layers, consolidate config, and extract shared frontend components.
- **API Designer**: Must document API contracts for all endpoints.
- **Database Engineer**: Must review and optimize SQLModel entities and migrations.

## Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for RoboEase refactor, including modular monolith decision, layer boundaries, data flows, failure modes, and downstream constraints.
  key_decisions:
    - decision: Maintain modular monolith with clear layer boundaries
      rationale: Team size, evolving domain, operational simplicity
    - decision: Consolidate backend configuration into core.config
      rationale: Eliminate duplication
    - decision: Standardize API versioning under /api/v1/
      rationale: Future-proofing
    - decision: Use SQLModel for ORM
      rationale: Already in use, reduces boilerplate
    - decision: Separate domain logic from infrastructure
      rationale: Testability and maintainability
    - decision: Extract shared frontend components
      rationale: Reduce duplication
    - decision: Complete cloud Docker profile
      rationale: Enable production deployment
    - decision: Document robot communication protocol
      rationale: Essential for development
  handoff_focus:
    - Refactor backend layers (senior-engineer)
    - Document API contracts (api-designer)
    - Review database schema (database-engineer)
  open_questions:
    - What is the exact database schema?
    - How do robots communicate (MQTT topics, WebSocket messages)?
    - What is the CI/CD pipeline?
    - What is the testing strategy?
  known_constraints:
    - Backend must remain a single deployable unit for now
    - Shared database requires careful schema management
    - Robot communication protocol must be documented
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```