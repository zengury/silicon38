## Code Review: RoboEase Modular Monolith Infrastructure

**Verdict:** CHANGES_REQUIRED

### Correctness Findings

1. **File:** `core/security.py`, line 12
   **Issue:** `hash_password()` uses SHA-256 (`hashlib.sha256(password.encode()).hexdigest()`). SHA-256 is not a password hashing algorithm; it is fast and vulnerable to brute-force attacks. This is a security correctness issue.
   **Suggested Resolution:** Replace with `bcrypt` or `argon2` using `passlib` or `bcrypt` library. If backward compatibility is required, implement a migration strategy (e.g., rehash on login).

2. **File:** `infrastructure/db/connection.py`, line 25
   **Issue:** SQLite auto-detection uses `'sqlite' in str(settings.DATABASE_URL)` which can false-positive if the URL contains 'sqlite' in a path or parameter.
   **Suggested Resolution:** Use `urlparse(settings.DATABASE_URL).scheme == 'sqlite'` for reliable detection.

3. **File:** `db/repositories/base_repository.py`, line 45
   **Issue:** `BaseCRUDRepository` uses `getattr(self.entity, field)` for dynamic filtering without validating that `field` is a valid column. This can raise `AttributeError` or allow SQL injection via column names if user-controlled.
   **Suggested Resolution:** Validate `field` against `self.entity.__table__.columns` before access.

4. **File:** `infrastructure/observability/middleware.py`, line 30
   **Issue:** Correlation ID middleware does not propagate the correlation ID to downstream services (e.g., via HTTP headers). This breaks distributed tracing.
   **Suggested Resolution:** Add `request.state.correlation_id` and inject into outgoing requests via `httpx` or `aiohttp` client middleware.

### Maintainability Findings

1. **File:** `core/config.py`, line 50
   **Issue:** `Settings` class has 28 environment variables with no grouping or documentation. This makes it hard to understand which settings are related.
   **Suggested Resolution:** Split into nested models (e.g., `DatabaseSettings`, `JWTSettings`, `MQTTSettings`) and compose them in `Settings`.

2. **File:** `di/container.py`, line 20
   **Issue:** DI container uses lazy-loading properties with `@property` and `if self._user_repo is None: self._user_repo = SQLUserRepository(...)`. This is not thread-safe.
   **Suggested Resolution:** Use `threading.Lock` or switch to a library like `dependency-injector`.

3. **File:** `infrastructure/db/entities.py`, line 200
   **Issue:** 35 SQLModel entities in a single file. This violates the single-responsibility principle and makes the file hard to navigate.
   **Suggested Resolution:** Split into separate files per domain (e.g., `entities/user.py`, `entities/robot.py`).

4. **File:** `db/repositories/user_repository.py`, line 80
   **Issue:** `SQLUserRepository.get_by_username()` uses `self.session.exec(select(User).where(User.username == username)).first()`. This is fine, but there is no index hint or comment about performance for large user tables.
   **Suggested Resolution:** Add a comment noting that `username` should be indexed in MySQL.

### Style Notes

1. **File:** `core/exception_handlers.py`, line 15
   **Note:** `DomainError` mapping uses `if isinstance(exc, DomainError):` — consider using a dictionary mapping exception types to status codes for extensibility.

2. **File:** `infrastructure/observability/logging.py`, line 10
   **Note:** `structured_log` uses `loguru.logger` but the rest of the codebase may use standard `logging`. Consider unifying.

### Summary

- **Correctness:** 4 issues (1 security-critical, 3 logic/robustness)
- **Maintainability:** 4 issues
- **Style:** 2 notes

**Action Required:** Address correctness findings before merging. Maintainability findings should be addressed in a follow-up PR.

## Completion Report

```yaml
completion_report:
  what_was_done: Reviewed the senior-engineer implementation of the RoboEase modular monolith infrastructure layer. Analyzed 40 files across core, infrastructure, ports, DI, application, common, and repository layers. Identified 4 correctness issues, 4 maintainability issues, and 2 style notes.
  key_decisions:
    - decision: Verdict is CHANGES_REQUIRED due to security-critical SHA-256 password hashing and potential SQL injection in dynamic filtering.
      rationale: SHA-256 is not suitable for password storage; dynamic filtering without column validation is a security risk.
    - decision: Maintainability findings are required changes, not blockers.
      rationale: They affect long-term code health but do not introduce bugs.
  handoff_focus:
    - senior-engineer: Address correctness findings (SHA-256, SQLite detection, dynamic filter validation, correlation ID propagation).
    - security-engineer: Review SHA-256 migration to bcrypt and overall authentication security.
  open_questions:
    - Should the 9 high-Session-count services be refactored to use repositories? (from senior-engineer)
    - What is the migration strategy from SHA-256 to bcrypt? (from senior-engineer)
    - Should MQTT client move from common/ to infrastructure/mqtt/? (from senior-engineer)
  known_constraints:
    - Cannot access robot-side code without additional permissions.
    - MySQL 8.0 required for production; SQLite only for dev/test.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```
