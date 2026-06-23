# Architecture Design — ink-pet Refactor

## Module Structure

```
src/
  types.ts                 # All shared types
  storage.ts               # Persistence adapter
  engine/
    pet.ts                 # Pet lifecycle: needs, XP, leveling
    text.ts                # Text segment buffer
    field.ts               # Physics: displacement, collision
  canvas/
    renderer.ts            # Core draw loop — text + pet + effects
    particles.ts           # Ink particle system (pretext-inspired)
    ascii.ts               # Dynamic ASCII art via brightness field
  api/
    client.ts              # Claude HTTP client
    prompts.ts             # Chat + evolution prompt templates
    parser.ts              # [STATE]/[FORM]/[NEWCHAR] parsers
    fallback.ts            # Local keyword-based responses
  components/
    TextCanvas.tsx          # Canvas wrapper + ResizeObserver
    SelectRadical.tsx       # Radical picker
    NamePet.tsx             # Name input
    StatusBar.tsx           # Header: character, needs, XP
    InputBar.tsx            # Chat input
    EvolveFlash.tsx         # Evolution celebration overlay
  App.tsx                   # Root orchestrator
  main.tsx                  # Entry point
  index.css                 # Global styles
```

## New Features

### 1. Ink Particle System (`canvas/particles.ts`)
- Lightweight class managing `<100` active particles
- Emit on: pet movement (trail), text insertion (bloom), evolution (burst)
- Physics: gravity, diffusion, fade
- Rendered on same canvas with globalCompositeOperation

### 2. Mouse Interaction (`App.tsx` + canvas events)
- **Click pet**: pulse animation + XP bonus
- **Drag pet**: move pet, real-time text reflow
- **Hover**: subtle glow/breathing effect
- **Click text**: select region, pet navigates there

### 3. Dynamic ASCII Art (`canvas/ascii.ts`)
- Brightness field driven by pet mood + frame
- Character selection from brightness gradient
- Different character sets per radical
- Morphs between states instead of hard cuts

### 4. Enhanced Rendering (`canvas/renderer.ts`)
- Extracted from current TC component
- Layer-based: paper → text → field → pet → particles
- Supports multiple rendering passes
- inkDrop field, peek field, artToField extracted as functions

## Data Flow

```
User Input → App.tsx (state) → api/client.ts → Claude
                                      ↓
                              parser.ts → state/mood/art
                                      ↓
              engine/pet.ts ← XP/needs update
              engine/text.ts ← text segments
              engine/field.ts ← pet position → displacement
                                      ↓
              canvas/renderer.ts → draws frame
              canvas/particles.ts → emits particles
              canvas/ascii.ts → generates pet art
```

## Invariants
- Storage format unchanged (version key preserved)
- Same Claude API integration
- Same radical selection flow
- Same XP/evolution system
- Canvas-based rendering preserved
