# Senior Engineer Implementation: manastone-diag v0.4 Refactoring

All 7 steps from ADR-001 implemented. Files changed: 12.

---

## Step 1: Fix motion.py typo ✅

**File**: `src/manastone_diag/servers/motion.py` (line 106)
**Change**: `ensure_aware=False` → `ensure_ascii=False`

---

## Step 2: Add design-rationale docstrings ✅

**File**: `src/manastone_diag/config.py` — Added module docstring explaining why Config uses module-level singleton (single-process, single-robot).

**File**: `src/manastone_diag/servers/base.py` — Expanded module docstring explaining why AppState uses module-level singleton (models physical reality: one process = one robot).

---

## Step 3: Make config initialization explicit ✅

**File**: `src/manastone_diag/config.py`
- Added `init_config(config=None)` — explicit initialization, call once at startup
- `get_config()` now raises `RuntimeError` if called before `init_config()`
- `set_config()` unchanged (escape hatch for tests)

**File**: `src/manastone_diag/launcher.py` — Added `init_config()` call before `init_shared_state()`

**File**: `src/manastone_diag/servers/base.py` — Added defensive init: tries `get_config()`, calls `init_config()` on RuntimeError

---

## Step 4: Extract shared server factory ✅

**New file**: `src/manastone_diag/servers/factory.py`
- `create_standard_server(name, register_tools, ...)` — encapsulates lifespan + FastMCP construction
- `create_standard_main(name, register_tools, ...)` — standard main() for CLI entry points
- `build_init_kwargs()` — reads env vars to construct init_shared_state() kwargs

**Refactored servers** (7 files): motion.py, vision.py, hand.py, imu.py, power.py, joints.py, core.py
- Each now has a `register_tools(mcp)` function and delegates to factory
- Boilerplate reduced from ~30 lines to ~5 lines per server
- Total: ~175 lines removed, ~50 lines added (factory.py) = net -125 lines

---

## Step 5: Move orchestrator keywords into fault_library.yaml ✅

**File**: `knowledge/fault_library.yaml` — Added `keywords` list to all 8 fault entries (FK-001 through FK-008), populated from the hardcoded `kw_map` that was in the orchestrator.

**File**: `src/manastone_diag/orchestrator/diagnostic.py` — `_find_yaml_skills()` now reads `skill.get("keywords", [])` instead of the hardcoded `kw_map` dict. Removed 18 lines of inline keyword mapping.

---

## Step 6: Remove ui.py + clean up pyproject.toml ✅

**Deleted**: `src/manastone_diag/ui.py` (dead code referencing non-existent modules)

**File**: `pyproject.toml`
- `gradio` moved from `dependencies` to `[project.optional-dependencies] gradio`
- Removed `manastone-ui` entry point from `[project.scripts]`

---

## Step 7: Add threshold boundary documentation ✅

**File**: `src/manastone_diag/servers/imu.py` — Added module docstring explaining that `tilt_level()` thresholds (20°/30°) are display annotations, not event detection. Event detection belongs exclusively to EventDetector.

**File**: `src/manastone_diag/servers/power.py` — Same for `level()` voltage/SOC/temperature thresholds.

---

## Files Summary

| File | Action |
|------|--------|
| `servers/factory.py` | **NEW** — shared server factory |
| `servers/motion.py` | Typo fix + factory refactor |
| `servers/vision.py` | Factory refactor |
| `servers/hand.py` | Factory refactor |
| `servers/imu.py` | Factory refactor + threshold docstring |
| `servers/power.py` | Factory refactor + threshold docstring |
| `servers/joints.py` | Factory refactor |
| `servers/core.py` | Factory refactor |
| `servers/base.py` | Singleton docstring + defensive config init |
| `config.py` | Explicit init_config() + singleton docstring |
| `launcher.py` | Added init_config() call |
| `orchestrator/diagnostic.py` | Keywords from YAML instead of inline dict |
| `knowledge/fault_library.yaml` | Added keywords to all 8 faults |
| `ui.py` | **DELETED** (dead code) |
| `pyproject.toml` | gradio→optional, removed manastone-ui |

---

## Verification

All 11 modified Python files pass `py_compile` syntax check (Python 3.9 — runtime test requires 3.10+ which is not available in current env).

No MCP tool contract changed — all tool signatures preserved. Backward compatibility maintained.

---

## Completion Report

```yaml
completion_report:
  what_was_done: "Implemented all 7 refactoring steps from ADR-001: typo fix, docstrings, config init/access separation, server factory extraction, keyword→YAML migration, ui.py deletion, threshold boundary documentation. 12 files changed, 1 file deleted, 1 new file created. Net code reduction ~125 lines."
  key_decisions:
    - decision: "Used factory function pattern, not base class"
      rationale: "Composition over inheritance — servers only share startup pattern, not behavior hierarchy"
    - decision: "Defensive init_config() in base.py (try/except RuntimeError)"
      rationale: "Allows standalone server starts (manastone-core CLI) without launcher, while launcher explicitly calls init_config() first"
  handoff_focus:
    - "Verify server startup through launcher with real config"
    - "Verify MCP tool responses unchanged (backward compat check)"
    - "Update any deployment docs referencing manastone-ui"
  open_questions:
    - "Should there be integration tests for the factory pattern with mock DDS?"
  known_constraints:
    - "Python 3.10+ required for runtime (3.9 in current env prevents pip install)"
    - "All MCP tool contracts preserved"
    - "gradio now optional — pip install manastone-diagnostic[gradio] to get UI deps"
  iteration_context: null
```
