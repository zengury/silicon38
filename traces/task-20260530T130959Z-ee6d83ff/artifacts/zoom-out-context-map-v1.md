# RoboEase Codebase Context Map

## Overview
RoboEase is a multi-module system for robot management, consisting of a Vue.js frontend (portal and admin), a Python FastAPI backend, Docker deployment infrastructure, and supporting artifacts. The system provides robot control, monitoring, and management capabilities.

## Module Map

### Frontend
- **portal** (`frontend/portal/`): Public-facing Vue 3 + TypeScript SPA for robot showcase, solution pages, and API documentation. Uses Vue Router, Element Plus, Axios, and Vite.
- **admin** (`frontend/admin/`): Internal admin panel (based on vue3-element-admin) for managing robots, users, roles, menus, dicts, logs, and notices. Uses Vue 3, TypeScript, UnoCSS, and mock data.

### Backend
- **backend** (`backend/`): Python FastAPI server providing REST APIs for robot control, authentication, data management, and integration with external services (Redis, MQTT, OpenAI, Volcengine, etc.).

### Docker
- **docker/edge/**: Edge deployment configuration with Nginx reverse proxy, web frontend, and backend services.
- **docker/robot/**: Robot-side services including star_walker and planning-backend.
- **docker/cloud/**: Cloud deployment configuration.
- **docker/base/**: Base Docker images (digit-base, python-base).
- **docker/docker-compose.ci.yml**: CI compose file.
- **docker/docker-compose.prod.yaml**: Production compose file.
- **docker/deploy-build.sh**: Deployment build script.

### Artifacts
- **artifacts/**: Contains release plans, implementation plans, ops plans, data designs, and observability designs (v1-v8). These are planning documents, not runtime code.

## Call Relationships
- **portal** → Axios → **backend** (REST API)
- **admin** → Axios → **backend** (REST API)
- **backend** → Redis (external cache)
- **backend** → MQTT (external message broker)
- **backend** → OpenAI API (external LLM)
- **backend** → Volcengine API (external service)
- **backend** → MySQL/PostgreSQL (external databases)
- **backend** → paramiko (SSH for robot control)
- **backend** → websockets (real-time communication)
- **Docker edge** → Nginx → **portal** and **backend**
- **Docker robot** → **star_walker** and **planning-backend** (internal services)

## Data Flows
1. User → portal/admin → HTTP → backend → (Redis, MQTT, DB, external APIs) → response
2. Robot → MQTT → backend → (DB, WebSocket) → portal/admin
3. Backend → SSH → robot devices for command execution

## External Dependencies
- **Redis**: Caching and session store
- **MQTT (paho-mqtt)**: Robot messaging
- **OpenAI API**: LLM integration
- **Volcengine API**: Chinese cloud services
- **MySQL/PostgreSQL**: Persistent storage (via pymysql/psycopg2-binary)
- **OpenCV**: Image processing
- **Pillow**: Image manipulation
- **PyJWT**: Authentication tokens
- **Snowflake ID generation**: Unique IDs

## Key Config Files
- `frontend/portal/package.json`, `vite.config.ts`, `tsconfig.json`
- `frontend/admin/package.json`, `uno.config.ts`, `tsconfig.json`
- `backend/requirements.txt`
- `docker/docker-compose.ci.yml`, `docker/docker-compose.prod.yaml`
- `docker/edge/nginx/nginx.conf`

## Unknowns
- Exact backend module structure (not fully explored)
- Robot-side service details (star_walker, planning-backend)
- Authentication flow specifics
- Database schema
- Deployment environment specifics (cloud provider, CI/CD pipeline)
