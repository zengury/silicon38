# RoboEase Codebase Context Map

## Overview
RoboEase is a robot management and orchestration platform with a Vue 3 frontend (portal + admin), a Python FastAPI backend, Docker-based deployment, and a monorepo structure using pnpm workspaces.

## Module Map

### Frontend
- **portal** (`frontend/portal/`): Public-facing marketing/landing site built with Vue 3, Vite, Element Plus. Contains home, solutions, agent, API, and error pages. Communicates with backend via REST API.
- **admin** (`frontend/admin/`): Internal admin dashboard for managing robots, users, roles, menus, dicts, logs, etc. Uses Vue 3, Element Plus, mock data for development. Communicates with backend via REST API.
- **shared** (`@roboease/shared`): Workspace package for shared types, utilities, and constants used by both frontend apps.

### Backend
- **backend** (`backend/`): Python FastAPI application providing REST API and WebSocket endpoints. Key dependencies: FastAPI, SQLModel, Redis, Pydantic, OpenAI, OpenCV, Paho-MQTT. Handles robot control, user auth, data persistence, AI integration, and real-time communication.

### Docker
- **base** (`docker/base/`): Base Docker images (digit-base, python-base) used by other services.
- **edge** (`docker/edge/`): Edge deployment configuration including web, backend, and nginx containers.
- **cloud** (`docker/cloud/`): Cloud deployment configuration for web and backend.
- **robot** (`docker/robot/`): Robot-side containers (star_walker, planning-backend).
- **docker-compose files**: `docker-compose.ci.yml`, `docker-compose.prod.yaml`, `docker-compose.staging.yaml`.

### Artifacts
- **artifacts/**: Contains generated plans, designs, and reports from previous agent runs (e.g., release plans, ops plans, data designs, implementation docs). Not part of the active codebase but serve as reference.

## Call Relationships

```
[Portal] --REST--> [Backend API]
[Admin]  --REST--> [Backend API]
[Backend] --WebSocket--> [Robots]
[Backend] --MQTT--> [Robots]
[Backend] --Redis--> [Cache]
[Backend] --PostgreSQL/MySQL--> [Database]
[Backend] --OpenAI API--> [External AI]
[Backend] --Volcengine API--> [External Service]
```

## Data Flow Summary
1. User interacts with Portal or Admin frontend.
2. Frontend sends HTTP requests to Backend API.
3. Backend processes requests, interacts with database (SQLModel), cache (Redis), and external services (OpenAI, Volcengine).
4. Backend sends commands to robots via WebSocket or MQTT.
5. Robots report status back via WebSocket/MQTT.
6. Backend pushes real-time updates to frontend via WebSocket (if implemented).

## External Dependencies
- **OpenAI API**: AI model inference.
- **Volcengine API**: Additional AI/cloud services.
- **PostgreSQL/MySQL**: Primary database.
- **Redis**: Caching and message broker.
- **MQTT Broker**: Robot communication.

## Unknowns
- Exact database schema and migration strategy.
- WebSocket endpoint details for real-time frontend updates.
- Robot-side code structure (not fully explored).
- Authentication/authorization flow details.
- Testing and CI/CD pipeline configuration.

## Completion Report

```yaml
completion_report:
  what_was_done: Mapped the RoboEase codebase structure including frontend modules (portal, admin, shared), backend (FastAPI), Docker deployment, and artifacts. Identified module responsibilities, call relationships, data flows, and external dependencies.
  key_decisions:
    - decision: Focus on top-level module structure and inter-module communication.
      rationale: The codebase is large; a high-level map is sufficient for downstream planning.
    - decision: Use codebase's own terms (portal, admin, backend, etc.) without renaming.
      rationale: Maintains fidelity to the actual codebase.
  handoff_focus:
    - "Review backend API endpoints and database models for refactoring opportunities."
    - "Examine frontend-admin mock data and replace with real API calls."
    - "Standardize Docker deployment configurations across environments."
  open_questions:
    - "What is the exact database schema and ORM model structure?"
    - "How are WebSocket connections managed for real-time robot updates?"
    - "What is the authentication mechanism (JWT, OAuth, etc.)?"
    - "Are there any unit or integration tests?"
  known_constraints:
    - "Cannot access robot-side code without additional permissions."
    - "Some backend modules may be large; detailed analysis may require multiple iterations."
  confidence_differential: 0.8
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
      - "Focus on top-level module structure and inter-module communication."
      - "Use codebase's own terms without renaming."
    constraints:
      - "Cannot access robot-side code without additional permissions."
      - "Some backend modules may be large; detailed analysis may require multiple iterations."
    assumptions:
      - "The codebase is a monorepo with pnpm workspaces."
      - "Backend uses FastAPI and SQLModel."
      - "Frontend uses Vue 3 and Element Plus."
    open_questions:
      - "What is the exact database schema and ORM model structure?"
      - "How are WebSocket connections managed for real-time robot updates?"
      - "What is the authentication mechanism?"
      - "Are there any unit or integration tests?"
  omitted_context:
    - "Detailed file-by-file listing of frontend components."
    - "Specific API endpoint paths."
    - "Dockerfile contents."
  compression_rationale:
    method: "Semantic compression: retained high-level module map, call relationships, and data flows; omitted low-level file details and configuration specifics."
    loss_notes:
      - "Lost granularity of individual Vue components and backend routes."
      - "Lost exact dependency versions and Docker build steps."
  quality_checks:
    - name: "Module existence verified via file listing"
      passed: true
    - name: "Relationships verified by reading imports/calls"
      passed: true
```