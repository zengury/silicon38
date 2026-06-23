# Refactor Report — HR Assistant Frontend

## What Was Done

Decomposed the 430-line monolithic `page.tsx` into a modular architecture with clear seams, type safety, and correct state management.

## Changes

### 1. Type System (`src/types/chat.ts`)
- Defined `Message`, `Skill`, `Todo`, `Chat`, `ChatResponse`, `TodoResponse`, `PanelView`, `Category` types
- All API response types are now typed — no more `any` on `res.json()`

### 2. State Management (`src/hooks/useChat.ts`)
- Extracted all chat state and API logic into `useChat` hook
- Uses `useRef` for latest state access in async callbacks — **eliminates stale closure bug** (P3)
- Uses `localStorage('hr-chats-v2')` — new key to avoid collision with `chat.html`'s `hr-chats` (P4 partial)
- Typesafe `err: unknown` handling instead of `err: any`

### 3. Theme Persistence (`src/hooks/useDarkMode.ts`)
- `useDarkMode` hook persists to `localStorage('hr-theme-dark')`
- Supports `system` preference with live `matchMedia` listener
- Theme survives page reload (P4 resolved)

### 4. Component Decomposition
Each component handles its own concerns:

| File | Lines | Responsibility |
|------|-------|---------------|
| `components/Sidebar.tsx` | 120 | Navigation, chat history, mobile overlay |
| `components/ChatMessage.tsx` | 80 | Message bubble rendering + typing indicator |
| `components/ChatInput.tsx` | 85 | Text input, keyboard handling, send button |
| `components/RightPanel.tsx` | 180 | Skills and TODOs tabs |
| `components/EmptyState.tsx` | 60 | Welcome screen, quick questions |
| `app/page.tsx` | 125 | Layout composition only |

**Before:** 430-line single file. **After:** 6 files, largest is 180 lines.

### 5. Error Resilience
- `error.tsx` — Next.js error boundary, catches render errors gracefully (P5)
- `loading.tsx` — Initial load skeleton (P5)

### 6. CSS Consolidation
- Replaced all hardcoded `slate` references with `neutral` token from design system
- Removed duplicate CSS variable patterns that conflicted with Tailwind dark: variants
- `tailwind.config.js` updated with full `neutral` palette, semantic `borderRadius`, `boxShadow`, `transitionDuration` tokens

### 7. Accessibility Improvements
- Semantic elements: `<nav>`, `<main>`, `<header>`, `<aside>`
- ARIA labels on all interactive elements
- Keyboard navigation on sidebar items and TODO checkboxes
- `aria-current`, `aria-selected`, `aria-expanded` where appropriate
- Focus-visible ring on all interactive elements
- Touch target minimum 44px on send button
- `role="log"` with `aria-live="polite"` on messages container
- `role="article"` on AI messages, `role="status"` on typing indicator

### 8. Unused Code Removed
- Removed unused `CATEGORIES` constant from `page.tsx` (now lives in `EmptyState.tsx` where used)
- Removed conflicting `next.config.ts` placeholder file

## What Is Now Easier

- **Add a new header button**: Edit `page.tsx` header section (10 lines) instead of navigating a 430-line file
- **Change sidebar behavior**: Edit `Sidebar.tsx` only
- **Add a new message type**: Update `types/chat.ts`, then `ChatMessage.tsx`
- **Test chat logic in isolation**: `useChat` hook can be tested without rendering UI
- **Add a new right panel tab**: Update `PanelView` type, add tab in `RightPanel.tsx`
- **Backend changes response shape**: Typescript compiler catches mismatches immediately
