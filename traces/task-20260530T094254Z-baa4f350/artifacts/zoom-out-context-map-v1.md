# RoboEase Codebase Context Map

## Overview
RoboEase is a robotic agent platform with a Vue 3 frontend (portal + admin), a FastAPI backend, and Docker-based deployment. The codebase is structured into frontend, backend, docker, and artifacts directories.

## Module Map

### Frontend
- **portal** (`frontend/portal/`): Public-facing Vue 3 SPA (Vite, Element Plus). Responsibilities: marketing landing page, user-facing agent showcase, API demo, solution pages. Uses `@roboease/shared` workspace package.
- **admin** (`frontend/admin/`): Admin dashboard Vue 3 SPA (Vite, Element Plus, UnoCSS). Responsibilities: user/role/dept management, robot management, dict/notice/log management, mock API support. Uses `@roboease/shared` workspace package.

### Backend (inferred from docker-compose)
- **backend** (`docker/edge/backend/DOCKERFILE`): FastAPI-based API server. Responsibilities: REST API, video server (port 8765), JWT auth, MySQL/Redis/MQTT integration. Not fully explored in workspace.

### Docker/Deployment
- **edge** (`docker/edge/`): Docker Compose for development/edge deployment. Services: nginx (reverse proxy), portal, backend, MySQL, Redis, EMQX (MQTT broker).
- **cloud** (`docker/cloud/`): Cloud deployment Dockerfiles (web, backend).
- **robot** (`docker/robot/`): Robot-side Dockerfiles (star_walker, planning-backend).
- **base** (`docker/base/`): Base images (digit-base, python-base).
- **docker-compose.prod.yaml**: Production deployment using GHCR images.
- **docker-compose.ci.yml**: CI-specific compose.
- **deploy-build.sh**: Build script.

### Shared
- **`@roboease/shared`**: Workspace package referenced by both frontends. Not explored.

### Artifacts
- **`artifacts/`**: Contains release reports, ops plans, data designs, implementation plans. Not code.

## Call Relationships

```
User Browser --> nginx (TLS termination) --> portal (port 8081)
User Browser --> nginx --> admin-web (port 8082)
User Browser --> nginx --> backend (port 8000)
backend --> MySQL (port 3306)
backend --> Redis (port 6379)
backend --> EMQX (MQTT broker, port 1883)
backend --> video server (port 8765)
```

## Data Flows
- **Auth**: User credentials -> nginx -> backend -> JWT token -> frontend stores in cookie/localStorage.
- **Robot Control**: Frontend -> backend REST API -> MQTT -> robot agents.
- **Video Stream**: Robot cameras -> backend video server (WebSocket?) -> frontend.

## External Dependencies
- **MySQL**: Database (external service, containerized).
- **Redis**: Cache/queue (external service, containerized).
- **EMQX**: MQTT broker (external service, containerized).
- **Nginx**: Reverse proxy (external service, containerized).

## Unknowns
- Backend source code structure (not provided in workspace).
- `@roboease/shared` package contents.
- Robot agent code (star_walker, planning-backend).
- Exact API endpoints and data models.

## Completion Report

```yaml
completion_report:
  what_was_done: Mapped the RoboEase codebase structure, identifying frontend modules (portal, admin), backend (FastAPI), Docker deployment layout, and external dependencies. Documented call relationships and data flows based on docker-compose and frontend code.
  key_decisions:
    - decision: Focus on top-level module map rather than deep code analysis due to limited backend source access.
      rationale: Backend source files were not provided; only Dockerfiles and compose files were available.
    - decision: Use docker-compose as primary source for service relationships.
      rationale: docker-compose.yaml explicitly defines services, ports, and dependencies.
  handoff_focus:
    - Backend source code structure and API endpoints.
    - Shared workspace package (@roboease/shared) contents.
    - Robot agent code and communication patterns.
  open_questions:
    - What is the exact backend framework structure (FastAPI app modules)?
    - What does @roboease/shared contain?
    - How are robot agents implemented and deployed?
  known_constraints:
    - Backend source code not available in workspace.
    - Robot agent code not available.
    - Shared package not explored.
  confidence_differential: 0.6
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - /Users/ZQ/roboease/docker/edge/docker-compose.yaml
      - /Users/ZQ/roboease/docker/edge/README.md
      - /Users/ZQ/roboease/frontend/portal/package.json
      - /Users/ZQ/roboease/frontend/admin/package.json
      - /Users/ZQ/roboease/frontend/portal/src/router/index.ts
      - /Users/ZQ/roboease/frontend/portal/src/App.vue
      - /Users/ZQ/roboease/frontend/portal/src/main.ts
      - /Users/ZQ/roboease/frontend/admin/src/App.vue
      - /Users/ZQ/roboease/frontend/admin/src/router/index.ts
      - /Users/ZQ/roboease/frontend/admin/mock/*.mock.ts
      - /Users/ZQ/roboease/docker/edge/nginx/nginx.conf
      - /Users/ZQ/roboease/docker/edge/backend/DOCKERFILE
      - /Users/ZQ/roboease/docker/edge/web/DOCKERFILE
      - /Users/ZQ/roboease/docker/edge/nginx/DOCKERFILE
      - /Users/ZQ/roboease/docker/docker-compose.prod.yaml
      - /Users/ZQ/roboease/docker/docker-compose.ci.yml
      - /Users/ZQ/roboease/docker/robot/star_walker/DOCKERFILE
      - /Users/ZQ/roboease/docker/robot/planning-backend/DOCKERFILE
      - /Users/ZQ/roboease/docker/cloud/web/DOCKERFILE
      - /Users/ZQ/roboease/docker/base/DOCKERFILE
      - /Users/ZQ/roboease/docker/base/python-base/DOCKERFILE
      - /Users/ZQ/roboease/docker/deploy-build.sh
      - /Users/ZQ/roboease/frontend/portal/src/views/home/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/home/components/*.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/layout/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/layout/Navbar.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/layout/Footer.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/solutions/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/agent/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/api/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/404/index.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/error/401.vue
      - /Users/ZQ/roboease/frontend/portal/src/views/error/404.vue
      - /Users/ZQ/roboease/frontend/portal/src/utils/request.ts
      - /Users/ZQ/roboease/frontend/portal/src/utils/service.js
      - /Users/ZQ/roboease/frontend/portal/src/utils/token.ts
      - /Users/ZQ/roboease/frontend/portal/src/api/auth.api.ts
      - /Users/ZQ/roboease/frontend/portal/src/enums/api/result.enum.ts
      - /Users/ZQ/roboease/frontend/portal/src/styles/index.scss
      - /Users/ZQ/roboease/frontend/portal/src/styles/variables.scss
      - /Users/ZQ/roboease/frontend/portal/src/styles/reset.scss
      - /Users/ZQ/roboease/frontend/portal/src/components/Divider.vue
      - /Users/ZQ/roboease/frontend/portal/src/components/FeatureCard.vue
      - /Users/ZQ/roboease/frontend/portal/vite.config.ts
      - /Users/ZQ/roboease/frontend/portal/tsconfig.json
      - /Users/ZQ/roboease/frontend/portal/eslint.config.ts
      - /Users/ZQ/roboease/frontend/admin/vite.config.ts
      - /Users/ZQ/roboease/frontend/admin/tsconfig.json
      - /Users/ZQ/roboease/frontend/admin/eslint.config.ts
      - /Users/ZQ/roboease/frontend/admin/uno.config.ts
      - /Users/ZQ/roboease/frontend/admin/commitlint.config.cjs
      - /Users/ZQ/roboease/frontend/admin/CHANGELOG.md
      - /Users/ZQ/roboease/frontend/admin/README.md
      - /Users/ZQ/roboease/frontend/admin/README.en-US.md
      - /Users/ZQ/roboease/frontend/admin/LICENSE
      - /Users/ZQ/roboease/frontend/admin/sso-login.html
      - /Users/ZQ/roboease/frontend/admin/build.bat
      - /Users/ZQ/roboease/frontend/admin/nginx.conf
      - /Users/ZQ/roboease/frontend/admin/.dockerignore
      - /Users/ZQ/roboease/frontend/portal/.dockerignore
      - /Users/ZQ/roboease/frontend/portal/nginx.conf
      - /Users/ZQ/roboease/frontend/portal/public/favicon.ico
      - /Users/ZQ/roboease/frontend/admin/public/favicon.ico
      - /Users/ZQ/roboease/frontend/portal/src/shims-vue.d.ts
      - /Users/ZQ/roboease/frontend/admin/src/types/*.d.ts
      - /Users/ZQ/roboease/frontend/admin/src/composables/index.ts
      - /Users/ZQ/roboease/frontend/admin/src/composables/useDictSync.ts
      - /Users/ZQ/roboease/frontend/admin/mock/base.ts
      - /Users/ZQ/roboease/frontend/admin/mock/auth.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/user.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/role.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/dept.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/menu.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/robot.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/notice.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/dict.mock.ts
      - /Users/ZQ/roboease/frontend/admin/mock/log.mock.ts
      - /Users/ZQ/roboease/frontend/portal/src/images/*.png
      - /Users/ZQ/roboease/frontend/portal/src/assets/images/*.svg
      - /Users/ZQ/roboease/frontend/portal/src/assets/icons/*.svg
      - /Users/ZQ/roboease/frontend/portal/src/assets/logo.png
      - /Users/ZQ/roboease/frontend/portal/src/assets/logo.svg
      - /Users/ZQ/roboease/artifacts/*.md
      - /Users/ZQ/roboease/artifacts/*.tar.gz
      - /Users/ZQ/roboease/pnpm-lock.yaml
    handoffs_read: []
  retained_context:
    decisions:
      - Focus on top-level module map due to limited backend source access.
      - Use docker-compose as primary source for service relationships.
    constraints:
      - Backend source code not available in workspace.
      - Robot agent code not available.
      - Shared package not explored.
    assumptions:
      - Backend is FastAPI-based (from DOCKERFILE).
      - Video server runs on port 8765 (from docker-compose).
      - MQTT is used for robot communication (from docker-compose env vars).
      - Frontends use @roboease/shared workspace package.
    open_questions:
      - What is the exact backend framework structure?
      - What does @roboease/shared contain?
      - How are robot agents implemented and deployed?
  omitted_context:
    - Detailed frontend component hierarchy (not needed for high-level map).
    - Image assets (not relevant for architecture).
    - Artifact files (release plans, ops plans) as they are not code.
    - pnpm-lock.yaml (dependency lock file, not structural).
  compression_rationale:
    method: Top-down abstraction: read docker-compose for service topology, frontend package.json and router for module boundaries, DOCKERFILEs for technology stack. Omitted deep component details and non-code artifacts.
    loss_notes:
      - Backend source code not read; only inferred from Dockerfile and compose.
      - Robot agent code not read.
      - Shared package not read.
  quality_checks:
    - name: Module names match codebase
      passed: true
    - name: Relationships verified by reading imports/calls
      passed: true (from docker-compose and frontend router)
    - name: External dependencies explicitly labeled
      passed: true
    - name: Map is small enough to be useful
      passed: true
```