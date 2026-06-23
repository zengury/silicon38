# Strategy Canvas for iOS — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-05-23  
**Status:** Ready for Implementation

---

## Problem Statement

Strategy Canvas is a strategic coaching tool — an AI-guided dialogue system that helps individuals and teams crystallize complex decisions into named concepts, golden phrases, and a structured "Strategy House" diagram. The product already exists as a web application (FastAPI + React + 3D Force Graph) and an Electron desktop app (IPC-based, local-first with DeepSeek AI).

The problem: **users cannot access Strategy Canvas on their iPhones.** Strategic thinking often happens during commutes, walks, or coffee breaks — moments when a desktop is unavailable. The web version is not optimized for mobile (3D Force Graph, 5-panel layout, and WebSocket chat degrade on small touch screens). No mobile client exists.

## Solution

Build a native iOS client (SwiftUI, targeting iOS 17+) that connects to an existing Strategy Canvas backend instance. The client adapts the 5-panel architecture to a mobile-appropriate navigation model — collapsing panels into a tab-based interface with drill-down screens while preserving the core interaction: real-time AI coaching dialogue, progressive graph visualization, Strategy House generation, and project management.

The app will be distributed via **Apple TestFlight** using the standard Xcode → App Store Connect pipeline. The user configures their backend URL and API key in Settings; the app connects over WebSocket for real-time chat and REST for data operations.

---

## User Stories

1. As a strategy coach, I want to open Strategy Canvas on my iPhone so that I can continue a coaching session during my commute.
2. As a startup founder, I want to chat with the AI coach on my phone so that I can work through strategic decisions while on the go.
3. As an existing web user, I want my conversation and graph state to persist across devices so that I can start on desktop and continue on mobile.
4. As a new user, I want to connect my phone to my Strategy Canvas backend so that I can use my existing API key.
5. As a visual thinker, I want to see my strategy graph in 3D on my phone so that I can interact with nodes and understand relationships.
6. As a user in a meeting, I want to quickly generate a Strategy House diagram from my conversation so that I can share it with the team.
7. As a user, I want to download the Strategy House as a PNG so that I can paste it into a presentation.
8. As a user, I want to see my golden phrases and named concepts so that I can reference them in discussion.
9. As a user, I want the AI coach to respond in under 5 seconds on a cellular connection so that the conversation feels natural.
10. As a user, I want to manage multiple projects (cases) so that I can work on different strategic decisions.
11. As a user, I want to rename and delete projects so that my workspace stays organized.
12. As a user, I want the app to support Dark Mode so that I can use it comfortably at night.
13. As a user, I want the app to respect Dynamic Type so that I can read comfortably at my preferred text size.
14. As a user with accessibility needs, I want VoiceOver to work properly on all screens so that I can use the app.
15. As a user, I want to see connection status (online/offline) so that I know if I need to check my network.
16. As a user, I want to configure my backend URL and API key in Settings so that I can connect to my own server or a shared instance.
17. As a beta tester, I want to install the app via TestFlight so that I can try it before it goes to the App Store.
18. As a user, I want to see a node selector that groups nodes by type so that I can understand my strategy at a glance.
19. As a user, I want to tap a node in the graph to fly to it and see details so that I can explore specific strategic elements.
20. As a user, I want the app to show my current strategy stage (Explore → Converge → Stress Test → Commit → Review) so that I know where I am in the process.

---

## Implementation Decisions

### Architecture: Native iOS Client + Existing Backend

The mobile client is a **thin client** — it does not replicate the AI engine or skill routing logic. All AI processing happens on the backend. The client is responsible for:
- Rendering the UI (SwiftUI)
- Managing local project state (SwiftData / UserDefaults)
- Connecting to the backend over WebSocket + REST
- Rendering the 3D graph (SceneKit)
- Generating the Strategy House canvas (Core Graphics)

**No local AI inference.** This keeps the app binary small, avoids on-device LLM complexity, and ensures consistent behavior with the web/desktop versions.

### Module Decomposition

| Module | Responsibility | Deep? | Test? |
|--------|---------------|-------|-------|
| `BackendClient` | WebSocket + REST communication with configurable URL | Deep — encapsulates all network concerns | Yes |
| `ChatViewModel` | Chat message state, send/receive, thinking indicator | Deep — clean ObservableObject | Yes |
| `ProjectStore` | CRUD for projects, localStorage sync, active project management | Shallow — wraps UserDefaults | No |
| `GraphViewModel` | 3D graph data, node selection, camera control | Deep — isolates SceneKit concerns | Yes |
| `StrategyHouseRenderer` | Generates Strategy House PNG from graph data | Deep — pure function, input → output | Yes |
| `SettingsStore` | Backend URL, API key, model selection | Shallow | No |
| `Navigator` | Tab + NavigationStack routing, deep links | Shallow | No |

### Navigation Model

The 5-panel desktop layout collapses into a **TabView with 3 tabs**:

1. **Chat** (primary) — conversation with AI coach
2. **Graph** — 3D force graph viewing and interaction
3. **Analysis** — Strategy House, golden phrases, named concepts, stage indicator

A **sidebar sheet** (swipe from left) or Settings gear icon provides:
- Project list (create, select, rename, delete)
- Settings (backend URL, API key, model)

### API Contract

The mobile app uses the **same API as the web client** (no new endpoints needed):

**REST:**
- `GET /api/skills` — list available skills
- `GET /api/canvas` — current canvas state
- `POST /api/canvas/lock/{node_id}` — lock a node
- `POST /api/canvas/unlock/{node_id}` — unlock a node
- `POST /api/reset` — reset session

**WebSocket:**
- `WS /ws` — real-time chat
  - Send: `{type: "chat", text: "..."}`
  - Receive: `{type: "response", reply, stage, confidence, canvas, ...}`

### Data Flow

```
User types message → ChatViewModel.send()
  → BackendClient.ws.send({type:"chat", text})
  → Backend AI processes
  → BackendClient receives response
  → ChatViewModel updates messages
  → GraphViewModel updates graphData
  → AnalysisViewModel updates stage/confidence/phrases
```

### 3D Graph Adaptation

The web app uses `react-force-graph-3d` (Three.js). The iOS app uses **SceneKit** with:
- `SCNView` as the rendering surface
- Nodes rendered as `SCNSphere` with emissive materials matching the 14 node-type colors
- Edges as `SCNCylinder` with transparency
- Label sprites (billboard constraint) for node names
- Orbit camera with pan/zoom gestures
- Auto-rotate when idle
- Tap node → camera fly-to animation

### Strategy House Rendering

The web app renders the Strategy House on an HTML canvas using 2D drawing APIs. The iOS app uses **Core Graphics** with the same algorithm (translated to Swift):
- `UIGraphicsImageRenderer` to create a UIImage
- `CGContext` for drawing rectangles, text, gradients
- Output: shareable PNG via standard iOS Share Sheet

### Offline Behavior

The app requires a backend connection for AI features. When offline:
- Chat input is disabled with a "Reconnecting..." indicator
- Graph reflects the last known canvas state (cached)
- Analysis panel shows last known data
- Settings and project management remain available

### State Persistence

Projects and settings are stored locally:
- **Settings**: `@AppStorage` / UserDefaults
- **Projects**: JSON-encoded array in UserDefaults (compatible with web localStorage schema)
- **Graph cache**: Last canvas state stored per-project for offline viewing

### TestFlight Distribution

1. Create Xcode project with bundle ID `com.strategiccanvas.ios`
2. Configure code signing with Apple Developer account
3. Archive → Distribute App → App Store Connect
4. Create TestFlight group, upload build
5. Invite testers via email or public link

---

## Testing Decisions

### What Makes a Good Test

- Test external behavior, not implementation details
- `BackendClient` tests: verify correct WebSocket framing and REST request formation, mock the server
- `StrategyHouseRenderer` tests: given a set of nodes, verify PNG output dimensions and content markers
- `ChatViewModel` tests: verify message ordering, thinking state transitions
- `GraphViewModel` tests: verify graph data parsing, node selection state

### Modules to Test

| Module | Tests | Priority |
|--------|-------|----------|
| `BackendClient` | Mock server, verify send/receive framing | High |
| `ChatViewModel` | State transitions, message ordering | High |
| `StrategyHouseRenderer` | Input → output verification | Medium |
| `GraphViewModel` | Data parsing from JSON | Medium |

### Testing Strategy

- Use `XCTest` for unit tests
- Use `URLProtocol` mocking for network layer tests
- Snapshot testing (optional) for Strategy House rendering

---

## Out of Scope

- **Offline AI**: No on-device LLM inference. Requires backend connection for AI features.
- **iPad layout optimization**: v1 targets iPhone only. iPad will use iPhone layout at 2x scale (acceptable for TestFlight beta).
- **Push notifications**: No remote push notifications in v1.
- **Widget**: No iOS home screen widget.
- **Watch companion**: No Apple Watch app.
- **Siri integration**: No Siri shortcuts or intents.
- **visionOS**: Not in scope — different interaction paradigm.
- **Android client**: Not in scope for this PRD.
- **Multi-backend support**: One backend URL per configuration. No automatic failover.
- **File upload/attachment**: Text-only chat in v1.
- **Web search integration from mobile**: Relies on backend web search capabilities if configured.

---

## Success Criteria

1. App builds, archives, and uploads to App Store Connect without errors
2. TestFlight beta is accessible to invited testers within 24 hours of upload
3. User can configure backend URL and API key and connect successfully within 60 seconds of first launch
4. AI coach responses appear within 5 seconds on a 4G connection (including network latency)
5. 3D graph renders at 30+ FPS on iPhone 14 and newer
6. Strategy House PNG exports at the same visual quality as the web version
7. All interactive elements are at least 44×44 points
8. VoiceOver reads all primary UI elements in logical order
9. Dark Mode renders correctly across all screens
10. App size under 50MB (uncompressed .ipa)
