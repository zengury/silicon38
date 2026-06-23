# Architecture Decision Record: RoboEase Refactoring

## Context
The RoboEase codebase is a robotic control and simulation framework with modules: `roboease/` (core), `roboease/sim/`, `roboease/plan/`, `roboease/perception/`, `roboease/utils/`, `tests/`, `examples/`, `docs/`. The zoom-out analysis identified top-level structure, call relationships, and data flows. The task is to refactor the codebase to eliminate duplicate code, improve module structure, and enhance maintainability and testability.

## Decision
Adopt a **Modular Monolith with Clear Interface Boundaries** architecture. Keep the codebase as a single deployable unit but enforce strict module boundaries via explicit public APIs and dependency inversion. Extract shared utilities into a dedicated `roboease/common/` module. Introduce an **Inversion of Control (IoC) container** for dependency management to decouple modules and improve testability.

## Rationale
- The team size (unknown but likely small) and current structure favor a monolith over microservices.
- The codebase already has logical modules; the main issues are implicit dependencies and code duplication.
- An IoC container allows modules to depend on abstractions, making them testable in isolation.
- A `common/` module consolidates shared code (math, logging, config) and eliminates duplication.
- This approach can be implemented incrementally without a full rewrite.

## Alternatives Considered
1. **Microservices**: Rejected due to high operational complexity, unclear domain boundaries, and small team size. The current modules are tightly coupled; extracting services would require significant upfront investment.
2. **Keep as-is with minor fixes**: Rejected because it does not address root causes of duplication and coupling.
3. **Hexagonal Architecture**: Considered but deemed too heavyweight for the current scale. The IoC container approach is a lighter form of ports-and-adapters.

## Consequences
- **Positive**: Reduced duplication, clearer module responsibilities, easier unit testing via mocking, and incremental migration path.
- **Negative**: Requires refactoring existing imports to use abstractions; IoC container adds a new dependency.
- **Risks**: Over-engineering if not scoped carefully; team must learn IoC patterns.

## Detailed Design

### Module Boundaries
- `roboease/common/`: Shared utilities (math, logging, config, data structures). No internal dependencies on other modules.
- `roboease/core/`: Robot models, kinematics, dynamics, control algorithms. Depends on `common/`.
- `roboease/sim/`: Physics simulation. Depends on `core/` and `common/`.
- `roboease/plan/`: Motion planning. Depends on `core/` and `common/`.
- `roboease/perception/`: Sensor processing. Depends on `core/` and `common/`.
- `tests/`: Unit and integration tests. Depends on all modules via abstractions.
- `examples/`: Example scripts. Depends on public APIs only.

### Interface Contracts
Each module exposes a public API via an `__init__.py` that re-exports only intended symbols. Internal classes and functions are prefixed with `_` or placed in `_internal` submodules.

### Dependency Injection
- Use a lightweight IoC container (e.g., `dependency-injector` for Python) to wire dependencies.
- Each module defines an interface (abstract base class) for its services.
- Concrete implementations are registered in the container.
- Tests can replace implementations with mocks.

### Data Flow
- User input → `examples/` → `roboease/plan/` (via interface) → `roboease/core/` (via interface) → `roboease/sim/` (via interface) → output.
- Sensor data → `roboease/perception/` → state → `roboease/plan/` → commands → `roboease/core/`.

### Failure Modes
- IoC container misconfiguration: Fail fast at startup with clear error messages.
- Module unavailability: Each module should handle missing dependencies gracefully (e.g., raise `ImportError` with guidance).

## Implementation Plan
1. Create `roboease/common/` and move shared utilities from `roboease/utils/` and other modules.
2. Define abstract interfaces for each module's public services.
3. Introduce IoC container and register implementations.
4. Refactor module imports to use interfaces and container.
5. Update tests to use mocks via container.
6. Remove duplicate code identified during refactoring.

## Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for RoboEase refactoring: modular monolith with IoC container, clear interface boundaries, and a shared common module.
  key_decisions:
    - decision: Adopt modular monolith with IoC container.
      rationale: Balances simplicity with decoupling; enables incremental refactoring and testability.
    - decision: Extract roboease/common/ for shared utilities.
      rationale: Eliminates duplication and centralizes cross-cutting concerns.
    - decision: Use abstract interfaces for module public APIs.
      rationale: Enables dependency injection and mocking for tests.
  handoff_focus:
    - senior-engineer: Implement common module extraction and IoC container setup.
    - api-designer: Define abstract interfaces for each module.
    - database-engineer: Not applicable; no database changes.
  open_questions:
    - What specific duplicate code patterns exist? (to be identified during implementation)
    - Which IoC library to use? (recommend dependency-injector for Python)
    - How to handle circular dependencies if they exist?
  known_constraints:
    - Must be implementable incrementally; no big-bang rewrite.
    - Must maintain backward compatibility for public APIs used by examples.
    - External dependencies (NumPy, PyBullet, Matplotlib) remain unchanged.
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```
