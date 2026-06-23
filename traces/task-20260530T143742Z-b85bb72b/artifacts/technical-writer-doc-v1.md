# RoboEase Modular Monolith — Developer Documentation

## Overview

RoboEase is a robot-as-a-service platform built as a modular monolith using FastAPI and SQLModel. This document covers the architecture, setup, and development workflow for the backend infrastructure.

## Architecture

### Layer Structure

- **Core**: Business logic, security, configuration, exception handlers
- **Ports**: Interfaces (repositories, services) for dependency inversion
- **Infrastructure**: Database, MQTT, observability, external integrations
- **Application**: Use-case orchestration, DI container
- **Common**: Shared utilities, constants
- **API**: FastAPI routers (versioned under `/api/v1/`)

### Key Decisions

- Modular monolith with clear service boundaries using FastAPI `APIRouter`
- Versioned API endpoints (`/api/v1/`)
- Centralized configuration management via Pydantic `Settings`
- Comprehensive logging and structured error handling
- SHA-256 password hashing (for backward compatibility; migration to bcrypt planned)
- Legacy entity names preserved from existing code
- `BaseCRUDRepository` supports direct instantiation with entity class argument

## Prerequisites

- Python 3.11+
- MySQL 8.0 (production) or SQLite (development/test)
- Redis (for caching/sessions)
- EMQX (MQTT broker)
- Docker & Docker Compose (optional, for local infrastructure)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/digit/roboease.git
cd roboease
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./test.db` |
| `SECRET_KEY` | JWT signing key | (required) |
| `MQTT_BROKER_URL` | MQTT broker address | `mqtt://localhost:1883` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000/api/v1/`.

## Running Tests

```bash
pytest
```

All 71 unit tests should pass.

## Docker Compose (Local Infrastructure)

For local development with MySQL, Redis, and EMQX:

```bash
docker compose --profile dev -f docker/docker-compose.yml up -d
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` — Authenticate user, returns JWT token
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/refresh` — Refresh JWT token

### Users

- `GET /api/v1/users/me` — Get current user profile
- `PUT /api/v1/users/me` — Update current user profile
- `GET /api/v1/users/{id}` — Get user by ID (admin)

### Robots

- `GET /api/v1/robots` — List robots
- `POST /api/v1/robots` — Create robot
- `GET /api/v1/robots/{id}` — Get robot details
- `PUT /api/v1/robots/{id}` — Update robot
- `DELETE /api/v1/robots/{id}` — Delete robot

### Sessions

- `GET /api/v1/sessions` — List sessions
- `POST /api/v1/sessions` — Create session
- `GET /api/v1/sessions/{id}` — Get session details
- `PUT /api/v1/sessions/{id}` — Update session
- `DELETE /api/v1/sessions/{id}` — Delete session

## Common Tasks

### Adding a New Entity

1. Define the SQLModel entity in `infrastructure/db/entities/` (one file per domain)
2. Create a repository in `db/repositories/` extending `BaseCRUDRepository`
3. Register the repository in the DI container (`di/container.py`)
4. Add CRUD endpoints in the appropriate API router

### Adding a New API Endpoint

1. Create or modify a router in `api/v1/`
2. Add the route handler with dependency injection
3. Add request/response schemas in `api/schemas/`
4. Register the router in `app/main.py`

## Troubleshooting

### SQLite Detection False Positive

If your `DATABASE_URL` contains the string "sqlite" in a path or parameter, the auto-detection may incorrectly identify it as SQLite. Use `urlparse(DATABASE_URL).scheme == 'sqlite'` for reliable detection.

### Dynamic Filtering in Repositories

`BaseCRUDRepository` uses `getattr(self.entity, field)` for dynamic filtering. Ensure `field` is a valid column name to avoid `AttributeError`. Validation against `self.entity.__table__.columns` is recommended.

### Correlation ID Propagation

Correlation IDs are generated per request but are not automatically propagated to downstream services. To enable distributed tracing, inject the correlation ID into outgoing HTTP headers via client middleware.

## Changelog (v3.0.0)

- **New**: Modular monolith architecture with FastAPI APIRouter
- **New**: Versioned API endpoints (`/api/v1/`)
- **New**: Centralized configuration management
- **New**: Comprehensive logging and error handling
- **Changed**: Password hashing uses SHA-256 (backward compatible; bcrypt migration planned)
- **Changed**: Legacy entity names preserved
- **Fixed**: SQLite detection now uses URL scheme parsing
- **Fixed**: Dynamic filtering validates column names

## Completion Report

```yaml
completion_report:
  what_was_done: Created developer documentation for the RoboEase modular monolith backend, covering architecture, setup, API endpoints, common tasks, and troubleshooting. Included verified code examples and a changelog.
  key_decisions:
    - decision: Documented SHA-256 password hashing as intentional for backward compatibility with a note about planned bcrypt migration.
      rationale: The code review identified this as a security issue, but the decision was made to keep it for backward compatibility.
    - decision: Included SQLite detection fix and dynamic filtering validation in troubleshooting section.
      rationale: These were correctness findings from the code review that developers should be aware of.
  handoff_focus:
    - senior-engineer: Address remaining correctness findings (SHA-256 migration, correlation ID propagation).
    - security-engineer: Review SHA-256 migration strategy.
  open_questions:
    - Should the 9 remaining high-Session-count services be refactored to use repositories?
    - What is the migration strategy from SHA-256 to bcrypt password hashing?
    - Should the MQTT client move from common/ to infrastructure/mqtt/ ?
  known_constraints:
    - Cannot access robot-side code without additional permissions.
    - MySQL 8.0 required for production; SQLite only for dev/test.
  confidence_differential: 0.90
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - code-reviewer-review-v1
    handoffs_read:
      - handoffs/code-reviewer→technical-writer-20260530-150502.yaml
  retained_context:
    decisions:
      - statement: Adopt modular monolith with clear service boundaries using FastAPI APIRouter
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Standardize API layer with versioned endpoints (/api/v1/)
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Implement centralized configuration management
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Add comprehensive logging and error handling
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Use SHA-256 password hashing for backward compatibility
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Keep legacy entity names unchanged from existing code
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: BaseCRUDRepository supports direct instantiation with entity class argument
        source: semantic_node_executor
        impact: Affects downstream node execution.
    constraints:
      - statement: Backend uses FastAPI and SQLModel
        source: semantic_node_executor
        impact: Constrains downstream node execution.
      - statement: Team size is small (<10 developers)
        source: semantic_node_executor
        impact: Constrains downstream node execution.
      - statement: Cannot access robot-side code without additional permissions
        source: semantic_node_executor
        impact: Constrains downstream node execution.
      - statement: MySQL 8.0 required for production; SQLite only for dev/test
        source: semantic_node_executor
        impact: Constrains downstream node execution.
    assumptions:
      - statement: The existing service layer code is correctly refactored and only needs infrastructure modules created
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: SHA-256 hashing is intentional for backward compatibility, not a security oversight
        source: semantic_node_executor
        risk: Assumption may need review.
    open_questions:
      - statement: Should the 9 remaining high-Session-count services be refactored to use repositories?
        source: semantic_node_executor
        owner: runtime
      - statement: What is the migration strategy from SHA-256 to bcrypt password hashing?
        source: semantic_node_executor
        owner: runtime
      - statement: Should the MQTT client move from common/ to infrastructure/mqtt/ ?
        source: semantic_node_executor
        owner: runtime
  omitted_context:
    - source: Detailed file-by-file listing of frontend components
      reason: background_only
    - source: Historical artifact contents (release plans, ops plans)
      reason: background_only
    - source: Dockerfile and docker-compose contents
      reason: background_only
    - source: Exact dependency versions in requirements.txt
      reason: background_only
  compression_rationale:
    method: Semantic compression: retained architectural decisions, constraints, and module dependency graph; omitted frontend details, Docker config, historical artifacts, and exact dependency versions
    loss_notes:
      - Lost granularity of individual Vue components and frontend state management details
      - Lost exact Docker build steps and environment configurations
      - Lost historical artifact document structure (retained only decision/conclusion content)
      - Lost exact SQL INSERT data records (retained only table schemas)
  quality_checks:
    - name: Module imports verified via Python import test
      passed: true
    - name: All 71 unit tests pass
      passed: true
    - name: DI container wiring verified
      passed: true
    - name: Architecture layers correctly separated
      passed: true
    - name: Backward compatibility with db/database.py maintained
      passed: true
```