# Architecture Decision Record: RoboEase Refactoring

## Context
RoboEase is a multi-tenant robot management platform with a FastAPI backend, Vue 3 frontends (admin and portal), and Docker-based deployment. The codebase has grown organically, with legacy configuration modules (`config/setting.py`, `config/dbconfig.py`) and backward-compatibility re-exports (`db/database.py`). The zoom-out context map identified the need for architectural clarity, especially around module boundaries, data flows, and deployment topology.

## Decision
Adopt a **Modular Monolith** architecture with clear domain boundaries, enforced by package structure and dependency rules. The system will remain a single deployable unit but with internal modules that could be extracted into microservices if needed.

## Rationale
- Team size is small (<10 developers), making microservices overhead unjustified.
- Domain boundaries are still emerging; a modular monolith allows refactoring without distributed system complexity.
- The existing codebase already has a layered structure (api -> services -> infrastructure) that can be evolved into domain modules.
- Deployment is currently a single Docker compose stack; splitting would require significant DevOps investment.
- The zoom-out map shows clear data flows (REST, MQTT, DB) that fit a monolith with well-defined internal interfaces.

## Alternatives Considered
1. **Microservices**: Rejected due to team size, operational complexity, and unclear domain boundaries. Would increase deployment, monitoring, and debugging overhead.
2. **Serverless (AWS Lambda)**: Rejected because the system has long-running MQTT connections and stateful robot sessions that don't fit Lambda's execution model.
3. **Event-Driven Architecture**: Considered for robot telemetry but rejected as premature; the current request-response pattern works and can evolve later.

## Consequences
- **Positive**: Simpler deployment, easier debugging, faster development velocity, lower operational cost.
- **Negative**: Risk of tight coupling if domain boundaries are not enforced; scaling requires vertical scaling or eventual extraction.
- **Mitigation**: Enforce strict module boundaries via Python package conventions and linting rules (e.g., no imports from `api` to `infrastructure` directly).

## Load-Bearing Decisions

### 1. Module Structure
- **`core/`**: Configuration, settings, dependency injection. No business logic.
- **`api/`**: FastAPI route handlers. Thin layer; delegates to services.
- **`services/`**: Business logic. Orchestrates infrastructure calls.
- **`infrastructure/`**: Database entities, external integrations (MQTT, Redis, AI APIs).
- **`schemas/`**: Pydantic models for API validation.
- **`config/`**: Legacy config; migrate to `core/` over time.
- **`db/`**: Legacy re-exports; remove after migration.

### 2. Data Flow
- **User Request**: Browser -> Nginx -> FastAPI -> Service -> Infrastructure (DB/MQTT/External API) -> Response.
- **Robot Telemetry**: Robot -> MQTT Broker -> Backend MQTT listener -> Service -> DB -> WebSocket push to frontend.
- **AI Agent**: User prompt -> API -> Service -> OpenAI/Volcengine -> Response.

### 3. Technology Choices
- **Database**: MySQL (primary) with SQLModel ORM. PostgreSQL supported via psycopg2.
- **Cache**: Redis for sessions, rate limiting, and MQTT message deduplication.
- **Message Broker**: MQTT (paho-mqtt) for robot communication. Topics structured as `{tenant_id}/{robot_id}/{command|telemetry|status}`.
- **Authentication**: JWT with HS256. Tokens stored in Redis for revocation.
- **AI APIs**: OpenAI and Volcengine via dedicated service classes.

### 4. Deployment
- **Edge**: Single Docker compose with all services (backend, frontends, nginx, MySQL, Redis, MQTT broker).
- **Cloud**: Similar but with separate databases and load balancing.
- **CI/CD**: GitHub Actions (inferred from `.github/` directory).

### 5. Failure Modes
- **Database Down**: Backend returns 503; retry with exponential backoff.
- **MQTT Broker Down**: Robot commands queued in Redis; retry on reconnect.
- **AI API Unavailable**: Fallback to cached responses or graceful degradation.
- **Redis Down**: Sessions fall back to JWT validation; rate limiting disabled.

## Downstream Constraints
- **Senior Engineer**: Must implement domain modules with clear interfaces; no circular dependencies.
- **API Designer**: Must follow RESTful conventions under `/api/v1/`; use Pydantic schemas.
- **Database Engineer**: Must align with SQLModel entities in `infrastructure/db/entities.py`; document schema.
- **DevOps Engineer**: Must maintain single Docker compose for edge; prepare for future service extraction.

## Open Questions
- Exact MQTT topic structure and message formats need documentation.
- Testing strategy (unit vs integration) needs definition.
- CI/CD pipeline details need confirmation.

## Completion Report

```yaml
what_was_done: Designed the target architecture for RoboEase refactoring, including module boundaries, data flows, technology choices, failure modes, and downstream constraints.
key_decisions:
  - decision: Adopt Modular Monolith architecture
    rationale: Team size, operational simplicity, and emerging domain boundaries favor monolith over microservices.
  - decision: Enforce strict module boundaries via package conventions
    rationale: Prevent tight coupling and enable future extraction.
  - decision: Keep existing technology stack (FastAPI, Vue 3, MySQL, Redis, MQTT)
    rationale: No compelling reason to change; stack is proven for this use case.
handoff_focus:
  - Senior Engineer: Implement domain modules with clear interfaces.
  - API Designer: Define RESTful API contracts under /api/v1/.
  - Database Engineer: Document and align schema with SQLModel entities.
  - DevOps Engineer: Maintain single Docker compose; prepare for extraction.
open_questions:
  - What is the exact MQTT topic structure?
  - What is the testing strategy?
  - What are the CI/CD pipeline details?
known_constraints:
  - Legacy config modules (config/setting.py, config/dbconfig.py) need migration.
  - Backward-compatibility re-exports (db/database.py) must be maintained during transition.
  - Team size limits ability to manage microservices complexity.
confidence_differential: 0.8
dissent_if_alone: null
iteration_context: null
```
