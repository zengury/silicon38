# PRD: RoboEase Refactor (Lite)

## Problem Statement

The RoboEase codebase has accumulated unnecessary complexity through layered abstractions (core/infrastructure/domain/API), a premature shared frontend package, and duplicate Docker compose files. This makes the system harder to understand, slower to iterate on, and more costly to maintain for a small team with evolving domain boundaries.

## Solution

Simplify the codebase to a flat, pragmatic structure that preserves essential architectural decisions (modular monolith, SQLModel, API versioning, JWT auth, MQTT/WebSocket) while removing layers and abstractions that do not yet pay for themselves. The result is "RoboEase Lite": a backend with a flat directory layout (config, db, api, services), a single frontend (admin) with portal as a separate static site, one Docker compose file, and protocol documentation in code comments.

## User Stories

1. As a backend developer, I want a flat backend structure (config, db, api, services) so that I can find and modify code quickly without navigating unnecessary layers.
2. As a frontend developer, I want the admin and portal frontends to be independent (no shared workspace package) so that I can build and deploy them separately without monorepo tooling overhead.
3. As a DevOps engineer, I want a single Docker compose file with environment variable overrides for edge/cloud so that I can maintain one configuration instead of two.
4. As a developer, I want robot communication protocol documented in code comments near the MQTT/WebSocket definitions so that I can understand the protocol without reading a separate document.
5. As a team lead, I want the refactoring to preserve all existing functionality (authentication, robot management, task execution, MQTT/WebSocket communication) so that users experience no regression.
6. As a developer, I want the backend to remain a single deployable unit so that deployment is simple and consistent.
7. As a developer, I want the database schema to remain unchanged so that existing data is not lost.
8. As a developer, I want the API endpoints to remain under /api/v1/ so that existing clients continue to work.
9. As a developer, I want the JWT authentication mechanism to remain unchanged so that security is not compromised.
10. As a developer, I want the MQTT and WebSocket communication patterns to remain unchanged so that robots continue to work.

## Implementation Decisions

### Backend Structure
- **Current**: `core/`, `infrastructure/`, `domain/`, `api/` layers.
- **Target**: Flat structure with `core/` (config), `db/` (models), `api/` (routes), `services/` (business logic). No `infrastructure/` or `domain/` directories.
- **Rationale**: Codebase is small (<50k lines). Layers add abstraction without benefit. Flat structure reduces cognitive load and refactoring effort.
- **Migration**: Move files from `infrastructure/` and `domain/` into appropriate `core/`, `db/`, `api/`, or `services/` directories. Update imports accordingly.

### Frontend
- **Current**: Two frontends (admin, portal) with a shared workspace package `@roboease/shared`.
- **Target**: Keep admin and portal as separate projects. Remove the shared workspace package. Extract only truly duplicated code (icons, utilities) into simple import paths (e.g., copy or symlink) within each project. No monorepo workspace.
- **Rationale**: Duplication is minimal. Workspace package adds build complexity (pnpm workspace, versioning, CI). Accept duplication now, extract later when pattern is clear.

### Docker
- **Current**: Two compose files: `docker/edge/docker-compose.yaml` and `docker/docker-compose.prod.yaml`.
- **Target**: Single compose file `docker/docker-compose.yaml` with profiles or environment variable overrides for edge vs. cloud.
- **Rationale**: Edge and cloud differ only by environment variables (e.g., database URL, secrets). One file reduces maintenance burden.

### Protocol Documentation
- **Current**: No centralized documentation; protocol is scattered in code.
- **Target**: Add comments in the backend code where MQTT topics and WebSocket messages are defined (e.g., in the MQTT service and WebSocket handler). No separate documentation file.
- **Rationale**: Less overhead, stays close to source, easier to keep in sync.

### CI/CD and Testing
- **No changes**: CI/CD pipeline and testing strategy are out of scope for this refactoring. Manual testing is sufficient for now.

## Testing Decisions

- **Scope**: No new tests will be added. Existing tests (if any) must continue to pass.
- **Verification**: Manual testing of all existing functionality (login, robot CRUD, task execution, MQTT/WebSocket communication) after refactoring.
- **Prior art**: No existing test infrastructure to reference.

## Out of Scope

- Adding new features (e.g., new API endpoints, new robot capabilities).
- Changing the database schema.
- Changing the API contract (endpoints, request/response formats).
- Changing the authentication mechanism.
- Changing the robot communication protocol (MQTT topics, WebSocket messages).
- Adding CI/CD pipeline.
- Adding automated tests.
- Adding observability (logging, monitoring, tracing).
- Refactoring the portal frontend beyond removing the shared package dependency.
- Changing the deployment architecture (still single deployable backend unit).

## Further Notes

- The refactoring should be done incrementally, with each change tested manually before proceeding.
- The team should agree on the final directory structure before starting.
- The shared package removal should be done after verifying that no critical functionality depends on it.
- The Docker compose merge should be done last, after backend and frontend changes are stable.

## Requirements

| ID | Description | Essential | Testable Criterion |
|----|-------------|-----------|-------------------|
| R1 | Backend uses flat structure: core/, db/, api/, services/ | true | All backend source files are under one of these four directories; no infrastructure/ or domain/ directories exist |
| R2 | All existing API endpoints under /api/v1/ remain functional | true | All endpoints return same status codes and response shapes as before refactoring |
| R3 | All existing database models remain unchanged | true | Database schema migration shows no changes; existing data is readable |
| R4 | JWT authentication works identically | true | Login with existing credentials returns a valid token; protected endpoints reject invalid tokens |
| R5 | MQTT communication with robots works identically | true | Robots can publish and subscribe to same topics; backend processes messages as before |
| R6 | WebSocket communication with robots works identically | true | Robots can establish WebSocket connections and exchange messages as before |
| R7 | Admin frontend builds and runs without the shared workspace package | true | `pnpm install && pnpm build` succeeds in admin directory; admin UI loads without errors |
| R8 | Portal frontend builds and runs without the shared workspace package | true | `pnpm install && pnpm build` succeeds in portal directory; portal UI loads without errors |
| R9 | Single Docker compose file works for both edge and cloud environments | true | `docker compose up` starts all services; environment variables control edge vs. cloud behavior |
| R10 | Robot communication protocol is documented in code comments | false | Comments exist near MQTT topic definitions and WebSocket message handlers explaining the protocol |

## Success Criteria

1. All backend tests (if any) pass.
2. Manual testing confirms all user stories are satisfied.
3. No regression in existing functionality.
4. Codebase size (lines of code) is reduced or unchanged.
5. Build and deployment time is not increased.

## Open Questions

1. What is the exact list of files that need to be moved in the backend? (Requires exploring current directory structure.)
2. What is the actual duplication between admin and portal frontends? (Requires comparing imports and usage of shared package.)
3. Are there any existing tests? (Not found in file list; assume none.)
4. What environment variables differ between edge and cloud? (Requires comparing existing compose files.)

## Completion Report

```yaml
completion_report:
  what_was_done: Produced PRD for RoboEase refactor (Lite) based on caveman analysis and upstream handoffs.
  key_decisions:
    - decision: Backend flat structure (core/db/api/services) instead of layered (core/infrastructure/domain/API)
      rationale: Codebase small, team small. Layers add abstraction without benefit.
    - decision: Remove shared frontend workspace package
      rationale: Duplication minimal. Workspace package adds build complexity.
    - decision: Merge Docker compose files into one
      rationale: Edge and cloud differ only by env vars.
    - decision: Protocol documentation in code comments
      rationale: Less overhead, stays close to source.
  handoff_focus:
    - to-issues: Create issues for each requirement (R1-R10) with testable criteria.
    - architect: Review backend flat structure and frontend independence decisions.
  open_questions:
    - Exact list of backend files to move.
    - Actual duplication between admin and portal frontends.
    - Environment variable differences between edge and cloud.
  known_constraints:
    - Backend must remain single deployable unit.
    - Database schema unchanged.
    - API contract unchanged.
    - Robot communication protocol unchanged.
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```
