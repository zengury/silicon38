# Triage Analysis — ink-pet Refactor

## Current State

### Architecture
- **Single monolithic file**: `InkPetV12.tsx` — 470 lines, 5 concerns tangled
- No separation between rendering, game logic, API, UI components
- Canvas rendering mixed with React state/effects
- Storage, prompts, parsing, physics all co-located

### What Works Well
- Unique concept: Chinese radical → evolving AI pet in text
- Canvas-based text rendering with ASCII pet overlay
- Claude API integration for both chat and evolution
- XP system, need decay, persistence all functional
- The "pet pushes text aside" physics effect is charming
- Fallback system ensures offline-friendly

### Pain Points
1. **Monolith**: Hard to extend, test, or understand flow
2. **No polish**: Transitions are basic lerp, animations are frame-count based
3. **Limited interaction**: Text input only, no click/drag/hover
4. **Static ASCII art**: Pet forms are predetermined, not procedurally generated
5. **Flat rendering**: No particles, no ink effects, no atmosphere
6. **No visual state feedback**: Mood changes have minimal visual impact

### Risk Assessment
- **Breaking API**: Low — self-contained app
- **Performance**: Canvas already 60fps, adding particles should stay smooth
- **Complexity**: Medium — adding effects without overengineering
- **User expectation**: High — pretext sets a premium visual bar

## Severity / Scope

| Dimension | Assessment |
|-----------|-----------|
| **Architecture** | Moderate — monolith but clean code internally |
| **Interaction** | High — text-only input limits expressiveness |
| **Visual Polish** | High — no particles, transitions, or dynamic art |
| **Extensibility** | Low — single file, hard to add features |

## Recommendation

**Priority order:**
1. **Dynamic visual effects** (pretext-inspired) — highest impact
2. **Interactive pet** (click/drag) — novel interaction
3. **Modular refactor** — enabler for 1 & 2
4. **ASCII art generation** — procedural pet forms

**Approach**: Refactor into modules, add particle/ink system, add mouse interaction, enhance ASCII art generation.
