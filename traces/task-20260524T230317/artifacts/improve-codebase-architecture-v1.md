# Architecture Improvement Roadmap — HR Assistant

## Current Problems

### P1: Monolithic Chat Page — Single Point of Change Fragility
**Affected modules:** `frontend/src/app/page.tsx` (430 lines)
**Consequence:** Any change to sidebar behavior risks breaking chat rendering or state management. Adding a new header button requires editing the same 430-line file where the API call logic lives. The file is a pass-through: it delegates no responsibility to child modules, keeping all decisions in one place so no seam exists for testing or independent modification.

**Deletion test:** Delete `page.tsx`. Complexity does not reappear across callers — it vanishes. All UI, state management, and API logic are in one module. This is maximum shallowness.

### P2: Duplicate Frontend Implementations — Shared localStorage Key Collision
**Affected modules:** `frontend/src/app/page.tsx`, `llm_assistant/frontend/chat.html`
**Consequence:** Both use localStorage key `hr-chats` with different schemas (page.tsx uses React state serialization, chat.html uses flat arrays). When a user switches between the two frontends, chat data corrupts. Two codebases implementing identical UX must be maintained in parallel — two places to fix bugs, two places to implement features.

### P3: Stale Closure in sendMessage — Silent Corruption Risk
**Affected modules:** `frontend/src/app/page.tsx` — `sendMessage` callback, `useCallback` dependencies
**Consequence:** `sendMessage` captures `chats` in its closure via `useCallback([input, isLoading, activeChatId, chats])`. The `chats.find()` inside the callback reads from the captured snapshot, not the latest state after the `setChats` update. If a chat is deleted concurrently, stale references create phantom chats.

### P4: Dark Mode Not Persisted — Inconsistent Between Frontends
**Affected modules:** `frontend/src/app/page.tsx`
**Consequence:** `chat.html` persists theme preference to localStorage (`hr-theme` key). Next.js page.tsx holds dark mode in React state only — resets on page reload. Users get flickering default theme on every visit. Two frontends = two different theme behaviors.

### P5: Missing Error Boundary — Full App Unmount on Any Error
**Affected modules:** `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`
**Consequence:** Any uncaught React rendering error unmounts the entire application. No graceful degradation. A malformed markdown message from the API that causes `ReactMarkdown` to throw crashes the entire chat interface, losing all unsent input and resetting scroll position.

### P6: No TypeScript Contracts for API Responses
**Affected modules:** `frontend/src/app/page.tsx` — fetch response handling
**Consequence:** API response is typed as `any` via `const data = await res.json()`. If the backend changes its response shape, the compiler provides no signal. Every response property access is an unverified assumption.

### P7: Singleton LLMHRAssistant Blocks Testing
**Affected modules:** `llm_assistant/backend/hr_assistant.py` — `get_assistant_instance()`
**Consequence:** Module-level `_assistant_instance` makes `LLMHRAssistant` untestable. Tests cannot isolate the assistant from the RAG loader. Cannot inject mock LLM clients. The singleton prevents dependency injection entirely.

---

## Improvement Roadmap

### Step 1: Component Decomposition & Type Contracts (P1 + P6)
**Change:** Extract `page.tsx` into co-located components: `Sidebar.tsx`, `ChatMessage.tsx`, `ChatInput.tsx`, `RightPanel.tsx`, `EmptyState.tsx`. Each handles its own component-local state. Create `types.ts` with full API response interfaces. Move API logic to a `useChat` custom hook.
**Rationale:** Each component becomes independently testable. Type contracts catch backend changes at compile time.
**Risk:** Low — pure mechanical extraction, no behavior change.
**Unlocks:** Each component can be tested independently. Future UI changes stay scoped to one component.

### Step 2: Error Boundary (P5)
**Change:** Add `error.tsx` (Next.js error boundary) at `src/app/error.tsx`. Add `loading.tsx` for loading states.
**Rationale:** Next.js file-based error boundaries catch uncaught errors within a route segment. Loading state provides skeleton UI during suspense.
**Risk:** Near zero — Next.js convention, zero custom code.
**Unlocks:** App survives render errors gracefully.

### Step 3: State Management Fixes (P3 + P4)
**Change:** Replace `useCallback` with `useRef` for latest state access in async callbacks. Add `useDarkMode` hook persisting to localStorage (`hr-theme-dark` — different key to not collide with chat.html's `hr-theme`). Use `useReducer` for `chats` state instead of multiple `setChats` calls.
**Rationale:** `useRef` pattern eliminates stale closure risk. `useReducer` ensures atomic state transitions. localStorage persistence unifies theme behavior.
**Risk:** Medium — state management change touches the core data flow.
**Unlocks:** Concurrent chat operations become safe. Theme persists across reloads.

### Step 4: De-duplicate Chat Data Schema (P2)
**Change:** Add `version: 1` field to chat data stored in localStorage. On load, check version and migrate if schema changes. (Full de-duplication of chat.html is a separate project.)
**Rationale:** Version field prevents silent corruption if schemas diverge again.
**Risk:** Low — additive field, backward compatible.
**Unlocks:** Safe evolution of persistence format.

### Step 5: Backend Dependency Injection (P7)
**Change:** Extract `LLMHRAssistant` construction to a factory function accepting `SkillsRAG` and `AsyncOpenAI` client as dependencies. Expose `create_assistant()` alongside legacy `get_assistant_instance()`.
**Rationale:** Tests can inject mock dependencies. Phase out singleton gradually.
**Risk:** Low — additive, existing callers unchanged.
**Unlocks:** Backend becomes testable.

### Step 6: CSS Architecture Consolidation
**Change:** Remove `CATEGORIES` unused constant. Define CSS custom properties for all design tokens in `globals.css`. Replace inline color values in `tailwind.config.js` with semantic token references. Remove `.css` variables that duplicate Tailwind dark: variants.
**Rationale:** Single source of truth for visual language. Prevents token drift between CSS and Tailwind.
**Risk:** Low — visual consistency improvement.
**Unlocks:** Design system token adoption (from ui-design-system).

---

## Priority Justification

Steps 1-3 are ordered by **impact-to-risk ratio** and **dependency chain**:
1. Component decomposition (Step 1) must happen first — it creates the seams where everything else slots in.
2. Error boundary (Step 2) is independent and near-zero risk — can be done in parallel.
3. State fixes (Step 3) depend on the component boundaries established in Step 1.
4. Schema versioning (Step 4) is defensive and low urgency.
5. Backend DI (Step 5) affects testability only, not user-facing behavior.
6. CSS consolidation (Step 6) is cosmetic cleanup.

Every step is independently deployable. No big-bang rewrite.
