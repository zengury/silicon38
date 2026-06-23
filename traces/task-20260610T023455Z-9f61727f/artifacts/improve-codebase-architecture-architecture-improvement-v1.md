# Architecture Improvement Roadmap — roboease

> task_id: `task-20260610T023455Z-9f61727f`
> date: 2026-06-10
> role: improve-codebase-architecture
> html_report: `/var/folders/_2/cvlfl9914hj0dhzxr00m_8340000gn/T/architecture-review-20260610-024500.html`

---

## Current Problems

### P1 — Robot module service duplication (xiaqi_api vs xialan_api)

- **Affected modules**: `robot/modules/xiaqi_api/services/*`, `robot/modules/xialan_api/services/*`, `robot/modules/xiaqi_api/controller/*`, `robot/modules/xialan_api/controller/*`
- **Consequence**: 9 service pairs (Action, Motion, Camera, HDS, Map, Task, TTS, Other, Video) with ~95% identical logic. Each bug fix must be mirrored across two codebases. Adding a new robot variant would require a third full copy. The deletion test confirms shallowness: delete `xiaqi_api/actionservice.py` and all its complexity reappears in `xialan_api/actionservice.py` — it was a pass-through adapter, not a deep module.
- **Evidence**: 
  - `robot/modules/xiaqi_api/services/actionservice.py` (lines 1-55) and `robot/modules/xialan_api/services/actionservice.py` (lines 1-48) are structurally identical differing only in logging statements
  - `robot/modules/xiaqi_api/controller/action.py` and `robot/modules/xialan_api/controller/action.py` are byte-for-byte identical
  - Both import the same shared utilities: `robot/modules/common/http_rpc.py`, `robot/modules/common/action_rules.py`

### P2 — N+1 query pattern in TaskBaseService

- **Affected modules**: `backend/shared/task_base_service.py` — `page()` and `list()` methods
- **Consequence**: Each paginated task list issues 1 + 2N queries (one for tasks, then one each for steps and results per task). With page size 50, this is 101 queries per page load. This pattern spreads across all task subtypes (InspectionTask, InventoryTask) that inherit from TaskBaseService.
- **Evidence**: 
  - `task_base_service.py` line ~171-202: the `page()` method iterates over fetched tasks and calls `select(cls._STEPS_ENTITY)` and `select(cls._RESULTS_ENTITY)` for each task
  - `task_base_service.py` line ~212-240: the `list()` method has the same loop
  - No `WHERE task_id IN (...)` batch query exists

### P3 — Wildcard imports obscure dependency graph

- **Affected modules**: 18+ API route files under `backend/api/admin/*.py`, `backend/api/portal/*.py`, `backend/api/qianhai/*.py`
- **Consequence**: Every file that does `from common.models import *` creates an opaque dependency. No tool or human can determine which imports a module actually uses without reading the entire file. Refactoring `common.models` becomes dangerous because no caller list is discoverable.
- **Evidence**: 
  - `backend/api/admin/agent.py` line 3: `from common.models import *` (also line 12: duplicate wildcard import)
  - `backend/api/qianhai/dashboard.py` lines 3, 7: two wildcard imports from the same module
  - Full list: auth, menu, robot, user, dict, dashboard, screenProject, role, permission, file, common_interface, task, extractLogs, robot_ext_info, logAnalysis, agent, face_recognition, redirect, and portal equivalents

### P4 — Shallow entity services with zero domain logic

- **Affected modules**: `backend/services/action_library_service.py`, `expression_library_service.py`, `voice_library_service.py`, `knowledge_library_service.py`, `dict_service.py`, `device_service.py`
- **Consequence**: Six service files that define only 2–3 config class attributes with zero method overrides. The interface (entity class, name field) is exactly as complex as the implementation (nothing). Applying the deletion test: removing any of these files concentrates zero complexity because `BaseEntityService` already provides identical behavior.
- **Evidence**: 
  - `backend/services/action_library_service.py`: 14 lines, only sets `_ENTITY_CLASS`, `_NAME_FIELD`, `_DESC_FIELD`
  - `backend/services/expression_library_service.py`: same pattern
  - All inherit from `BaseEntityService` which provides all CRUD methods

### P5 — DI container boilerplate (260 lines, ~30 meaningful)

- **Affected modules**: `backend/di/container.py`
- **Consequence**: 15 near-identical repository property definitions (private attr + property getter + setter, each 6 lines). Adding a new repository requires 3 copy-paste edits. The boilerplate obscures the actual architecture — which repositories exist and what their concrete types are.
- **Evidence**: 
  - `backend/di/container.py` lines 35-36, 56-60 repeated for every repository
  - The `_lazy_load` method is called identically in all 15 properties
  - The setter pattern is identical across all 15 properties

### P6 — Two incompatible error response shapes

- **Affected modules**: `backend/core/exception_handlers.py`, `backend/common/models.py` (BaseResponse), all API route files
- **Consequence**: Routes return `BaseResponse{code, msg, data}` for both success and errors, while raised exceptions produce `{error: {code, message, detail}, meta: {requestId}}`. A client must handle both formats depending on whether the error was `return return_error(...)` or `raise NotFoundError(...)`.
- **Evidence**: 
  - `backend/core/exception_handlers.py` produces structured `{"error": {...}, "meta": {...}}` responses
  - `backend/common/models.py` `return_error()` produces `BaseResponse{code: 500, msg: "...", data: None}`
  - API routes like `backend/api/admin/agent.py` use both patterns inconsistently

---

## Improvement Roadmap

### Step 1: Extract shared robot capability adapters

- **Change**: Extract capability classes into `robot/modules/common/capabilities/`. Each capability (McActionCapability, MotionCapability, CameraCapability, etc.) accepts a robot-specific configuration dict at initialization. Robot-specific modules become thin configuration bundles that import and configure the shared capabilities.
- **Rationale**: Highest impact-to-risk ratio. Removes ~2,000 lines of duplicated code, creates a single test surface per capability, makes adding new robot variants a configuration exercise instead of a copy-paste operation.
- **Risk**: Low. The shared utilities (`RobotHttpRpcClient`, `action_rules`) already prove the pattern works. Controllers are already byte-identical — only service classes need extraction.
- **Unlocks**: Adding a new robot variant (e.g., a 7th robot type) becomes a 30-line config file instead of a full copy of 9 services + 9 controllers.

### Step 2: Batch-load task steps and results

- **Change**: In `TaskBaseService.page()` and `list()`, after loading the task list, collect all task IDs, issue one `WHERE task_id IN (...)` query for steps and one for results. Assemble in-memory by task_id.
- **Rationale**: Pure performance optimization with zero behavior change. Reduces query count from 1+2N to always 3. Affects every task list endpoint (inspection, inventory, synergy).
- **Risk**: Near-zero. SQL `IN()` clause with many IDs; test with realistic page sizes (10, 50, 100).
- **Unlocks**: Makes pagination scalable to larger page sizes; reduces database load under concurrent access.

### Step 3: Eliminate wildcard imports

- **Change**: Replace every `from common.models import *` with explicit named imports. Write a script that auto-detects which symbols each file uses from the wildcard.
- **Rationale**: Zero behavior change, pure clarity improvement. Makes the dependency graph machine-readable, enabling safer refactoring of `common.models`.
- **Risk**: Near-zero. Static analysis (pyflakes, ruff F403/F405 rules) verifies correctness automatically.
- **Unlocks**: Safe refactoring of `common/models.py`; AI-navigable dependency graph.

### Step 4: Collapse DI container boilerplate

- **Change**: Define a `LazyRepo` descriptor class that encapsulates lazy-load, metric tracking, and mock injection. Each repository becomes a single line declaration.
- **Rationale**: Reduces `container.py` from 260 lines to ~80 lines without losing any functionality. The descriptor becomes a single test surface for lazy-load behavior.
- **Risk**: Low. Behavior-preserving refactor; descriptor pattern is well-understood Python.
- **Unlocks**: Adding/removing repositories becomes a one-line change; descriptor can be unit-tested independently.

### Step 5: Unify error response paths (phased)

- **Change**: Phase 1: route all errors through exception handlers (`raise NotFoundError` instead of `return_not_found`). Phase 2: replace `return_success` with direct FastAPI response model returns.
- **Rationale**: Single seam for error formatting, single response contract for clients.
- **Risk**: Medium. Touches every route; requires phased migration with backward compatibility.
- **Unlocks**: Consistent client-side error handling; one module to change error format.

### Step 6: Deepen or inline shallow entity services

- **Change**: For each of the six shallow services, either (a) add real domain logic (validation rules, export/import, bulk operations) to justify the module, or (b) delete the file and use `BaseEntityService[Entity]` directly in route handlers.
- **Rationale**: The deletion test says they can be removed — but some may grow domain logic as features are added. Decision per service.
- **Risk**: Low. Using `BaseEntityService` directly is already tested via the existing service pattern.
- **Unlocks**: Fewer files, clearer structure, or genuinely deep modules if domain logic is added.

---

## Priority Order Justification

1. **Robot capability extraction** first — highest lines-removed-to-risk ratio, immediately prevents further copy-paste divergence, creates the test surface that's currently missing for robot services.
2. **N+1 query fix** second — pure performance, near-zero risk, affects all task endpoints.
3. **Wildcard imports** third — mechanical change, scriptable, enables all subsequent refactoring by making dependencies visible.
4. **DI container** fourth — internal cleanup, low urgency but reduces friction when adding new entities.
5. **Error response unification** fifth — higher risk, requires cross-cutting migration. Start only after steps 1-4 are stable.
6. **Shallow services** last — speculative. Only worth doing if the services won't gain domain logic soon; otherwise adding depth is the better path.

Each step is independently deployable. No step requires a preceding step to be complete (though step 3 makes step 4 safer).
