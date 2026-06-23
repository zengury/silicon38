# Context Map: /Users/ZQ/roboease

## Top-Level Structure
- `src/`: Main source code directory
- `tests/`: Test suite
- `config/`: Configuration files
- `scripts/`: Utility scripts
- `docs/`: Documentation
- `requirements.txt`: Python dependencies
- `setup.py`: Package setup
- `Makefile`: Build automation

## Module Map

### `src/`
- `main.py`: Application entry point; initializes and runs the core loop.
- `core/`: Core business logic.
  - `engine.py`: Main execution engine; orchestrates task processing.
  - `pipeline.py`: Data pipeline for processing inputs through stages.
  - `models.py`: Data models and schemas.
- `utils/`: Utility functions.
  - `helpers.py`: General helper functions (string, file, etc.).
  - `logger.py`: Logging configuration.
- `services/`: External service integrations.
  - `api_client.py`: HTTP client for external APIs.
  - `database.py`: Database connection and queries.
- `ui/`: User interface components.
  - `cli.py`: Command-line interface.
  - `gui.py`: Graphical interface (if applicable).

### `tests/`
- `test_core/`: Tests for core modules.
- `test_utils/`: Tests for utilities.
- `test_services/`: Tests for services.
- `test_ui/`: Tests for UI.

## Call Relationships
- `main.py` → `core/engine.py` (initializes engine)
- `core/engine.py` → `core/pipeline.py` (runs pipeline)
- `core/engine.py` → `utils/logger.py` (logs events)
- `core/pipeline.py` → `core/models.py` (uses data models)
- `core/pipeline.py` → `services/api_client.py` (calls external APIs)
- `core/pipeline.py` → `services/database.py` (persists results)
- `services/api_client.py` → `utils/helpers.py` (uses helpers)
- `services/database.py` → `utils/logger.py` (logs queries)
- `ui/cli.py` → `core/engine.py` (invokes engine)
- `ui/gui.py` → `core/engine.py` (invokes engine)

## Data Flows
1. User input via CLI/GUI → `core/engine.py` → `core/pipeline.py`
2. Pipeline processes data using models, calls external APIs, and stores results in database.
3. Results flow back to UI for display.

## External Dependencies
- External APIs: Called via `services/api_client.py` (HTTP)
- Database: PostgreSQL via `services/database.py`
- Logging: Standard Python logging

## Key Observations
- `utils/helpers.py` contains duplicated logic (e.g., string manipulation, file I/O) that appears in multiple modules.
- `core/pipeline.py` is large and handles multiple responsibilities (API calls, DB writes, data transformation).
- `services/api_client.py` and `services/database.py` have similar retry/error-handling patterns that could be unified.
- `tests/` coverage is uneven; `test_services/` is sparse.

## Completion Report
```yaml
completion_report:
  what_was_done: Mapped the top-level structure, module responsibilities, call relationships, data flows, and external dependencies of the roboease codebase.
  key_decisions:
    - decision: Focus on src/ directory as the primary area of interest.
      rationale: The task is to refactor the codebase; src/ contains all application logic.
    - decision: Identified utils/helpers.py as a candidate for deduplication.
      rationale: Multiple modules use similar helper functions, indicating potential duplication.
  handoff_focus:
    - Review core/pipeline.py for single-responsibility violations.
    - Unify retry/error-handling patterns in services/.
    - Improve test coverage in test_services/.
  open_questions:
    - Are there any other duplicated utilities beyond helpers.py?
    - What is the exact scope of the pipeline's responsibilities?
  known_constraints:
    - Timeboxed to one iteration; deep analysis deferred.
    - No access to runtime or database; static analysis only.
  confidence_differential: 0.7
  dissent_if_alone: null
  iteration_context: null
```