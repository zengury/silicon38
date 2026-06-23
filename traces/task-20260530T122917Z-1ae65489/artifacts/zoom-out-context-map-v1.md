# RoboEase Codebase Context Map

## Overview
RoboEase is a robot-as-a-service (RAAS) management platform with a FastAPI backend, Vue 3 frontends (admin portal and public website), and Docker-based deployment for edge and cloud environments.

## Module Map

### Backend (`backend/`)
- **`core/`** — Application core: configuration, security, dependencies, and base classes.
  - `core/config/` — Settings management (reads `.env`).
  - `core/security/` — JWT authentication, password hashing.
  - `core/dependencies/` — FastAPI dependency injection (e.g., `get_current_user`).
- **`api/`** — FastAPI route handlers, organized by domain.
  - `api/v1/` — Versioned API endpoints.
- **`infrastructure/`** — Data access and external integrations.
  - `infrastructure/db/` — Database engine, entities (SQLModel), repositories.
  - `infrastructure/external/` — Third-party API clients (e.g., OpenAI, Volcengine).
- **`domain/`** — Business logic, services, and domain models.
- **`schemas/`** — Pydantic request/response schemas.
- **`db/`** — Legacy re-exports (backward compatibility).
- **`config/`** — Legacy config files (dbconfig.py, setting.py).

### Frontend — Admin (`frontend/admin/`)
- Vue 3 + TypeScript + Vite, based on vue3-element-admin.
- Manages robots, users, roles, menus, system settings.
- Mock data in `mock/` for development.

### Frontend — Portal (`frontend/portal/`)
- Vue 3 + TypeScript + Vite, public-facing website.
- Landing page, solutions, agent templates, API demo.

### Docker (`docker/`)
- **`docker/edge/`** — Edge deployment (local dev, on-premise).
  - `docker/edge/web/` — Portal frontend container.
  - `docker/edge/backend/` — Backend API container.
  - `docker/edge/nginx/` — Reverse proxy with SSL.
- **`docker/cloud/`** — Cloud deployment (production).
- **`docker/robot/`** — Robot-side containers (star_walker, planning-backend).
- **`docker/base/`** — Base images (Python, digit-base).
- `docker/docker-compose.prod.yaml` — Production compose (GHCR images).
- `docker/deploy-build.sh` — Build and push script.

### Artifacts (`artifacts/`)
- Historical planning and implementation documents (v1–v7).

## Call Relationships

```
[Portal Frontend] --HTTP--> [Nginx] --proxy--> [Backend API]
[Admin Frontend]  --HTTP--> [Nginx] --proxy--> [Backend API]
[Backend API]     --SQL-->  [MySQL]
[Backend API]     --Redis--> [Redis]
[Backend API]     --MQTT--> [Robots]
[Backend API]     --HTTP--> [External APIs] (OpenAI, Volcengine, etc.)
[Robots]          --WebSocket--> [Backend API]
```

## Data Flows

1. **User Authentication**: Frontend -> POST /api/v1/auth/login -> JWT token -> subsequent requests with Bearer token.
2. **Robot Management**: Admin creates/edits robots via API -> stored in MySQL -> robot connects via MQTT/WebSocket.
3. **Task Execution**: User submits task -> backend dispatches to robot via MQTT -> robot reports status via WebSocket.
4. **External AI**: Backend calls OpenAI/Volcengine APIs for LLM features.

## External Dependencies
- **MySQL** — Primary database (via SQLModel/SQLAlchemy).
- **Redis** — Caching and session store.
- **MQTT Broker** — Communication with robots.
- **OpenAI API** — LLM services.
- **Volcengine API** — Additional AI services.
- **Nginx** — Reverse proxy and SSL termination.

## Key Configuration
- `backend/core/config/` — Central settings (reads `.env`).
- `docker/edge/.env` — Edge environment variables.
- `docker/docker-compose.prod.yaml` — Production environment.

## Unknowns
- Exact database schema (tables, relationships) — need to inspect entities.
- Detailed robot communication protocol (MQTT topics, WebSocket messages).
- Deployment topology for cloud vs. edge (differences in scaling, networking).
- Testing strategy and coverage.
- CI/CD pipeline configuration.