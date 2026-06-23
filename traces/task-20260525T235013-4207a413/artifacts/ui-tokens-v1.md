# Fleet Ops Dashboard — Design Tokens v1

> Tokens only. No component CSS. Senior-frontend builds from these.

---

## 1. Color Tokens

```css
:root {
  /* Canvas */
  --color-canvas:          oklch(8% 0.005 250);      /* near-black ground; the Salk plaza */
  --color-canvas-raised:   oklch(12% 0.006 250);     /* card surface; one step off the ground */
  --color-canvas-overlay:  oklch(8% 0.005 250 / 0.88); /* modal scrim over canvas */
  --color-drawer-dim:      oklch(8% 0.005 250 / 0.55); /* drawer-open: canvas dims, not gone */

  /* Semantic red — critical only */
  --color-critical:        oklch(62% 0.22 25);       /* INCIDENT card border, failure type */
  --color-critical-muted:  oklch(62% 0.22 25 / 0.18); /* card rim fill at low alpha */

  /* Semantic amber — warning only */
  --color-warning:         oklch(72% 0.17 68);       /* WATCH tick, HANDOFF border shift */
  --color-warning-muted:   oklch(72% 0.17 68 / 0.14); /* ambient glow on card in HANDOFF */

  /* Type surfaces */
  --color-text-primary:    oklch(93% 0.004 250);     /* off-white; failure type, robot ID */
  --color-text-secondary:  oklch(65% 0.006 250);     /* vitals values, CLAIM label */
  --color-text-recessive:  oklch(42% 0.005 250);     /* vital labels, timestamps, system line */

  /* Interactive — servant elements only */
  --color-btn-surface:     oklch(18% 0.007 250);     /* CLAIM / ACK button resting surface */
  --color-btn-border:      oklch(32% 0.008 250);     /* button edge; separates from card */

  /* Dividers */
  --color-divider:         oklch(20% 0.005 250 / 0.6); /* vitals slab separator */
}
```

---

## 2. Typography Tokens

Font family stance: `system-ui, ui-sans-serif` for all display and body. No external typeface. Rationale: the soul demands the interface be *true*, not performed. A bespoke font imports personality; system-ui is the building that lets the operator bring theirs. For the monospace tier: `ui-monospace, 'Cascadia Code', monospace` — raw wire values and timestamps have a different *nature* than the names of failing machines; the fixed-width face makes that nature visible without comment.

```css
:root {
  /* Tier 1 — failure type: loudest thing on screen */
  --type-size-failure:    clamp(1.75rem, 1.2rem + 2.2vw, 2.5rem);
  --type-weight-failure:  700;
  --type-lh-failure:      1.1;

  /* Tier 2 — robot ID: second matter */
  --type-size-robot-id:    clamp(1.1rem, 0.9rem + 0.8vw, 1.4rem);
  --type-weight-robot-id:  500;
  --type-lh-robot-id:      1.25;

  /* Tier 3 — vitals values: compact, legible */
  --type-size-vitals-value:   clamp(0.875rem, 0.8rem + 0.3vw, 1rem);
  --type-weight-vitals-value: 500;

  /* Tier 3b — vitals labels: recessive partner to values */
  --type-size-vitals-label:   clamp(0.7rem, 0.65rem + 0.2vw, 0.8rem);
  --type-weight-vitals-label: 400;

  /* Tier 4 — monospace: raw shadow + timestamps */
  --type-family-mono:     ui-monospace, 'Cascadia Code', monospace;
  --type-size-mono:       clamp(0.7rem, 0.65rem + 0.15vw, 0.78rem);
  --type-weight-mono:     400;
  --type-lh-mono:         1.6;
}
```

---

## 3. Spacing Tokens

"In a small room one does not speak as in a large one." The card is a small room — tight, purposeful, no breath wasted. The canvas is a large one — open, quiet, the emptiness is information.

```css
:root {
  /* Card internal rhythm (small room) */
  --space-card-pad-x:     1.25rem;
  --space-card-pad-y:     1rem;
  --space-card-gap:       0.5rem;    /* failure type → robot ID */
  --space-vitals-gap:     0.75rem;   /* between individual vitals */
  --space-gutter-top:     0.875rem;  /* claim/note zone above vitals */

  /* Canvas outer rhythm (large room) */
  --space-canvas-pad-x:   clamp(2rem, 4vw, 5rem);
  --space-canvas-pad-y:   clamp(1.5rem, 3vh, 3rem);
  --space-card-stack-gap: 1.25rem;   /* stacked cards on INCIDENT */
  --space-system-line-y:  66vh;      /* system-status line anchor from top */
}
```

---

## 4. Motion Tokens

Three motions. One each. Nothing else moves.

```css
:root {
  /* Entrance: card slides in from below on INCIDENT */
  --motion-enter-duration: 240ms;
  --motion-enter-easing:   cubic-bezier(0.22, 1, 0.36, 1);
  /* Decelerates hard at landing. Card arrives, then stops. */

  /* Exit: card slides up on RESOLVED */
  --motion-exit-duration:  300ms;
  --motion-exit-easing:    cubic-bezier(0.4, 0, 1, 1);
  /* Accelerates out. Resolved matter leaves quickly; does not linger. */

  /* Modal overlay fade */
  --motion-modal-duration: 120ms;
  --motion-modal-easing:   cubic-bezier(0, 0, 0.2, 1);
  /* Fast in, standard decel. Interrupts must land with weight, not drift. */
}
```

---

## 5. One Thing Refused

**`--color-success` (success green) was considered and cut.**

Resolution is not a celebration — it is the restoration of calm, the return to the empty Salk plaza. A success green would teach the eye to look for reward, to feel finished. But the true act is *the robot working again*, not the dashboard congratulating the operator. The card slides off; the canvas empties; the system line resumes its quiet count. That is the reward. Green would be paint at the end of a building that needed none.

---

```yaml
completion_report:
  what_was_done: "Produced color, typography, spacing, and motion tokens for the Fleet Ops Dashboard, derived strictly from ux §8 constraints and soul.md."
  key_decisions:
    - decision: "system-ui for display; ui-monospace for raw/timestamps only"
      rationale: "Soul demands truth over performance. Mono tier communicates a different nature (wire data) without labeling it."
    - decision: "No success green token"
      rationale: "Resolution is subtraction, not reward. Canvas emptying IS the feedback."
    - decision: "canvas-overlay and drawer-dim as separate alpha tokens"
      rationale: "Modal scrim and drawer-dim serve different depths per §6; conflating them breaks the foreground/forensics hierarchy."
  handoff_focus:
    - "Card border uses --color-critical at INCIDENT; shifts to --color-warning on HANDOFF — implement as data-attribute swap"
    - "Vitals slab uses --color-divider between each vital at 1px; must not bleed into card padding"
    - "Raw shadow tooltip renders in --type-family-mono at --type-size-mono; do not inherit parent type context"
  open_questions:
    - "Should --color-btn-surface lighten on :hover or remain flat? §8 bans idle animation; a static hover shift is not motion."
  known_constraints:
    - "§8 is binding: no color beyond critical/warning/off-white without explicit justification against the true act"
    - "Three motion tokens defined; no others may be added without revisiting ux §8"
```
