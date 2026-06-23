# Architecture Decision Record: Strategy Canvas Refactoring

**Date:** 2026-05-26
**Context:** `zengury/strategy-cavas` — Strategic Canvas Live, a strategy coaching tool
**Zoom-out findings:** Identified critical Python-JS engine duplication (6 files, ~900 LOC duplicated), monolithic schema, no tests, mixed concerns

---

## Current Architecture (As-Is)

```
┌────────────────────────────────────────────────────────────┐
│                     TWO DEPLOYMENT PATHS                    │
├──────────────────────────┬─────────────────────────────────┤
│   Web (Render.com)       │   Desktop (Electron .dmg)       │
├──────────────────────────┤─────────────────────────────────┤
│                          │                                  │
│  main.py (FastAPI)       │  electron-app/main/main.js      │
│      │                   │       │                          │
│      ▼                   │       ▼                          │
│  engine/  (Python .py)   │  electron-app/main/engine/ (JS) │
│  ├─ conversation.py      │  ├─ conversation.js    ← DUPE    │
│  ├─ skill_router.py      │  ├─ skill-router.js   ← DUPE    │
│  ├─ skill_registry.py    │  ├─ skill-registry.js ← DUPE    │
│  ├─ context_bus.py       │  ├─ context-bus.js    ← DUPE    │
│  └─ canvas_state.py      │  └─ canvas-state.js   ← DUPE    │
│      │                   │       │                          │
│  models/schema.py  ←────────── schema.js          ← DUPE    │
│      │                   │       │                          │
│  skills/  (.md files) ←─────── skills/  (same .md files)   │
│      │                   │       │                          │
│  web/ (static)           │  electron-app/renderer/ ← DUPE   │
│                          │                                  │
│  API: REST + WebSocket   │  API: IPC (main↔renderer)       │
└──────────────────────────┴─────────────────────────────────┘
```

**Problem:** Any logic change to the engine requires editing **both** Python and JS versions. The JS port is structurally identical but simplified — no docstrings, less error handling, but same control flow. This doubles maintenance burden and guarantees eventual divergence.

---

## Decision 1: Eliminate Engine Duplication

**Status:** Load-bearing — determines all downstream decisions.

### Option A: Python-First + Electron as Web Wrapper

Convert the Electron app into a thin shell that:
1. Bundles the Python backend as a subprocess (spawn `python main.py` at app start)
2. Electron BrowserWindow loads `http://localhost:8000`
3. Removes ALL `electron-app/main/engine/` JS files

```
┌─────────────────────────────────────┐
│        Electron Shell (thin)        │
│  ┌───────────────────────────────┐  │
│  │   BrowserWindow               │  │
│  │   → http://localhost:8000     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   child_process (Python)      │  │
│  │   python main.py --port 8000  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Pros:**
- Single engine implementation (Python)
- Electron becomes a zero-logic wrapper — no maintenance
- All features available in both web and desktop
- WebSocket and REST API work identically

**Cons:**
- Desktop app requires Python runtime (bundled via PyInstaller or similar)
- Startup latency (Python boot + uvicorn start)
- ~50-80MB additional package size for Python runtime

### Option B: JavaScript-First — Migrate Python to Node.js

Rewrite `engine/` and `main.py` in JavaScript/TypeScript. Run one codebase across both.

**Pros:**
- Single codebase in one language
- Electron native — no subprocess complexity
- Smaller desktop package (no Python runtime)

**Cons:**
- Massive rewrite of existing Python code (~800 LOC engine + 180 LOC main.py)
- Python ecosystem advantage lost (no good FastAPI equivalent in JS, ecosystem fragmentation)
- The Python version is the more complete/robust one (docstrings, better error handling, dataclasses)
- Risk of regressions and feature disparity during rewrite

### Option C: Rust Core with Language Bindings

Build a shared Rust core library, export via FFI to both Python and JS.

**Pros:**
- True single source of truth at the logic level
- Performance for graph computation

**Cons:**
- Massive overengineering for a ~1000 LOC project
- FFI complexity
- The core logic is LLM orchestration, not CPU-bound computation — performance is not the bottleneck

### **Decision: Option A — Python-First + Electron as Web Wrapper**

**Rationale:**
1. The Python codebase is the primary, more mature implementation
2. The LLM orchestration logic is inherently IO-bound (API calls) — language performance is irrelevant
3. Python ecosystem (FastAPI, websockets, openai, pyyaml) is well-suited for this domain
4. Eliminates ~900 LOC of duplicated code immediately
5. Desktop packaging via PyInstaller is a solved problem and only needed for release, not development
6. Electron's `child_process.spawn()` is stable and well-documented

**Rejected alternatives:** Option B risks regressions in a working codebase with no tests. Option C is overengineered for a project of this scale.

**Consequences:**
- Must add PyInstaller or similar Python bundling for Electron release
- Electron `main.js` becomes a thin launcher (~30 LOC)
- All `electron-app/main/engine/` files are deleted
- Engine development happens exclusively in Python

---

## Decision 2: Schema File Organization

**Current state:** `models/schema.py` — 340 lines containing 17 dataclasses, 4 enums, 3 constant maps, 1 alias.

### **Decision: Split into domain, constants, and graph modules**

```
models/
├── __init__.py          # Re-exports for backward compatibility
├── enums.py             # Stage, SkillStatus, NodeType (14), EdgeType (14)
├── domain.py            # ConversationTurn, SkillInvocation, ContextObject,
│                        #   GraphNode, GraphEdge, GraphDiff, CanvasGraph,
│                        #   DecisionCase, SkillMeta
├── graph_config.py      # NODE_SPATIAL_BIAS, NODE_COLORS, EDGE_COLORS,
│                        #   CANVAS_ZONES, NODE_TYPE_TO_ZONE
└── compat.py            # CanvasState = CanvasGraph (legacy alias)
```

**Rationale:** Separates the data model from visual/presentation constants. Domain objects and enums are the core contract; graph_config can change independently for visualization tuning.

---

## Decision 3: Configuration Management

**Current state:** 
- `config/app.yaml` for top-level config
- Hardcoded `GAP_RULES` dict in `skill_router.py` and `skill-router.js`
- Hardcoded `stage_skills` mapping
- `SYSTEM_PROMPT` as Python string literal
- `SPACE_SCALE`, `JITTER`, `MAX_SKILL_CHARS` as module constants
- API keys via `os.getenv("DEEPSEEK_API_KEY")`

### **Decision: Centralize all configuration**

```
config/
├── app.yaml              # LLM, paths, limits (existing, expand)
├── routing.yaml          # GAP_RULES + stage_skills (extracted from code)
├── prompts.yaml          # SYSTEM_PROMPT (extracted from code)
└── graph.yaml            # SPACE_SCALE, JITTER, visual constants
```

Plus a `config.py` loader module using `pydantic` / `dataclasses` for validation:

```python
@dataclass
class LLMConfig:
    provider: str = "deepseek"
    api_base: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    router_model: str = "deepseek-chat"
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))

@dataclass
class AppConfig:
    llm: LLMConfig
    routing: RoutingConfig
    prompts: PromptConfig
    graph: GraphConfig
    skills_dir: str = "skills"
    store_path: str = "store"
    max_turns: int = 50
```

**Rationale:** Non-code configuration should not live in source files. Enables A/B testing of prompts, routing rules, and visual parameters without code changes.

---

## Decision 4: Test Infrastructure

**Current state:** Zero tests. No test framework, no test directory.

### **Decision: Add pytest with async support**

```
tests/
├── conftest.py                   # Fixtures: mock LLM client, sample canvas
├── test_schema.py                # Dataclass construction, serialization
├── test_skill_registry.py        # Skill loading, parsing, counts
├── test_skill_router.py          # Rule-based routing, gap detection
├── test_context_bus.py           # Turn management, truncation, snapshot
├── test_canvas_state.py          # Node/edge CRUD, diff application, 3D positioning
├── test_conversation.py          # Turn processing (with mocked LLM)
└── fixtures/
    ├── sample_skills/            # Minimal skill .md files for testing
    └── sample_canvas.json        # Pre-built canvas state
```

**Priority tests (smoke tests):**
1. `test_schema.py` — all dataclasses construct and serialize correctly
2. `test_skill_registry.py` — loads sample skills, counts correctly
3. `test_canvas_state.py` — add node, add edge, apply diff, export JSON
4. `test_conversation.py` — process_turn with mocked DeepSeek response

Add to `requirements.txt`:
```
pytest>=8.0
pytest-asyncio>=0.23
pytest-mock>=3.12
```

---

## Decision 5: Engine Module Improvements

### 5a. Add `engine/__init__.py`

```python
from engine.skill_registry import SkillRegistry
from engine.skill_router import SkillRouter
from engine.context_bus import ContextBus
from engine.canvas_state import CanvasStateManager
from engine.conversation import ConversationEngine

__all__ = [
    "SkillRegistry", "SkillRouter", "ContextBus",
    "CanvasStateManager", "ConversationEngine",
]
```

### 5b. Async Skill Loading

`SkillRegistry.__init__()` currently does sync filesystem I/O. Add async factory:

```python
class SkillRegistry:
    @classmethod
    async def create(cls, skills_dir: str = "skills") -> "SkillRegistry":
        instance = cls.__new__(cls)
        instance.skills_dir = Path(skills_dir)
        instance._skills = {}
        instance._definitions = {}
        await instance._load_all_async()
        return instance
```

### 5c. Extract ConversationEngine into Concern-Separated Classes

`conversation.py` (200 lines, 9-step `process_turn`) should delegate to focused collaborators:

```
engine/
├── ...
├── conversation.py      # Orchestrator only (coordinates steps)
├── prompt_builder.py     # SYSTEM_PROMPT, user message assembly (extracted)
├── llm_client.py         # DeepSeek API wrapper, retry logic (extracted)
└── response_parser.py    # JSON extraction, fallback parsing (extracted)
```

---

## Target Architecture (To-Be)

```
┌──────────────────────────────────────────────────────────────┐
│                    SINGLE PYTHON BACKEND                      │
│                                                               │
│  main.py (FastAPI)                                            │
│      │                                                        │
│      ▼                                                        │
│  engine/                                                      │
│  ├── __init__.py             ← NEW: package exports           │
│  ├── conversation.py         ← REFACTORED: orchestrator only  │
│  ├── prompt_builder.py       ← NEW: extracted from conv.py    │
│  ├── llm_client.py           ← NEW: extracted from conv.py    │
│  ├── response_parser.py      ← NEW: extracted from conv.py    │
│  ├── skill_registry.py       ← IMPROVED: async loading        │
│  ├── skill_router.py         ← CLEANED: config-driven rules   │
│  ├── context_bus.py          ← AS-IS (good shape)             │
│  └── canvas_state.py         ← AS-IS (good shape)             │
│      │                                                        │
│  models/                                                      │
│  ├── __init__.py             ← NEW: re-exports                │
│  ├── enums.py                ← SPLIT from schema.py           │
│  ├── domain.py               ← SPLIT from schema.py           │
│  ├── graph_config.py         ← SPLIT from schema.py           │
│  └── compat.py               ← SPLIT from schema.py           │
│      │                                                        │
│  config/                                                      │
│  ├── app.yaml                ← EXPANDED                       │
│  ├── routing.yaml            ← NEW: GAP_RULES + stage_skills  │
│  ├── prompts.yaml            ← NEW: SYSTEM_PROMPT             │
│  └── graph.yaml              ← NEW: visual constants          │
│      │                                                        │
│  tests/                        ← NEW                          │
│  ├── conftest.py                                               │
│  ├── test_schema.py                                            │
│  ├── test_skill_registry.py                                    │
│  ├── test_skill_router.py                                      │
│  ├── test_context_bus.py                                       │
│  ├── test_canvas_state.py                                      │
│  ├── test_conversation.py                                      │
│  └── fixtures/                                                 │
│                                                               │
│  DEPLOYMENT: Two paths, one engine                            │
│  ┌─────────────────────┐  ┌──────────────────────────────┐   │
│  │ Web (Render.com)    │  │ Electron Shell (thin)        │   │
│  │ uvicorn main:app    │  │ child_process: python main.py │   │
│  │ Port from $PORT     │  │ BrowserWindow → localhost     │   │
│  └─────────────────────┘  └──────────────────────────────┘   │
│                                                               │
│  REMOVED:                                                     │
│  ✗ electron-app/main/engine/  (all .js files — 6 files)      │
│  ✗ electron-app/renderer/     (duplicate web/ frontend)      │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Sequence (Incremental)

Phases ordered to deliver value without breaking existing functionality:

### Phase 1 — Split Schema + Add Tests (no behavior change)
1. Create `models/enums.py` — move enums, verify `main.py` imports still work
2. Create `models/domain.py` — move dataclasses
3. Create `models/graph_config.py` — move constants
4. Create `models/compat.py` — legacy aliases
5. Create `models/__init__.py` — re-export all
6. Create `tests/` with smoke tests for schema and canvas state
7. **Verify:** `python main.py` starts, all endpoints work

### Phase 2 — Externalize Configuration (no behavior change)
1. Create `config/routing.yaml` — extract GAP_RULES, stage_skills
2. Create `config/prompts.yaml` — extract SYSTEM_PROMPT
3. Create `config/graph.yaml` — extract visual constants
4. Create `engine/config.py` — typed config loader
5. Update `skill_router.py` to read from config
6. Update `conversation.py` to read SYSTEM_PROMPT from config
7. **Verify:** conversation flow unchanged, skill routing unchanged

### Phase 3 — Engine Refinement (minor behavior improvement)
1. Add `engine/__init__.py`
2. Add async `SkillRegistry.create()` factory
3. Extract `prompt_builder.py` from `conversation.py`
4. Extract `llm_client.py` from `conversation.py`
5. Extract `response_parser.py` from `conversation.py`
6. Add tests for extracted modules
7. **Verify:** conversation flow unchanged

### Phase 4 — Eliminate JS Duplication
1. Remove `electron-app/main/engine/` (all 6 files)
2. Update `electron-app/main/ipc-handlers.js` to spawn Python backend via `child_process`
3. Remove `electron-app/renderer/` — point to shared `web/` or serve from Python
4. Update `electron-app/main/main.js` to launch Python subprocess on app start
5. **Verify:** Electron app starts, chat works, graph renders

### Phase 5 — Unify Frontend (if needed)
1. Single `web/` directory serves both web and Electron
2. Electron `BrowserWindow` loads from localhost or file://
3. Remove all duplicate HTML/JSX/CSS

---

## Failure Modes & Mitigations

| Component | Failure Mode | Mitigation |
|-----------|-------------|------------|
| DeepSeek API | Rate limit / downtime | Exponential backoff in `llm_client.py`, graceful degradation message |
| Skill .md files | Corrupt / missing | Validation on load, skip with log warning (already implemented) |
| Canvas state | Memory growth (unbounded nodes) | Add max node limit (default 500), LRU eviction of lowest-confidence nodes |
| Python subprocess (Electron) | Crash / port conflict | Auto-restart with health check, random port fallback |
| WebSocket | Client disconnect during LLM call | Cancel in-flight request, clean up context bus |

---

## Open Questions for User

1. **Electron retention:** Is the Electron desktop app a hard requirement? Or can it be deferred/deprecated in favor of web-only?
2. **Skill definition format:** Currently Markdown with YAML frontmatter. Migrate to pure YAML/JSON for easier parsing and validation?
3. **LLM provider flexibility:** Currently DeepSeek-only. Should the config support OpenAI, Anthropic, and local Ollama as alternates?
4. **Multi-tenant / multi-session:** Current `CanvasStateManager` holds one graph in memory. When adding persistence, should it support multiple concurrent sessions?
5. **Phase priority:** Should we prioritize "eliminate JS duplication" (Phase 4) ahead of "structural cleanup" (Phases 1-3), or build incrementally?

---

## Handoff Focus for Downstream Agents

- **senior-engineer:** Phase 1+2 implementation (split schema, externalize config, add tests)
- **improve-codebase-architecture:** Phase 3 implementation (engine refactoring — extract modules, async registry)
- **refactor-specialist:** Phase 4+5 (eliminate JS duplication, unify frontend)
- **code-reviewer:** Review all Phase 1-3 changes for regression risk
