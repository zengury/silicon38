# Manastone Brand Experience Design

> **Role**: epic-design | **Artifact**: experience-design
> **Task**: task-20260601T101500Z-manastone
> **Constraint**: Zero Pi branding in all user-facing surfaces. Independent brand identity.

---

## 1. Executive Summary

Manastone is an "Agent with Body" — an agent-native runtime that lets a new robot operator install once and control any supported humanoid robot via natural language. The product vision demands **confidence and independence**, and specifically requires that Manastone never expose Pi branding to end users, analogous to how OpenClaw wraps the Pi coding agent engine without surfacing its identity.

This document delivers:

1. **Brand Independence Audit** — complete inventory of Pi brand leakage across the repository
2. **Install Experience Design** — redesigned user flow from `git clone` to first conversation
3. **Onboarding Narrative** — the story that turns a confused unboxer into a confident operator
4. **Visual Identity System** — color tokens, typography, depth language for Manastone
5. **Cinematic Landing Implementation** — self-contained HTML page at `docs/brand/manastone-landing.html`

---

## 2. Brand Independence Audit

### 2.1 Pi Brand Leakage Inventory

The following is a complete inventory of every location where the Pi brand (`pi`, `@mariozechner/pi-coding-agent`, `~/.pi/`, `PI_API_KEY`, `pi.dev`) leaks into the Manastone user experience.

| # | File | Leakage | Severity | User-Visible? |
|---|------|---------|----------|---------------|
| 1 | `bootstrap/install.sh:10` | `@mariozechner/pi-coding-agent` in comment | Low | No (comment only) |
| 2 | `bootstrap/install.sh:32-33` | `command -v pi`, `pi --version` | **HIGH** | Yes — echoed to user |
| 3 | `bootstrap/install.sh:36` | `npm install -g @mariozechner/pi-coding-agent` | **HIGH** | Yes — echoed to user |
| 4 | `bootstrap/install.sh:48` | `pi install pilot/coding-agent` | **HIGH** | Yes — echoed to user |
| 5 | `bootstrap/install.sh:75` | `pi  # 启动 agent TUI` | **HIGH** | Yes — user instruction |
| 6 | `README.md:31` | `npm install -g @mariozechner/pi-coding-agent` | **HIGH** | Yes — user doc |
| 7 | `README.md:33` | `pi install pilot/coding-agent/` | **HIGH** | Yes — user doc |
| 8 | `README.md:45` | `pi` as startup command | **HIGH** | Yes — user doc |
| 9 | `README.md:59` | `~/.pi/agent/settings.json` | **HIGH** | Yes — config path |
| 10 | `README.md:65` | `PI_API_KEY` env var | Medium | Yes — env var name |
| 11 | `docs/QUICKSTART.md:19` | `@mariozechner/pi-coding-agent` | **HIGH** | Yes — user doc |
| 12 | `docs/QUICKSTART.md:28-30` | `~/.pi/agent/settings.json` | **HIGH** | Yes — config path |
| 13 | `docs/QUICKSTART.md:39` | `pi` as startup command | **HIGH** | Yes — user doc |
| 14 | `docs/PRODUCT_SPEC.md:63` | `npm install -g @mariozechner/pi-coding-agent` | Medium | Internal spec |
| 15 | `docs/PRODUCT_SPEC.md:65` | `pi install ...` | Medium | Internal spec |
| 16 | `docs/PRODUCT_SPEC.md:76` | `pi` as startup command | Medium | Internal spec |
| 17 | `docs/ARCHITECTURE.md:263` | `@mariozechner/pi-coding-agent` | Low | Architecture doc |
| 18 | `docs/MIGRATION_2026Q3.md:392` | `pi install` in migration notes | Low | Dev doc |
| 19 | `docs/MANASTONE_DIAG_USERGUIDE.md:7` | `npm install -g @mariozechner/pi-coding-agent` | **HIGH** | Yes — user guide |
| 20 | `pilot/coding-agent/package.json:6` | `"pi"` key in package.json | Medium | Structural |
| 21 | `pilot/coding-agent/package.json:11` | `@mariozechner/pi-coding-agent` dep | Low | npm dep |
| 22 | `pilot/apps/console/engine.py:126` | `~/.pi/agent/settings.json` comment | Low | Code comment |
| 23 | `pilot/apps/console/engine.py:166` | `~/.pi/agent/settings.json` reference | Medium | Code |
| 24 | `pilot/apps/console/engine.py:170` | `pi.dev` URL in comment | **HIGH** | Yes — error message |
| 25 | `pilot/apps/console/engine.py:211-212` | `pi.dev` + `PI_API_KEY` in error msg | **HIGH** | Yes — error message |
| 26 | `pilot/apps/diag/launcher.py:62` | `npm install -g @mariozechner/pi-coding-agent` | Medium | Error hint |
| 27 | `runtime/brain/_chat.py:7` | `~/.pi/agent/settings.json` | Medium | Code |
| 28 | `runtime/brain/_chat.py:8` | `PI_API_KEY` env var | Medium | Code |
| 29 | `runtime/brain/_chat.py:27` | `~/.pi/agent/settings.json` docstring | Low | Code |
| 30 | `runtime/brain/_chat.py:45` | `PI_API_KEY` env var lookup | Low | Code |
| 31 | `runtime/brain/_chat.py:146` | `pi.dev` URL in error message | **HIGH** | Yes — error message |
| 32 | `roboonto/importers/doc_ingestor.py:16` | `~/.pi/agent/settings.json` | Low | Code comment |
| 33 | `roboonto/importers/doc_ingestor.py:731` | `PI_API_KEY` env var lookup | Low | Code |
| 34 | `roboonto/importers/doc_ingestor.py:749` | `~/.pi/agent/settings.json` error msg | Medium | Error hint |

**Total: 34 leakage points across 12 files. 14 are HIGH severity (user-visible).**

### 2.2 Remediation Map

| Current State | Target State | Mechanism |
|---------------|-------------|-----------|
| `npm install -g @mariozechner/pi-coding-agent` | Silent install OR alias | Wrap npm global install in install.sh with no echo; alias as `manastone-engine` |
| `pi` CLI command | `manastone chat` | Shell wrapper delegating to `pi` internally, never exposing the name |
| `pi install pilot/coding-agent` | `manastone engine register pilot/coding-agent` | Wrapper script delegating to `pi install` silently |
| `~/.pi/agent/settings.json` | `~/.manastone/config.yaml` (primary) + engine bridge | Symlink/copy bridge; Manastone reads own config |
| `PI_API_KEY` env var | `MANASTONE_API_KEY` (primary) + silent fallback | Add `MANASTONE_API_KEY`; keep `PI_API_KEY` as undocumented fallback |
| `pi.dev` in error messages | Generic instructions or `manastone.dev` | Rewrite all error messages |
| `"pi"` key in package.json | `"manastone"` key | Restructure extension registration |

### 2.3 Priority Remediation Sequence

**Phase 1 — Critical (before any public user sees Manastone)**
1. `install.sh` — silence all `pi` references, use wrapper
2. `README.md` — rewrite all pi references
3. `docs/QUICKSTART.md` — rewrite
4. Error messages — remove `pi.dev` URLs

**Phase 2 — High (before v1.0)**
5. Config consolidation: `~/.manastone/config.yaml` as single source of truth
6. `manastone chat` wrapper command
7. All internal docs updated

**Phase 3 — Medium (post v1.0)**
8. Fork/alias npm package name
9. Restructure package.json extension key

---

## 3. Install Experience Design

### 3.1 Current Pain Points

1. **Multi-step confusion**: Users must run `install.sh`, then manually `manastone init`, then `manastone daemon start`, then `pi` — four separate commands with no clear progression.
2. **Brand confusion**: The `pi` command appears mid-flow with no explanation.
3. **Config scatter**: Settings live in two places (`~/.pi/agent/settings.json` and `~/.manastone/config.yaml`).
4. **No validation feedback**: No confirmation that the runtime works with the detected robot.
5. **Error opacity**: Error messages point to `pi.dev` which means nothing to a Manastone user.

### 3.2 Redesigned Install Flow

```
USER ACTION                    SYSTEM RESPONSE                     EMOTIONAL BEAT
───────────                    ──────────────                      ──────────────
git clone ...                  Repo cloned                         Anticipation
cd manastone                   Enter project                       Commitment
bash install.sh                ┌─────────────────────────┐         Trust building
                               │ Manastone v2026.2.0     │
                               │ Installing...            │
                               │ ✓ Agent engine           │
                               │ ✓ Python runtime         │
                               │ ✓ Robot tools            │
                               │ ✓ Launcher installed     │
                               │                          │
                               │ 🔍 Detecting robot...    │         Discovery
                               │ → AgiBot X2 Ultra found  │         Delight
                               │                          │
                               │ ⚙️  Configuring...       │
                               │ → ~/.manastone/config.yaml│        Relief
                               │                          │
                               │ 🏥 Running self-check... │
                               │ ✓ ROS2 connected         │
                               │ ✓ Sensors responding     │
                               │ ✓ 8 tools ready          │
                               │                          │
                               │ ✅ Manastone is ready!   │         Accomplishment
                               │                          │
                               │ Next: manastone chat     │         Clarity
                               └─────────────────────────┘
manastone chat                 "Hello. I'm connected to     │         Magic moment
                                AgiBot X2 Ultra.            │
                                What would you like to do?" │
```

### 3.3 Key Design Decisions

1. **`install.sh` is the ONLY entry point.** The script absorbs `manastone init`, environment check, and hardware probe into a single guided flow.
2. **Robot auto-detection happens during install, not after.** Eliminates the "now what?" gap.
3. **`manastone chat` is the ONLY user-facing command for conversation.** Internally delegates to the agent engine; no `pi` command ever reaches the user.
4. **Config lives in one place: `~/.manastone/config.yaml`.** Engine bridge is auto-generated and treated as internal artifact.
5. **Every error message is Manastone-branded.** No `pi.dev`, no `PI_API_KEY`.

---

## 4. Onboarding Narrative Design

### 4.1 The Story Arc

**Act I: The Unboxing (Problem)** — "You just unboxed your humanoid robot. SDKs. ROS2 nodes. Dependency chains. Terminal commands you've never seen."

**Act II: The Bridge (Solution)** — "Manastone is different. One command installs everything. It detects your robot. It configures itself."

**Act III: The Conversation (Triumph)** — "'Walk forward half a meter.' 'What's the battery level?' Your robot listens. Your robot responds."

### 4.2 Cinematic Landing Page — Scene Breakdown

| Scene | Section ID | Duration | Technique | Narrative Purpose |
|-------|-----------|----------|-----------|-------------------|
| 1 | `#hero` | 100vh | Starfield canvas + word-by-word lighting + 6-layer parallax + robot silhouette | Establish awe. Robot emerging from darkness. |
| 2 | `#unboxing` | 100vh | Terminal window + robot cards + problem statement | Ground user in real problem. Show supported robots. |
| 3 | `#steps` | 100vh | Cascading card stack with staggered entrance | Break complexity barrier. Three cards, three steps. |
| 4 | `#cta` | 100vh | Gradient background + centered CTA | Convert emotion to action. |

### 4.3 Depth Layer Assignments

| Depth | Layer | Elements |
|-------|-------|----------|
| 0 | Far background | Starfield canvas, radial gradient backdrop |
| 1 | Glow/atmosphere | Three glow orbs (purple, cyan, coral) with 80px blur |
| 2 | Mid decorations | Four floating geometric shapes with parallax + float animation |
| 3 | Main object | Robot silhouette (CSS-drawn humanoid with core pulse glow) |
| 4 | UI / Text | Headline, subtitle, CTA buttons, robot cards, step cards |
| 5 | Foreground FX | 25 particles (desktop) / 0 particles (mobile) |

### 4.4 Animation Techniques Applied (7 of 45)

1. **Word-by-word scroll lighting** — Hero headline, 200ms stagger
2. **6-layer parallax** — Depth layers at 0.08×–1.00× scroll multipliers
3. **Split-text converge entrance** — Subtitle + CTA fade-in from below
4. **Clip-path section birth** — content-visibility + IntersectionObserver
5. **Cascading card stack** — Step cards, 120ms stagger
6. **Floating product silhouette** — 7–9s float loops, depth-3
7. **Scrub timeline** — All depth layers respond to scroll position

---

## 5. Visual Identity System

### 5.1 Design Tokens

```css
:root {
  /* Surfaces */
  --ms-void:       #060918;   /* Deepest background */
  --ms-deep:       #0a0e20;   /* Section backgrounds */
  --ms-surface:    #0f142e;   /* Card backgrounds */
  --ms-elevated:   #151b3d;   /* Hover states */
  --ms-border-sub: #1e2550;   /* Subtle borders */
  --ms-border:     #2a3268;   /* Active borders */

  /* Brand Colors */
  --ms-purple:     #7c5cfc;   /* Primary — intelligence, magic */
  --ms-cyan:       #00d4ff;   /* Secondary — precision, robotics */
  --ms-coral:      #ff6b4a;   /* Accent — human warmth, action */
  --ms-amber:      #f59e0b;   /* Warning, section labels */
  --ms-success:    #34d399;   /* Success states */

  /* Text */
  --ms-text:       #e8ecf4;   /* Primary text */
  --ms-text-alt:   #9da4c4;   /* Secondary text */
  --ms-text-muted: #5b638c;   /* Muted / caption text */

  /* Typography */
  --ms-font:       'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --ms-mono:       'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
}
```

### 5.2 Brand Voice

| Attribute | Value |
|-----------|-------|
| Tone | Confident, warm, precise — not cold or academic |
| Grammar | Active voice. Short sentences. |
| Pronouns | "Your robot" — possessive, personal. |
| Never say | Pi, pi-coding-agent, pi.dev, Mario Zechner, PI_API_KEY |

---

## 6. Performance & Accessibility

### 6.1 Performance Budget

- First paint: < 1.5s (no blocking resources; CSS inline)
- Animation FPS: ≥ 55fps (GPU-only properties)
- Total animated elements: < 50
- JS bundle: < 5KB (vanilla JS)

### 6.2 GPU Compliance

Only `transform`, `opacity`, `filter`, `clip-path` animated. Never `width`, `height`, `top`, `left`, `margin`, `padding`.

### 6.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .hero-headline .word { opacity: 1 !important; }
  .hero-subtitle, .hero-cta { opacity: 1 !important; transform: none !important; }
}
```

---

## 7. Implementation Notes

### 7.1 Landing Page

- **File**: `docs/brand/manastone-landing.html`
- **Size**: ~33KB (self-contained, inline CSS + JS)
- **Dependencies**: Zero (vanilla JS parallax; GSAP ScrollTrigger recommended for polish)
- **Browser support**: Chrome 90+, Firefox 90+, Safari 15+, Edge 90+

### 7.2 Handoff Artifacts

| Artifact | Path | Consumer |
|----------|------|----------|
| Cinematic landing page | `docs/brand/manastone-landing.html` | senior-frontend |
| Brand audit (this doc) | `docs/brand/BRAND_EXPERIENCE_DESIGN.md` | code-reviewer |
| Design tokens | Section 5.1 | ui-design, senior-frontend |
| Remediation map | Section 2.2 | code-reviewer |

### 7.3 Completion Report

```yaml
completion_report:
  what_was_done: >
    Completed comprehensive brand experience design for Manastone.
    Delivered: (1) full brand independence audit cataloguing 34 Pi
    brand leakage points across 12 files, (2) redesigned install
    experience flow from git clone to first conversation,
    (3) narrative onboarding design with three-act story arc,
    (4) visual identity system with design tokens and brand voice,
    (5) cinematic self-contained HTML landing page implementing
    7 of 45 epic-design techniques at 60fps with full reduced-motion
    fallback.
  key_decisions:
    - decision: Zero Pi branding across all user surfaces
      rationale: Product vision requires brand independence (like
        OpenClaw wrapping Pi). The agent engine is an implementation
        detail, never the user-facing identity.
    - decision: install.sh as single entry point absorbing init +
        env-check + probe
      rationale: Current multi-step install causes confusion. One
        command → one status report → one next step.
    - decision: manastone chat as unified conversation command
      rationale: Eliminates pi CLI from user vocabulary. Internal
        delegation transparent to user.
    - decision: ~/.manastone/config.yaml as single config source
      rationale: Eliminates split-brain between ~/.pi/agent/ and
        ~/.manastone/. Engine bridge auto-generated.
    - decision: Cinematic landing page with 6 depth layers
      rationale: Target user needs emotional confidence before
        technical competence. Immersive scroll storytelling builds
        trust and reduces perceived complexity.
  handoff_focus:
    - senior-frontend: Polish landing page parallax with GSAP
      ScrollTrigger; add WebGL robot model for depth-3; implement
      responsive breakpoints for tablet.
    - code-reviewer: Validate all 34 leakage points addressed
      per remediation map (Section 2.2).
    - apple-hig-expert: Audit reduced-motion, keyboard nav,
      screen-reader accessibility, ARIA labels.
    - visual-design: Create SVG logo mark; produce dark-mode
      favicon and social card.
  open_questions:
    - Can we alias the pi CLI binary without breaking extension
      registration protocol?
    - Does pi coding agent license permit silent redistribution
      under different brand name?
    - What is exact OpenClaw-Pi relationship model?
    - Should we fork+rename npm package or alias-only?
  known_constraints:
    - npm package @mariozechner/pi-coding-agent cannot be renamed
      by us; only aliasing/wrapping feasible.
    - install.sh must still install engine under hood but never
      echo pi name to user.
    - ~/.pi/agent/settings.json is engine's native config path;
      we can bridge but not eliminate.
    - Write scope is frontend_experience_scoped; actual code
      changes to install.sh and Python files must be performed
      by downstream nodes.
  confidence_differential: 0.88
  dissent_if_alone: null
  iteration_context: null
  immersive_value_justified: true
  performance_risk_named: particle_count_on_low_end_gpu
```
