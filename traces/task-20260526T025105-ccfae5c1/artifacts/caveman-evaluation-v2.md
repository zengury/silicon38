# Caveman: Architecture Evaluation

## Are we subtracting or just rearranging?

**Subtracting.** Original: 1 file, 500 lines, 8 responsibilities tangled. Target: 13 files, each ~30-80 lines, each does ONE thing.

This is real subtraction: removing coupling, not just moving lines.

## Does each module earn its existence?

| Module | Earns? | Why |
|--------|--------|-----|
| `math.ts` | Barely | 3 one-liners. But used everywhere. Cost of extraction: zero. Keep. |
| `growth-model.ts` | Yes | 6 levels, binary search, XP tracking. 3 functions hide real complexity. |
| `pet-geometry.ts` | Yes | Procedural ASCII art across 6 growth stages. Pure math. Testable without React. |
| `response-engine.ts` | Yes | 10 intents, regex matching, random selection, state transitions. Currently scattered. |
| `render-pet.ts` | Yes | Canvas draw calls: force field, fill pattern, outlines, sparkles, scanlines. ~80 lines of drawing extracted from component. |
| `use-pet-state.ts` | Yes | 15 state vars + orchestration. Thin coordinator, delegates to core modules. |
| `use-storage.ts` | Marginal | Async localStorage wrapper. 15 lines. But storage might change (IndexedDB later). Keep. |
| `PetCanvas.tsx` | Yes | Thin shell. All logic in render-pet.ts. This is the Kahn wall. |
| `ChatInput.tsx` | Marginal | Input + button. Could be inline. But extraction costs nothing. |
| `XpBar.tsx` | Yes | Visual widget with progress math. Reusable. |
| `LevelUpFlash.tsx` | Yes | Animation with auto-dismiss. Self-contained. |
| `PetSelect.tsx` | Yes | Onboarding screen. 3 type choices. Clear boundary. |
| `PetName.tsx` | Yes | Name input with keyboard handling. Clear boundary. |

## The Salk Test

> "Remove until only the true act remains."

Original App.tsx:
```tsx
function App() { return <InkPetV10 /> }
```

Refactored App.tsx: layout shell with onboarding screens + main view. Still thin (~40 lines). The true act — showing the pet in its canvas — is what remains.

## The Kimbell Test

> "Light is data. Design backward from arrival."

The data flow is now explicit: `UserInput → response-engine → use-pet-state → pet-geometry → render-pet → canvas`. Every step is a named module, not an inline closure. Data arrives at the canvas having passed through named transformations, not anonymous callbacks.

## The Esherick Test

> "An interface faces both ways."

`use-pet-state` is the Esherick wall. Outward: 8 actions (addXp, setMood, sendMessage...). Inward: 15 state variables, animation loop, storage calls, API orchestration. The user-facing components see only the narrow outward face.

## Verdict: APPROVED

This is simpler. 13 small files are easier to understand than 1 large file. Each file's name tells you what it does. The original required reading 500 lines to find anything.

---

## Completion Report

- **what_was_done**: Evaluated architecture against Kahn's 3 principles. Salk: real subtraction, not rearrangement. Kimbell: data flow explicit. Esherick: use-pet-state as thick interface wall. 12 of 13 modules earn their existence. APPROVED.
- **key_decisions**: [(1) APPROVED — architecture is genuinely simpler, (2) math.ts is marginal but zero-cost, keep it, (3) use-storage.ts is marginal but future-proofs against IndexedDB migration]
- **handoff_focus**: senior-engineer must keep use-pet-state thin — delegate, don't inline
- **open_questions**: None
- **known_constraints**: Pixel-identical rendering is the acceptance test
- **confidence_differential**: 0.93
