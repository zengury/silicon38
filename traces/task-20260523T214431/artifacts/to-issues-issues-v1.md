# Strategy Canvas iOS — Issue Decomposition

**Source:** `to-prd-prd-v1.md`  
**Date:** 2026-05-23  
**Vertical slices (tracer bullets) across all layers: schema → API → UI → test**

---

## Issue Breakdown (Dependency Order)

### Issue 1: Xcode Project Scaffold & Configuration
**Type:** HITL  
**Blocked by:** None — can start immediately  
**User stories:** #17 (TestFlight installation)  
**Size:** M

**What to build:** Create the Xcode project with bundle ID `com.strategiccanvas.ios`, configure Info.plist (privacy manifest, encryption exemption), set deployment target to iOS 17+, enable TestFlight distribution settings, and add the AppIcon asset catalog.

**Acceptance criteria:**
- [ ] Xcode project opens and builds without errors
- [ ] Bundle ID registered in Apple Developer account
- [ ] PrivacyInfo.xcprivacy present with required declarations
- [ ] ITSAppUsesNonExemptEncryption = NO
- [ ] Development team and signing configured

---

### Issue 2: BackendClient — REST + WebSocket Client
**Type:** AFK  
**Blocked by:** Issue 1 (project scaffold)  
**User stories:** #3, #7, #12  
**Size:** L

**What to build:** A `BackendClient` module that encapsulates all network communication with the Strategy Canvas backend. Uses `URLSession` for REST calls and `URLSessionWebSocketTask` for the WebSocket chat connection. Supports configurable `baseURL` and `apiKey`, automatic reconnection with exponential backoff, and JSON encoding/decoding for all API payloads. Exposes async/await APIs.

**Acceptance criteria:**
- [ ] REST: `GET /api/skills`, `GET /api/canvas`, `POST /api/reset` return decoded models
- [ ] WebSocket: connects to `ws://<baseURL>/ws` and delivers messages via AsyncStream
- [ ] WebSocket auto-reconnects on disconnect with 1s/2s/4s/8s backoff
- [ ] All network errors are typed and surfaced to callers
- [ ] Unit tested with `URLProtocol` mocking for REST and mock WebSocket for streaming

---

### Issue 3: ProjectStore — Local Project Persistence
**Type:** AFK  
**Blocked by:** Issue 1 (project scaffold)  
**User stories:** #10, #11  
**Size:** M

**What to build:** A `ProjectStore` ObservableObject that manages project CRUD (create, read, update, delete, select active) using `UserDefaults` + JSON encoding. Schema matches the web app's localStorage format for cross-device compatibility. Exposes `@Published` properties for active project, project list, and graph state.

**Acceptance criteria:**
- [ ] Create, rename, delete projects with persistence across app launches
- [ ] Active project selection persisted and restored on launch
- [ ] JSON schema compatible with web app's `localStorage` format
- [ ] Empty state: new user gets a default "My Strategy" project
- [ ] Unit tested for CRUD operations and schema compatibility

---

### Issue 4: SettingsStore — Backend Configuration
**Type:** AFK  
**Blocked by:** Issue 1 (project scaffold)  
**User stories:** #2, #16  
**Size:** S

**What to build:** A `SettingsStore` ObservableObject using `@AppStorage` for backend URL, API key, and model selection. Includes a `testConnection()` method that pings the backend health endpoint to validate configuration. Key is stored in Keychain, not UserDefaults, for security.

**Acceptance criteria:**
- [ ] Backend URL, API key, model selection persisted
- [ ] API key stored in Keychain with read/write through SettingsStore
- [ ] `testConnection()` verifies reachability and returns success/failure
- [ ] URL auto-trims trailing slash on save
- [ ] Unit tested for Keychain read/write and URL normalization

---

### Issue 5: ChatViewModel — Conversation State Machine
**Type:** AFK  
**Blocked by:** Issue 2 (BackendClient), Issue 4 (SettingsStore)  
**User stories:** #1, #2, #9  
**Size:** L

**What to build:** A `ChatViewModel` ObservableObject that manages the conversation lifecycle: message list, send/receive, thinking state, error handling, reconnection. Connects to `BackendClient` for WebSocket chat. Parses incoming response JSON into messages, graph updates, stage changes, confidence scores, golden phrases, and named concepts.

**Acceptance criteria:**
- [ ] User messages appended locally and sent via WebSocket
- [ ] Coach responses parsed: reply, stage, confidence, graph data, golden phrases, named concepts
- [ ] "Thinking" state shown while waiting for response
- [ ] Send button disabled during thinking or when disconnected
- [ ] Error state: shows error bubble with retry action
- [ ] Response time tracked and displayed
- [ ] Unit tested for message ordering, parsing, and state transitions

---

### Issue 6: Chat Screen — Primary Tab UI
**Type:** AFK  
**Blocked by:** Issue 5 (ChatViewModel), Issue 3 (ProjectStore)  
**User stories:** #1, #2, #8  
**Size:** L

**What to build:** The Chat tab screen in SwiftUI. Features: message list (`ScrollView` + `LazyVStack`), user bubbles (blue, right-aligned), coach bubbles (gray, left-aligned), thinking indicator (animated dots), text input bar with `TextEditor` + send button, keyboard avoidance via `.ignoresSafeArea(.keyboard)`, and scroll-to-bottom on new messages.

**Acceptance criteria:**
- [ ] Messages render with correct alignment and styling per speaker
- [ ] New messages auto-scroll to bottom
- [ ] Thinking indicator animates (3 bouncing dots)
- [ ] Input bar rises with keyboard
- [ ] Send via button or keyboard return
- [ ] Empty state: "Start a conversation about the decision you're facing..."
- [ ] VoiceOver: message bubbles are accessible with speaker identification

---

### Issue 7: GraphViewModel — 3D Graph Data Management
**Type:** AFK  
**Blocked by:** Issue 5 (ChatViewModel)  
**User stories:** #5  
**Size:** M

**What to build:** A `GraphViewModel` ObservableObject that receives graph data from chat responses and transforms it into a format suitable for SceneKit rendering. Tracks node positions (from backend spatial engine), selected node state, camera target, and provides filtered/grouped node access by type.

**Acceptance criteria:**
- [ ] Parses `canvas.nodes` and `canvas.links` from chat response JSON
- [ ] Exposes `@Published` arrays of nodes and edges for SceneKit
- [ ] Node selection state: tap to select, tap again to deselect
- [ ] Camera animation target computed on selection
- [ ] Node grouping by type for legend display
- [ ] Unit tested for JSON parsing and selection logic

---

### Issue 8: Graph Screen — 3D SceneKit View
**Type:** AFK  
**Blocked by:** Issue 7 (GraphViewModel)  
**User stories:** #5, #19  
**Size:** XL

**What to build:** The Graph tab screen with a SceneKit `SCNView` wrapped in `UIViewRepresentable`. Renders nodes as `SCNSphere` with emissive materials matching the 14 node-type colors (light mode and dark mode variants). Edges as `SCNCylinder` with transparency. Node labels as billboarded `SCNText` or sprite overlays. Camera: orbit (`allowsCameraControl`), auto-rotate when idle, fly-to on node tap. Legend: horizontal scroll of node types with counts, tappable to highlight/filter.

**Acceptance criteria:**
- [ ] Nodes render at correct 3D positions with type-based colors
- [ ] Edges render between connected nodes
- [ ] Camera: drag to orbit, pinch to zoom, auto-rotate (can be toggled off)
- [ ] Tap node: camera flies to node with animation, node highlights
- [ ] Node labels visible as billboarded text
- [ ] Minimum sphere radius 12pt, hit region expanded to 44pt minimum
- [ ] Legend shows all node types present, tap legend item highlights those nodes
- [ ] FPS counter: 30+ FPS on iPhone 14 and newer
- [ ] Reduces motion: auto-rotate and fly-to disabled when system setting on
- [ ] VoiceOver: node selector list in Analysis tab serves as accessible fallback

---

### Issue 9: AnalysisViewModel — Summary State Management
**Type:** AFK  
**Blocked by:** Issue 5 (ChatViewModel)  
**User stories:** #8, #20  
**Size:** S

**What to build:** An `AnalysisViewModel` that aggregates conversation state for the Analysis tab: current stage (explore/converge/stress_test/commit/review), confidence score, judgment text, golden phrases list, and named concepts list. Updates in real-time as chat responses arrive.

**Acceptance criteria:**
- [ ] Stage displayed with bilingual label (e.g., "Converge / 收敛")
- [ ] Confidence bar: 0-100% with animated fill
- [ ] Judgment: one-line current assessment
- [ ] Golden phrases: styled quotes list
- [ ] Named concepts: tag-style list
- [ ] All values default to empty/nil until first chat response populates them

---

### Issue 10: Analysis Screen — Summary + Strategy House Tab
**Type:** AFK  
**Blocked by:** Issue 9 (AnalysisViewModel)  
**User stories:** #6, #13  
**Size:** L

**What to build:** The Analysis tab screen. Top section: stage badge, confidence bar, judgment text. Middle: golden phrases with quote styling. Bottom: Strategy House generation area. Before generation: "Generate Strategy House" button. After generation: scrollable PNG preview + Share/Regenerate buttons. Uses Core Graphics for rendering (see Issue 11).

**Acceptance criteria:**
- [ ] Stage and confidence display updates live from chat responses
- [ ] Golden phrases render with proper quotation styling
- [ ] Named concepts appear as tappable tags
- [ ] Generate button visible when graph has nodes, disabled when empty
- [ ] Generated Strategy House scrollable in preview
- [ ] Share button opens iOS Share Sheet (Save Image, AirDrop, Messages, etc.)
- [ ] Regenerate button available after first generation
- [ ] Dark Mode: all elements use semantic colors

---

### Issue 11: StrategyHouseRenderer — Core Graphics PNG Generator
**Type:** AFK  
**Blocked by:** Issue 7 (GraphViewModel) — needs node data  
**User stories:** #6, #13, #18  
**Size:** XL

**What to build:** A Swift port of the web app's `drawStrategyHouse()` canvas renderer. Takes a list of nodes and produces a `UIImage` using `UIGraphicsImageRenderer`. Sections: roof triangle (vision/goals), pillars (strategic options), foundation, tensions, signals, actions, external. Each section has bordered background, colored node badges, labels with content excerpts, confidence percentages. Responsive width: fits device width up to 600pt.

**Acceptance criteria:**
- [ ] Produces PNG matching the visual quality of the web version
- [ ] Roof section: triangle with vision/goal nodes
- [ ] Pillars: side-by-side rounded rectangles
- [ ] Sections adapt to number of nodes (dynamic height)
- [ ] Node confidence percentage shown
- [ ] "Generated by Strategic Canvas" watermark
- [ ] Dark Mode: background and text colors adapt
- [ ] Dynamic Type: text sizes scale with user preference
- [ ] Output image is high-resolution (@3x)
- [ ] Unit tested: given a known node set, output has expected dimensions and visual markers

---

### Issue 12: ProjectSidebar — Project Management Sheet
**Type:** AFK  
**Blocked by:** Issue 3 (ProjectStore)  
**User stories:** #10, #11  
**Size:** M

**What to build:** A project management view accessible from the Chat tab's toolbar (folder icon). Shows: list of projects with name, node count, and date. Active project highlighted. "+ New Project" button. Swipe-to-delete. Tap to rename (inline text field). Tap to switch active project.

**Acceptance criteria:**
- [ ] Project list with active project highlighted
- [ ] Create project with auto-generated name ("New Project N")
- [ ] Rename via inline editing
- [ ] Delete with confirmation (swipe or context menu)
- [ ] Switching projects updates chat, graph, and analysis immediately
- [ ] At least one project always exists

---

### Issue 13: TabView & Navigation Shell
**Type:** AFK  
**Blocked by:** Issues 6, 8, 10 (all three tab screens)  
**User stories:** #13, #14  
**Size:** M

**What to build:** The root `TabView` with three tabs (Chat, Graph, Analysis). Each tab has its own `NavigationStack`. Tab bar uses SF Symbols: `bubble.left.and.bubble.right` (Chat), `point.3.connected.trianglepath.dotted` (Graph), `chart.bar.doc.horizontal` (Analysis). Chat tab toolbar includes: project selector (folder icon → sheet) and settings (gear icon → push). Status bar overlay at top shows connection status and stage.

**Acceptance criteria:**
- [ ] Three tabs with correct SF Symbols
- [ ] Each tab has independent NavigationStack
- [ ] Toolbar buttons: folder (projects), gear (settings)
- [ ] Connection indicator: green dot (connected), red dot (disconnected)
- [ ] Tab bar respects safe area insets
- [ ] Dark Mode: tab bar uses system material

---

### Issue 14: Settings Screen
**Type:** AFK  
**Blocked by:** Issue 4 (SettingsStore), Issue 13 (Navigation shell)  
**User stories:** #16  
**Size:** S

**What to build:** Settings screen pushed from Chat tab toolbar. Fields: Backend URL (text field with paste detection), API Key (secure field with reveal toggle), Model picker (DeepSeek Chat / DeepSeek Reasoner). "Test Connection" button that calls SettingsStore.testConnection(). Connection status indicator. App version display.

**Acceptance criteria:**
- [ ] URL field with paste-from-clipboard detection and auto-trim
- [ ] API key field: secure entry with show/hide toggle, stored in Keychain
- [ ] Model picker with saved selection
- [ ] Test Connection: shows spinner → ✅ Connected or ❌ Failed with reason
- [ ] Changes persisted immediately on edit (no Save button needed)
- [ ] App version at bottom from Bundle

---

### Issue 15: App Launch & Onboarding Flow
**Type:** AFK  
**Blocked by:** Issue 4 (SettingsStore), Issue 3 (ProjectStore), Issue 13 (Navigation shell)  
**User stories:** #2, #16  
**Size:** M

**What to build:** App launch logic: if settings are configured (URL + API key exist), show the main TabView with last active project. If settings are missing (first launch), show a Welcome screen that guides the user to enter backend URL and API key. After successful connection test, transition to main view.

**Acceptance criteria:**
- [ ] First launch: Welcome → Settings → Connection Test → Main View
- [ ] Subsequent launches: Main View directly
- [ ] Welcome screen: app icon, tagline, "Get Started" button
- [ ] Transition animation: crossfade or navigation push
- [ ] If connection test fails, show error with option to retry or skip
- [ ] Skipped configuration: show main view with disconnected state, settings available from toolbar

---

### Issue 16: Dark Mode & Dynamic Type Support
**Type:** AFK  
**Blocked by:** Issues 6, 8, 10, 12, 13, 14 (all UI screens)  
**User stories:** #12, #14  
**Size:** M

**What to build:** Audit all screens for Dark Mode and Dynamic Type compliance. Replace all hardcoded colors with semantic colors (`.label`, `.secondaryLabel`, `.systemBackground`, `.systemGray5`, etc.). Ensure all text uses `.font(.body)`, `.font(.title3)`, etc. (system dynamic type). Verify at accessibility sizes (AX1-AX5) that no content is clipped.

**Acceptance criteria:**
- [ ] No hardcoded `Color.black`, `Color.white`, or hex colors for UI chrome
- [ ] Node colors (14 types) remain branded but labels adapt contrast
- [ ] All ScrollViews scroll when content exceeds screen at large Dynamic Type
- [ ] Chat bubbles scale text correctly
- [ ] Strategy House canvas text scales with `.preferredFont(forTextStyle:)`
- [ ] Tested with Accessibility Inspector at all size categories

---

### Issue 17: VoiceOver & Accessibility Audit
**Type:** AFK  
**Blocked by:** Issues 6, 8, 10, 12, 13, 14 (all UI screens)  
**User stories:** #14  
**Size:** M

**What to build:** Add accessibility labels, hints, and traits to all interactive elements. Graph screen: implement accessibility rotor for node list exploration. Chat: message bubbles read with speaker identification. Ensure logical VoiceOver reading order on every screen. Test navigation without visual feedback.

**Acceptance criteria:**
- [ ] Every button has `.accessibilityLabel` and `.accessibilityHint`
- [ ] Every text field has `.accessibilityLabel`
- [ ] Chat messages read as "You: [text]" or "Coach: [text]"
- [ ] Graph: rotor action reads node list by type + confidence
- [ ] Tab bar items labelled with position ("tab 1 of 3")
- [ ] Reduce Motion respected: graph auto-rotate and animations disabled
- [ ] VoiceOver navigation order is logical on every screen

---

### Issue 18: Error Handling & Offline States
**Type:** AFK  
**Blocked by:** Issue 2 (BackendClient), Issue 5 (ChatViewModel)  
**User stories:** #15  
**Size:** M

**What to build:** Comprehensive error handling: network errors, backend errors, parse errors, timeout. Offline banner ("No connection") with retry action. Backend error bubbles in chat. Connection indicator in status area. Graceful degradation: chat disabled when offline, graph shows cached state, analysis shows last known data.

**Acceptance criteria:**
- [ ] Offline: banner appears, chat input disabled, "Reconnecting..." shown
- [ ] Backend error: error bubble in chat with retry button
- [ ] Parse error: graceful fallback ("Coach had trouble understanding. Ask again?")
- [ ] Connection restored: banner dismisses, pending retry fires
- [ ] Settings shows connection status in real-time

---

### Issue 19: Chat Quick Replies & Dictation
**Type:** AFK  
**Blocked by:** Issue 6 (Chat Screen)  
**User stories:** #1, #2  
**Size:** S

**What to build:** Add quick-reply suggestion chips above the chat input based on conversation context (e.g., "Tell me more", "What are the risks?", "Let's move to the next step"). Support dictation via microphone button in the input bar (uses SFSpeechRecognizer or system dictation key).

**Acceptance criteria:**
- [ ] Suggestion chips appear above input, horizontally scrollable
- [ ] Tap chip inserts text into input (does not auto-send)
- [ ] Microphone button triggers system dictation
- [ ] Dictation results populate input field
- [ ] Suggestions update based on current stage

---

### Issue 20: Haptics & Polish
**Type:** AFK  
**Blocked by:** Issues 6, 8, 10 (all screens)  
**User stories:** All  
**Size:** S

**What to build:** Add haptic feedback for key interactions: light impact on node tap in graph, medium impact on message send, success notification on Strategy House generation complete, error notification on connection failure. Polish: launch screen, app icon, smooth transitions.

**Acceptance criteria:**
- [ ] Haptic: light impact on graph node tap
- [ ] Haptic: medium impact on send message
- [ ] Haptic: success on Strategy House generated
- [ ] Haptic: error on connection failure
- [ ] Launch screen: centered app icon + "Strategic Canvas" text
- [ ] App icon: 1024x1024 with all required sizes in asset catalog

---

### Issue 21: TestFlight Archive & Distribution
**Type:** HITL  
**Blocked by:** Issues 1-20 (all prior issues complete)  
**User stories:** #17  
**Size:** M

**What to build:** Final build configuration: increment version to 1.0 (build 1), verify all signing and capabilities, archive for App Store Connect, upload, create TestFlight group, invite testers. Write TestFlight build notes. Verify install flow on a physical device.

**Acceptance criteria:**
- [ ] Archive builds and validates without errors or warnings
- [ ] Upload to App Store Connect succeeds
- [ ] App passes beta review (privacy manifest, no crashes, no private APIs)
- [ ] TestFlight group created with at least 1 internal tester
- [ ] Build installs and launches on physical iPhone
- [ ] Build notes written in App Store Connect

---

## Dependency Graph

```
Issue 1 (scaffold)
├── Issue 2 (BackendClient)
│   └── Issue 5 (ChatViewModel)
│       ├── Issue 6 (Chat Screen) ──┐
│       ├── Issue 7 (GraphViewModel)│
│       │   ├── Issue 8 (Graph) ────┤
│       │   └── Issue 11 (Renderer)─┤
│       └── Issue 9 (AnalysisVM)    │
│           └── Issue 10 (Analysis)─┤
├── Issue 3 (ProjectStore)          │
│   └── Issue 12 (Sidebar) ─────────┤
├── Issue 4 (SettingsStore)         │
│   ├── Issue 5 ────────────────────┤
│   └── Issue 14 (SettingsScreen) ──┤
└── Issue 15 (Launch Flow) ─────────┤
                                    ├── Issue 13 (TabView Shell)
                                    │   └── Issue 16 (Dark Mode)
                                    │       ├── Issue 17 (VoiceOver)
                                    │       ├── Issue 18 (Error States)
                                    │       ├── Issue 19 (Quick Replies)
                                    │       └── Issue 20 (Haptics)
                                    │           └── Issue 21 (TestFlight)
```

## Summary

| Metric | Value |
|--------|-------|
| Total issues | 21 |
| AFK (autonomous) | 19 |
| HITL (human-in-loop) | 2 (scaffold, TestFlight) |
| Size S | 5 |
| Size M | 9 |
| Size L | 5 |
| Size XL | 2 |
| Max chain depth | 5 |
