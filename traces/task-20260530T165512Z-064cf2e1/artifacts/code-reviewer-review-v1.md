# Code Review: Robot Fleet Monitor Backend

## Verdict: CHANGES_REQUIRED

## Correctness Findings

### 1. [HIGH] Missing input validation in POST /api/ingest
- **File**: `src/server/routes/data-ingest.ts` (line 25)
- **Issue**: The endpoint accepts raw JSON body without schema validation. Malformed or malicious payloads could cause unexpected behavior or crashes.
- **Fix**: Integrate a validation library (e.g., Joi, Zod) to validate `NormalizedTelemetry` fields: `robotId` (non-empty string), `battery` (0-100), `cpu` (0-100), `network_latency` (>=0), `joint_temperatures` (array of numbers), `status` (enum), `location` (object with lat/lng), `current_task` (optional string).

### 2. [HIGH] ProtobufAdapter and ModbusAdapter stubs return hardcoded data
- **File**: `src/adapters/protobuf-adapter.ts` (line 10), `src/adapters/modbus-adapter.ts` (line 10)
- **Issue**: Both stubs return a hardcoded `NormalizedTelemetry` object. If these are used in production, they will silently produce incorrect data.
- **Fix**: Either implement real parsing or throw a clear error indicating the adapter is not yet implemented.

### 3. [MEDIUM] WebSocket message authentication missing
- **File**: `src/collaboration/messages.ts` (line 30)
- **Issue**: The `CollaborationManager` broadcasts messages without verifying the sender's identity. Any connected client can impersonate another user.
- **Fix**: Add a simple token-based authentication (e.g., JWT) on WebSocket connection. Validate sender ID against token claims.

### 4. [MEDIUM] Export service silently falls back to CSV when Puppeteer/exceljs unavailable
- **File**: `src/export/service.ts` (line 45)
- **Issue**: If PDF or Excel generation fails due to missing libraries, the service falls back to CSV without notifying the user. This could lead to unexpected output format.
- **Fix**: Log a warning and return an appropriate HTTP status code (e.g., 501 Not Implemented) with a clear error message, or include a header indicating the fallback.

### 5. [LOW] Alert engine cooldown uses seconds but rule creation API accepts any number
- **File**: `src/alert/engine.ts` (line 60)
- **Issue**: The `cooldown_s` field is documented as seconds, but no validation ensures it's a positive integer. Negative or zero values could cause unexpected behavior.
- **Fix**: Validate `cooldown_s` > 0 in the rule creation endpoint.

## Maintainability Findings

### 1. [HIGH] No error handling middleware in Express app
- **File**: `src/server/app.ts` (line 20)
- **Issue**: The Express app does not have a global error handler. Uncaught exceptions in async route handlers will crash the process.
- **Fix**: Add an error-handling middleware that catches errors and returns a 500 response. Use `express-async-errors` or wrap async handlers.

### 2. [MEDIUM] Hardcoded database credentials in pool.ts
- **File**: `src/db/pool.ts` (line 5)
- **Issue**: Database connection string is hardcoded. This is a security risk and makes configuration changes difficult.
- **Fix**: Use environment variables (e.g., `DATABASE_URL`) with a fallback to a local development default.

### 3. [MEDIUM] Redis cache fallback to in-memory map is not thread-safe
- **File**: `src/cache/redis.ts` (line 30)
- **Issue**: The in-memory fallback uses a plain `Map` without any locking. In a multi-threaded Node.js environment (e.g., with worker threads), this could cause race conditions.
- **Fix**: Use a simple mutex or document that the fallback is only for single-threaded development.

### 4. [LOW] Magic numbers in alert engine thresholds
- **File**: `src/alert/engine.ts` (line 40)
- **Issue**: Threshold values like `battery_level < 20` and `cpu_usage > 90` are hardcoded. These should be configurable via the config API.
- **Fix**: Move default thresholds to configuration and allow runtime overrides.

### 5. [LOW] No TypeScript strict null checks on some variables
- **File**: `src/server/routes/history.ts` (line 15)
- **Issue**: The `robotId` parameter is used without checking for `undefined`. TypeScript strict mode should catch this, but the code uses `any` in some places.
- **Fix**: Enable `strictNullChecks` and fix all resulting errors.

## Style Notes

### 1. [STYLE] Inconsistent naming: `robotId` vs `robot_id` in API paths
- **File**: `src/server/routes/history.ts` (line 10)
- **Issue**: Some routes use camelCase (`robotId`) while others use snake_case (`robot_id`). Stick to one convention (preferably camelCase for consistency with JavaScript).

### 2. [STYLE] Long lines in export service
- **File**: `src/export/service.ts` (line 80)
- **Issue**: Several lines exceed 120 characters. Break them for readability.

### 3. [STYLE] Missing JSDoc comments on public methods
- **File**: `src/adapters/registry.ts` (line 15)
- **Issue**: Public methods like `register`, `unregister`, `normalize` lack documentation. Add brief JSDoc comments.

## Summary

| Severity | Count |
|----------|-------|
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 2 |
| STYLE | 3 |

**Total findings: 10**

## Completion Report

```yaml
completion_report:
  what_was_done: Reviewed the Robot Fleet Monitor backend implementation for correctness, maintainability, and style. Identified 10 findings: 2 high-severity correctness issues (missing input validation, stub adapters returning hardcoded data), 3 medium-severity issues (WebSocket auth, export fallback, cooldown validation), 2 low-severity issues (error handling middleware, hardcoded credentials), and 3 style notes.
  key_decisions:
    - decision: Verdict is CHANGES_REQUIRED due to high-severity correctness issues.
      rationale: Missing input validation on ingest endpoint and stub adapters returning hardcoded data could lead to data corruption or silent failures in production.
    - decision: Handoff to senior-engineer for fixes.
      rationale: Correctness issues require code changes before merging.
  handoff_focus:
    - Fix input validation on POST /api/ingest.
    - Implement real parsing in ProtobufAdapter and ModbusAdapter or throw clear errors.
    - Add WebSocket authentication.
    - Improve error handling in Express app.
  open_questions:
    - Should the export service return a 501 when libraries are unavailable, or silently fall back?
    - Should alert thresholds be configurable via the config API?
  known_constraints:
    - Review performed without running the application; static analysis only.
    - Some findings may be mitigated by existing tests not reviewed.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - senior-engineer-implementation-v1
    handoffs_read:
      - handoffs/senior-engineer→code-reviewer-20260530-171349.yaml
  retained_context:
    decisions:
      - Adapter pattern for data normalization with hot-plug support.
      - Backend Node.js + Express + WebSocket + PostgreSQL + Redis.
      - Alert engine rule-based with configurable thresholds.
      - Collaboration via WebSocket.
      - Export via Puppeteer (PDF) and exceljs (Excel).
    constraints:
      - Initial support for 10 robots.
      - Data format unification required.
      - Data retention 30 days.
    assumptions:
      - Robots report via HTTP/WebSocket.
      - No authentication required for MVP.
    open_questions:
      - Should alert escalation auto-create higher-severity follow-up alerts?
      - Should WebSocket messages be signed/authenticated?
      - Should historical data use PostgreSQL partitioning?
      - 告警通知方式是否需要邮件/短信？
      - 是否需要角色权限管理？
  omitted_context:
    - source: npm dependency versions
      reason: Declared in package.json, not relevant for review.
    - source: Test fixture details
      reason: Self-documenting; not needed for review.
    - source: UX spec visual details
      reason: Frontend concern, not load-bearing for backend review.
  compression_rationale:
    method: Retained all architectural decisions, constraints, and open questions from upstream. Omitted library versions, test fixtures, and UX details.
    loss_notes:
      - Caveman analysis details omitted.
      - UX spec visual details omitted.
      - npm dependency exact versions omitted.
  quality_checks:
    - name: All findings have file and line references
      passed: true
    - name: Verdict justified by findings
      passed: true
    - name: Correctness findings distinguished from maintainability and style
      passed: true
    - name: No unsubstantiated blocks
      passed: true
```