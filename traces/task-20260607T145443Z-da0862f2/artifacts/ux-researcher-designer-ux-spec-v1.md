# UX Specification: Demonstration-Taught Guided Tour System

## 1. User Persona: Robot Tour Operator

**Name:** Alex
**Role:** Robot Operator / Facility Guide
**Context:** Works in a facility (museum, factory, office) where humanoid robots (Unitree G1, Agibot X2) are used to guide visitors. Alex needs to set up tours quickly without technical programming.

**Goals:**
- Teach a tour path and narration in one walk-through
- Start/stop tours hands-free while working near the robot
- Ensure tours are accurate and repeatable
- Manage multiple tours for different routes

**Frustrations:**
- Manual waypoint programming is slow and error-prone
- Touching a screen while working on the robot is inconvenient
- Tour inaccuracies (hallucinated waypoints) erode visitor trust

**Design Implications:**
- Voice-only interaction must be reliable and unambiguous
- Teaching must feel natural: walk, speak, mark
- Guiding must be autonomous but abortable
- Tours must persist across reboots

## 2. User Journey Map

### Teaching Mode

| Stage | Actions | Touchpoints | Emotions | Pain Points | Opportunities |
|-------|---------|-------------|----------|-------------|---------------|
| Initiate | Say "start teaching" | Voice | Ready | None | Clear confirmation |
| Walk & Mark | Walk to location, say "mark" | Voice, Robot pose | Focused | Must remember to say "mark" | Audible prompt after each mark |
| Narrate | Speak narration for waypoint | Voice | Natural | Narration may be too long/short | Indicate recording duration |
| Repeat | Walk to next location, mark, narrate | Voice, Robot pose | Engaged | Losing count of waypoints | Announce waypoint number |
| Finalize | Say "stop teaching" | Voice | Satisfied | None | Confirm tour saved with name |

### Guiding Mode

| Stage | Actions | Touchpoints | Emotions | Pain Points | Opportunities |
|-------|---------|-------------|----------|-------------|---------------|
| Select | Say "start guiding [tour id]" | Voice | Expectant | Must remember tour ID | List tours on demand |
| Navigate | Robot moves to waypoint | Robot motion | Curious | Robot may be slow | Show progress indicator |
| Narrate | Robot plays audio at waypoint | Audio | Engaged | Narration may not sync perfectly | Allow pause between nav and audio |
| Continue | Robot moves to next waypoint | Robot motion | Following | Path may be blocked | Stop and wait, then retry |
| Complete | Robot says "Tour complete" | Voice | Satisfied | None | Offer to repeat or end |

## 3. Interaction Model

### Voice Command Grammar

| Command | Valid States | Action |
|---------|--------------|--------|
| "start teaching" | IDLE | Enter TEACHING, confirm |
| "mark" | TEACHING | Record pose, prompt narration |
| "stop teaching" | TEACHING | Save tour, return to IDLE |
| "start guiding [tour id]" | IDLE | Enter GUIDING, navigate to first waypoint |
| "stop guiding" | GUIDING | Abort tour, return to IDLE |
| "status" | Any | Speak current state and waypoint count |
| "list tours" | IDLE | Speak list of saved tours |
| "delete tour [id]" | IDLE | Delete tour after confirmation |

### Confirmation Flow

- **Start Teaching:** System says "Ready to record tour. Say 'mark' to record a waypoint."
- **Start Guiding:** System says "Starting tour [id]. Say 'stop guiding' to abort."
- **Delete Tour:** System says "Are you sure you want to delete tour [id]? Say 'yes' to confirm."

### Error Handling

- **Unrecognized command:** System says "Command not recognized. Please try again."
- **Invalid state command:** System says "Cannot [command] while in [current state]."
- **Navigation failure:** Robot stops, says "Navigation blocked. Waiting..." then retries or aborts.

## 4. UX Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Voice command false positive | High | Fixed grammar, confirmation for critical actions |
| Hallucinated waypoints | Critical | Never generate waypoints; only record from demonstration |
| Narration audio corruption | Medium | Validate audio file after recording; retry on failure |
| Robot navigation error | High | Stop and wait; operator can abort via voice |
| Tour data loss | High | Persist to JSONL; atomic writes |
| Operator confusion about state | Medium | "status" command always available; state announced on transitions |

## 5. Validation Approach

### Usability Test Plan

**Research Questions:**
1. Can operators teach a tour without prior training?
2. Can operators start/stop guiding without errors?
3. Do operators feel confident in the system's accuracy?

**Method:** Moderated remote usability test with 5 participants (robot operators or simulant).

**Tasks:**
1. Teach a 3-waypoint tour with narration
2. Start guiding the tour
3. Stop guiding mid-tour
4. List and delete a tour
5. Query status

**Success Metrics:**
- Task completion rate > 80%
- Errors per task < 2
- System Usability Scale (SUS) score > 70

### Heuristic Evaluation

| Heuristic | Check |
|-----------|-------|
| Visibility of system status | State announced on transitions; "status" command |
| Match between system and real world | Commands are natural phrases |
| User control and freedom | "stop guiding" aborts at any time |
| Consistency and standards | Consistent grammar across commands |
| Error prevention | Confirmation for critical actions |
| Recognition rather than recall | "list tours" provides options |
| Flexibility and efficiency | Direct "start guiding [id]" |
| Aesthetic and minimalist design | Minimal voice prompts |
| Help users recognize, diagnose, recover | Clear error messages |
| Help and documentation | "status" command |

## 6. Design Requirements for Engineering

### State Machine

```
States: IDLE, TEACHING, GUIDING
Transitions:
  IDLE -> TEACHING: on "start teaching" (with confirmation)
  TEACHING -> IDLE: on "stop teaching"
  IDLE -> GUIDING: on "start guiding [id]" (with confirmation)
  GUIDING -> IDLE: on "stop guiding" or tour complete
```

### Voice Interface

- STT: Must parse against fixed grammar list; reject unrecognized
- TTS: Must speak prompts, confirmations, errors, and narration
- Confirmation: After critical commands, system must ask for verbal confirmation

### Navigation Interface

- `record_pose()`: Returns current (x, y, yaw)
- `navigate_to(pose)`: Blocks until arrival or failure; returns success/failure
- `stop_navigation()`: Aborts current navigation

### Persistence

- Store tours as JSONL in `~/.manastone/tours/`
- Each entry: `{"tour_id": "...", "waypoints": [{"pose": {...}, "audio_path": "..."}]}`
- Atomic writes: write to temp file, then rename

### Anti-Hallucination

- Never generate waypoints or narration
- All data comes from operator demonstration
- Voice commands parsed against fixed grammar; unrecognized rejected
- Confirmation required for state transitions

## 7. Edge Cases

- **Empty tour:** If operator says "stop teaching" without marking any waypoints, system should discard and warn.
- **Duplicate tour names:** System should auto-generate unique tour IDs or ask for confirmation.
- **Audio recording failure:** If narration recording fails, system should retry or skip with warning.
- **Navigation timeout:** If robot cannot reach waypoint within timeout, stop and wait for operator command.
- **Power loss during teaching:** Unsaved tour data is lost; system should warn on next startup.

## Completion Report

```yaml
completion_report:
  what_was_done: Created UX specification for demonstration-taught guided tour system including persona, journey map, interaction model, UX risks, validation approach, and design requirements.
  key_decisions:
    - decision: Voice-only interface with fixed grammar
      rationale: Hands-free operation required; fixed grammar prevents hallucination and false positives.
    - decision: Confirmation required for critical state transitions
      rationale: Prevents accidental starts/stops that could disrupt operation.
    - decision: Tours stored as JSONL for append-friendly logging and easy inspection
      rationale: Matches existing project patterns and allows manual editing if needed.
    - decision: Navigation failure handled by stopping and waiting
      rationale: Simplifies implementation; operator can abort via voice.
  handoff_focus:
    - ui-design-system: Voice prompt templates and error message patterns
    - prototype: Implement state machine and voice command parsing
    - apple-hig-expert: Voice interaction guidelines for confirmation flows
  open_questions:
    - What is the maximum number of waypoints per tour?
    - How is audio narration stored? (file path, format, duration limits?)
    - What specific STT/TTS engine will be used?
    - How does the robot handle navigation failure during guiding? (stop and wait, retry, abort?)
  known_constraints:
    - Must work on Unitree G1 and Agibot X2 robots
    - Voice-only interface, no GUI
    - Must not hallucinate waypoints or narration
    - Must persist tours across reboots
  confidence_differential: 0.8
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
      - handoffs/to-prd→ux-researcher-designer-20260607-145552.yaml
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
      - What specific STT/TTS engine will be used? (macOS built-in, cloud API, etc.)
      - How is audio narration stored? (file path, format, duration limits?)
      - What is the maximum number of waypoints per tour?
      - How does the robot handle navigation failure during guiding? (stop and wait, retry, abort?)
  omitted_context:
    - source: Detailed file list of entire repository
      reason: background_only
    - source: Bootstrap and packaging details
      reason: background_only
    - source: Existing skill files and robot-specific configurations
      reason: background_only
  compression_rationale:
    method: Semantic filtering: retained only context directly relevant to the tour feature (user stories, acceptance criteria, implementation decisions, constraints). Omitted unrelated code files and infrastructure details.
    loss_notes: []
  quality_checks:
    - name: primary_workflow_present
      passed: true
    - name: usability_risks_named
      passed: true
```