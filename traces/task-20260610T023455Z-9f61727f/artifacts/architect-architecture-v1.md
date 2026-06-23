# Architecture Decision Record: RoboEase Refactoring

## Context
The RoboEase codebase at `/Users/ZQ/roboease` is a Python application with a monolithic structure. The zoom-out analysis identified:
- Duplicated utility logic in `utils/helpers.py`
- Large `core/pipeline.py` with multiple responsibilities
- Similar retry/error-handling patterns in `services/api_client.py` and `services/database.py`
- Uneven test coverage, especially in `test_services/`

The task is to refactor the codebase to eliminate duplication, improve module structure, and enhance maintainability and testability.

## Decision: Modular Refactoring with Clear Separation of Concerns

We will refactor the codebase incrementally, focusing on:
1. **Extract shared utilities** from `utils/helpers.py` into focused modules.
2. **Split `core/pipeline.py`** into smaller, single-responsibility components.
3. **Unify retry/error-handling** into a shared service layer.
4. **Improve test coverage** by adding unit tests for extracted modules.

### Rationale
- Incremental refactoring minimizes risk and allows continuous integration.
- Clear separation of concerns improves maintainability and testability.
- Unifying patterns reduces duplication and future bugs.

### Alternatives Considered
- **Full rewrite**: Rejected due to high risk and time constraints.
- **Microservices extraction**: Premature; codebase is not large enough to justify operational overhead.
- **No refactoring**: Rejected because duplication and large modules will hinder future development.

### Consequences
- Positive: Cleaner code, easier testing, reduced duplication.
- Negative: Temporary disruption during refactoring; need to update imports and tests.
- Risk: Extracting utilities may introduce new dependencies if not done carefully.

## Architecture Overview

### Module Structure (After Refactoring)
```
src/
├── main.py
├── core/
│   ├── engine.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Orchestrates pipeline stages
│   │   ├── stage_base.py        # Abstract base for stages
│   │   ├── transform_stage.py   # Data transformation
│   │   ├── api_stage.py         # External API calls
│   │   └── storage_stage.py     # Database persistence
│   └── models.py
├── utils/
│   ├── __init__.py
│   ├── string_utils.py          # String manipulation
│   ├── file_utils.py            # File I/O operations
│   ├── retry.py                 # Retry logic
│   └── logger.py
├── services/
│   ├── api_client.py            # HTTP client (uses retry)
│   └── database.py              # Database client (uses retry)
└── ui/
    ├── cli.py
    └── gui.py
```

### Data Flow
1. User input via CLI/GUI → `core/engine.py` → `core/pipeline/orchestrator.py`
2. Orchestrator runs stages: `transform_stage` → `api_stage` → `storage_stage`
3. Each stage uses `utils/` for common operations
4. Results flow back to UI

### Failure Modes
- **API failure**: `api_stage` retries via `utils/retry.py`; if all retries fail, error is logged and pipeline continues with next item.
- **Database failure**: `storage_stage` retries; if persistent failure, pipeline halts and reports error.
- **Invalid input**: `transform_stage` validates data; invalid items are skipped and logged.

## Implementation Plan

### Phase 1: Extract Utilities
1. Create `utils/string_utils.py` and `utils/file_utils.py` from `utils/helpers.py`.
2. Create `utils/retry.py` with generic retry decorator.
3. Update imports across codebase.
4. Write unit tests for new modules.

### Phase 2: Refactor Pipeline
1. Create `core/pipeline/` package.
2. Extract `orchestrator.py` with main pipeline logic.
3. Extract `stage_base.py` with abstract `Stage` class.
4. Extract `transform_stage.py`, `api_stage.py`, `storage_stage.py`.
5. Update `core/engine.py` to use new pipeline.
6. Write unit tests for each stage.

### Phase 3: Unify Service Patterns
1. Refactor `services/api_client.py` and `services/database.py` to use `utils/retry.py`.
2. Ensure consistent error handling and logging.
3. Add integration tests for services.

### Phase 4: Improve Test Coverage
1. Add missing tests for `test_services/`.
2. Ensure all new modules have >80% line coverage.

## Tradeoffs
- **Granularity**: More modules increase complexity but improve testability.
- **Performance**: Slight overhead from additional abstraction layers; negligible for this application.
- **Learning curve**: Team needs to understand new structure; mitigated by documentation.

## Downstream Constraints
- All changes must pass existing tests before merging.
- No new external dependencies.
- Refactoring must be done in small, mergeable PRs.

## Completion Report
```yaml
completion_report:
  what_was_done: Designed architecture for refactoring RoboEase codebase, including module structure, data flows, failure modes, and incremental implementation plan.
  key_decisions:
    - decision: Extract shared utilities into focused modules (string_utils, file_utils, retry).
      rationale: Eliminates duplication and centralizes common patterns.
    - decision: Split core/pipeline.py into a package with orchestrator and stage classes.
      rationale: Single-responsibility principle improves maintainability and testability.
    - decision: Unify retry/error-handling in utils/retry.py.
      rationale: Reduces duplication and ensures consistent behavior.
  handoff_focus:
    - Implement Phase 1: Extract utilities and update imports.
    - Implement Phase 2: Refactor pipeline into stages.
    - Implement Phase 3: Unify service patterns.
    - Implement Phase 4: Improve test coverage.
  open_questions:
    - Should we use dependency injection for stages to improve testability?
    - What is the exact retry policy (max retries, backoff) for services?
  known_constraints:
    - No runtime or database access; static analysis only.
    - Timeboxed to one iteration; deep analysis deferred.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```
