# Zoom-Out: HR Assistant Codebase Territory Map

## System Overview

The HR Assistant is a dual-frontend, single-backend application providing AI-powered management consulting. It uses LLM APIs (Kimi/DeepSeek/OpenAI) and a RAG system over 287 management skills derived from Andy Grove's "High Output Management".

---

## Module Map

### 1. Frontend A — `frontend/` (Next.js SPA)
**Responsibility:** Primary user-facing React application with chat interface, sidebar, and right panel.
**Framework:** Next.js 14 (Pages Router), React 18, TypeScript, Tailwind CSS 3
**Deployment:** Static export via `next-pwa` → served by nginx reverse proxy

| File | Responsibility | Lines | State |
|------|---------------|-------|-------|
| `src/app/page.tsx` | Entire application: sidebar, chat, right panel, all state management, API calls | ~430 | Monolithic; all components in single file |
| `src/app/layout.tsx` | Root HTML, metadata, viewport, PWA manifest | ~38 | Thin |
| `src/app/globals.css` | Tailwind directives, custom scrollbar, markdown styles, animations | ~66 | Mixed CSS approaches |
| `tailwind.config.js` | Primary color palette (indigo/violet), no Tailwind plugins | ~25 | Minimal |
| `next.config.js` | PWA config (static export, offline support) | ~14 | Actual config |
| `next.config.ts` | Empty NextConfig placeholder | ~8 | Unused/conflicting with .js |

**Dependencies:** react-markdown, remark-gfm, lucide-react, next-pwa

**External Connections:**
- API calls to backend at `/api/chat`, `/api/todos` (proxied through nginx in production)
- localStorage key: `hr-chats` — persists conversation history

---

### 2. Frontend B — `llm_assistant/frontend/chat.html` (Legacy SPA)
**Responsibility:** Older, simpler vanilla HTML/CSS/JS chat interface.
**Framework:** None — single HTML file with inline CSS and JS
**Deployment:** Served as static file by FastAPI at `/`

| File | Responsibility | Lines | State |
|------|---------------|-------|-------|
| `chat.html` | Complete app: CSS variables for theming, regex markdown parsing, sidebar, chat, right panel | ~230 | Functional but brittle; regex-based markdown |

**External Connections:**
- Same API endpoints: `/chat`, `/todos`
- Same localStorage key: `hr-chats` — **COLLIDES with Next.js frontend** (same origin shares localStorage)

---

### 3. Backend — `llm_assistant/backend/` (FastAPI)
**Responsibility:** LLM orchestration, skills RAG, REST API, static file serving.

| File | Responsibility | Lines | State |
|------|---------------|-------|-------|
| `main.py` | FastAPI app, CORS, lifespan, endpoints: /chat, /chat/stream, /todos, /skills, /health, /stats | ~200 | Well-structured |
| `hr_assistant.py` | Core domain: SkillsRAG (inverted index search), LLMHRAssistant (prompt construction, multi-provider LLM), Skill dataclass | ~310 | Singleton pattern; bare excepts; hardcoded token limits |

**Domain Vocabulary:**
- `Skill` — dataclass: name, folder, description, body, category
- `SkillsRAG` — inverted index tokenizer with Chinese/English support, keyword-weighted search
- `LLMHRAssistant` — multi-provider LLM client (Kimi/DeepSeek/OpenAI), system prompt templating
- `Todo` — generated action items from conversation context

**External Connections:**
- Kimi API (`api.moonshot.cn`) or DeepSeek or OpenAI
- `data/skills.json` — 287 skills loaded at startup

---

### 4. Skills Data — `skills/` + `data/skills.json`
**Responsibility:** Domain knowledge corpus. 287 management skills in markdown folders, bundled into `data/skills.json`.

| Path | Responsibility |
|------|---------------|
| `skills/` | ~287 folders, each containing SKILL.md with management methodology |
| `data/skills.json` | Pre-processed JSON bundle: name, folder, description, body (truncated 3000 chars), category |

---

### 5. Infrastructure — `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `deploy.sh`
**Responsibility:** Containerization, reverse proxy, deployment scripts.

| File | Responsibility |
|------|---------------|
| `Dockerfile` | Python backend container |
| `docker-compose.yml` | Multi-service orchestration |
| `nginx.conf` | Reverse proxy config (frontend static + API proxy) |
| `deploy.sh` | One-click deployment script |

---

## Call Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
└───────┬─────────────────────┬───────────────────────────────┘
        │                     │
        ▼                     ▼
┌───────────────┐   ┌──────────────────┐
│  Next.js SPA  │   │ chat.html (legacy)│
│  page.tsx     │   │ vanilla HTML/CSS  │
│  layout.tsx   │   │ inline JS         │
│  globals.css  │   │ regex markdown    │
└───────┬───────┘   └────────┬─────────┘
        │                    │
        │  POST /api/chat    │  POST /chat
        │  POST /api/todos   │  POST /todos
        │                    │
        └────────┬───────────┘
                 │
        ┌────────▼────────┐
        │  nginx / FastAPI │
        │  main.py         │
        │  - /chat         │
        │  - /chat/stream  │
        │  - /todos        │
        │  - /skills       │
        │  - /health       │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ LLMHRAssistant   │
        │ hr_assistant.py  │
        │  ┌──────────┐    │
        │  │SkillsRAG │    │
        │  └────┬─────┘    │
        └───────┼──────────┘
                │
        ┌───────▼─────────┐
        │ data/skills.json │
        │ (287 skills)     │
        └─────────────────┘
                │
        ┌───────▼─────────┐
        │  LLM API         │
        │  (Kimi/DeepSeek/ │
        │   OpenAI)        │
        └─────────────────┘
```

---

## Data Flow

### Chat Flow
1. User types message → `page.tsx` captures in React state
2. `POST /api/chat` with `{message, history, stream: false}`
3. `main.py` → `LLMHRAssistant.chat()` → `SkillsRAG.search(query)` → retrieves top-3 skills
4. Skills context injected into system prompt → sent to LLM API
5. Response returned → rendered via `ReactMarkdown` + `remarkGfm`
6. Response also sent to `POST /todos` → generates structured action items

### State Management (page.tsx)
- `chats[]` — persisted to `localStorage('hr-chats')` — **conflicts with chat.html**
- `activeChatId` — which chat is selected
- `input` — current textarea value
- `isLoading` — request in flight
- `sidebarOpen` — mobile sidebar toggle
- `darkMode` — theme toggle (NOT persisted to localStorage)
- `rightPanel` — "skills" | "todos" | null
- `skills[]` — skills returned from API
- `todos[]` — action items from API

---

## Code Quality Issues — Territory Scan

### Critical
1. **Duplicate frontends**: `page.tsx` and `chat.html` implement identical UX, share same localStorage key → data corruption risk
2. **Monolithic `page.tsx` (430 lines)**: Single component handles sidebar, chat, right panel, API calls, state management — no separation of concerns
3. **Stale closure in `sendMessage`**: Uses `chats` from closure, not latest state; `chats.find` inside callback after async setState
4. **Dark mode not persisted**: Unlike `chat.html` which persists theme, Next.js version does not
5. **Unused `next.config.ts`**: Conflicting with `next.config.js` — only `.js` is active

### High
6. **`CATEGORIES` constant unused** in `page.tsx`
7. **Bare except** clauses in `hr_assistant.py` (`get_todos`, `load_skills`)
8. **Regex-based markdown** in `chat.html` — fragile parsing, misses nestings
9. **No TypeScript interfaces** for API responses (any types)
10. **No error boundary** in React app — any uncaught render error crashes entire app
11. **No debouncing** on textarea input or send

### Medium
12. **Singleton `_assistant_instance`** — untestable, prevents DI
13. **Hardcoded token limit** (3000 in body, 2000 in LLM call, 800 in skills context)
14. **CSS variables + Tailwind dark: mix** — uses CSS custom properties AND Tailwind dark variants inconsistently
15. **`_reload_env_from_file`** redundant — called in `__init__` after module-level `load_dotenv`
16. **No PWA install prompt or update handling** in Next.js PWA

### Low
17. **`next-pwa` v5** — could upgrade to `@serwist/next` for better Next.js 14 support
18. **No loading skeletons** — typing indicator only for AI response, no skeleton for sidebar/panel loads

---

## Design Principles Gap (per soul.md Louis Kahn)

The current UI is **functional but not resonant**. Mapping against the three rooms:

| Room | Principle | Current State | Gap |
|------|-----------|---------------|-----|
| **Kimbell** | Light is data — structure determined by how it must arrive | Messages arrive in flat bubbles. No hierarchy of importance. Skills and TODOs in separate panel — not integrated into the reading flow. | Data arrival is mechanical, not designed backward from the person's reading experience |
| **Esherick** | Interface faces both ways — outward to world, inward to person | Dark/light toggle implicit. Panel tabs let user switch between skills/todos, but no unification. | Module depth is shallow — toggling between skills and todos is a manual choice, not a reconciliation |
| **Salk** | Subtract until only true act remains | Empty state has 4 quick-questions. Sidebar always visible. Header with title and dark toggle. Right panel always present. | Too much chrome. Empty state should be serene. The question is the act — everything else is subordinate |

---

## Scope Boundaries

**In scope for this refactor:**
- `frontend/src/app/page.tsx` — component decomposition, state management patterns, dark mode persistence
- `frontend/src/app/globals.css` — CSS architecture, design tokens
- `frontend/src/app/layout.tsx` — error boundary, metadata completeness
- `frontend/tailwind.config.js` — design system foundation

**Out of scope (not requested / high risk):**
- Backend `hr_assistant.py` structural changes — functional, well-tested
- `chat.html` — user asked to optimize the Next.js frontend, not the legacy one
- Infrastructure files
- Skills data format changes
