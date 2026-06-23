# Zoom-Out: Strategy Canvas Codebase Map

**Date:** 2026-05-26
**Scope:** Full codebase — `zengury/strategy-cavas`

---

## 1. Repository Structure

```
strategy-cavas/
├── main.py                          # FastAPI entry point (Python, ~180 lines)
├── requirements.txt                 # 5 deps: fastapi, uvicorn, websockets, openai, pyyaml
├── config/app.yaml                  # LLM config (DeepSeek)
├── render.yaml                      # Render.com deploy config
├── .gitignore
├── DEPLOY.md
│
├── engine/                          # Core Python engine (5 files, ~800 lines total)
│   ├── skill_registry.py            # Skill .md loader + metadata
│   ├── skill_router.py              # 2-channel routing: rules + LLM
│   ├── context_bus.py               # Multi-modal context bus
│   ├── canvas_state.py              # 3D graph state manager
│   └── conversation.py              # Dialogue engine (LLM prompt + turn processing)
│
├── models/schema.py                 # All dataclasses, enums, constants (~340 lines)
│
├── skills/                          # 30+ strategic management skill .md files
│   ├── _template.md
│   ├── index.md
│   └── <skill-name>/SKILL.md        # Each in its own directory
│
├── web/                             # Static frontend
│   ├── index.html
│   ├── app.jsx
│   ├── styles/themes.css
│   └── demo_graph.json
│
├── electron-app/                    # Desktop Electron variant (~900 lines total)
│   ├── package.json
│   ├── main/
│   │   ├── main.js                  # Electron entry point
│   │   ├── preload.js               # Context bridge
│   │   ├── store.js                 # Key-value settings store
│   │   ├── ipc-handlers.js          # Engine wiring for Electron IPC
│   │   └── engine/                  # ⚠️ JS port of Python engine (DUPLICATE)
│   │       ├── conversation.js      # ~100 lines (← duplicate of conversation.py)
│   │       ├── skill-registry.js    # ~70 lines (← duplicate of skill_registry.py)
│   │       ├── skill-router.js      # ~90 lines (← duplicate of skill_router.py)
│   │       ├── canvas-state.js      # ~60 lines (← duplicate of canvas_state.py)
│   │       ├── context-bus.js       # ~35 lines (← duplicate of context_bus.py)
│   │       └── schema.js            # ~120 lines (← duplicate of schema.py)
│   └── renderer/                    # Frontend for Electron
│       ├── index.html
│       ├── app.jsx
│       ├── styles/themes.css
│       └── demo_graph.json
│
├── demo/                            # Standalone demo
│   ├── index.html
│   ├── graph_data.json
│   ├── serve.py
│   └── simulate_conversation.py
│
└── docs/
    └── product-architecture-v2.md    # Architecture vision doc (~260 lines)
```

---

## 2. Module Responsibility Map (Python — Primary Implementation)

### `main.py` → Application Assembly
- **Responsibility:** Bootstraps all engines, mounts FastAPI routes and WebSocket
- **Imports:** All engine modules + models.schema
- **Exposes:** 7 REST endpoints, 1 WebSocket endpoint
- **Config source:** `config/app.yaml`
- **Concern:** Manual DI wiring — all 5 engine instances constructed inline

### `models/schema.py` → Domain Model
- **Responsibility:** All data structures for the entire system
- **Contains:**
  - Enums: `Stage`, `SkillStatus`, `NodeType` (14 values), `EdgeType` (14 values)
  - Dataclasses: `ConversationTurn`, `SkillInvocation`, `ContextObject`, `GraphNode`, `GraphEdge`, `GraphDiff`, `CanvasGraph`, `DecisionCase`, `SkillMeta`
  - Constants: `NODE_SPATIAL_BIAS`, `NODE_COLORS`, `EDGE_COLORS`, `CANVAS_ZONES`, `NODE_TYPE_TO_ZONE`
  - Legacy alias: `CanvasState = CanvasGraph`
- **Issue:** Monolith — models, constants, and config maps all in one file

### `engine/skill_registry.py` → Skill Catalog
- **Responsibility:** Load & index 30+ skill .md files from disk
- **Init behavior:** Sync filesystem scan at `__init__` (blocking)
- **Key methods:** `get()`, `list_active()`, `catalog_for_prompt()`, `record_hit()`, `reload()`
- **Dependency:** Reads `models.schema.SkillMeta`

### `engine/skill_router.py` → Skill Selection
- **Responsibility:** Choose 1-3 relevant skills per conversation turn
- **Two channels:**
  - Rule-based: Gap detection in canvas zones → hardcoded `GAP_RULES` map
  - LLM-based: DeepSeek API call for semantic skill matching (fallback)
- **Hardcoded:** `GAP_RULES`, `stage_skills` mapping
- **Dependency:** `SkillRegistry`, `CanvasGraph`, `ContextBus` snapshot

### `engine/context_bus.py` → Context Management
- **Responsibility:** Store conversation turns, documents, structured data
- **Window:** Last 50 turns, truncation on overflow
- **Snapshot:** Returns composite context dict for LLM prompt assembly

### `engine/canvas_state.py` → Graph State
- **Responsibility:** Manage `CanvasGraph` (nodes + edges in free graph)
- **3D positioning:** Semantic bias + random jitter (`SPACE_SCALE=200`, `JITTER=40`)
- **Diff processing:** `apply_diff()`, `parse_llm_canvas_output()` (zone→NodeType mapping)
- **Export:** JSON for `react-force-graph-3d`

### `engine/conversation.py` → Dialogue Orchestrator
- **Responsibility:** Core turn processing loop (9 steps)
- **Flow:** Input → normalize → route skills → load definitions → LLM call → parse JSON → update stage → apply canvas diff → record turn
- **Contains:** 80-line `SYSTEM_PROMPT` constant (Chinese, ~2K chars), JSON parsing fallback
- **Dependency:** All other engine modules + `AsyncOpenAI`

---

## 3. Data Flow (Per Turn)

```
User WebSocket message (JSON)
  │
  ▼
main.py: websocket_chat()
  │
  ▼
conversation.py: process_turn()
  ├─► context_bus.add_turn()           [store user message]
  ├─► context_bus.snapshot()            [build context dict]
  ├─► skill_router.route()             [select skills]
  │     ├─► rule-based: canvas gap detection
  │     └─► LLM-based: DeepSeek API (if rule returns <2 skills)
  ├─► skill_registry.get_definition()  [load skill .md content]
  ├─► _call_llm()                      [DeepSeek API with compiled prompt]
  ├─► _parse_response()                [extract JSON from LLM output]
  ├─► canvas_state.apply_diff()        [update graph state]
  ├─► context_bus.add_turn()           [store assistant reply]
  └─► return result dict → WebSocket response
```

---

## 4. Call Graph (Python)

```
main.py
  ├── skill_registry.py
  │     └── models/schema.py (SkillMeta, SkillStatus)
  ├── skill_router.py
  │     ├── models/schema.py (SkillInvocation, CanvasGraph, ConversationTurn, CANVAS_ZONES, NODE_TYPE_TO_ZONE, Stage)
  │     └── skill_registry.py
  ├── context_bus.py
  │     └── models/schema.py (ContextObject, ConversationTurn, CanvasGraph)
  ├── canvas_state.py
  │     └── models/schema.py (CanvasGraph, GraphNode, GraphEdge, GraphDiff, NodeType, EdgeType, NODE_SPATIAL_BIAS)
  └── conversation.py
        ├── models/schema.py (ConversationTurn, SkillInvocation, Stage)
        ├── skill_registry.py
        ├── skill_router.py
        ├── context_bus.py
        └── canvas_state.py
```

---

## 5. External Dependencies

| Dependency | Where Used | Type |
|---|---|---|
| **DeepSeek API** (`api.deepseek.com`) | `skill_router.py`, `conversation.py`, `electron-app/main/ipc-handlers.js` | External LLM service |
| **FastAPI** | `main.py` | Framework |
| **uvicorn** | `main.py` | ASGI server |
| **websockets** | `main.py` (via FastAPI) | WebSocket protocol |
| **openai** (Python) | `skill_router.py`, `conversation.py` | LLM SDK (used with DeepSeek base_url) |
| **openai** (Node) | `electron-app/main/ipc-handlers.js` | LLM SDK (JS version) |
| **PyYAML** | `main.py`, `skill_registry.py` (implicit via .md parse) | Config loading |
| **Electron** | `electron-app/` | Desktop shell |
| **react-force-graph-3d** | Web/Electron renderer | 3D graph visualization |
| **Render.com** | `render.yaml` | Deployment platform |

---

## 6. Critical Architectural Smells

### A. PYTHON-JS DUPLICATION (HIGH SEVERITY)
The entire engine (`models/` + `engine/`) has been duplicated from Python to JavaScript for the Electron app. Six files are near-line-by-line ports:
- `models/schema.py` ↔ `electron-app/main/engine/schema.js`
- `engine/skill_registry.py` ↔ `electron-app/main/engine/skill-registry.js`
- `engine/skill_router.py` ↔ `electron-app/main/engine/skill-router.js`
- `engine/context_bus.py` ↔ `electron-app/main/engine/context-bus.js`
- `engine/canvas_state.py` ↔ `electron-app/main/engine/canvas-state.js`
- `engine/conversation.py` ↔ `electron-app/main/engine/conversation.js`

Any logic change must be made in TWO places. The JS versions are slightly simplified (no docstrings, less error handling) but otherwise identical in logic.

### B. MONOLITHIC SCHEMA (MEDIUM)
`models/schema.py` mixes concerns: 17 dataclasses + 4 enums + 3 constant maps + 1 alias in a single 340-line file. No separation between domain objects and presentation constants.

### C. HARDCODED CONFIGURATION (MEDIUM)
- `GAP_RULES` dict hardcoded in both `skill_router.py` and `skill-router.js`
- `stage_skills` mapping hardcoded in both
- `SYSTEM_PROMPT` as 80-line Python string literal in `conversation.py` and `conversation.js`
- Model names, API base URLs scattered across files
- `SPACE_SCALE`, `JITTER`, `MAX_SKILL_CHARS` are module-level constants

### D. NO TESTS (HIGH SEVERITY)
Zero test files in the entire repository. No `tests/` directory, no test frameworks in dependencies.

### E. MIXED CONCERNS IN CONVERSATION ENGINE (MEDIUM)
`conversation.py` handles: LLM API calls, JSON parsing, prompt assembly, stage state machine, canvas diff application, and turn recording — all in one 200-line file with one method (`process_turn`).

### F. MISSING ENGINE __init__.py (LOW)
Engine modules import each other via `engine.xxx` but there's no `engine/__init__.py`. Imports work only because `main.py` runs from the repo root.

### G. SYNC I/O AT IMPORT TIME (LOW)
`SkillRegistry.__init__()` does a synchronous filesystem scan of all skill files. Blocks startup.

### H. WEB/ELECTRON FRONTEND DUPLICATION (LOW)
`web/` and `electron-app/renderer/` both contain `index.html`, `app.jsx`, `themes.css`, `demo_graph.json`. Same content in two places.

---

## 7. Open Questions for Refactoring

1. Is the Electron app actively deployed? Or is it a prototype that can be retired in favor of the web version?
2. Should the skill definitions (30 .md files) remain on-disk or move to a structured format (YAML/JSON)?
3. What is the targeted deployment environment? (Render.com vs. local Electron vs. both?)
4. Are there users with active sessions relying on the current API format?
5. What LLM backends should be supported beyond DeepSeek? (OpenAI, Anthropic, Ollama?)

---

## 8. Recommended Refactoring Scope (Triage Notes)

**Tier 1 — Immediate High Impact:**
- Consolidate Python and JS engine into a single shared backend (eliminate duplication)
- Add test framework + basic smoke tests

**Tier 2 — Structural:**
- Split `models/schema.py` into domain objects + constants
- Extract `SYSTEM_PROMPT` and `GAP_RULES` to config files
- Add `engine/__init__.py`

**Tier 3 — Polish:**
- Async skill registry loading
- Proper config management (pydantic/dataclass with env vars)
- Unify web/Electron frontend into a single build pipeline
- Add proper logging with structured levels

