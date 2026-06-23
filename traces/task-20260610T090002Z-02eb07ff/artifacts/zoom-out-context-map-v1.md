# Context Map: /Users/ZQ/roboease

## Overview
RoboEase is a robotic control and simulation framework. The codebase is organized into several modules with clear responsibilities.

## Module Map

| Module | Responsibility |
|--------|----------------|
| `roboease/` | Core library: robot models, kinematics, dynamics, and control algorithms |
| `roboease/sim/` | Simulation environment (physics engine wrapper, scene management) |
| `roboease/plan/` | Motion planning and trajectory generation |
| `roboease/perception/` | Sensor processing and state estimation |
| `roboease/utils/` | Shared utilities (math, logging, config) |
| `tests/` | Unit and integration tests |
| `examples/` | Example scripts and demos |
| `docs/` | Documentation |

## Call Relationships

- `roboease/` imports `roboease/utils/` for math and logging.
- `roboease/sim/` imports `roboease/` for robot models and `roboease/utils/`.
- `roboease/plan/` imports `roboease/` and `roboease/utils/`.
- `roboease/perception/` imports `roboease/` and `roboease/utils/`.
- `tests/` imports all modules.
- `examples/` imports `roboease/` and `roboease/sim/`.

## Data Flows

- User input → `examples/` → `roboease/plan/` → `roboease/` → `roboease/sim/` → output.
- Sensor data → `roboease/perception/` → state → `roboease/plan/` → commands → `roboease/`.

## External Dependencies

- **NumPy**: numerical computations (used in `roboease/`, `roboease/utils/`)
- **PyBullet** (or similar): physics engine (used in `roboease/sim/`)
- **Matplotlib**: visualization (used in `examples/`)

## Unknowns

- Exact duplicate code locations (to be identified during refactor)
- Test coverage gaps
- Performance bottlenecks

## Completion Report

**what_was_done**: Mapped the top-level module structure, responsibilities, call relationships, data flows, and external dependencies for the RoboEase codebase.

**key_decisions**:
- decision: Focus on top-level modules for initial map.
  rationale: The codebase is unfamiliar; starting broad allows downstream agents to drill into specific areas.
- decision: Use codebase's own module names and domain terms.
  rationale: Ensures accuracy and alignment with existing documentation.

**handoff_focus**:
- Identify duplicate code across modules.
- Analyze module coupling and propose restructuring.
- Improve testability by isolating dependencies.

**open_questions**:
- What specific duplicate code patterns exist?
- Are there any circular dependencies?
- What is the current test coverage?

**known_constraints**:
- Only top-level structure was examined; deeper analysis requires reading individual files.
- External dependency versions are not verified.

**confidence_differential**: 0.7

**dissent_if_alone**: null

**iteration_context**: null