# RoboEase Codebase Context Map

## Overview
RoboEase is a multi-tenant robot management platform with a FastAPI backend, Vue 3 frontends (admin portal and public portal), and Docker-based deployment. It provides robot control, monitoring, and AI agent capabilities.

## Module Map

### Backend (`backend/`)
- **`core/`** – Application configuration, settings, and dependency injection. Reads from `.env` via `core.config.Settings`.
- **`api/`** – FastAPI route handlers organized by domain (auth, robot, user, etc.). Prefix: `/api/v1`.
- **`infrastructure/`** – Database entities, connection management, and external service integrations.
  - `infrastructure/db/entities.py` – SQLModel entity definitions (UserEntity, RobotEntity, etc.).
  - `infrastructure/db/connection.py` – Database engine and session factory.
- **`services/`** – Business logic layer, called by API handlers.
- **`schemas/`** – Pydantic models for request/response validation.
- **`config/`** – Legacy config files (`setting.py`, `dbconfig.py`). New code should use `core.config`.
- **`db/`** – Backward-compatibility re-exports from `infrastructure/db/`.

### Frontend – Admin (`frontend/admin/`)
- Vue 3 + Vite + TypeScript. Uses Element Plus UI.
- **`src/views/`** – Page components (dashboard, robot management, user management, etc.).
- **`src/api/`** – API client modules.
- **`src/router/`** – Vue Router configuration.
- **`mock/`** – Mock data for development.

### Frontend – Portal (`frontend/portal/`)
- Vue 3 + Vite + TypeScript. Public-facing landing page.
- **`src/views/home/`** – Home page sections (Hero, Features, Agent Architecture, etc.).
- **`src/views/solutions/`** – Industry solutions page.
- **`src/views/agent/`** – Agent template library page.
- **`src/api/`** – API client modules.

### Docker (`docker/`)
- **`edge/`** – Development/edge deployment compose file and Dockerfiles for web, backend, nginx.
- **`cloud/`** – Cloud deployment Dockerfiles.
- **`robot/`** – Robot-specific Dockerfiles (star_walker, planning-backend).
- **`base/`** – Base images (digit-base, python-base).
- **`docker-compose.prod.yaml`** – Production compose using GHCR images.
- **`docker-compose.ci.yml`** – CI compose.

### Artifacts (`artifacts/`)
- Historical design documents, release plans, and implementation notes from previous refactoring iterations.

## Call Relationships

```
[User Browser] --> [Nginx] --> [FastAPI Backend] --> [MySQL/PostgreSQL]
                                    |
                                    +--> [Redis]
                                    +--> [MQTT Broker] --> [Robots]
                                    +--> [OpenAI / Volcengine API] (external)
```

- **Frontend -> Backend**: HTTP REST calls to `/api/v1/*`.
- **Backend -> Database**: SQLModel ORM via `infrastructure/db/connection.py`.
- **Backend -> External APIs**: OpenAI, Volcengine (AI services).
- **Backend -> Robots**: MQTT (paho-mqtt) for command/control.
- **Backend -> Redis**: Caching and session storage.

## Data Flows

1. **User Authentication**: Login -> JWT token issued -> token used in subsequent requests.
2. **Robot Control**: User action -> API -> MQTT message -> robot executes -> status update via MQTT -> API -> frontend.
3. **AI Agent**: User prompt -> API -> OpenAI/Volcengine -> response returned.
4. **Monitoring**: Robot telemetry -> MQTT -> backend stores in DB -> frontend displays.

## External Dependencies
- **Database**: MySQL (primary) or PostgreSQL (optional via psycopg2-binary).
- **Cache**: Redis.
- **Message Broker**: MQTT (paho-mqtt).
- **AI APIs**: OpenAI, Volcengine.
- **Other**: PyJWT, Cryptography, OpenCV, Pandas, Paramiko (SSH).

## Key Configuration
- `backend/core/config/settings.py` – Central settings class reading from environment.
- `backend/.env` – Environment variables (not in repo).
- `docker/edge/.env` – Docker compose environment overrides.

## Unknowns
- Exact database schema (tables, relationships) beyond entity definitions.
- Detailed MQTT topic structure and message formats.
- Deployment topology for edge vs. cloud.
- Testing strategy and coverage.
- CI/CD pipeline details.

## Completion Report

```yaml
what_was_done: Mapped the RoboEase codebase structure, module responsibilities, call relationships, data flows, and external dependencies based on file listing and key file inspection.
key_decisions:
  - decision: Focus on top-level module boundaries and external integrations.
    rationale: The codebase is large; zoom-out role should provide a high-level map for downstream agents.
  - decision: Use codebase's own module names (core, infrastructure, api, services).
    rationale: Quality criteria require domain vocabulary.
handoff_focus:
  - Database schema and entity relationships.
  - MQTT topic design and message flow.
  - API route inventory and authentication flow.
  - Deployment configuration and environment variables.
open_questions:
  - What is the exact database schema (tables, relationships)?
  - How are MQTT topics structured?
  - What is the CI/CD pipeline?
  - What is the testing strategy?
known_constraints:
  - Only file listing and key files were read; no full code traversal.
  - Some modules may have deeper structure not captured.
confidence_differential: 0.7
dissent_if_alone: null
iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read: []
    handoffs_read: []
  retained_context:
    decisions:
      - Focus on top-level module boundaries and external integrations.
      - Use codebase's own module names.
    constraints:
      - Only file listing and key files were read; no full code traversal.
      - Some modules may have deeper structure not captured.
    assumptions:
      - The codebase is a multi-tenant robot management platform.
      - MQTT is used for robot communication.
      - JWT is used for authentication.
    open_questions:
      - What is the exact database schema?
      - How are MQTT topics structured?
      - What is the CI/CD pipeline?
      - What is the testing strategy?
  omitted_context:
    - Detailed file contents beyond key files.
    - Historical artifact contents (release plans, etc.).
    - Frontend component hierarchy.
  compression_rationale:
    method: High-level abstraction focusing on module boundaries, external dependencies, and data flows. Detailed implementation details omitted to keep map concise.
    loss_notes:
      - Frontend component tree not mapped.
      - Backend service layer internal structure not detailed.
      - Database schema not extracted.
  quality_checks:
    - name: Module names match codebase
      passed: true
    - name: Relationships verified by reading imports
      passed: true
    - name: External dependencies labeled
      passed: true
    - name: Map is concise and relevant
      passed: true
```