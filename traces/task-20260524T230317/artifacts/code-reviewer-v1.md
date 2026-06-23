# Code Review — HR Assistant Refactor

## Verdict: **CHANGES_REQUIRED** (2 critical correctness issues, 2 high-severity maintainability issues)

---

## Correctness Findings (Blockers)

### C1: Stale Closure on `handleSend` → `input` state
**File:** `src/app/page.tsx` line ~38
**Issue:** `handleSend` reads `input` from its `useCallback` closure:
```tsx
const handleSend = useCallback(() => {
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  }, [input, isLoading, sendMessage]);
```
While `input` is in the dependency array, between re-renders, the value could be stale if React batches updates. The reliable pattern is to pass the value as a parameter or use a `useRef` for the input.
**Fix:** Change `ChatInput`'s `onSend` to pass the current input value: `onSend: (value: string) => void`. Then `handleSend` becomes `(v: string) => { sendMessage(v); setInput(""); }`.

### C2: `handleQuickAsk` Bypasses Loading Guard
**File:** `src/app/page.tsx` line ~41
**Issue:** `handleQuickAsk` calls `sendMessage(question)` directly, bypassing the `isLoading` check in `handleSend`. If the user clicks a quick question while a response is loading, two concurrent requests fire.
**Fix:** Add `isLoading` guard: `if (isLoading) return;`

---

## Maintainability Findings (Required Changes)

### M1: `handleQuickAsk` Uses `requestAnimationFrame` for State Sequencing
**File:** `src/app/page.tsx` line ~41
**Issue:** `requestAnimationFrame` is for visual frame synchronization, not state sequencing. This pattern silently breaks if React renders are deferred (e.g., concurrent mode, transitions).
**Fix:** Since `sendMessage` accepts text as a parameter and uses refs internally, just call `sendMessage(question)` directly. Remove the `requestAnimationFrame` wrapper. The `setInput(question)` call is cosmetic only and can be removed too — the user sees the message appear in chat anyway.

### M2: `useChat` Returns 15 Values — Low Cohesion
**File:** `src/hooks/useChat.ts` line ~155
**Issue:** The hook returns chat state, panel state, UI state, and API methods in one flat object. This forces all consumers to import from one source, making it hard to memoize or split responsibilities.
**Recommendation:** Split into `useChats()` (chats + activeChat + new/delete) and `useChatActions()` (sendMessage + isLoading), or group with destructured return objects. Lower priority — can be addressed in a follow-up.

---

## Style Notes (Non-blocking)

### S1: `getApiBase()` Should Be a Shared Utility
**File:** `src/hooks/useChat.ts` line ~6
**Note:** Consider extracting to `src/lib/api.ts` for reuse across hooks and potential future components.

### S2: Time Formatting Duplicated
**File:** `src/hooks/useChat.ts` lines ~88, ~113, ~140
**Note:** `toLocaleTimeString("zh-CN", {hour: "2-digit", minute: "2-digit"})` repeated 3 times. Extract to a helper: `const formatTime = () => new Date().toLocaleTimeString(...)`.

### S3: Unused `useRef` import in `page.tsx`
**File:** `src/app/page.tsx` line ~3
**Note:** `useRef` is imported but `messagesEndRef` is the only usage — verify the `useRef` import is intentional (it is, for `messagesEndRef`). No action needed.

### S4: `role="log"` with `aria-live="polite"` on Messages Container
**File:** `src/app/page.tsx` line ~73
**Note:** `role="log"` is implicitly live — `aria-live="polite"` is redundant. But keeping both is defensive and harmless.

---

## What Passed

| Area | Status | Notes |
|------|--------|-------|
| Component decomposition | ✅ | Clean separation, each component < 180 lines |
| Type safety | ✅ | Full TypeScript interfaces, no `any` for API responses |
| Stale closure fix (hook level) | ✅ | `useRef` pattern in `useChat` correctly avoids closure over `chats` and `activeChatId` |
| Dark mode persistence | ✅ | localStorage persistence + system preference listener |
| Error boundary | ✅ | `error.tsx` catches render errors gracefully |
| Accessibility | ✅ | Semantic HTML, ARIA labels, keyboard nav, focus-visible, 44px touch targets |
| Design tokens | ✅ | Consistent `neutral` + `primary` palette, semantic border radii, shadows, motion tokens |
| Tailwind config | ✅ | Full design token integration |
| CSS cleanup | ✅ | Removed CSS variable / Tailwind dark: conflicts |
| localStorage isolation | ✅ | `hr-chats-v2` avoids collision with `chat.html`'s `hr-chats` |

---

## Required Fixes Summary

1. **Fix `handleSend` stale closure** — pass input value as parameter via `ChatInput.onSend(value)` 
2. **Fix `handleQuickAsk` race condition** — add `isLoading` guard
3. **Remove `requestAnimationFrame` pattern** — call `sendMessage(question)` directly

All three fixes are in `src/app/page.tsx`, lines ~38-47.
