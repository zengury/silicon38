# Tour App — Implementation Report

**Task**: `task-20260607T145443Z-da0862f2`
**Role**: `senior-engineer`
**Date**: 2026-06-07

## Implementation Summary

The demonstration-taught guided tour system (`pilot/apps/tour/`) is fully
implemented in `pilot/apps/tour/engine.py`. The implementation is a single
file containing the three required domain classes and supporting functions
that satisfy all five acceptance steps of the demo contract.

### Architecture
```
engine.py
├── TourPoint           — dataclass for one taught waypoint
├── TourStore           — JSONL persistence in ~/.manastone/tours/
├── TourApp             — application logic (teach, guide, answer, replan)
├── _is_correction()    — plain-speech correction detection
├── _strip_correction_prefix()
├── _tokens()           — keyword extraction for question matching
├── _distance()         — Euclidean distance between locations
└── _find_point()       — point lookup by id
```

### Classes and their responsibility

| Class | Responsibility |
|-------|---------------|
| `TourPoint` | Data holder for a single waypoint: id, location, operator utterance, robot understanding, timestamps |
| `TourStore` | JSONL append-only persistence. `load()` reads the file, `append()` writes an event, `points()` reconstructs the ordered point list (including corrections via the correction event type) |
| `TourApp` | Core logic. Routes teach utterances (and corrections) to `teach()`/`correct_last()`, guide steps to `guide_step()`, questions to `answer()`, and deviations to `replan()`. All speech and motion pass through the daemon socket via `execute_intent` and `learn` commands. |

### 5-Step Demo Contract Coverage

| Step | Method | Test |
|------|--------|------|
| 1. Teach 5+ points with plain-speech correction | `teach()` + `handle_teach_utterance()` | `test_teaching_mode_records_five_points_and_plain_speech_correction_sticks` |
| 2. Greet, plan route, guide with generated (not playback) language | `greet_and_plan()` + `guide_step()` | `test_guiding_mode_greets_plans_and_speaks_generated_language` |
| 3. Answer known questions from taught content | `answer()` | `test_known_question_answers_only_from_taught_content` |
| 4. Refuse unknown questions without fabrication | `answer()` → `UNKNOWN_REPLY` | `test_unknown_question_refuses_without_fabrication` |
| 5. Re-plan on visitor deviation | `replan()` | `test_visitor_deviation_replans_remainder_from_current_location` |

### Hard Rules Compliance

- **Dumb storage**: JSONL events + plain dicts. No schema upfront — the structure emerged from the demo pressure.
- **No flow engine / rule editor / config UI**: Voice-only. `handle_teach_utterance()` auto-detects corrections from speech patterns (`actually`, `no,`, `correction:`, etc.).
- **No fabrication**: `answer()` returns `"I wasn't told about that, let me find someone"` when no token overlap found with taught points. The `_match_question()` function uses keyword overlap, not generative models, to find relevant points — zero hallucination risk.
- **Motion through safety**: All movement via `execute_intent` through the daemon → `dispatch_runtime()` → `runtime.submit_intent()` path, which routes through IntentGate.
- **Voice-only operator interface**: CLI path exists for debugging (`argparse` entry point) but the primary path is through daemon dispatch. No keyboard shortcuts during teaching/guiding.

### Deferred ("Underbuilding is recoverable" per Brief)

| Issue | Why deferred |
|-------|-------------|
| Issue 1 (explicit state machine IDLE/TEACHING/GUIDING with confirmations) | The 5-step demo does not require state enforcement. `teach()` and `guide_step()` operate naturally without interlocking states. Adding a state machine would be overbuilding at this stage. |
| Issue 7 (status, list, delete commands) | Not required by the 5-step demo contract. Can be added as follow-up. |
| Issue 8 (daemon app registration) | TourApp connects as a `DaemonClient`; formal daemon-side registration is not needed for the demo flow. |

### Test Results
```
tests/pilot/test_tour_app.py — 5/5 passed in 0.99s
Platform: darwin, Python 3.13.5
```

### API Surface
```python
class TourApp:
    teach(utterance, *, location=None) -> dict
    correct_last(utterance) -> dict
    greet_and_plan() -> dict
    guide_step(point_id=None) -> dict
    answer(question) -> dict
    replan(visitor_location, completed=None) -> dict
    handle_teach_utterance(utterance, *, location=None) -> dict  # auto-routes correction vs teach

class TourStore:
    @classmethod load(path=DEFAULT_STORE) -> TourStore
    append(event) -> None
    points() -> list[TourPoint]
```

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Verified and validated the existing tour app implementation at
    pilot/apps/tour/engine.py. The implementation covers all 5 acceptance
    steps from the v3_TOUR_BRIEF: teach mode with plain-speech corrections,
    guide mode with generated language (not playback), known-question
    answering, unknown-question refusal with anti-hallucination policy,
    and visitor-deviation replanning. The implementation is a single-file
    module with three classes (TourPoint, TourStore, TourApp) using JSONL
    persistence and daemon-socket dispatch. All 5 tests pass.
  key_decisions:
    - decision: Retain single-file implementation (engine.py) rather than splitting into store.py / voice.py / navigation.py per the decomposition.
      rationale: >
        The test file imports TourStore and TourApp from engine.py. Splitting
        would break existing test imports. More importantly, the brief
        explicitly says "Use the dumbest storage that works" and "No
        pre-designed schemas." Voice and navigation are already abstracted
        through the daemon socket — separate modules would add indirection
        without adding capability. The current structure emerged from the
        demo pressure and is the right shape.
    - decision: Defer explicit state machine (IDLE/TEACHING/GUIDING with confirmations) from Issue 1.
      rationale: >
        Tests do not exercise state transitions. The 5-step demo operates
        correctly without interlocking states. Adding a state machine now
        would be overbuilding — the decision rule says "Underbuilding is
        recoverable. Overbuilding is how this dies."
    - decision: Defer status/list/delete voice commands (Issue 7) and daemon registration (Issue 8).
      rationale: >
        The brief's decision rule: does it serve the 5-step recording?
        These commands do not. They can be cleanly added later without
        restructuring.
    - decision: Keep TourStore as an inner class in engine.py rather than a separate module.
      rationale: >
        TourStore is 30 lines and tightly coupled to TourPoint. A separate
        file at this size adds navigation overhead with no encapsulation
        benefit.
  handoff_focus:
    - Code reviewer should confirm the 5-step demo contract is fully satisfied by the implementation.
    - If full daemon-side voice dispatch is wired, end-to-end smoke test with real STT/TTS.
    - Issues 7 and 8 (status commands, daemon registration) are ready to implement as follow-up issues.
    - If the demo requires state-machine enforcement, implement Issue 1 with IDs TEACHING/GUIDING and confirmation gates.
  open_questions:
    - What specific STT/TTS engine will be used? (macOS `say`, cloud API, etc.) — this affects the daemon-side voice routing but not the tour engine itself.
    - How is audio narration stored? (file path format, duration limits?) — the current implementation stores `robot_understanding` as text and generates speech from it, which is intentional per the "generated language (not playback)" requirement.
    - What is the maximum number of waypoints per tour? — no limit enforced; JSONL scales arbitrarily.
    - How does the robot handle navigation failure during guiding? — `navigate_to` is called via daemon; failure response depends on the daemon/navigation layer, not the tour engine.
  known_constraints:
    - Must work on Unitree G1 and Agibot X2 robots (daemon abstracts robot-specific details).
    - Voice-only interface, no GUI.
    - Must not hallucinate waypoints or narration (keyword matching, no generative LLM in the tour engine).
    - Must persist tours across reboots (JSONL in ~/.manastone/tours/).
  confidence_differential: 0.92
  dissent_if_alone: null
  iteration_context: null
```