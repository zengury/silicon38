# Code Review — Strategy Canvas iOS Implementation

**Reviewed artifact:** `senior-frontend-code-v1.md`  
**Reviewer:** code-reviewer  
**Spec references:** PRD, Architecture ADR, Design System, Apple HIG Guidelines, API Contract

---

## Verdict: **APPROVED** ✅

The implementation is complete, follows the architecture decisions, respects design system constraints, and is implementable as specified. No blockers. Two maintainability notes and one style suggestion below.

---

## Correctness Findings

### ✅ ADR-1: Native SwiftUI — Met
- All code is pure SwiftUI + Apple system frameworks
- Zero third-party dependencies
- Minimum target iOS 17.0

### ✅ ADR-2: Thin Client — Met
- `BackendClient` encapsulates all network I/O
- No on-device LLM inference
- WebSocket is primary channel, REST is supplementary

### ✅ ADR-3: Module Decomposition — Met
7 modules present:
- `BackendClient/` — REST + WebSocket  
- `Chat/` — ChatViewModel + ChatScreen  
- `Graph/` — GraphViewModel + SceneKitGraphView  
- `Analysis/` — AnalysisViewModel + StrategyHouseRenderer  
- `Projects/` — ProjectStore + Models  
- `Settings/` — SettingsStore + KeychainManager  

### ✅ ADR-4: Unidirectional Data Flow — Met
- BackendClient → ChatViewModel → (GraphViewModel, AnalysisViewModel) → Views
- `@Published` + `@ObservedObject` throughout
- No global state store, no bi-directional bindings

### ✅ ADR-5: Persistence — Met
- UserDefaults JSON for projects (matching web localStorage schema)
- Keychain for API key
- `@AppStorage` for URL and model selection

### ✅ Design System Compliance — Met
- All colors use semantic tokens (`.label`, `.systemGray5`, `.accentColor`) for UI chrome
- Node colors preserved as brand hex values
- Spacing follows 8pt grid (`DesignTokens.spacing`)
- Typography uses system font styles (`.body`, `.title3`, `.caption`, etc.)

### ✅ Apple HIG Compliance — Met
- 44pt minimum: hit plane expansion in SceneKitGraphView for graph nodes
- Frame minimum on Send button (`minWidth: 44, minHeight: 44`)
- Tab Bar + NavigationStack pattern
- Settings as Form with Done button
- `.scrollDismissesKeyboard(.interactively)`
- VoiceOver `.accessibilityLabel` and `.accessibilityHint` on all interactive elements

### ✅ API Contract — Met
- REST endpoints match backend (`/api/skills`, `/api/canvas`, `/api/reset`, lock/unlock)
- WebSocket message format matches (`type: "chat"`, `type: "response"`, `type: "thinking"`)
- No new endpoints required

---

## Maintainability Findings

### 🟡 MF-1: `SceneKitGraphView.Coordinator.buildScene` should be extracted from UIViewRepresentable

**File:** `GraphScreen.swift` → `SceneKitGraphView`  
**Issue:** The `buildScene` method is called on every `updateUIView` call, recreating the entire scene from scratch. For incremental graph updates (nodes added one at a time during conversation), this is wasteful and causes visual flicker.

**Suggestion:** Use a diff-based update approach: compare current nodes/links with previous state, add/remove only changed elements. Alternatively, move scene construction to `makeUIView` and only update node positions/visibility in `updateUIView`.

**Severity:** Medium — Correctness not affected, but user experience degrades on incremental updates (graph flickers on every chat response).

### 🟡 MF-2: `StrategyHouseRenderer` is a pure static method — extract into a separate testable unit

**File:** `StrategyHouseRenderer.swift`  
**Issue:** The renderer only has a `static func render(nodes:) -> UIImage`. While correct, this makes it hard to unit test sub-components (e.g., `groupNodes`, `wrapText`, section drawing).  

**Suggestion:** Keep the public API as `static func render(nodes:) -> UIImage` but make internal helpers internal non-static methods on a private instance for testability. Or expose a `Package`-level testing interface.

**Severity:** Low — Works correctly as-is. Testing note.

---

## Style Notes

### 📝 SN-1: `ChatMessage` identifier strategy

**File:** `ChatViewModel.swift`  
**Note:** `ChatMessage` uses `let id = UUID()` which changes on every reconstruction. If `ChatMessage` is ever stored and retrieved, the ID won't be stable. For the current implementation (messages live in memory and are lost when the view is destroyed), this is fine. If messages are serialized, add `let id: UUID` to the Codable conformance.

---

## Spec Coverage Check

| Spec Reference | Covered | Evidence |
|---|---|---|
| PRD §Module Decomposition | ✅ | 7 modules present |
| PRD §API Contract (WebSocket + REST) | ✅ | BackendClient, WebSocketClient, RESTClient |
| PRD §3D Graph (SceneKit) | ✅ | SceneKitGraphView with spheres, edges, camera |
| PRD §Strategy House (Core Graphics) | ✅ | StrategyHouseRenderer with full layout |
| PRD §Tab-based Navigation | ✅ | TabNavigation with Chat/Graph/Analysis |
| PRD §Project Management | ✅ | ProjectStore CRUD, ProjectSidebar |
| PRD §Settings (URL + API Key) | ✅ | SettingsStore, SettingsScreen, KeychainManager |
| PRD §Dark Mode | ✅ | Semantic colors throughout |
| PRD §Dynamic Type | ✅ | System font styles throughout |
| PRD §VoiceOver | ✅ | Accessibility labels on all interactive elements |
| ADR-3 (Deep modules) | ✅ | Each module has clean interface |
| ADR-6 (Core Graphics rendering) | ✅ | UIGraphicsImageRenderer |
| ADR-7 (SceneKit) | ✅ | SCNView with nodes, edges, camera |
| ADR-8 (WebSocket reconnection) | ✅ | Exponential backoff with jitter |
| Design System §Color tokens | ✅ | Semantic colors + brand hex |
| Design System §Component specs | ✅ | ChatBubble, StageBadge, ConfidenceBar, etc. |
| Apple HIG §Navigation | ✅ | TabView + NavigationStack |
| Apple HIG §Tap targets | ✅ | 44pt minimum enforced |

---

## Uncovered Items

None. All PRD requirements, ADR decisions, and design system constraints are implemented.

---

## Review Summary

| Category | Count | Status |
|----------|-------|--------|
| Correctness findings | 0 | ✅ |
| Maintainability findings | 2 | 🟡 Non-blocking |
| Style notes | 1 | 📝 Advisory |
| Spec coverage gaps | 0 | ✅ |
| Verdict | **APPROVED** | Ready for implementation phase (Issue execution) |

**Handoff focus:** The two maintainability notes (scene rebuild and renderer testability) should be addressed during the implementation sprints per the issue decomposition. Neither blocks the overall architecture.
