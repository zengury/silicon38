# Zoom-Out: manastone-diag Codebase Map

## Top-Level Architecture

```
manastone-diag (v0.4.0)
├── launcher.py              — Multi-server startup orchestrator (entry point)
├── server.py                — DEPRECATED legacy wrapper → delegates to launcher
├── config.py                — Global Config/LLMConfig singletons
├── ui.py                    — Gradio Web UI (v0.1-era, partially broken with v0.4)
└── [packages]
    ├── schema/loader.py     — YAML→RobotSchema, FieldRule, TopicSchema parser
    ├── dds_bridge/bridge.py — DDS data acquisition (mock + stub for real)
    ├── event/log.py         — SQLite append-only EventLog
    ├── event/detector.py    — Schema-driven threshold detector (polling loop)
    ├── servers/base.py      — AppState (shared singleton), init/shutdown
    ├── servers/core.py      — Core agent server (:8080, LLM tools)
    ├── servers/joints.py    — Joint subsystem server (:8081)
    ├── servers/power.py     — Power/BMS server (:8082)
    ├── servers/imu.py       — IMU/posture server (:8083)
    ├── servers/hand.py      — Dexterous hand server (:8084)
    ├── servers/vision.py    — Vision stub (:8085, M2)
    ├── servers/motion.py    — Motion stub (:8086, M2)
    ├── orchestrator/diagnostic.py — LLM + knowledge base query router
    ├── llm/client.py        — OpenAI-compatible LLM client (httpx)
    ├── memory/memdir.py     — File-based persistent memory (markdown+YAML)
    ├── memory/store.py      — Query-time memory recall (keyword overlap)
    ├── memory/extractor.py  — LLM-assisted memory extraction
    ├── discovery/ros2_discovery.py — ROS2 topic auto-discovery
    └── extensions/registry.py — Runtime extension loading (env-var driven)
```

## Module Responsibilities (one sentence each)

| Module | Responsibility |
|---|---|
| `launcher.py` | Reads `config/servers.yaml`, starts enabled MCP servers concurrently on dedicated ports, initializes shared AppState |
| `server.py` | Deprecated v0.1 entry point; warns and delegates to launcher for backward compatibility |
| `config.py` | Holds `LLMConfig` (URLs, model names, API keys) and `Config` (mock mode, paths); exposed as module-level global singleton via `get_config()` |
| `ui.py` | Gradio web UI with tabs for chat-diagnosis, real-time status, quick-diagnosis, and scenario switching; references v0.1-era modules (`resources.joints`, `mock_scenarios`) that no longer exist |
| `schema/loader.py` | Parses `config/robot_schema.yaml` into typed dataclasses (`RobotSchema`, `TopicSchema`, `FieldRule`, `ComponentInfo`, `EventTypeInfo`); auto-generates joint components from `motor_index_map` |
| `dds_bridge/bridge.py` | Subscribes to ROS2 topics (mock mode: generates synthetic data; real mode: stub), caches per-topic sliding windows, exposes `get_topic_data()` and `get_all_latest()` |
| `event/log.py` | SQLite `EventLog` with append-only semantics, causal chains (`prev_event_id`), active-warning detection, component history queries |
| `event/detector.py` | Background polling loop: reads DDSBridge cache, evaluates `FieldRule` thresholds per topic, fires `SemanticEvent` into EventLog; includes STALE detection |
| `servers/base.py` | `AppState` dataclass holding all shared services (schema, dds, event_log, detector, orchestrator, memory); singleton `init_shared_state()` with idempotent init |
| `servers/core.py` | MCP server with LLM-powered tools: `system_status`, `diagnose`, `lookup_fault`, `schema_overview`, `run_discovery`, `recent_events`, `event_stats`, `server_registry` |
| `servers/joints.py` | MCP server: `joint_status`, `joint_alerts`, `joint_history`, `joint_compare`, `joint_schema` |
| `servers/power.py` | MCP server: `power_status`, `power_alerts`, `power_history`, `charge_estimate`; contains hardcoded voltage/temperature thresholds |
| `servers/imu.py` | MCP server: `posture_status`, `posture_alerts`, `posture_history`, `fall_risk`; contains hardcoded tilt thresholds (20°/30°) |
| `servers/hand.py` | MCP server: `hand_status`, `hand_alerts`, `hand_history`, `grasp_test` |
| `servers/vision.py` | MCP stub (M2): `vision_status`, `vision_alerts` |
| `servers/motion.py` | MCP stub (M2): `motion_status`, `motion_alerts`; contains typo `ensure_aware` |
| `orchestrator/diagnostic.py` | Routes user natural-language queries: retrieves active warnings from EventLog, matches against YAML fault library and SKILL.md docs, calls LLM, falls back to rule-based response |
| `llm/client.py` | Async httpx client for OpenAI-compatible `/chat/completions`; supports local + remote endpoints |
| `memory/memdir.py` | File-based memory: markdown files with YAML frontmatter, MEMORY.md index, upsert/scan/sanitize utilities |
| `memory/store.py` | `FileMemoryStore.build_recall_context()` — selects relevant memories by keyword overlap for injection into LLM prompt |
| `memory/extractor.py` | `MemDirExtractor.extract_and_apply()` — calls LLM with context to generate memory upserts/deletes, applies them safely |
| `discovery/ros2_discovery.py` | Calls `ros2 topic list/info/echo` via subprocess, infers component types and field semantics, generates `discovered_schema.yaml` draft |
| `extensions/registry.py` | `ExtensionRegistry` loads modules by env var, calls each module's `register(server)` to add tools/resources at runtime |

## Call Graph (directional)

```
launcher.py
  ├─► servers/base.py:init_shared_state()
  │     ├─► schema/loader.py:SchemaLoader.load()
  │     ├─► dds_bridge/bridge.py:DDSBridge.start()
  │     ├─► event/log.py:EventLog.__init__()
  │     ├─► event/detector.py:EventDetector.start()
  │     ├─► llm/client.py:LLMClient.__init__()
  │     ├─► memory/memdir.py:ensure_robot_identity_memory()
  │     ├─► memory/store.py:FileMemoryStore.__init__()
  │     ├─► memory/extractor.py:MemDirExtractor.__init__()
  │     └─► orchestrator/diagnostic.py:DiagnosticOrchestrator.__init__()
  │           ├─► knowledge/fault_library.yaml (disk read)
  │           └─► knowledge/skills/*/SKILL.md (disk read)
  │
  └─► servers/core.py:create_server()
  └─► servers/joints.py:create_server()
  └─► servers/power.py:create_server()
  └─► servers/imu.py:create_server()
  └─► servers/hand.py:create_server()
  └─► servers/vision.py:create_server()
  └─► servers/motion.py:create_server()
        └─ (each) → servers/base.py:get_shared_state() for tool calls

server.py (deprecated)
  └─► launcher.py:main()  (delegation)

ui.py (v0.1, partially broken)
  ├─► dds_bridge/bridge.py:DDSBridge  (direct, not through AppState)
  ├─► llm/client.py:LLMClient
  ├─► orchestrator/diagnostic.py:DiagnosticOrchestrator  (wrong constructor sig)
  └─► resources.joints:JointsResource  (module no longer exists)
```

## Data Flow

```
ROS2 Topics / Mock Generators
        │
        ▼
  DDSBridge (TopicCache sliding windows)
        │
        ▼
  EventDetector (polling loop: FieldRule.evaluate() per topic)
        │
        ├──► EventLog (SQLite append-only, causal chain)
        │      │
        │      ▼
        │   MCP Tools (get_active_warnings, query_recent, query_component_history)
        │      │
        │      ▼
        │   Orchestrator (LLM prompt assembly + YAML/SKILL.md retrieval)
        │      │
        │      ▼
        │   LLM Client (httpx → local Qwen / remote OpenAI)
        │      │
        │      ▼
        │   MemDir (auto-enrich memories after each query)
        │
        ▼
  MCP Servers → SSE transport → External LLM agents (Claude, Cursor, etc.)
```

## External Dependencies

| Dependency | Role |
|---|---|
| `mcp>=1.0.0` | FastMCP server framework (all servers) |
| `gradio>=4.0.0` | Web UI (ui.py) |
| `httpx>=0.25.0` | Async HTTP client (LLM calls) |
| `pyyaml>=6.0` | YAML parsing (schema, config, fault library) |
| `numpy>=1.24.0` | Numerical operations |
| `cyclonedds>=0.10.0` (optional) | Real DDS communication |
| `sqlite3` (stdlib) | Event log persistence |
| OpenAI-compatible API | LLM inference (local Qwen or remote) |
| `ros2` CLI | Topic discovery (subprocess) |

## Key Architectural Decisions

1. **Schema-driven thresholds**: All event detection rules live in `robot_schema.yaml`, not code. The `FieldRule.evaluate()` method is the single point of threshold evaluation.
2. **Multi-server MCP**: One MCP server per hardware subsystem, each on its own port. This allows selective enable/disable via `servers.yaml`.
3. **Shared AppState singleton**: All servers in the same process share one `AppState` containing schema, DDSBridge, EventLog, EventDetector, and orchestrator.
4. **Append-only EventLog**: SQLite with no UPDATE/DELETE. Causal chains via `prev_event_id`. Hash-based tamper detection.
5. **Mock-first development**: DDSBridge defaults to mock mode; real DDS is a stub (`_start_real_dds` falls back to mock).

## Known Issues (non-exhaustive, for downstream attention)

1. **ui.py is stale**: References `resources.joints`, `mock_scenarios`, old `DiagnosticOrchestrator(2 args)` — won't run on v0.4.
2. **Hardcoded thresholds in server tools**: `power.py` has 46.0V/43.0V, `imu.py` has 20°/30° — these duplicate what should come from the schema's FieldRule system.
3. **Server boilerplate duplication**: 7 server files share ~15 identical lines each (`main()`, `_lifespan`, import block).
4. **Motion server typo**: `ensure_aware=False` should be `ensure_ascii=False`.
5. **config.py global mutable singleton**: `get_config()` has side effects (loads dotenv on first call).
6. **Orchestrator hardcoded keyword map**: `_find_yaml_skills()` has a `kw_map` dict mapping fault IDs to keywords, duplicating knowledge in YAML.
7. **Real DDS unimplemented**: DDSBridge falls back to mock — no CycloneDDS integration yet.
8. **No DI container**: Global singletons everywhere (`_shared`, `_config`), making testing and multi-robot support difficult.

## Completion Report

```yaml
completion_report:
  what_was_done: "Mapped all 34 Python source files across 11 packages. Identified module responsibilities, call graph, data flow, external dependencies, and 8 known issues."
  key_decisions:
    - decision: "Scope covers entire src/manastone_diag tree"
      rationale: "Refactor task is broad — all modules are candidates for optimization"
    - decision: "Included ui.py despite being stale"
      rationale: "It's still in the project and has entry point; downstream must decide to fix or remove"
  handoff_focus:
    - "Remove server boilerplate via shared factory"
    - "Fix or remove ui.py"
    - "Move hardcoded thresholds from server tools into schema/FieldRule system"
    - "Fix motion.py typo"
    - "Extract orchestrator keyword mapping into data file"
    - "Consider proper DI instead of global singletons"
    - "Implement real DDS bridge"
  open_questions:
    - "Should ui.py be deleted or rewritten for v0.4?"
    - "Should hardcoded server thresholds be removed (breaking change to tools) or kept as UI convenience layer?"
    - "Is multi-process deployment needed, or is single-process with multiple SSE ports sufficient?"
  known_constraints:
    - "Must stay offline-friendly (no forced cloud dependency)"
    - "Must preserve MCP tool contracts (backward compatible API)"
    - "Python 3.10+ required"
    - "DDS domain ID 0 (G1 hardware constraint)"
  iteration_context: null
```
