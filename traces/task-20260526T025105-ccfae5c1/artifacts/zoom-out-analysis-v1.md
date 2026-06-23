# Zoom-Out: ink-pet Codebase Map

## Current Structure

```
ink-pet/
├── src/
│   ├── main.tsx               # React root mount
│   ├── App.tsx                # Trivial wrapper → InkPetV10
│   ├── index.css              # Global reset styles
│   ├── App.css                # (unused — App has no styles)
│   └── components/
│       └── InkPetV10.tsx       # ~500 line monolith — THE PROBLEM
```

## InkPetV10 Internal Map (Single File, ~500 lines)

The monolith contains 8 logically distinct responsibilities all in one file:

### 1. Math Utilities (lines 1-3)
- `dist()`, `lerp()`, `clamp()` — 3 pure functions, no dependencies
- **Depth**: shallow utility. Could stay inline or move to `utils/math.ts`.

### 2. Level Progression System (lines 5-20)
- `LEVELS[]` — statically defined: 6 tiers (墨点→觉醒), each with xp threshold, name, desc
- `getLevel(xp)` — binary search on LEVELS
- `getNextXp(lv)` — next level threshold
- **Dependency**: none (pure data + pure functions)
- **Role**: defines the pet's growth curve

### 3. Pet Shape Generator (lines 22-70)
- `getPetShape(cx, cy, frame, mood, level)` → `Shape {parts, features}`
- `getPeekShape(cx, cy, frame, level)` → `Shape`
- Computes position/size of all body parts based on frame animation, mood, and level
- Uses the math utils (`dist`, `lerp`, `Math.sin`)
- **Dependency**: LEVELS (implicitly through `level` parameter)
- **Role**: procedural generation of ASCII art geometry

### 4. Text Canvas Renderer — `TextCanvas` Component (lines 74-176)
- 100-line React component with canvas ref, character physics, rendering loop
- Maintains `charsRef` — array of CharData with positions, velocities
- Physics: characters are pushed away from pet body parts (inverse-square-ish force field)
- Renders: grid lines, background characters (with glow near pet), body fill pattern (BF characters), outline dots, features (eyes/mouth with mood chars), sparkles at level 5, scanlines
- **Dependencies**: `getPetShape`, `getPeekShape`, math utils, LEVELS (implicitly)
- **Role**: THE core — the pet lives in this canvas

### 5. Response System (lines 178-206)
- `Rs` — regex → response mapping (10 intents: greet, sleep, wake, feed, play, hide, praise, question, sad, grow)
- `getLocal(t, n)` — local fallback response matcher
- `sysPr(type, name, level)` — system prompt template for API
- `parseR(t)` — parses `[STATE:X]` from AI response
- **Dependency**: LEVELS
- **Role**: natural language understanding + pet personality

### 6. Storage Adapter (lines 208-224)
- `storage.get/set/delete` — async wrapper over localStorage with optional `window.storage` override
- **Dependency**: none
- **Role**: persistence abstraction

### 7. Sub-Components (lines 226-246)
- `XpBar` — XP progress bar display
- `LevelUpFlash` — evolution animation overlay
- **Dependency**: LEVELS, math utils
- **Role**: UI widgets

### 8. Main Component — `InkPetV10` (lines 248-500)
- State machine: `select → name → chat` (3 phases)
- State: xp, level, mood, petVisible, petPos, textContent, loading, etc. (~15 state variables)
- Handles: animation loop (rAF), resize observer, keyboard input, message sending (API + fallback), pet movement, save/load, reset
- **Dependencies**: ALL of the above
- **Role**: orchestrator — but currently does EVERYTHING

## Data Flow

```
User Input (keyboard)
    │
    ▼
InkPetV10.sendMessage()
    │
    ├──► addXp() ──► setXp → setLevel (level-up check) → save()
    │
    ├──► anthropic API (optional, falls back)
    │        │
    │        ▼
    │    parseR(response) → {s: state, t: text}
    │
    └──► getLocal() (fallback) → {s, t}
             │
             ▼
         setMood(s)  ──► TextCanvas reads mood for shape/eyes
         setTextContent(t) ──► TextCanvas reads textContent for char placement
         movePet() ──► petTarget ref → animation loop lerps petPos → TextCanvas
```

## Coupling Analysis

| From | To | Coupling | Severity |
|------|----|----------|----------|
| InkPetV10 | TextCanvas | Props: width, height, text, petX, petY, frame, mood, petVisible, level (9 props) | **Tight** — every state change ripples to TextCanvas |
| InkPetV10 | sendMessage | Directly calls addXp, setMood, setTextContent, movePet, save | **Tight** — orchestration logic mixed with UI |
| TextCanvas | getPetShape | Direct import + call | **Tight** — shape gen embedded in renderer |
| TextCanvas | LEVELS | Implicitly coupled through `level` number | **Loose** — just reads level for visual scaling |
| getPetShape | Math utils | Pure function calls | **Healthy** |
| Response system | LEVELS | Reads LEVELS[level]?.name for sysPr | **Loose** |

## Identified Module Boundaries (Kahn Analysis)

### Served Spaces (what the user experiences)
- **PetCanvas** — the ASCII pet world the user sees and interacts with
- **ChatInterface** — input bar, message display
- **EvolutionDisplay** — XP bar, level-up flash

### Servant Spaces (what makes it work, invisible to user)
- **PetGeometry** — procedural shape generation (getPetShape, getPeekShape)
- **ResponseEngine** — intent matching + AI/fallback response
- **GrowthModel** — level progression, XP tracking
- **Persistence** — save/load state

### What Bleeds (servant leaking into served)
Currently: `InkPetV10` manages animation loop, resize observer, WebSocket/API calls, state transitions, pet positioning, AND renders UI — all in one component. The 9 props on TextCanvas are symptoms of this: every internal state leaks through the interface.

---

## Completion Report

- **what_was_done**: Mapped InkPetV10 monolith: identified 8 internal responsibilities, data flow, coupling matrix, and 7 module boundaries (4 served, 3 servant) per Kahn's served/servant distinction
- **key_decisions**: [(1) PetGeometry should be extracted as a pure module — no React dependency, (2) ResponseEngine should own all NLU logic — currently scattered across sendMessage + getLocal + Rs, (3) GrowthModel (LEVELS + xp/level state) is natural deep module — simple interface, complex internal progression, (4) TextCanvas should be split: rendering logic (pure) vs. React wrapper (thin)]
- **handoff_focus**: refactor-specialist should execute the split per these boundaries; improve-codebase-architecture should validate module depth
- **open_questions**: None
- **known_constraints**: Must preserve React 19 + TypeScript + Vite build; must not change pet behavior or visual output; no new dependencies
- **confidence_differential**: 0.90
