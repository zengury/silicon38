# Grill-Me: Architecture Challenge

## Verdict: ROBUST — One minor refinement

---

## Challenges

### 1. `use-pet-state.ts` May Become a New Monolith

**Assumption**: Consolidating 15 state variables into one hook solves the scattering problem.

**Failure condition**: The hook becomes 200+ lines of intertwined state logic, repeating the original monolith problem at a different granularity. "One hook to rule them all" is still a monolith.

**Severity**: **Minor** (depends on implementation discipline)

**Recommendation**: The architect's interface contract is good — narrow surface, wide internals. But enforce in implementation: `sendMessage()` should delegate to `response-engine.getLocalResponse()`, not inline NLU logic. `addXp()` should delegate to `growth-model`. The hook should be a thin coordinator, not a fat container.

### 2. Canvas Rerender Trigger is Implicit

**Assumption**: `PetCanvas` re-renders when any of its props change (mood, petPosition, textContent, frame, etc.).

**Failure condition**: The animation loop updates `frame` 60fps via rAF, which triggers a React re-render, which triggers a `useEffect`, which calls `renderPetFrame`. This is 3 hops for something that should be 1. At 60fps, the React reconciliation overhead is non-trivial.

**Severity**: **Minor** (works fine for a pet app at 60fps)

**Recommendation**: The animation loop should call `renderPetFrame` directly via a ref to the canvas, bypassing React's render cycle for frame updates. Only structural changes (mood shift, text content change) should go through React props. This is the original architecture's approach (canvas ref + imperative draw), which is actually correct. Don't over-React-ify the render loop.

### 3. Missing: Type-Safe Mood Transitions

**Assumption**: `PetMood` is a string union, and any mood can transition to any other mood.

**Failure condition**: A response sets mood to `'walk'` but some component doesn't handle `'walk'` → visual glitch or crash. The old code handles this implicitly because everything is in one file.

**Severity**: **Minor**

**Recommendation**: Define a `MOOD_TRANSITIONS` map: which moods can follow which. `response-engine` validates before returning. This prevents impossible states like `hidden → walk` without a `peek` transition.

---

## Architecture Strengths

1. **`render-pet.ts` as pure function is THE right call.** Canvas rendering should never have been in a React component. This subtraction is Kahn-perfect.
2. **`growth-model.ts` is a textbook deep module.** 3 functions hide 6-level progression, binary search, threshold math.
3. **Phase migration strategy is pragmatic.** Each phase is independently testable — no "big bang" refactor risk.
4. **`response-engine.ts` consolidation fixes real scattering.** Currently regex patterns, fallback logic, and prompt generation are in 4 different places.
5. **Explicit data flow diagram makes handoff clear.** Senior engineer knows exactly where data originates and terminates.

---

## Completion Report

- **what_was_done**: Challenged architecture on 3 points: hook monolith risk, canvas render inefficiency, mood transition safety. Found 3 minor concerns. Verdict: ROBUST.
- **key_decisions**: [(1) APPROVED — architecture is Kahn-coherent, (2) hook must delegate to servant modules, not inline logic, (3) animation loop should draw imperatively via canvas ref, not via React re-render, (4) mood transitions should be type-safe]
- **handoff_focus**: senior-engineer must keep use-pet-state thin (delegate to core modules); animation loop must bypass React for frame updates
- **open_questions**: None
- **known_constraints**: React 19 + Vite; no new deps
- **confidence_differential**: 0.88
