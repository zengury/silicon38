# Architecture Decision Record: ink-pet Refactor

## Context

InkPetV10.tsx is a ~500-line React monolith containing 8 distinct responsibilities. The refactor applies Kahn's architectural principles:
- **Served / Servant separation** — the pet canvas is a served space (what the user experiences); geometry, response engine, growth model are servant spaces (what makes it work)
- **Deep modules** — narrow interfaces hiding complex internals
- **Subtraction (Salk)** — remove until only the true act remains
- **Light is data (Kimbell)** — data flows should be explicit, not hidden in closures

## Target Architecture

```
src/
├── main.tsx                    # unchanged — React mount
├── App.tsx                     # unchanged — thin wrapper
├── index.css                   # unchanged — global reset
│
├── core/                       # Servant layer — zero React dependency
│   ├── pet-geometry.ts         # Procedural shape generation (pure functions)
│   ├── response-engine.ts      # Intent matching + personality
│   ├── growth-model.ts         # Level progression + XP state
│   └── math.ts                 # dist, lerp, clamp
│
├── engine/                     # Servant layer — thin React wrappers
│   ├── use-pet-animation.ts    # rAF loop + pet position lerp
│   ├── use-pet-state.ts        # Central state machine (xp, level, mood, phase)
│   └── use-storage.ts          # Persistence hook
│
├── components/                 # Served layer — React components
│   ├── pet-canvas/
│   │   ├── PetCanvas.tsx       # Canvas component (thin wrapper)
│   │   ├── render-pet.ts       # Pure rendering logic (canvas draw calls)
│   │   └── PetCanvas.css       # Canvas styles
│   ├── chat/
│   │   ├── ChatInput.tsx       # Input bar + send button
│   │   └── MessageDisplay.tsx  # Text content display area
│   ├── evolution/
│   │   ├── XpBar.tsx           # XP progress bar
│   │   └── LevelUpFlash.tsx    # Evolution animation overlay
│   └── onboarding/
│       ├── PetSelect.tsx       # Type selection screen
│       └── PetName.tsx         # Name input screen
│
└── types.ts                    # Shared type definitions
```

## Module Contracts

### 1. `math.ts` — Pure Utility Functions

```typescript
export function dist(x1: number, y1: number, x2: number, y2: number): number;
export function lerp(a: number, b: number, t: number): number;
export function clamp(v: number, lo: number, hi: number): number;
```

**Depth**: Shallow. One-line implementations. Extracted only for clean imports elsewhere.

### 2. `growth-model.ts` — Level Progression (Deep Module)

```typescript
export interface Level {
  xp: number;
  name: string;
  desc: string;
}

export const LEVELS: readonly Level[];
export function getLevel(xp: number): number;       // returns level index
export function getNextXp(level: number): number | null;
export function getLevelProgress(xp: number): { current: number; next: number; pct: number };
```

**Interface**: 3 functions + 1 constant. Narrow surface.
**Internals**: 6-level progression, binary search, threshold computation. Complex inside, simple outside.
**Rationale**: The level system is a natural deep module — the XP thresholds, names, and progression logic change together. Nobody outside needs to know there are exactly 6 levels.

### 3. `pet-geometry.ts` — Procedural Shape Generation (Deep Module)

```typescript
export interface Part { x: number; y: number; r: number; label: string; }
export interface Feature { x: number; y: number; ch: string; s: number; }
export interface PetShape { parts: Part[]; features: Feature[]; }

export type PetMood = 'present' | 'happy' | 'sleep' | 'hidden' | 'peek' | 'sad' | 'eat' | 'excited' | 'walk';

export function getPetShape(
  cx: number, cy: number,
  frame: number, mood: PetMood, level: number
): PetShape;

export function getPeekShape(
  cx: number, cy: number,
  frame: number, level: number
): PetShape;
```

**Interface**: 2 functions. Pure — no side effects, no React.
**Internals**: Complex trigonometric animation, mood-to-glyph mapping, body part composition across 6 level tiers, sine-wave driven movement parameters.
**Rationale**: Shape generation is a pure computation problem. Separating it from React enables testing without DOM, and makes the visual behavior fully deterministic given inputs.

### 4. `response-engine.ts` — NLU + Personality (Deep Module)

```typescript
export interface PetResponse {
  state: PetMood;
  text: string;
  nextState?: PetMood;
  nextStateDelay?: number;
}

export function getLocalResponse(userText: string, petName: string): PetResponse;
export function buildSystemPrompt(petType: string | null, petName: string, level: number): string;
export function parseAIResponse(raw: string): PetResponse;
export function getDefaultResponses(): PetResponse[];
```

**Interface**: 4 functions. The caller doesn't know about regex patterns or response databases.
**Internals**: 10 intent patterns (greet, sleep, wake, feed, play, hide, praise, question, sad, grow), randomized response selection, state machine transitions for peek→present sequences.
**Rationale**: NLU logic is the pet's "brain." Currently scattered across `Rs`, `getLocal`, `sysPr`, `parseR`, and inline in `sendMessage`. Consolidating makes personality configurable and testable.

### 5. `use-pet-state.ts` — Central State Hook

```typescript
export interface PetState {
  phase: 'select' | 'name' | 'chat' | 'resume';
  petType: string | null;
  petName: string;
  xp: number;
  level: number;
  mood: PetMood;
  petVisible: boolean;
  petPosition: { x: number; y: number };
  textContent: string;
  loading: boolean;
  showLevelUp: boolean;
  
  // Actions
  addXp: (amt?: number) => void;
  setMood: (mood: PetMood) => void;
  movePet: () => void;
  appendText: (text: string) => void;
  sendMessage: (text: string) => Promise<void>;
  resetPet: () => Promise<void>;
  dismissLevelUp: () => void;
}
```

**Interface**: 1 hook returning state + actions. All mutation goes through actions.
**Internals**: 15 state variables, animation loop coordination, API call orchestration, save/load, level-up detection, mood transition logic.
**Rationale**: The current `InkPetV10` is essentially a state machine with UI. Extracting the state machine into a hook leaves only UI layout in the component. This is the Esherick wall — thick interface depth hiding complex internals.

### 6. `render-pet.ts` — Pure Canvas Renderer

```typescript
export function renderPetFrame(
  ctx: CanvasRenderingContext2D,
  chars: CharData[],
  shape: PetShape | null,
  frame: number,
  level: number,
  mood: PetMood,
  petX: number,
  petY: number,
  width: number,
  height: number
): void;

export function buildCharGrid(text: string, cols: number, rows: number, cellW: number, cellH: number): CharData[];
```

**Interface**: 2 functions. Stateless — given inputs, draw one frame. The React component (`PetCanvas`) just calls this in useEffect.
**Internals**: Character physics (force field from body parts), body fill pattern, outline dots, feature rendering, sparkle animation, scanlines, grid rendering.
**Rationale**: Separating canvas rendering from React lifecycle makes the drawing logic testable and the component a thin shell. This is subtraction (Salk): the component becomes an empty plaza between the state and the renderer.

---

## Data Flow (Refactored)

```
User types message
        │
        ▼
ChatInput.onSubmit(text)  ──►  usePetState.sendMessage(text)
                                      │
                        ┌─────────────┼────────────────┐
                        ▼             ▼                ▼
              growth-model.addXp()  response-engine   storage.save()
                        │           .getLocalResponse()
                        ▼             │
              level-up check          ▼
                        │       {state, text}
                        ▼             │
              usePetState ────────────┘
              .setMood(state)
              .appendText(text)
              .movePet()
                        │
                        ▼
              PetCanvas reads: mood, petPosition, textContent, level
                        │
                        ▼
              renderPetFrame(ctx, chars, shape, frame, level, mood, petX, petY, w, h)
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
        pet-geometry  math.ts   character grid
        .getPetShape()
```

---

## What Stays in the Top-Level Component

```typescript
// App.tsx — only layout, no logic
function App() {
  const pet = usePetState();
  
  if (pet.phase === 'select') return <PetSelect onSelect={pet.selectType} />;
  if (pet.phase === 'name') return <PetName onSubmit={pet.setName} />;
  
  return (
    <div className="pet-app">
      <Header>
        <XpBar xp={pet.xp} level={pet.level} />
        <ResetButton onClick={pet.resetPet} />
      </Header>
      <PetCanvas state={pet} />
      <ChatInput onSubmit={pet.sendMessage} disabled={pet.loading} />
      {pet.showLevelUp && <LevelUpFlash level={pet.level} onDone={pet.dismissLevelUp} />}
    </div>
  );
}
```

The component becomes a Salk plaza: spacious, empty of logic, where the user experiences the pet through cleanly separated servant modules.

---

## Migration Strategy

1. **Phase 1 — Extract pure servant modules** (zero risk, no behavior change):
   - `math.ts` — 3 lines, trivial
   - `growth-model.ts` — already pure
   - `pet-geometry.ts` — already pure
   - `response-engine.ts` — already pure

2. **Phase 2 — Extract rendering logic** (medium risk, verify visual output):
   - `render-pet.ts` — move canvas draw calls out of component
   - `PetCanvas.tsx` — thin wrapper calling `renderPetFrame`

3. **Phase 3 — Extract state machine** (highest risk, verify all interactions):
   - `use-pet-state.ts` — consolidate scattered state + actions
   - Wire up: PetSelect, PetName, ChatInput, XpBar, LevelUpFlash

4. **Phase 4 — Final cleanup**:
   - Remove original `InkPetV10.tsx`
   - Verify: dev build compiles, all interactions work identically

---

## Completion Report

- **what_was_done**: Designed refactored architecture per Kahn principles: 6 new modules (4 pure servant, 2 thin React wrappers), interface contracts for each, explicit data flow, 4-phase migration strategy
- **key_decisions**: [(1) `use-pet-state` hook as central state machine — single thick interface replaces 15 scattered state variables, (2) `render-pet.ts` as pure function — canvas drawing decoupled from React lifecycle, (3) `response-engine.ts` consolidates NLU — currently 4 scattered functions merged into one module, (4) 4-phase migration minimizes risk — each phase independently testable]
- **handoff_focus**: senior-engineer should implement Phase 1-4 in order; code-reviewer should verify no behavioral changes
- **open_questions**: None
- **known_constraints**: Must maintain React 19 + Vite build; no new npm dependencies; pet visual output must be identical pixel-for-pixel
- **confidence_differential**: 0.92
