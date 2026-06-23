# Fleet Ops Dashboard — Interaction Design

## 1. The Salk Move — Idle Canvas
At idle, the canvas holds almost nothing. A single status line sits near the bottom third — not centered, not screaming — reading the count of robots online and the last-seen timestamp in quiet monospace. No cards. No charts. No robot grid. No colored indicators sweeping the perimeter. The background is a deep, nearly-black surface: not for aesthetic drama but because darkness makes the eye rest until there is something worth moving for. The emptiness is not a loading state. It is the true condition of a healthy fleet: nothing requires the operator's hand, so the canvas offers nothing to grip. What is NOT on it: robot thumbnails in a passive grid, a live donut spinning in the corner, rolling event logs, connection-state badges for each machine, a toolbar of tabs visible at top. All of that is elsewhere, waiting. The emptiness tells the operator that the moment they see something fill this surface, it is real, and it is theirs to act on.

*What the room wanted was the right to be empty.*

## 2. State Machine — Canvas

```
IDLE      — empty canvas; one quiet system line "12 robots online · 09:41:02"
  │  warning threshold crossed
  ▼
WATCH     — soft amber tick at canvas edge; robot ID in muted type; body still empty
  │  critical threshold breached / alert fires
  ▼
INCIDENT  — alert modal interrupts; on ACK, card emerges as the central matter;
            multiple failing robots → multiple cards, newest at top, sorted by
            severity then time
  │  CLAIM pressed
  ▼
HANDOFF   — card becomes a working surface; claimer name read-only to others;
            note field active; vitals live; border shifts red → calmer amber
  │  Mark Resolved
  ▼
RESOLVED  — card slides off canvas (300ms ease-out, upward); if no cards
            remain, return to IDLE; archived card available in History drawer
```

## 3. Triage Card — Anatomy

**Center — the question being answered.** The failure type is the loudest type on screen. `JOINT OVERTEMP — LEFT HIP ACTUATOR` must read across the room in two seconds. Beneath it, robot ID in the next tier of weight. These two lines are the card.

**Rim — vitals slab.** Four vitals as compact labeled values along the lower edge, ordered by urgency not alphabet: the metric that caused the alert is leftmost. Temperature canonical °C; battery %; CPU %; network ms.

**Gutter — claim and note.** CLAIM button (or claimer's name if claimed) and a single-line note field. Servant space; does not compete with the center.

**Back — raw shadow on hover.** See §5.

**Hierarchy in words:** failure type loudest; robot ID second; vital values + CLAIM third; vital labels + timestamps recessive monospace, requiring the eye to approach.

## 4. Alert Modal — The Only Interrupt
Full-bleed overlay. Dims everything beneath. Large enough to read without leaning in.

**Sound:** a single tone, once. Repeated tones train operators to ignore them.

**Three buttons, ordered for reading when seconds are gone:** `ACK` → `CLAIM` → `ESCALATE`.
- ACK is leftmost, default focus — smallest commitment, closes the modal, lets the operator assess before owning.
- ESCALATE is rightmost — most consequential, must never be the accidental Enter.

**Dedup:** identical alerts within window — second suppressed; `+N more since ACK` badge appears on the card after ACK.

**Queue:** distinct-robot simultaneous alerts queue. Header reads `1 of 3`. Next/Prev at modal edges. The queue count is the information; no special panic layout.

## 5. The Raw-Shadow Gesture — FR-003
Hover any canonical vital value. 200ms dwell → tooltip-adjacent label appears immediately below: `raw: 68.3 °C (0x441120F6)` or `raw: 0.89 (unitless ratio)`. Both coexist; canonical above, raw below; visible simultaneously while pointer dwells.

Justification: soul says *"an interface faces both ways — outward to the world, inward to the person. The depth of the module is where the two are reconciled, out of sight."* The hover IS that depth. Persistent toggle flattens it; modifier key hides it. Hover is discoverable, momentary, and locates the reconciliation exactly at the threshold between the two worlds — visible only when you press against it.

## 6. Drawer and Tab Access

**Opening History:** a "View History" link appears at the lower-right of each card once it is in HANDOFF or RESOLVED — not before, because forensics belong to calm. Click → drawer slides in from the right at 280ms, covering 40% of the canvas. Cards remain visible on the left. Default zoom: last 15 minutes.

**Alert during drawer-open:** modal renders over everything including the drawer. Drawer does not close — it darkens. After ACK, drawer is still there. Foreground steals focus; does not destroy forensics context.

**Fleet Health tab:** pinned top (two tabs: `Triage` default, `Fleet Health` secondary). During INCIDENT, switching is permitted but the tab label shows a count badge `Fleet Health · 2 incidents`. Modals render regardless of active tab.

## 7. Three Rejected Designs
1. **Kanban three-column board (Triaging / Claimed / Resolved).** Trains operators to manage the board, not resolve the robot. True act is resolution.
2. **Executive overview with fleet KPIs at top (uptime %, MTTR, incident rate).** KPIs answer yesterday's question; push the failing machine down the page.
3. **Slack-like chronological incident feed.** Rewards reading speed, not decision speed. A JOINT OVERTEMP buried under fourteen LOW_BATTERY warnings is a feed failure. Cards surface urgency, not recency.

## 8. Constraints for ui-design-system
- **Palette:** start from near-black; let color earn every appearance — one semantic red for critical, one amber for warning, one off-white for primary type; anything beyond must justify against the true act.
- **Density:** canvas is low-density by design; the card is the density maximum.
- **Motion:** one entrance (card slides in from below on INCIDENT, 240ms ease-out), one exit (card slides up on RESOLVED, 300ms ease-out), one modal overlay fade (120ms); nothing else moves.
