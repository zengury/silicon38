# PRD: Demonstration-Taught Guided Tour System

## Problem Statement

Operators of humanoid robots (Unitree G1, Agibot X2) need to demonstrate a physical tour path to the robot once, and then have the robot autonomously guide visitors along that same path with voice narration. Current solutions require manual waypoint programming or teleoperation for each tour, which is time-consuming and error-prone. The operator interface must be voice-only (hands-free) to allow natural interaction while working on the robot.

## Solution

A two-mode system:
- **Teaching Mode**: Operator walks the robot through the tour path while speaking narration. The robot records pose waypoints and associated voice clips.
- **Guiding Mode**: Robot autonomously replays the tour by navigating through recorded waypoints and playing back the narration at each stop.

The system must be resistant to hallucination — it should not invent waypoints or narration that were not recorded. A voice-only operator interface allows the operator to start/stop teaching, start/stop guiding, and query status without touching a screen.

## User Stories

1. As an operator, I want to start teaching mode via voice command, so that I can begin recording a tour without using my hands.
2. As an operator, I want the robot to record its current pose (x, y, yaw) as a waypoint when I speak a "mark" command, so that the tour path is captured accurately.
3. As an operator, I want to speak narration for each waypoint, and have the robot record the audio clip associated with that waypoint, so that the tour guide narration is captured naturally.
4. As an operator, I want to end teaching mode via voice command, so that the tour is finalized and saved.
5. As an operator, I want to start guiding mode via voice command, so that the robot autonomously replays the tour.
6. As an operator, I want the robot to navigate to each waypoint in sequence during guiding mode, so that the tour path is followed.
7. As an operator, I want the robot to play back the recorded narration at each waypoint during guiding mode, so that visitors hear the correct commentary.
8. As an operator, I want to stop guiding mode at any time via voice command, so that I can abort the tour if needed.
9. As an operator, I want to query the current status (idle, teaching, guiding, waypoint count) via voice, so that I know what the system is doing.
10. As an operator, I want the system to reject voice commands that are ambiguous or unrecognized, so that accidental activations do not occur.
11. As an operator, I want the system to confirm critical actions (start teaching, start guiding) before executing, so that I can avoid unintended state changes.
12. As an operator, I want the system to never invent waypoints or narration that were not recorded, so that the tour is faithful to the demonstration.
13. As an operator, I want the system to persist the tour across robot reboots, so that I do not have to reteach the tour after power cycling.
14. As an operator, I want to list saved tours via voice, so that I can select which tour to guide.
15. As an operator, I want to delete a saved tour via voice, so that I can manage storage.

## Implementation Decisions

- **Modules to build/modify**:
  - `pilot/apps/tour/` — New application module containing:
    - `engine.py` — Core TourApp class with state machine (idle, teaching, guiding).
    - `store.py` — TourStore for persistence (JSONL file).
    - `voice.py` — Voice interface module (speech-to-text, text-to-speech, command parsing).
    - `navigation.py` — Navigation interface (waypoint following, pose recording).
  - `pilot/apps/tour/tests/` — Test suite.
  - `pilot/daemon/` — Modify daemon to register the tour app and route voice commands.
- **Interfaces**:
  - `TourApp` exposes methods: `teach(waypoint, narration)`, `start_teaching()`, `stop_teaching()`, `start_guiding(tour_id)`, `stop_guiding()`, `status()`, `list_tours()`, `delete_tour(tour_id)`.
  - `TourStore` exposes: `save(tour)`, `load(tour_id)`, `list()`, `delete(tour_id)`.
  - `VoiceInterface` exposes: `listen() -> Command`, `speak(text)`, `confirm(prompt) -> bool`.
  - `NavigationInterface` exposes: `record_pose() -> Pose`, `navigate_to(pose)`, `stop_navigation()`.
- **State machine**:
  - States: `IDLE`, `TEACHING`, `GUIDING`.
  - Transitions: `start_teaching` (IDLE→TEACHING), `stop_teaching` (TEACHING→IDLE), `start_guiding` (IDLE→GUIDING), `stop_guiding` (GUIDING→IDLE).
  - Commands are only valid in certain states; invalid commands are rejected with a spoken error.
- **Anti-hallucination**:
  - The system never generates waypoints or narration. All data comes from operator demonstration.
  - Voice commands are parsed against a fixed grammar; unrecognized utterances are rejected.
  - Confirmation required for state transitions that could disrupt operation.
- **Persistence**: Tours are stored as JSONL files in `~/.manastone/tours/`. Each tour is a sequence of `(pose, narration_audio_path)` entries.
- **Voice interface**: Uses platform TTS/STT (e.g., macOS `say` and `speech-to-text` via `npx` or built-in engine). Commands are matched against a predefined list: "start teaching", "mark waypoint", "stop teaching", "start guiding", "stop guiding", "status", "list tours", "delete tour [id]".

## Testing Decisions

- **What makes a good test**: Test external behavior (state transitions, command acceptance/rejection, persistence round-trip) not internal implementation details. Use fake daemon and fake voice interface to isolate TourApp logic.
- **Modules to test**:
  - `TourApp` — State machine, command routing, anti-hallucination.
  - `TourStore` — Save/load/list/delete, file format, error handling.
  - `VoiceInterface` — Command parsing, confirmation flow.
- **Prior art**: See `tests/pilot/test_tour_app.py` for existing test patterns using `FakeDaemon`.

## Out of Scope

- Multi-tour simultaneous guiding.
- Dynamic obstacle avoidance during guiding (robot follows path; if blocked, stops and waits).
- Editing tours after recording (must re-teach).
- Visual SLAM or map building; uses odometry-based pose recording.
- Web or GUI interface; voice-only.
- Multi-language narration.
- Tour scheduling or calendar integration.

## Further Notes

- The system is designed for Unitree G1 and Agibot X2 robots, but the navigation interface abstracts robot-specific details.
- Voice commands should be simple and unambiguous. Example grammar: `"start teaching"`, `"mark"`, `"stop teaching"`, `"start guiding"`, `"stop guiding"`, `"status"`, `"list tours"`, `"delete tour [id]"`.
- Confirmation: After "start teaching", system says "Ready to record tour. Say 'mark' to record a waypoint." After "start guiding", system says "Starting tour [id]. Say 'stop guiding' to abort."
- The tour store uses JSONL format for append-friendly logging and easy inspection.

## Acceptance Criteria

1. **Teaching mode**: Operator says "start teaching", robot enters teaching mode. Operator walks robot to a location and says "mark". Robot records pose and prompts for narration. Operator speaks narration. Robot records audio. Repeat. Operator says "stop teaching". Tour is saved.
2. **Guiding mode**: Operator says "start guiding" (or "start guiding [tour id]"). Robot navigates to first waypoint, plays narration, waits 2 seconds, navigates to next waypoint, etc. After last waypoint, robot says "Tour complete." and returns to idle.
3. **Anti-hallucination**: Robot never generates waypoints or narration. All commands are validated against grammar. Invalid commands are rejected with spoken error.
4. **Persistence**: After teaching a tour and rebooting the robot, the tour is available via "list tours" and can be guided.
5. **Voice-only operation**: All interactions (start/stop teaching, start/stop guiding, status, list, delete) are performed via voice commands. No GUI required.