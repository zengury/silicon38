# Caveman Review: manastone-diag v0.4 Refactoring Plan (ADR-001)

## Plain-Language Explanation

manastone-diag is a diagnostic tool for a walking robot. It watches the robot's parts (joints, battery, posture) and tells you when something is wrong. It does this by:

1. **Reading robot data** — either from the real robot or fake test data
2. **Checking thresholds** — if a joint gets too hot or the battery gets too low, it notices
3. **Remembering what happened** — stores events in a small database so you can look back
4. **Answering questions** — "why is the left leg hot?" → it looks at recent events, checks its knowledge book, and gives an answer (using a language model if available, or simple rules if not)
5. **Serving tools over the network** — other programs can ask it questions using a standard protocol (MCP)

The program grew from one big file into seven smaller ones, one for each robot subsystem. But during the growth, some old parts were left behind and some patterns got copied seven times.

## What the Architect Wants to Do (7 Things)

| # | Action | Why |
|---|--------|-----|
| 1 | Fix a typo | Motion server has `ensure_aware` instead of `ensure_ascii` — would crash if used |
| 2 | Add explanation comments | Tell future readers why global singletons are used here |
| 3 | Clean up config loading | Don't hide file-reading inside a getter function — make it explicit |
| 4 | Make a shared server starter | Seven servers all start the same way — write the pattern once |
| 5 | Move keywords to the knowledge book | Fault-matching keywords are hardcoded in code but should live with the fault data |
| 6 | Delete the broken web UI | It references files that don't exist anymore — dead code |
| 7 | Add comments about thresholds | Clarify that server display thresholds ≠ event detection thresholds |

## Minimum Viable Version

What is the simplest thing that would make the codebase better?

**Only 3 things are load-bearing.** The other 4 are nice but not essential:

**Must do:**
1. Fix the typo (motion.py) — prevents a crash
4. Create shared server factory — stops the same bug from appearing in 7 places again
6. Delete ui.py — removes dead code that misleads new readers

**Should do:**
3. Clean up config loading — makes testing possible
5. Move keywords to YAML — prevents future drift between code and data

**Nice to have:**
2. Add docstrings — documentation is always good but doesn't change behavior
7. Threshold boundary comments — clarifies intent but doesn't fix a bug

## Complexity Assessment

### Justified complexity (keep it):
- **Multi-server architecture (7 MCP servers)**: Each server isolates one hardware domain. This is real complexity — the robot has legs, a battery, an IMU, etc. Separating them means you can turn off the hand server on a robot without hands without touching the rest.
- **Schema-driven thresholds**: Having all the "when to warn" rules in one YAML file instead of scattered across code is good. One place to look, one place to change.
- **Append-only EventLog**: No deleting events means the audit trail is always complete. Worth the SQLite setup cost.
- **Shared AppState singleton**: There is exactly one robot, one data stream, one event log. Making a fancy system to pretend otherwise would be the unnecessary complexity.

### Unnecessary complexity (the refactoring fixes):
- **Dead ui.py**: Code that can't run. The architect says delete it. Correct.
- **7 copies of the same server startup code**: The architect says extract to one function. Correct.
- **Keywords duplicated in code and YAML**: The architect says put them only in YAML. Correct.
- **Hidden side effects in config getter**: Silent dotenv loading. The architect says make it explicit. Correct.

### What the architect got right:
Every decision is reversible. The server factory can be inlined again if it proves too rigid. The deleted ui.py can be recreated from git history. The config changes can be reverted. No decision locks the project into an irreversible direction.

### What the architect might have missed:
The architect deferred `grill-me` review. But the decisions are straightforward — fixing a typo, deleting dead code, extracting a shared pattern. There's nothing controversial to grill. The deferral is correct.

## Verdict

**APPROVED**. The 7 decisions are the right ones. They are small, independent, reversible, and grounded in the actual codebase problems found by zoom-out. No over-engineering detected. The minimum that would work (steps 1, 4, 6) is a valid subset if time is constrained.

---

## Completion Report

```yaml
completion_report:
  what_was_done: "First-principles review of ADR-001: explained system in plain language, identified minimum viable subset (3 of 7 steps are load-bearing), confirmed all decisions are reversible and grounded in actual codebase problems. No unnecessary complexity found."
  key_decisions:
    - decision: "APPROVED — all 7 architect decisions are correct"
      rationale: "Each fixes a real problem found by zoom-out; no decision is irreversible; minimum viable subset (typo, factory, ui.py deletion) is valid"
    - decision: "Deferred grill-me is correct"
      rationale: "No controversial decisions to grill — fixing typos and deleting dead code doesn't need adversarial review"
  handoff_focus:
    - "Implement steps 1, 4, 6 first (load-bearing)"
    - "Steps 3, 5 next (preventive)"
    - "Steps 2, 7 last (documentation)"
  open_questions:
    - "None — all architect decisions are unambiguous"
  known_constraints:
    - "Same as architect: offline-friendly, MCP backward compat, Python 3.10+"
  iteration_context: null
```
