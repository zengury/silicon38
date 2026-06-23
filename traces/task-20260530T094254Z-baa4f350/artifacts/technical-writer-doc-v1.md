# RoboEase Backend Refactoring — Developer Documentation

## Overview

This document describes the refactored RoboEase backend architecture, which adopts a **Modular Monolith** pattern with **Domain-Driven Design (DDD)** bounded contexts. The goal is to improve maintainability, testability, and separation of concerns while keeping the deployment simple for a small team (<10 developers).

## Architecture

### Modular Monolith with DDD Bounded Contexts

The backend is organized into domain modules, each with its own models, repositories, services, and API routes. All modules share a common `core/` module for cross-cutting concerns.

```
backend/
├── core/               # Shared kernel (config, security, exceptions, DI)
├── modules/
│   ├── auth/           # Authentication & authorization
│   ├── users/          # User management
│   ├── robots/         # Robot management
│   ├── agents/         # Agent templates
│   ├── enterprises/    # Enterprise management
│   ├── notifications/  # Notifications
│   ├── logs/           # Audit logs
│   └── ...
├── db/                 # Database session, migrations, repositories
├── api/                # API routes (versioned under /api/v1)
└── main.py
```

### Ports and Adapters (Hexagonal Architecture)

Domain logic is separated from infrastructure using the **ports and adapters** pattern:

- **Ports**: Abstract interfaces (e.g., `Repository`, `UnitOfWork`) defined in the domain layer.
- **Adapters**: Concrete implementations (e.g., `SQLModelRepository`, `FastAPIAdapter`) in the infrastructure layer.

This allows swapping databases, message brokers, or web frameworks without changing business logic.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Modular Monolith** | Simpler than microservices for a small team; easy to deploy and debug. |
| **DDD Bounded Contexts** | Clear boundaries between domains reduce cognitive load and merge conflicts. |
| **Ports and Adapters** | Domain logic remains testable without infrastructure dependencies. |
| **Centralized Configuration** | `core.config.settings` loads all environment variables in one place. |
| **Standardized Error Handling** | Custom exception hierarchy with FastAPI exception handlers ensures consistent API error responses. |
| **API Versioning** | All routes under `/api/v1/` allow future breaking changes without disrupting clients. |

## Prerequisites

- Python 3.10+
- FastAPI
- SQLModel (ORM)
- MySQL or SQLite (for testing)
- Redis (for caching/sessions)
- MQTT broker (for robot communication)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/roboease.git
cd roboease
```

### 2. Set up environment variables

Copy the example env file and adjust as needed:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | MySQL connection string (e.g., `mysql+pymysql://user:pass@localhost:3306/raas`) |
| `REDIS_HOST` | Redis host |
| `REDIS_PORT` | Redis port |
| `MQTT_BROKER` | MQTT broker address |
| `JWT_SECRET_KEY` | Secret key for JWT token signing |
| `JWT_ALGORITHM` | JWT signing algorithm (default: HS256) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 1440) |

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the development server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/api/v1/`. Interactive docs at `http://localhost:8000/docs`.

## API Usage

### Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

#### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Example: List Users

```bash
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_active": true
    }
  ],
  "total": 1
}
```

### Example: Create a Robot

```bash
curl -X POST http://localhost:8000/api/v1/robots/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Robot-1", "model": "R2D2", "status": "idle"}'
```

**Response:**

```json
{
  "id": 42,
  "name": "Robot-1",
  "model": "R2D2",
  "status": "idle",
  "created_at": "2025-06-01T12:00:00Z"
}
```

## Repository Pattern

All database access goes through repositories. The base class `BaseCRUDRepository` provides standard CRUD operations:

```python
from db.repositories.base_repository import BaseCRUDRepository
from modules.users.models import User

class UserRepository(BaseCRUDRepository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    def find_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter(User.email == email).first()
```

## Error Handling

Standardized error responses follow this format:

```json
{
  "detail": {
    "code": "USER_NOT_FOUND",
    "message": "User with id 42 not found"
  }
}
```

Common error codes:

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

## Testing

### Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database (see `core.config.settings` for the `TEST_DATABASE_URL` override).

### Writing Tests

Example test for a repository:

```python
import pytest
from sqlmodel import Session, SQLModel, create_engine
from modules.users.models import User
from modules.users.repositories import UserRepository

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_create_user(session):
    repo = UserRepository(session)
    user = User(username="test", email="test@example.com")
    created = repo.create(user)
    assert created.id is not None
    assert created.username == "test"
```

## Deployment

### Docker Compose (Edge/Development)

```bash
docker compose -f docker/edge/docker-compose.yaml up -d
```

### Docker Compose (Production)

```bash
docker compose -f docker/docker-compose.prod.yaml up -d
```

See `docker/README.md` for detailed deployment instructions.

## Known Limitations

- **Direct Session usage**: ~40 remaining calls in 11 services still use `Session(engine)` directly. These are documented as technical debt and will be migrated to the repository pattern incrementally.
- **MD5 password hashing**: Used for backward compatibility. A migration to bcrypt/Argon2 is planned.
- **Cross-entity joins**: Some services (e.g., `enterprise_service.py`) perform joins using direct `Session` access. Future iterations may introduce query services.

## Changelog (v3.0.0)

- **Users can now** authenticate using JWT tokens with configurable expiry.
- **Users can now** manage robots, agents, and enterprises through a unified API.
- **Developers can now** extend the system by adding new bounded context modules following the established pattern.
- **API responses** now follow a consistent error format with machine-readable codes.
- **Database access** is now centralized through repositories, improving testability.

## Completion Report

```yaml
completion_report:
  what_was_done: Wrote developer documentation for the RoboEase backend refactoring (v3.0.0). Covers architecture overview, key decisions, prerequisites, getting started guide, API usage examples, repository pattern, error handling, testing, deployment, known limitations, and changelog.
  key_decisions:
    - decision: Documented the Modular Monolith with DDD bounded contexts as the primary architectural pattern.
      rationale: Provides clear separation of concerns while keeping deployment simple for a small team.
    - decision: Included runnable code examples for authentication, listing users, and creating robots.
      rationale: Ensures documentation is verifiable and useful for onboarding.
    - decision: Documented known limitations (direct Session usage, MD5 hashing) as technical debt.
      rationale: Sets accurate expectations for developers and prioritizes future work.
  handoff_focus:
    - Review documentation for accuracy against the actual codebase.
    - Verify that all API endpoints and response formats match the implementation.
    - Consider adding more detailed API reference (OpenAPI spec) in a separate document.
  open_questions:
    - Should we include a full API reference (OpenAPI) in this document or keep it separate?
    - Is the testing section sufficient, or should we add more examples?
  known_constraints:
    - Team size is small (<10 developers), simple patterns preferred.
    - Backend uses FastAPI with SQLModel ORM.
    - Existing SQLModel entities couple domain and persistence; full separation requires phased migration.
    - Backend API prefix is /api/v1.
  confidence_differential: 0.90
  dissent_if_alone: null
  iteration_context: null
```
