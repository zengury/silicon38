## Issues

### Issue 1: Restructure backend into flat directories (core, db, api, services)

**Description:**
Move all backend source files from the current layered structure (core/, infrastructure/, domain/, api/) into a flat structure with four directories: core/ (config), db/ (models), api/ (routes), services/ (business logic). Remove infrastructure/ and domain/ directories. Update all import paths accordingly. Ensure the application still starts and all endpoints respond.

**Acceptance Criteria:**
- [ ] No infrastructure/ or domain/ directories exist under backend/
- [ ] All backend source files are under core/, db/, api/, or services/
- [ ] Application starts without import errors
- [ ] All existing API endpoints under /api/v1/ return same status codes and response shapes as before

**Estimated Size:** L

**Blocked By:** None

---

### Issue 2: Remove shared frontend workspace package (@roboease/shared)

**Description:**
Remove the shared workspace package `@roboease/shared` from both admin and portal frontends. Identify any truly duplicated code (icons, utilities) and copy or symlink them into each project. Update package.json files to remove the workspace dependency. Ensure both frontends build and run independently.

**Acceptance Criteria:**
- [ ] `@roboease/shared` is removed from admin/package.json and portal/package.json
- [ ] `pnpm install && pnpm build` succeeds in admin directory
- [ ] `pnpm install && pnpm build` succeeds in portal directory
- [ ] Admin UI loads without errors
- [ ] Portal UI loads without errors

**Estimated Size:** M

**Blocked By:** None

---

### Issue 3: Merge Docker compose files into one with environment variable overrides

**Description:**
Merge `docker/edge/docker-compose.yaml` and `docker/docker-compose.prod.yaml` into a single `docker/docker-compose.yaml`. Use Docker Compose profiles or environment variable overrides to differentiate edge vs. cloud environments. Remove the duplicate compose files. Update any scripts or documentation that reference the old files.

**Acceptance Criteria:**
- [ ] Single `docker/docker-compose.yaml` exists
- [ ] `docker compose up` starts all services for edge environment
- [ ] Environment variables control edge vs. cloud behavior (e.g., database URL, secrets)
- [ ] Old compose files (`docker/edge/docker-compose.yaml`, `docker/docker-compose.prod.yaml`) are removed or deprecated

**Estimated Size:** M

**Blocked By:** Issue 1, Issue 2

---

### Issue 4: Document robot communication protocol in code comments

**Description:**
Add comments in the backend code where MQTT topics and WebSocket messages are defined (e.g., in the MQTT service and WebSocket handler). Document the protocol: topic names, message formats, expected payloads, and any relevant notes. No separate documentation file.

**Acceptance Criteria:**
- [ ] Comments exist near MQTT topic definitions explaining the protocol
- [ ] Comments exist near WebSocket message handlers explaining the protocol
- [ ] Comments are clear and sufficient for a new developer to understand the protocol

**Estimated Size:** S

**Blocked By:** Issue 1

---

### Issue 5: Verify no regression in existing functionality

**Description:**
After all refactoring changes are complete, manually test all existing functionality: login, robot CRUD, task execution, MQTT/WebSocket communication. Ensure no regression. This is a verification issue to be done after all other issues are merged.

**Acceptance Criteria:**
- [ ] Login with existing credentials returns a valid token
- [ ] Protected endpoints reject invalid tokens
- [ ] Robot CRUD operations work as before
- [ ] Task execution works as before
- [ ] MQTT communication with robots works identically
- [ ] WebSocket communication with robots works identically

**Estimated Size:** M

**Blocked By:** Issue 1, Issue 2, Issue 3, Issue 4

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the PRD for RoboEase refactor (Lite) into 5 independent implementation issues with acceptance criteria, estimated sizes, and dependency relationships.
  key_decisions:
    - decision: Backend restructuring is the first issue (no blockers) because it is foundational.
      rationale: All other backend changes depend on the new directory structure.
    - decision: Frontend shared package removal is independent of backend restructuring.
      rationale: Frontend and backend are separate deployable units; they can be worked on in parallel.
    - decision: Docker compose merge is blocked by both backend and frontend changes.
      rationale: The compose file references both backend and frontend services; changes to those services should be stable before merging.
    - decision: Protocol documentation is blocked by backend restructuring.
      rationale: The MQTT and WebSocket code may move during restructuring; documenting after the move avoids rework.
    - decision: Regression verification is the final issue, blocked by all others.
      rationale: It must be done after all changes are merged to ensure no regression.
  handoff_focus:
    - Implementation of Issue 1 (backend restructuring) and Issue 2 (frontend shared package removal) can start immediately.
    - Issue 3 and Issue 4 should be planned after Issue 1 and Issue 2 are complete.
    - Issue 5 is the final verification step.
  open_questions:
    - Exact list of backend files to move (requires exploring current directory structure).
    - Actual duplication between admin and portal frontends (requires comparing imports and usage of shared package).
    - Environment variable differences between edge and cloud (requires comparing existing compose files).
  known_constraints:
    - Backend must remain single deployable unit.
    - Database schema unchanged.
    - API contract unchanged.
    - Robot communication protocol unchanged.
  confidence_differential: 0.9
  dissent_if_alone: null
  iteration_context: null
```
