## Issues

### Issue 1: TourApp State Machine & Command Routing
- **Title**: Implement TourApp state machine with IDLE, TEACHING, GUIDING states and command routing
- **Description**: Create the core TourApp class in `pilot/apps/tour/engine.py` with a state machine (IDLE, TEACHING, GUIDING). Implement command routing: voice commands are accepted only in valid states (e.g., "mark waypoint" only in TEACHING). Invalid commands are rejected with a spoken error. Expose methods: `start_teaching()`, `stop_teaching()`, `start_guiding(tour_id)`, `stop_guiding()`, `status()`, `list_tours()`, `delete_tour(tour_id)`. Confirmation required for state transitions (start_teaching, start_guiding).
- **Acceptance Criteria**:
  - [ ] State machine starts in IDLE.
  - [ ] `start_teaching()` transitions IDLE→TEACHING after confirmation.
  - [ ] `stop_teaching()` transitions TEACHING→IDLE.
  - [ ] `start_guiding(tour_id)` transitions IDLE→GUIDING after confirmation.
  - [ ] `stop_guiding()` transitions GUIDING→IDLE.
  - [ ] Invalid commands in current state return spoken error.
  - [ ] Confirmation prompt is issued for start_teaching and start_guiding.
- **Estimated Size**: M
- **Blocked By**: None

### Issue 2: TourStore Persistence Layer
- **Title**: Implement TourStore for JSONL-based tour persistence
- **Description**: Create `pilot/apps/tour/store.py` with TourStore class. Tours are stored as JSONL files in `~/.manastone/tours/`. Each tour is a sequence of `(pose, narration_audio_path)` entries. Methods: `save(tour)`, `load(tour_id)`, `list()`, `delete(tour_id)`. Handle file I/O errors gracefully.
- **Acceptance Criteria**:
  - [ ] `save(tour)` writes tour data to a JSONL file.
  - [ ] `load(tour_id)` returns the tour from file.
  - [ ] `list()` returns list of saved tour IDs.
  - [ ] `delete(tour_id)` removes the tour file.
  - [ ] File format is valid JSONL.
  - [ ] Error handling for missing files, corrupt data.
- **Estimated Size**: S
- **Blocked By**: None

### Issue 3: Voice Interface Module
- **Title**: Implement VoiceInterface for speech-to-text, text-to-speech, and command parsing
- **Description**: Create `pilot/apps/tour/voice.py` with VoiceInterface class. Uses platform TTS/STT (e.g., macOS `say` and speech-to-text via `npx` or built-in engine). Exposes: `listen() -> Command`, `speak(text)`, `confirm(prompt) -> bool`. Commands are parsed against a fixed grammar: "start teaching", "mark waypoint", "stop teaching", "start guiding", "stop guiding", "status", "list tours", "delete tour [id]". Unrecognized utterances are rejected.
- **Acceptance Criteria**:
  - [ ] `listen()` returns a Command object for recognized grammar.
  - [ ] `listen()` returns None for unrecognized utterances.
  - [ ] `speak(text)` outputs audio via TTS.
  - [ ] `confirm(prompt)` returns True/False based on user response.
  - [ ] Grammar matching is exact (no fuzzy matching).
- **Estimated Size**: M
- **Blocked By**: None

### Issue 4: Navigation Interface
- **Title**: Implement NavigationInterface for pose recording and waypoint following
- **Description**: Create `pilot/apps/tour/navigation.py` with NavigationInterface class. Abstracts robot-specific navigation. Exposes: `record_pose() -> Pose`, `navigate_to(pose)`, `stop_navigation()`. Uses robot's odometry for pose (x, y, yaw). For Unitree G1 and Agibot X2, interface with existing robot adapters.
- **Acceptance Criteria**:
  - [ ] `record_pose()` returns current robot pose (x, y, yaw).
  - [ ] `navigate_to(pose)` moves robot to target pose.
  - [ ] `stop_navigation()` halts current navigation.
  - [ ] Works with both Unitree G1 and Agibot X2 (via adapter pattern).
- **Estimated Size**: M
- **Blocked By**: None

### Issue 5: Teaching Mode Integration
- **Title**: Wire up teaching mode: voice commands, waypoint recording, narration capture, tour save
- **Description**: Integrate TourApp, TourStore, VoiceInterface, and NavigationInterface for teaching mode. When operator says "start teaching", robot enters teaching mode. Operator walks robot to location and says "mark waypoint". Robot records pose and prompts for narration. Operator speaks narration, robot records audio. Repeat. Operator says "stop teaching". Tour is saved via TourStore. Audio narration stored as files (path stored in tour data).
- **Acceptance Criteria**:
  - [ ] "start teaching" triggers teaching mode after confirmation.
  - [ ] "mark waypoint" records current pose and prompts for narration.
  - [ ] Narration audio is recorded and stored.
  - [ ] "stop teaching" saves tour and returns to IDLE.
  - [ ] Tour data includes waypoints with poses and audio paths.
- **Estimated Size**: L
- **Blocked By**: Issue 1, Issue 2, Issue 3, Issue 4

### Issue 6: Guiding Mode Integration
- **Title**: Wire up guiding mode: tour selection, waypoint navigation, narration playback
- **Description**: Integrate TourApp, TourStore, VoiceInterface, and NavigationInterface for guiding mode. Operator says "start guiding [tour id]" (or "start guiding" with selection). Robot navigates to each waypoint in sequence, plays recorded narration at each stop, waits 2 seconds, then proceeds. After last waypoint, robot says "Tour complete." and returns to IDLE. "stop guiding" aborts at any time.
- **Acceptance Criteria**:
  - [ ] "start guiding [tour id]" starts guiding mode after confirmation.
  - [ ] Robot navigates to each waypoint in order.
  - [ ] Narration audio plays at each waypoint.
  - [ ] 2-second pause between waypoints.
  - [ ] After last waypoint, robot announces completion and returns to IDLE.
  - [ ] "stop guiding" aborts guiding and returns to IDLE.
- **Estimated Size**: L
- **Blocked By**: Issue 1, Issue 2, Issue 3, Issue 4

### Issue 7: Voice Commands for Status, List Tours, Delete Tour
- **Title**: Implement status, list tours, and delete tour voice commands
- **Description**: Add support for "status", "list tours", and "delete tour [id]" voice commands. "status" reports current state and waypoint count. "list tours" enumerates saved tours. "delete tour [id]" removes a tour after confirmation.
- **Acceptance Criteria**:
  - [ ] "status" speaks current state (idle/teaching/guiding) and waypoint count.
  - [ ] "list tours" speaks list of saved tour IDs.
  - [ ] "delete tour [id]" deletes the tour after confirmation.
  - [ ] Invalid tour ID for delete returns error.
- **Estimated Size**: S
- **Blocked By**: Issue 2, Issue 3

### Issue 8: Daemon Registration & Voice Command Routing
- **Title**: Register tour app with daemon and route voice commands
- **Description**: Modify `pilot/daemon/` to register the TourApp and route incoming voice commands to it. Ensure voice commands from the platform's STT are dispatched to the tour app's command handler.
- **Acceptance Criteria**:
  - [ ] Daemon registers TourApp on startup.
  - [ ] Voice commands are routed to TourApp.
  - [ ] TourApp responses are spoken via TTS.
- **Estimated Size**: M
- **Blocked By**: Issue 5, Issue 6, Issue 7

### Issue 9: Anti-Hallucination & Grammar Validation Tests
- **Title**: Write tests for anti-hallucination and command grammar validation
- **Description**: Write unit tests verifying that the system never generates waypoints or narration, and that voice commands are strictly parsed against the fixed grammar. Use FakeDaemon and fake voice interface to isolate TourApp logic.
- **Acceptance Criteria**:
  - [ ] Test that invalid commands are rejected with spoken error.
  - [ ] Test that no waypoints or narration are generated by the system.
  - [ ] Test state transitions with confirmation.
  - [ ] Test persistence round-trip.
- **Estimated Size**: S
- **Blocked By**: Issue 1, Issue 2, Issue 3

### Issue 10: End-to-End Integration Test
- **Title**: Write end-to-end integration test for teaching and guiding flow
- **Description**: Write an integration test that simulates a full teaching session (start teaching, mark waypoints with narration, stop teaching) and a full guiding session (start guiding, verify navigation and narration playback, stop guiding). Use fake implementations for voice and navigation.
- **Acceptance Criteria**:
  - [ ] Test covers full teaching flow.
  - [ ] Test covers full guiding flow.
  - [ ] Test verifies persistence across sessions.
  - [ ] Test verifies anti-hallucination.
- **Estimated Size**: M
- **Blocked By**: Issue 5, Issue 6, Issue 9

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the PRD for the demonstration-taught guided tour system into 10 independently implementable issues. Each issue has acceptance criteria, estimated size, and dependency information. The decomposition follows vertical slice principles where possible, with core infrastructure issues (state machine, persistence, voice, navigation) as foundational blocks, followed by integration issues for teaching and guiding modes, then auxiliary commands, daemon integration, and tests.
  key_decisions:
    - decision: Split voice interface and navigation interface into separate issues from the core state machine to allow parallel development.
      rationale: These modules have no interdependencies and can be built concurrently.
    - decision: Teaching and guiding mode integration are separate issues, each depending on the four core modules.
      rationale: They are independent vertical slices that can be implemented and tested separately.
    - decision: Tests are split into unit tests (anti-hallucination/grammar) and integration tests (end-to-end flow).
      rationale: Unit tests can be written early; integration tests require all components.
    - decision: Daemon registration is a separate issue to avoid blocking other work.
      rationale: The tour app can be tested in isolation before daemon integration.
  handoff_focus:
    - Implement issues in dependency order: core modules first (Issues 1-4), then teaching/guiding integration (5-6), then auxiliary commands (7), daemon (8), and tests (9-10).
    - Each issue is independently testable with mocks/fakes.
  open_questions:
    - What specific STT/TTS engine will be used? (macOS built-in, cloud API, etc.)
    - How is audio narration stored? (file path, format, duration limits?)
    - What is the maximum number of waypoints per tour?
    - How does the robot handle navigation failure during guiding? (stop and wait, retry, abort?)
  known_constraints:
    - Must work on Unitree G1 and Agibot X2 robots.
    - Voice-only interface, no GUI.
    - Must not hallucinate waypoints or narration.
    - Must persist tours across reboots.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→to-issues-20260607-145549.yaml
  retained_context:
    decisions:
      - Tour system implemented as new app module under pilot/apps/tour/
      - Voice-only operator interface using platform TTS/STT
      - Anti-hallucination enforced by fixed grammar and no generative data
      - Persistence via JSONL files in ~/.manastone/tours/
      - State machine with three states: IDLE, TEACHING, GUIDING
      - Confirmation required for state transitions
    constraints:
      - Must work on Unitree G1 and Agibot X2 robots
      - Voice-only interface, no GUI
      - Must not hallucinate waypoints or narration
      - Must persist tours across reboots
    assumptions:
      - Platform provides speech-to-text and text-to-speech capabilities
      - Robot provides odometry-based pose recording and navigation
      - Operator has physical access to robot during teaching
    open_questions:
      - What specific STT/TTS engine will be used?
      - How is audio narration stored?
      - What is the maximum number of waypoints per tour?
      - How does the robot handle navigation failure during guiding?
  omitted_context:
    - Detailed file list of entire repository (irrelevant to decomposition)
    - Bootstrap and packaging details (not needed for issues)
    - Existing skill files and robot-specific configurations (out of scope)
  compression_rationale:
    method: Semantic filtering: retained only context directly relevant to issue decomposition (PRD requirements, architecture decisions, constraints). Omitted unrelated code files and infrastructure details.
    loss_notes: []
  quality_checks:
    - name: independent_issues_present
      passed: true
    - name: dependencies_named
      passed: true
    - name: every_issue_has_acceptance_criteria
      passed: true
    - name: dependency_graph_acyclic
      passed: true
    - name: no_issue_blocked_by_unspecified_dependency
      passed: true
```