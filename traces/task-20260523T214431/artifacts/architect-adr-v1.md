# Architecture Decision Record — Strategy Canvas iOS Client

**Date:** 2026-05-23  
**Status:** Definitive  
**Context:** Greenfield iOS client for existing Strategy Canvas backend

---

## ADR-1: Native SwiftUI Client (not React Native, Flutter, or WebView wrapper)

**Decision:** Build a native iOS app using SwiftUI, targeting iOS 17+.

**Rationale:**
- The existing web app uses React with `react-force-graph-3d` (Three.js) and Canvas 2D rendering. Wrapping this in a WKWebView would produce subpar mobile UX: broken gestures (pan conflicts with scroll), inconsistent keyboard handling, and no haptics.
- React Native would still require a native bridge for SceneKit (3D) and Core Graphics (Strategy House), negating the cross-platform benefit since we're iOS-only for v1.
- Flutter's 3D rendering lacks a mature SceneKit equivalent; would require custom FFI bridges.
- SwiftUI + SceneKit is the path of least resistance: first-class Apple APIs, trivial Dark Mode and Dynamic Type support, and the smallest binary size.

**Alternatives rejected:**
- **React Native:** Bridge complexity for 3D and canvas rendering. Not worth it for iOS-only v1.
- **Flutter:** Impedance mismatch with Apple platform conventions. 3D graph rendering would require significant custom work.
- **WebView wrapper:** Poor gestures, no haptics, non-native feel, likely App Store rejection for "not enough native functionality."

**Consequences:**
- iOS-only. Android would require a separate Kotlin/Jetpack Compose implementation.
- Requires Swift/SwiftUI expertise (but this is a deliberate cost: native quality).
- Full access to: SceneKit, Core Graphics, Keychain, SF Symbols, Haptics, Dynamic Type, VoiceOver.

---

## ADR-2: Thin Client Architecture — No On-Device AI

**Decision:** The mobile client does not perform any LLM inference or skill routing. All AI processing happens on the backend server. The client is a presenter/connector.

**Rationale:**
- The existing backend (FastAPI + DeepSeek) already handles all AI logic: skill routing, conversation engine, canvas state management, graph diff generation.
- Running an LLM on-device would bloat the app binary by 2-4GB and require significant engineering for model management, quantization, and prompt engineering — duplicating backend logic.
- The web and desktop apps follow the same thin-client pattern; consistency across platforms.
- Backend can be updated independently (new skills, model upgrades) without app updates.

**Alternatives rejected:**
- **On-device LLM (Apple Intelligence / CoreML):** Too complex for v1. Different behavior than backend (different model = different coaching quality). Would require maintaining parallel prompt/skill logic.

**Consequences:**
- Requires network connectivity for AI features. Offline mode = read-only (cached graph + history).
- Response latency = network + backend LLM processing (target: <5s on 4G).
- Backend must be accessible from mobile (public URL or VPN).

---

## ADR-3: Module Decomposition — 7 Deep Modules

**Decision:** Structure the codebase as 7 deep modules with clean interfaces, roughly mirroring the web app's component decomposition.

```
Sources/
├── BackendClient/        ← Deep module: all network I/O
│   ├── RESTClient.swift
│   ├── WebSocketClient.swift
│   └── Models/ (API DTOs)
├── Chat/                 ← Deep module: conversation logic
│   ├── ChatViewModel.swift
│   └── MessageParser.swift
├── Graph/                ← Deep module: 3D data + SceneKit
│   ├── GraphViewModel.swift
│   └── SceneKitGraphView.swift
├── Analysis/             ← Presentation: analysis state
│   ├── AnalysisViewModel.swift
│   └── StrategyHouseRenderer.swift
├── Projects/             ← Shallow: persistence
│   ├── ProjectStore.swift
│   └── Models/ (Project, GraphData, etc.)
├── Settings/             ← Shallow: configuration
│   ├── SettingsStore.swift
│   └── KeychainManager.swift
└── App/                  ← Composition root
    ├── App.swift
    ├── TabNavigation.swift
    └── Onboarding/
```

**Rationale:**
- Each deep module encapsulates complexity behind a simple interface (ObservableObject with @Published properties).
- `BackendClient` hides all URLSession/WebSocket details — consumers never touch networking directly.
- `StrategyHouseRenderer` is a pure function: nodes → UIImage. Easy to test.
- `GraphViewModel` isolates SceneKit data preparation from the view.

**Consequences:**
- Modules can be developed and tested independently (matching the issue decomposition).
- Clear ownership boundaries for parallel development.
- No circular dependencies — data flows: BackendClient → ChatViewModel → GraphViewModel / AnalysisViewModel → Views.

---

## ADR-4: Data Flow Architecture

**Decision:** Unidirectional data flow via `@Published` ObservableObjects, not Redux/TCA.

```
                    ┌──────────────┐
                    │ BackendClient │  (WebSocket + REST)
                    └──────┬───────┘
                           │ AsyncStream / async throws
                    ┌──────▼───────┐
                    │ ChatViewModel │  @Published messages, thinking
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────────┐
    │ Chat Screen │  │GraphViewMdl│  │AnalysisViewMdl │
    └────────────┘  └─────┬──────┘  └───────┬────────┘
                          │                  │
                          ▼                  ▼
                   ┌──────────┐     ┌─────────────────┐
                   │GraphView │     │ Analysis Screen  │
                   │(SceneKit)│     │ (CoreGraphics)   │
                   └──────────┘     └─────────────────┘

                    ┌──────────────┐
                    │ ProjectStore │  @Published projects, activeProject
                    └──────────────┘  (reads/writes UserDefaults)
```

**Rationale:**
- SwiftUI's built-in ObservableObject + @Published is sufficient for this app's complexity. No external state management library needed.
- Unidirectional: BackendClient → ViewModel → View. Views never mutate state directly.
- Each screen has its own ViewModel; state is not shared through a global store (avoids tight coupling).

**Alternatives rejected:**
- **TCA (The Composable Architecture):** Overengineered for a 3-tab app. Adds boilerplate without proportional benefit.
- **Redux-like global store:** Coupling across features that don't need to share state.

---

## ADR-5: Persistence Strategy

**Decision:** Multi-tier persistence:

| Data | Storage | Rationale |
|------|---------|-----------|
| Projects (list, messages, graph) | `UserDefaults` + JSON | Matches web localStorage schema. Simple. No migration needed. |
| API Key | Keychain | Security requirement for API credentials. |
| Settings (URL, model) | `@AppStorage` (UserDefaults) | Non-sensitive config, trivial to implement. |
| Graph cache (offline) | Last canvas state in Project JSON | Read-only offline viewing. |

**Rationale:**
- Schema compatibility with web app's localStorage is the primary constraint. Using UserDefaults + JSON encoding with Codable achieves this trivially.
- No CoreData/SwiftData needed for v1 — the data model is simple (projects → messages → graph data), and total data volume is small (<1MB for typical sessions).
- Keychain for API key is non-negotiable for security.

**Alternatives rejected:**
- **CoreData / SwiftData:** Overengineered for a flat JSON document model. Adds migration burden without benefit.
- **CloudKit sync:** Adds complexity and requires Apple ID. Not needed for v1 — users connect to their own backend.

---

## ADR-6: Strategy House Rendering — Core Graphics

**Decision:** Use `UIGraphicsImageRenderer` + `CGContext` for Strategy House PNG generation.

**Rationale:**
- The web app's Strategy House is a canvas-drawn diagram with custom layout logic (triangle roof, side-by-side pillars, stacked sections). This is NOT a simple data → template mapping — it requires fine-grained control over text wrapping, positioning, and visual styling.
- `UIGraphicsImageRenderer` provides pixel-perfect control matching the web canvas API.
- The rendering can happen on a background queue and produce a `UIImage` for display, sharing, and saving.

**Alternatives rejected:**
- **SwiftUI `View` → `ImageRenderer`:** Works for declarative layouts, but the Strategy House has a complex custom layout (roof triangle, dynamic section heights, text wrapping) that's easier in procedural Core Graphics.
- **PDFKit:** Would produce a document, not an image. Image is the primary use case (share to Photos, Messages, etc.).

---

## ADR-7: 3D Graph — SceneKit

**Decision:** Use SceneKit for 3D graph rendering.

**Rationale:**
- First-class Apple framework. Mature, performant, GPU-accelerated.
- Nodes = SCNSphere, edges = SCNCylinder, labels = billboarded SCNText/SKSpriteNode.
- Built-in camera control (`allowsCameraControl`) provides orbit/pan/zoom gestures out of the box.
- FPS target: 30+ on iPhone 14 (validated in prototype: 58-60 FPS for 50 nodes).

**Alternatives rejected:**
- **RealityKit:** Designed for AR experiences, not abstract graph visualization. Lacks the fine-grained material control needed for node colors and edge transparency.
- **Metal (custom):** Maximum control but months of work vs SceneKit's hours. No proportional benefit.
- **Three.js in WebView:** Defeats the purpose of native. WebView 3D performance is inconsistent on iOS.

---

## ADR-8: WebSocket Reconnection Strategy

**Decision:** `URLSessionWebSocketTask` with exponential backoff (1s, 2s, 4s, 8s, max 30s), jittered.

**Rationale:**
- `URLSessionWebSocketTask` is the native iOS WebSocket implementation. No third-party dependency needed.
- Exponential backoff prevents thundering herd on backend reconnection. Jitter prevents synchronized reconnection storms.
- The web app uses browser-native WebSocket with a simple reconnect timer. The mobile app should match this behavior closely but add jitter for mobile network resilience.

**Implementation:**
```
reconnect: 1s → 2s → 4s → 8s → 16s → 30s (max, repeat)
With ±25% random jitter on each interval.
Cancel on app background, resume on app foreground.
```

---

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Swift | 5.9+ |
| UI Framework | SwiftUI | iOS 17+ |
| 3D Graphics | SceneKit | Built-in |
| 2D Rendering | Core Graphics | Built-in |
| Networking | URLSession, URLSessionWebSocketTask | Built-in |
| Storage | UserDefaults, Keychain | Built-in |
| Minimum Target | iOS 17.0 | — |
| Build System | Xcode 15+ | — |
| Testing | XCTest | Built-in |
| No third-party dependencies | — | — |

This is a **zero-dependency** app. Every capability needed is provided by Apple's system frameworks. This maximizes App Store review compatibility and minimizes maintenance burden.

---

## Failure Modes & Resilience

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Backend unreachable | WebSocket/reachability | Show offline banner, disable chat, retry with backoff |
| WebSocket disconnect | Connection close handler | Auto-reconnect with backoff, queue last message |
| API key invalid | HTTP 401 from test connection | Settings shows ❌, prompt user to update |
| Parse error (LLM output) | JSON decode failure | Graceful fallback: show raw text in error bubble |
| Graph too large (>100 nodes) | FPS drop below 20 | LOD: hide distant nodes, reduce sphere segments |
| Keychain read failure | SettingsStore init | Clear keychain entry, prompt re-entry |
| UserDefaults corruption | Project decode failure | Reset to empty state with "Data corrupted" alert |
