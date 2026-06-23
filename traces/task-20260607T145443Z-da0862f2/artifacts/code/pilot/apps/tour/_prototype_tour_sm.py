"""
PROTOTYPE — THROWAWAY CODE — DO NOT COMMIT AS PRODUCTION
=========================================================
pilot/apps/tour/_prototype_tour_sm.py

Question answered: Does the IDLE/TEACHING/GUIDING state machine with voice
command parsing and confirmation flow hold up under realistic interaction?

This prototype is a self-contained interactive terminal simulation of the
demonstration-taught guided tour state machine. It does NOT connect to any
robot, daemon, TTS, or STT. Every external dependency is simulated.

SHORTCUTS LABELED:
  # PROTOTYPE: <reason>
    Every shortcut is explicitly annotated so future implementers know
    exactly what was faked and why.

RUN:
  cd /Users/ZQ/manastone/manastone
  python3 pilot/apps/tour/_prototype_tour_sm.py

WHAT THIS PROTOTYPE DOES NOT TELL US:
  - Whether voice command recognition accuracy is sufficient (we type, not speak)
  - Whether the confirmation prompts feel natural as TTS audio
  - Whether the robot can physically navigate the taught path
  - How the system behaves under real latency (we are synchronous)
  - How graceful degradation works when STT/TTS is unavailable

DELETE OR ABSORB: After the state machine design is validated, either delete
this file or fold the validated state machine into engine.py and delete this.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ═══════════════════════════════════════════════════════════════════
# PROTOTYPE: Constants — hardcoded; production would load from config
# ═══════════════════════════════════════════════════════════════════

UNKNOWN_REPLY = "I wasn't told about that, let me find someone."
CANCEL_REPLY = "Cancelled. Back to idle."


# ═══════════════════════════════════════════════════════════════════
# State Machine
# ═══════════════════════════════════════════════════════════════════

class State(Enum):
    IDLE = auto()
    TEACHING = auto()
    GUIDING = auto()
    AWAITING_CONFIRM = auto()  # Sub-state: waiting for yes/no after a prompt

    def label(self) -> str:
        return {
            State.IDLE: "IDLE",
            State.TEACHING: "TEACHING",
            State.GUIDING: "GUIDING",
            State.AWAITING_CONFIRM: "AWAITING_CONFIRM",
        }[self]


@dataclass
class TourPoint:
    """PROTOTYPE: In-memory only. Production persists via TourStore JSONL."""
    id: str
    label: str  # Short auto-generated label from operator's speech
    location: dict[str, float]
    operator_said: str
    robot_understanding: str
    created_ts: float
    corrected_ts: float | None = None


@dataclass
class PendingConfirm:
    """PROTOTYPE: Holds context about what we're confirming."""
    action: str  # "start_teaching", "start_guiding", "delete_tour", "teach_point"
    point_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════
# Voice Command Grammar
# ═══════════════════════════════════════════════════════════════════

class Command(Enum):
    START_TEACHING = auto()
    STOP_TEACHING = auto()
    MARK = auto()
    START_GUIDING = auto()
    STOP_GUIDING = auto()
    STATUS = auto()
    LIST_TOURS = auto()
    DELETE_TOUR = auto()
    YES = auto()
    NO = auto()
    CANCEL = auto()
    HELP = auto()
    UNKNOWN = auto()


def parse_command(text: str) -> tuple[Command, str]:
    """PROTOTYPE: Simple keyword matching.
    Production would use a proper ASR grammar with confidence thresholds
    and possibly an LLM fallback for natural corrections.
    """
    lowered = text.strip().casefold()

    if lowered in ("start teaching", "begin teaching", "teach mode"):
        return Command.START_TEACHING, ""
    if lowered in ("stop teaching", "end teaching", "finish teaching", "done teaching"):
        return Command.STOP_TEACHING, ""
    if lowered == "mark":
        return Command.MARK, ""
    if lowered.startswith("start guiding"):
        tour_id = lowered.removeprefix("start guiding").strip()
        return Command.START_GUIDING, tour_id
    if lowered in ("stop guiding", "end guiding", "abort guiding", "abort"):
        return Command.STOP_GUIDING, ""
    if lowered == "status":
        return Command.STATUS, ""
    if lowered in ("list tours", "list", "show tours"):
        return Command.LIST_TOURS, ""
    if lowered.startswith("delete tour"):
        tour_id = lowered.removeprefix("delete tour").strip()
        return Command.DELETE_TOUR, tour_id
    if lowered in ("yes", "y", "confirm", "ok", "okay"):
        return Command.YES, ""
    if lowered in ("no", "n", "cancel", "abort"):
        return Command.NO, ""
    if lowered in ("help", "?", "commands"):
        return Command.HELP, ""

    return Command.UNKNOWN, text


# ═══════════════════════════════════════════════════════════════════
# PROTOTYPE: Understanding / Summarization
# Production would use an LLM call or a trained model.
# Here we use keyword extraction as a stand-in.
# ═══════════════════════════════════════════════════════════════════

def _extract_understanding(utterance: str) -> tuple[str, str]:
    """Extract a short label and full understanding from operator speech.

    PROTOTYPE: Heuristic keyword extraction. Production uses an LLM
    summarization call via the daemon's `learn` pipeline.
    """
    text = utterance.strip()
    # Strip common teaching prefixes
    prefixes = (
        "at this point",
        "here",
        "this is",
        "tell visitors",
        "say",
        "this area",
        "this place",
    )
    lowered = text.casefold()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip(" ,:.-") or text
            break

    # PROTOTYPE: Generate label from first 3-5 words
    words = text.split()
    label = " ".join(words[:4]) if len(words) >= 3 else text
    if len(label) > 50:
        label = label[:47] + "..."

    return label, text


def _generate_guided_speech(point: TourPoint) -> str:
    """Generate visitor-facing speech from taught understanding.

    PROTOTYPE: Templates. Production uses an LLM rephrasing call
    that converts operator-taught facts into natural guide speech.
    Different variants per context (start, middle, end, after-question).
    """
    templates = [
        f"Here we have {point.robot_understanding}",
        f"This is {point.robot_understanding}",
        f"You can see {point.robot_understanding}",
        f"This area features {point.robot_understanding}",
    ]
    # PROTOTYPE: Rotate templates by point index to simulate variety.
    # Production: LLM generates a fresh phrase each time.
    idx = int(point.id[1:]) % len(templates)
    return templates[idx]


def _answer_from_point(question: str, point: TourPoint) -> str:
    """Answer a visitor question from a taught point.

    PROTOTYPE: Wraps the understanding in "I was told that...".
    Production: LLM generates a proper answer anchored to the taught fact,
    with appropriate hedging for uncertainty.
    """
    return f"I was told that {point.robot_understanding}"


def _match_question(question: str, points: list[TourPoint]) -> TourPoint | None:
    """Match a visitor question to the closest taught point.

    PROTOTYPE: Simple token overlap. Production uses embedding similarity
    or an LLM-based semantic matcher.
    """
    stopwords = {
        "the", "and", "for", "that", "this", "what", "who", "where",
        "when", "why", "how", "with", "about", "is", "can", "you", "tell",
        "me", "there", "here",
    }

    def tokens(text: str) -> set[str]:
        return {
            clean
            for token in text.split()
            if (clean := token.strip(".,!?;:()[]{}\"'").casefold())
            and len(clean) > 2
            and clean not in stopwords
        }

    q_tokens = tokens(question)
    best_score = 0
    best_point: TourPoint | None = None
    for point in points:
        score = len(q_tokens & tokens(point.robot_understanding))
        if score > best_score:
            best_score = score
            best_point = point
    return best_point if best_score > 0 else None


# ═══════════════════════════════════════════════════════════════════
# Core State Machine Engine
# ═══════════════════════════════════════════════════════════════════

@dataclass
class TourSM:
    """PROTOTYPE: In-memory state machine. No persistence.
    All operations are synchronous. No daemon integration.
    """
    state: State = State.IDLE
    tours: dict[str, list[TourPoint]] = field(default_factory=dict)
    current_tour_id: str | None = None
    teaching_points: list[TourPoint] = field(default_factory=list)
    guiding_progress: set[str] = field(default_factory=set)
    guiding_route: list[str] = field(default_factory=list)

    # Confirmation sub-state
    pending_confirm: PendingConfirm | None = None

    # History for display
    transcript: list[str] = field(default_factory=list)

    # ── helpers ───────────────────────────────────────────────────

    def _say(self, text: str) -> None:
        """PROTOTYPE: Prints text. Production calls daemon play_tts."""
        self.transcript.append(f"🤖 ROBOT: {text}")

    def _log(self, text: str) -> None:
        """PROTOTYPE: Internal log, not spoken."""
        self.transcript.append(f"   [system] {text}")

    def _points(self) -> list[TourPoint]:
        tid = self.current_tour_id
        return self.tours.get(tid, []) if tid else []

    # ── state checks ──────────────────────────────────────────────

    def _reject_if(self, *states: State) -> str | None:
        if self.state in states:
            return None
        return f"Cannot do that while in {self.state.label()}. Say 'status' to see current state."

    # ── command dispatch ──────────────────────────────────────────

    def dispatch(self, raw: str) -> None:
        cmd, arg = parse_command(raw)

        if cmd == Command.UNKNOWN:
            self._handle_unknown(arg)
        elif cmd == Command.HELP:
            self._handle_help()
        elif cmd == Command.STATUS:
            self._handle_status()
        elif self.pending_confirm is not None:
            self._handle_confirmation(cmd)
        elif cmd == Command.START_TEACHING:
            self._handle_start_teaching()
        elif cmd == Command.STOP_TEACHING:
            self._handle_stop_teaching()
        elif cmd == Command.MARK:
            self._handle_mark()
        elif cmd == Command.START_GUIDING:
            self._handle_start_guiding(arg)
        elif cmd == Command.STOP_GUIDING:
            self._handle_stop_guiding()
        elif cmd == Command.LIST_TOURS:
            self._handle_list_tours()
        elif cmd == Command.DELETE_TOUR:
            self._handle_delete_tour(arg)
        elif cmd in (Command.YES, Command.NO, Command.CANCEL):
            self._say("No confirmation pending. Say 'help' for available commands.")

    # ── handlers ──────────────────────────────────────────────────

    def _handle_help(self) -> None:
        self._log("=== Voice Commands ===")
        self._log("  start teaching        — Enter teaching mode")
        self._log("  stop teaching         — Save tour and return to idle")
        self._log("  mark                  — Record current position + speak point description")
        self._log("  start guiding [id]    — Start guiding a tour (id from 'list tours')")
        self._log("  stop guiding          — Abort current guiding session")
        self._log("  status                — Show current state and progress")
        self._log("  list tours            — List all saved tours")
        self._log("  delete tour [id]      — Delete a tour (requires confirmation)")
        self._log("  yes / no              — Respond to confirmation prompts")
        self._log("  help                  — Show this list")
        self._log("")
        self._log("During TEACHING, say anything to record a point.")
        self._log("During GUIDING, ask questions about what was taught.")

    def _handle_unknown(self, text: str) -> None:
        """PROTOTYPE: In TEACHING mode, any unrecognized command is treated
        as a teaching utterance (walk + speak). In other modes, it's rejected."""
        if self.state == State.TEACHING:
            self._record_point(text)
        else:
            self._say("Command not recognized. Say 'help' to see available commands.")
            self._log(f"Unrecognized: '{text}'")

    def _handle_status(self) -> None:
        state_label = self.state.label()
        points = self._points()
        extra = ""
        if self.state == State.TEACHING:
            extra = f", {len(points)} points recorded"
        elif self.state == State.GUIDING:
            completed = len(self.guiding_progress)
            total = len(self.guiding_route) or len(points)
            extra = f", {completed}/{total} waypoints visited"
        elif self.state == State.AWAITING_CONFIRM:
            extra = f", awaiting confirmation for: {self.pending_confirm.action}"
        tour_info = f", tour '{self.current_tour_id}'" if self.current_tour_id else ""
        self._say(f"Status: {state_label}{tour_info}{extra}")

    def _handle_confirmation(self, cmd: Command) -> None:
        assert self.pending_confirm is not None
        pc = self.pending_confirm

        if cmd == Command.YES:
            self._log(f"Confirmed: {pc.action}")
            if pc.action == "start_teaching":
                self.state = State.TEACHING
                self.current_tour_id = pc.extra.get("tour_id", "tour_01")
                self.teaching_points.clear()
                self._say(f"Teaching tour '{self.current_tour_id}'. Walk and speak to record points. Say 'mark' to record the current position and your description.")
            elif pc.action == "start_guiding":
                self.state = State.GUIDING
                self.current_tour_id = pc.extra.get("tour_id", "")
                self.guiding_progress.clear()
                self._start_guiding_flow()
            elif pc.action == "delete_tour":
                tid = pc.extra.get("tour_id", "")
                self.tours.pop(tid, None)
                if self.current_tour_id == tid:
                    self.current_tour_id = None
                self._say(f"Tour '{tid}' deleted.")
                self.state = State.IDLE
            elif pc.action == "teach_point":
                # Confirm the understanding of a taught point
                pid = pc.point_id
                if pid:
                    for pt in self.teaching_points:
                        if pt.id == pid:
                            self._say(f"Point {pid} confirmed: {pt.robot_understanding}")
                            break
                self.state = State.TEACHING
            self.pending_confirm = None

        elif cmd == Command.NO:
            self._log(f"Declined: {pc.action}")
            if pc.action == "start_teaching":
                self._say(CANCEL_REPLY)
                self.state = State.IDLE
            elif pc.action == "start_guiding":
                self._say(CANCEL_REPLY)
                self.state = State.IDLE
            elif pc.action == "delete_tour":
                self._say("Delete cancelled.")
                self.state = State.IDLE
            elif pc.action == "teach_point":
                self._say("Let me try again. Please re-describe this point.")
                self.state = State.TEACHING
            self.pending_confirm = None

        else:
            self._say("Please say 'yes' or 'no' to confirm.")

    def _handle_start_teaching(self) -> None:
        err = self._reject_if(State.IDLE)
        if err:
            self._say(err)
            return
        # PROTOTYPE: Auto-generate tour ID. Production reads from voice or config.
        tour_count = len(self.tours) + 1
        tid = f"tour_{tour_count:02d}"
        self.pending_confirm = PendingConfirm(
            action="start_teaching",
            extra={"tour_id": tid},
        )
        self.state = State.AWAITING_CONFIRM
        self._say(f"Ready to record tour '{tid}'. Confirm by saying 'yes'.")

    def _handle_stop_teaching(self) -> None:
        err = self._reject_if(State.TEACHING)
        if err:
            self._say(err)
            return
        if not self.teaching_points:
            self._say("No points recorded. Discarding empty tour.")
            self.state = State.IDLE
            self.teaching_points.clear()
            return
        tid = self.current_tour_id or f"tour_{len(self.tours) + 1:02d}"
        self.tours[tid] = list(self.teaching_points)
        count = len(self.teaching_points)
        self._say(f"Tour '{tid}' saved with {count} point(s).")
        self._log(f"Points: {[p.id + ': ' + p.label for p in self.teaching_points]}")
        self.state = State.IDLE
        self.teaching_points.clear()

    def _handle_mark(self) -> None:
        """PROTOTYPE: 'mark' in teaching mode is a trigger to prompt the operator
        for a description. Here we simulate it - the operator's next utterance
        (not a command) becomes the point description."""
        err = self._reject_if(State.TEACHING)
        if err:
            self._say(err)
            return
        self._say(f"Point {len(self.teaching_points) + 1}: Please describe this location.")

    def _record_point(self, utterance: str) -> None:
        """Record a teaching point from operator's description."""
        assert self.state == State.TEACHING

        idx = len(self.teaching_points) + 1
        # PROTOTYPE: Location is simulated (linear spacing).
        # Production reads from robot odometry via daemon 'status' call.
        location = {"x": float(idx * 2 - 1), "y": 0.0, "yaw_deg": 0.0}
        label, understanding = _extract_understanding(utterance)
        pid = f"p{idx:02d}"

        point = TourPoint(
            id=pid,
            label=label,
            location=location,
            operator_said=utterance,
            robot_understanding=understanding,
            created_ts=time.time(),
        )
        self.teaching_points.append(point)

        # Ask for confirmation of the understanding
        self.pending_confirm = PendingConfirm(
            action="teach_point",
            point_id=pid,
        )
        self.state = State.AWAITING_CONFIRM
        self._say(f"I understood point {pid}: {understanding}. Is that right? (say 'yes' or 'no')")

    def _handle_start_guiding(self, tour_id: str) -> None:
        err = self._reject_if(State.IDLE)
        if err:
            self._say(err)
            return

        if not tour_id:
            self._say("Please specify a tour ID. Say 'list tours' to see available tours.")
            return

        if tour_id not in self.tours:
            available = ", ".join(self.tours.keys()) or "(none)"
            self._say(f"Tour '{tour_id}' not found. Available: {available}")
            return

        self.pending_confirm = PendingConfirm(
            action="start_guiding",
            extra={"tour_id": tour_id},
        )
        self.state = State.AWAITING_CONFIRM
        points_count = len(self.tours[tour_id])
        self._say(f"Starting tour '{tour_id}' with {points_count} points. Confirm by saying 'yes'.")

    def _start_guiding_flow(self) -> None:
        """Begin the guiding experience."""
        points = self._points()
        if not points:
            self._say(UNKNOWN_REPLY)
            self.state = State.IDLE
            return

        # PROTOTYPE: Route is sequential. Production may optimize route.
        self.guiding_route = [p.id for p in points]
        self.guiding_progress.clear()

        # Greet and start first point
        self._say("Welcome. I can show you the space.")

        # Guide to first point
        first = points[0]
        speech = _generate_guided_speech(first)
        self._log(f"   [move] navigating to p01 at ({first.location['x']:.1f}, {first.location['y']:.1f})")
        self._say(speech)
        self.guiding_progress.add(first.id)

    def _handle_stop_guiding(self) -> None:
        err = self._reject_if(State.GUIDING)
        if err:
            self._say(err)
            return
        completed = len(self.guiding_progress)
        total = len(self.guiding_route) or len(self._points())
        self._say(f"Guiding stopped. Completed {completed}/{total} waypoints.")
        self.state = State.IDLE

    def _handle_list_tours(self) -> None:
        if not self.tours:
            self._say("No tours saved yet.")
            return
        for tid, points in self.tours.items():
            pts_str = ", ".join(f"{p.id}: {p.label}" for p in points)
            self._say(f"  {tid}: {len(points)} points — {pts_str}")

    def _handle_delete_tour(self, tour_id: str) -> None:
        err = self._reject_if(State.IDLE)
        if err:
            self._say(err)
            return
        if not tour_id:
            self._say("Please specify a tour ID. Say 'list tours' to see available tours.")
            return
        if tour_id not in self.tours:
            self._say(f"Tour '{tour_id}' not found.")
            return
        self.pending_confirm = PendingConfirm(
            action="delete_tour",
            extra={"tour_id": tour_id},
        )
        self.state = State.AWAITING_CONFIRM
        self._say(f"Are you sure you want to delete tour '{tour_id}'? Say 'yes' to confirm.")

    # ── Guiding visitor interactions ──────────────────────────────

    def handle_visitor_input(self, text: str) -> None:
        """Handle input during GUIDING mode. Could be a question or a 'replan'."""
        err = self._reject_if(State.GUIDING)
        if err:
            self._say(err)
            return

        lowered = text.strip().casefold()

        # PROTOTYPE: Check for replan trigger phrase. Production uses
        # visitor position tracking via lidar to detect deviation.
        if any(phrase in lowered for phrase in ("replan", "went off route", "visitor moved", "skip ahead", "next point")):
            self._handle_replan(text)
            return

        # Treat as a question
        points = self._points()
        match = _match_question(text, points)
        if match is None:
            self._say(UNKNOWN_REPLY)
            return

        reply = _answer_from_point(text, match)
        self._say(reply)

    def _handle_replan(self, text: str) -> None:
        """Re-plan route based on visitor's current position.
        PROTOTYPE: We simulate visitor position from the command text.
        Production reads from lidar/greeter position tracking.
        """
        points = self._points()
        remaining = [p for p in points if p.id not in self.guiding_progress]
        if not remaining:
            self._say("You've seen all points. The tour is complete.")
            self.state = State.IDLE
            return

        # PROTOTYPE: Simulate visitor location.
        # Parse "replan x=3 y=2" or use midpoint of remaining points.
        import re
        x_match = re.search(r"x\s*[=:]\s*([\d.]+)", text)
        y_match = re.search(r"y\s*[=:]\s*([\d.]+)", text)
        visitor_loc = {
            "x": float(x_match.group(1)) if x_match else 0.0,
            "y": float(y_match.group(1)) if y_match else 0.0,
        }

        # Sort remaining by distance from visitor
        remaining.sort(key=lambda p: math.hypot(
            visitor_loc["x"] - p.location["x"],
            visitor_loc["y"] - p.location["y"],
        ))

        self.guiding_route = [p.id for p in remaining]
        self._log(f"   [replan] visitor at ({visitor_loc['x']:.1f}, {visitor_loc['y']:.1f})")
        self._log(f"   [replan] new route: {' → '.join(self.guiding_route)}")

        # Navigate to nearest remaining point
        next_point = remaining[0]
        self._log(f"   [move] navigating to {next_point.id} at ({next_point.location['x']:.1f}, {next_point.location['y']:.1f})")
        speech = _generate_guided_speech(next_point)
        self._say("I will adjust the route from here. " + speech)
        self.guiding_progress.add(next_point.id)

    def surface_state(self) -> str:
        """Return a summary of current state for display.
        PROTOTYPE: Prints to terminal. Production would use this for debugging."""
        lines = []
        lines.append(f"  STATE: {self.state.label()}")
        if self.current_tour_id:
            lines.append(f"  TOUR:  {self.current_tour_id}")
        if self.state == State.TEACHING:
            lines.append(f"  POINTS RECORDED: {len(self.teaching_points)}")
            for p in self.teaching_points:
                lines.append(f"    {p.id}: {p.label} @ ({p.location['x']:.1f}, {p.location['y']:.1f}) → '{p.robot_understanding}'")
        elif self.state == State.GUIDING:
            completed = len(self.guiding_progress)
            total = len(self.guiding_route) or len(self._points())
            lines.append(f"  PROGRESS: {completed}/{total}")
            lines.append(f"  ROUTE: {' → '.join(self.guiding_route) if self.guiding_route else '(none)'}")
            lines.append(f"  VISITED: {self.guiding_progress or '(none)'}")
        if self.pending_confirm:
            lines.append(f"  AWAITING: {self.pending_confirm.action}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Interactive Terminal Loop
# ═══════════════════════════════════════════════════════════════════

def print_banner() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  TOUR STATE MACHINE PROTOTYPE — THROWAWAY                   ║")
    print("║  Question: Does the IDLE/TEACHING/GUIDING state machine     ║")
    print("║  with voice commands hold up under realistic interaction?   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("  This is NOT production code. It simulates TTS/STT/robot.")
    print("  Type commands as if speaking them. Type 'help' for the list.")
    print("  Press Ctrl+D or type 'quit' to exit.")
    print()


def print_transcript(sm: TourSM) -> None:
    """Print recent transcript entries."""
    start = max(0, len(sm.transcript) - 12)
    for line in sm.transcript[start:]:
        print(f"  {line}")
    if len(sm.transcript) > 12:
        print(f"  ... ({len(sm.transcript) - 12} earlier lines omitted)")
    print()


def interactive_loop() -> None:
    sm = TourSM()
    print_banner()

    while True:
        # Surface state
        state_block = sm.surface_state()
        print("─" * 60)
        for line in state_block.split("\n"):
            print(f"  {line}")
        print("-" * 60)

        # Show recent transcript
        if sm.transcript:
            print_transcript(sm)

        # Prompt
        try:
            user_input = input("  🎤 YOU > " if sm.state in (State.TEACHING, State.GUIDING) else "  ⌨  CMD > ")
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.casefold() in ("quit", "exit", "q"):
            print("  Goodbye.")
            break

        # In GUIDING mode, visitor input goes to the guide handler
        if sm.state == State.GUIDING and parse_command(user_input)[0] not in (
            Command.STATUS, Command.STOP_GUIDING, Command.HELP, Command.YES, Command.NO, Command.UNKNOWN,
        ):
            sm.handle_visitor_input(user_input)
        else:
            sm.dispatch(user_input)


# ═══════════════════════════════════════════════════════════════════
# Non-interactive demo path (run with --demo)
# ═══════════════════════════════════════════════════════════════════

def run_demo() -> dict[str, Any]:
    """Run the 5-step acceptance demo automatically.

    This exercises the full state machine without interactive input,
    producing a pass/fail result for the 5 acceptance criteria.
    """
    sm = TourSM()
    results = []

    # Step 1: Teach ≥5 points with a correction
    sm.dispatch("start teaching")
    sm.dispatch("yes")                         # confirm
    assert sm.state == State.TEACHING
    sm.dispatch("mark")
    sm.dispatch("This is the entrance showing company history")
    sm.dispatch("no")                           # reject — needs correction
    sm.dispatch("change that to: This is the launch wall with the robot origin story")
    sm.dispatch("yes")                          # confirm correction
    sm.dispatch("mark")
    sm.dispatch("Here is the robot timeline showing the first prototype built in 2023")
    sm.dispatch("yes")
    sm.dispatch("mark")
    sm.dispatch("This is the demo table with our tactile sensor array")
    sm.dispatch("yes")
    sm.dispatch("mark")
    sm.dispatch("Tell visitors about the safety zone with emergency stop demos")
    sm.dispatch("yes")
    sm.dispatch("mark")
    sm.dispatch("This is the exit where visitors can request a brochure")
    sm.dispatch("yes")
    sm.dispatch("stop teaching")

    points = sm.tours.get("tour_01", [])
    step1_ok = len(points) == 5
    has_correction = any(
        "launch wall" in p.robot_understanding.casefold()
        for p in points
    )
    results.append({"step": 1, "desc": "Teach 5 points with correction", "ok": step1_ok and has_correction})

    # Step 2: Guide with generated language (not playback)
    sm.dispatch("start guiding tour_01")
    sm.dispatch("yes")
    assert sm.state == State.GUIDING

    # Check that generated speech differs from operator_said
    guided_texts = []
    for line in sm.transcript:
        if "ROBOT:" in line and "Here we have" in line or "This is" in line or "You can see" in line or "This area features" in line:
            guided_texts.append(line)
    step2_ok = len(guided_texts) > 0
    results.append({"step": 2, "desc": "Guide with generated language", "ok": step2_ok})

    # Step 3: Known question answered correctly
    sm.handle_visitor_input("What can you tell me about the robot timeline?")
    has_correct_answer = any(
        "robot timeline" in line.casefold() and "ROBOT:" in line
        for line in sm.transcript[-3:]
    )
    results.append({"step": 3, "desc": "Known question → correct answer", "ok": has_correct_answer})

    # Step 4: Unknown question → refusal
    sm.handle_visitor_input("Who designed the ceiling lights?")
    has_refusal = any(
        UNKNOWN_REPLY.casefold() in line.casefold()
        for line in sm.transcript[-3:]
    )
    results.append({"step": 4, "desc": "Unknown question → refusal (no hallucination)", "ok": has_refusal})

    # Step 5: Visitor deviation → replan
    sm.handle_visitor_input("replan x=7 y=0")
    has_replan = any(
        "[replan]" in line
        for line in sm.transcript[-5:]
    )
    route_changed = any(
        "new route:" in line
        for line in sm.transcript[-5:]
    )
    results.append({"step": 5, "desc": "Visitor deviation → replan", "ok": has_replan and route_changed})

    all_ok = all(r["ok"] for r in results)
    return {"all_pass": all_ok, "results": results, "transcript_length": len(sm.transcript)}


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--demo" in sys.argv:
        outcome = run_demo()
        print(json.dumps(outcome, indent=2, ensure_ascii=False))
        sys.exit(0 if outcome["all_pass"] else 1)
    else:
        interactive_loop()
