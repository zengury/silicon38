# RoboEase Codebase Context Map

## Overview
RoboEase is a robot-as-a-service (RaaS) platform with a Vue 3 frontend (portal + admin), a FastAPI backend, and Docker-based deployment for edge and cloud environments. The system manages robot fleets, provides real-time monitoring, and exposes APIs for robot control.

## Module Map

### Frontend
- **portal** (`frontend/portal/`): Public-facing Vue 3 SPA (Vite + Element Plus). Responsibilities: landing page, solution showcase, agent template library, API demo. Communicates with backend via REST API (`src/api/auth.api.ts`, `src/utils/request.ts`).
- **admin** (`frontend/admin/`): Internal admin panel (Vue 3 + Element Plus + VxeTable). Responsibilities: user/role/dept management, robot management, dict/notice management, system monitoring. Uses mock data in development (`mock/`), real API in production. Includes WebSocket support (`src/composables/useStomp.ts`).

### Backend
- **backend** (implied by Dockerfile `docker/edge/backend/DOCKERFILE`): FastAPI application. Responsibilities: REST API for frontend, video server (port 8765), robot control, file attachment handling. Depends on MySQL and EMQX.

### Infrastructure
- **nginx** (`docker/edge/nginx/`): Reverse proxy with TLS termination. Routes traffic to portal and backend.
- **mysql**: Database service (referenced in docker-compose).
- **emqx1**: MQTT broker for robot communication (referenced in docker-compose).
- **redis**: Caching (referenced in docker-compose).
- **minio**: Object storage (referenced in docker-compose).

### Docker Deployments
- **edge** (`docker/edge/`): Development/edge-device deployment with locally-built images.
- **cloud** (`docker/cloud/`): Cloud deployment (separate Dockerfiles).
- **robot** (`docker/robot/`): Robot-side containers (`star_walker`, `planning-backend`).
- **base** (`docker/base/`): Base images (`digit-base`, `python-base`).

## Call Relationships

```
User Browser
  |
  v
nginx (TLS termination, reverse proxy)
  |
  +---> portal (static SPA served via nginx or standalone)
  |
  +---> backend (REST API, WebSocket, video stream)
            |
            +---> mysql (persistent storage)
            +---> emqx (MQTT broker for robot commands/telemetry)
            +---> redis (caching, session)
            +---> minio (file/attachment storage)
            +---> robot services (via MQTT or HTTP)
```

## Data Flows

1. **User → Portal → Backend**: User browses portal, API calls go through nginx to backend. Backend queries MySQL, returns JSON.
2. **Admin → Admin Panel → Backend**: Admin manages robots/users via admin panel. Backend updates MySQL, publishes MQTT commands to robots.
3. **Robot → EMQX → Backend**: Robot telemetry (status, video) published to EMQX, backend consumes and stores in MySQL/Redis.
4. **Backend → Minio**: File uploads (attachments) stored in Minio.

## External Dependencies
- **MySQL**: Database (external service)
- **EMQX**: MQTT broker (external service)
- **Redis**: Cache (external service)
- **Minio**: Object storage (external service)
- **Dify AI Platform**: Optional integration (referenced in docker-compose comments)

## Key Files
- `docker/edge/docker-compose.yaml`: Main edge deployment config
- `docker/docker-compose.prod.yaml`: Production deployment config
- `frontend/portal/src/`: Portal source
- `frontend/admin/src/`: Admin source
- `docker/edge/backend/DOCKERFILE`: Backend image build
- `docker/edge/nginx/nginx.conf`: Reverse proxy config

## Unknowns
- Backend source code location (not present in workspace; only Dockerfile exists)
- Robot-side service implementation details
- Exact API endpoints and data models
- Authentication/authorization mechanism details
- CI/CD pipeline configuration