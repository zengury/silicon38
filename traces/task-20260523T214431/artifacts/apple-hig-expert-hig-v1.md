# Strategy Canvas iOS — Apple HIG Compliance Guidelines

**Date:** 2026-05-23  
**Platform:** iOS 17+ (iPhone)  
**App Category:** Productivity / Business  
**Status:** Design guidelines for implementation

---

## Bottom Line

🟡 **HIG Readiness: 85/100.** The proposed design aligns well with iOS conventions (Tab Bar, NavigationStack, SF Symbols, standard gestures). Two areas need attention: (1) the 3D SceneKit graph must adapt to device size constraints — small nodes risk becoming untappable below 44pt, and (2) the Settings screen should use iOS Settings bundle or standard form patterns, not a custom modal with Done/Cancel.

---

## 1. Navigation Architecture (HIG §Navigation)

### Chosen Pattern: Tab Bar + NavigationStack

✅ **Correct choice.** The three-tab structure (Chat, Graph, Analysis) maps naturally to a `TabView` with `tabItem` modifiers. Each tab should have its own `NavigationStack` for drill-down navigation.

**Implementation:**

| Element | iOS Pattern | SF Symbol |
|---------|-------------|-----------|
| Chat tab | `TabView` tab | `bubble.left.and.bubble.right` (iOS 17+) |
| Graph tab | `TabView` tab | `point.3.connected.trianglepath.dotted` |
| Analysis tab | `TabView` tab | `chart.bar.doc.horizontal` |

**HIG Reference:** iOS → Navigation → Tab Bars  
**What:** Use standard `TabView` with 3–5 items  
**Why:** Tab bars provide persistent access to top-level destinations. Users expect tabs at the bottom on iPhone.  
**How:** `TabView { ... } .tabItem { Label("Chat", systemImage: "bubble.left") }`

### Settings Access

⚠️ **Deviation detected.** The design proposes a modal sheet with Done/Cancel for Settings. Standard iOS pattern is:
- **Primary:** Settings accessible from a gear icon in the navigation bar (top-right), pushing a settings screen onto the NavigationStack
- **Alternative (if >5 settings):** iOS Settings bundle in system Settings app

**Recommendation:** Use a gear icon (`gearshape`) in the Chat tab's toolbar. Push a `SettingsView` onto the `NavigationStack`. This is a transient configuration screen, but it's better served as a navigation push than a modal — modals are for self-contained tasks.

---

## 2. Layout & Spacing (HIG §Layout)

### Tap Target Minimum: 44×44 points

🔴 **Critical: Node tap targets in 3D graph.** SceneKit nodes rendered at small sizes (weight 1.0 = 3pt radius sphere on web) will be far below the 44pt minimum on mobile. 

**Recommendation:**
- Set minimum visual sphere radius to 12pt on mobile
- Expand the hit-test region around each node to 44×44pt (use `SCNNode` with a transparent `SCNPlane` collision geometry for tapped nodes)
- When two nodes are within 44pt, prioritize the one closer to the camera

### Responsive Layout

✅ The three-tab design naturally adapts to all iPhone sizes (SE to Pro Max). Ensure:
- Chat input bar is at least 44pt tall (touch area) + keyboard avoidance
- Strategy House canvas uses `GeometryReader` to fit available width
- `ScrollView` for content that exceeds screen height

### Safe Areas

✅ Tab bar at bottom respects `safeAreaInsets.bottom`. Ensure:
- Chat input bar accounts for home indicator area on notchless iPhones (SE)
- Graph view extends edge-to-edge for immersion, but controls stay within safe areas

---

## 3. Typography (HIG §Typography)

### Font: San Francisco (system default)

✅ SwiftUI uses SF Pro automatically. Semantic font usage:

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Navigation title | `.largeTitle` | 34pt | Bold |
| Tab titles | `.caption2` | 11pt | Medium |
| Chat message text | `.body` | 17pt | Regular |
| Timestamp / metadata | `.caption` | 12pt | Regular |
| Node labels (graph) | Custom sprite | 14pt | Bold |
| Golden phrases | `.title3` | 20pt | Semibold |
| Strategy House title | Custom (canvas) | 18pt | Bold |
| Buttons | `.body` | 17pt | Semibold |

### Dynamic Type

✅ **Required for HIG compliance.** All text must scale with the user's Dynamic Type preference.

- Use `@ScaledMetric` for custom sizes where needed (graph node label sprites, Strategy House canvas text)
- Wrap scrollable content in `ScrollView` — long text with large Dynamic Type must not be clipped
- Minimum content size should look correct at `xSmall` through `accessibility5`

⚠️ **Canvas-rendered Strategy House:** Core Graphics rendering must respect Dynamic Type. Render text at scaled sizes based on `UIFont.preferredFont(forTextStyle:)`.

---

## 4. Color & Theming (HIG §Color)

### Dark Mode

✅ **Required.** Support both Light and Dark appearance. Use semantic colors:

| Usage | Light | Dark |
|-------|-------|------|
| Background | `systemBackground` | `systemBackground` |
| Chat bubble (user) | `systemBlue` | `systemBlue` |
| Chat bubble (coach) | `systemGray5` | `systemGray6` |
| Text | `label` | `label` |
| Secondary text | `secondaryLabel` | `secondaryLabel` |

### Graph Node Colors

The 14 node-type colors from the web app should be preserved. These are semantic brand colors, not system colors. However:
- Reduce emissive intensity in Dark Mode to avoid eye strain
- Ensure node labels have sufficient contrast against both light and dark backgrounds (use a semi-transparent dark pill background for labels)

### Accent Color

Use `systemBlue` as the accent color for buttons and interactive elements. This is the iOS default and ensures consistency.

---

## 5. Interaction Patterns (HIG §User Interaction)

### Gestures

| Gesture | Action | Context |
|---------|--------|---------|
| Tap | Select node, send message, navigate | Universal |
| Drag (1 finger) | Rotate 3D camera | Graph view |
| Pinch | Zoom 3D camera | Graph view |
| Swipe right (from edge) | Back navigation | NavigationStack |
| Long press | Node detail popover | Graph view |
| Swipe left | Delete project (list) | Project list |

### Haptics

✅ **Recommended for premium feel:**
- `UIImpactFeedbackGenerator(.light)` on node tap in graph
- `UIImpactFeedbackGenerator(.medium)` on successful message send
- `UINotificationFeedbackGenerator(.success)` on Strategy House generation complete

### Keyboard

- Chat input should use `.keyboardType(.default)` with `.submitLabel(.send)`
- Use `.focused` modifier to manage keyboard state
- Dismiss keyboard on scroll in chat view (`.scrollDismissesKeyboard(.interactively)`)

---

## 6. Accessibility (HIG §Accessibility)

### VoiceOver

🔴 **Critical for App Store review.** Every interactive element must have accessibility labels:

| Element | accessibilityLabel | accessibilityHint |
|---------|-------------------|-------------------|
| Chat input | "Message input" | "Type your strategic question, then double-tap to send" |
| Send button | "Send message" | "Sends your message to the AI coach" |
| Graph node | "[Node label], [Node type], confidence [X]%" | "Double-tap to select and fly to this node" |
| Tab: Chat | "Chat, tab 1 of 3" | — |
| Tab: Graph | "Graph, tab 2 of 3" | — |
| Tab: Analysis | "Analysis, tab 3 of 3" | — |
| Generate button | "Generate Strategy House" | "Creates a visual diagram from your strategy conversation" |
| Connection dot | "Connected" or "Disconnected" | — |

### VoiceOver for 3D Graph

The 3D graph is inherently visual. For VoiceOver users:
- Provide an **accessibility rotor action** that reads node descriptions in logical order (by type, then by confidence)
- The node selector list (Analysis tab) should be fully accessible — this is the fallback for VoiceOver users who cannot interact with the 3D graph
- Do NOT mark the graph as inaccessible — provide a text-based exploration mode via the node selector

### Reduce Motion

✅ Required. Honor `UIAccessibility.isReduceMotionEnabled`:
- Disable 3D graph auto-rotation
- Disable camera fly-to animation (snap instead)
- Disable particle effects on edges

### Contrast

✅ All text on standard backgrounds uses system colors which guarantee WCAG AA compliance. Canvas-rendered Strategy House must use sufficient contrast — verify with Accessibility Inspector.

---

## 7. App Review Considerations

### TestFlight Requirements

🔴 **Critical path items for TestFlight distribution:**

1. **Privacy manifest (`PrivacyInfo.xcprivacy`)** — Required for all apps submitted after May 2024. Must declare:
   - No data collection (Strategy Canvas doesn't collect user data)
   - Network usage for API connection
   - No tracking (App Tracking Transparency not needed if no tracking)

2. **App Store Connect metadata:**
   - App name: "Strategy Canvas"
   - Subtitle: "AI Strategic Coaching"
   - Category: Productivity
   - Age rating: 4+ (no objectionable content)
   - Screenshots: iPhone 6.7" and 6.5" (required)

3. **Beta review:** TestFlight builds go through a lighter review than App Store. Key items still enforced:
   - No crashes on launch
   - Privacy manifest present
   - No private API usage

4. **Export compliance:** The app uses encryption (HTTPS/WebSocket). Set `ITSAppUsesNonExemptEncryption` to `NO` in Info.plist (uses only OS-provided encryption).

---

## 8. Implementation Checklist for HIG Compliance

### Before Archive → TestFlight:
- [ ] All tap targets ≥ 44×44pt (use Accessibility Inspector to verify)
- [ ] Dynamic Type works from xSmall to accessibility5
- [ ] Dark Mode renders correctly (no hardcoded colors)
- [ ] VoiceOver labels on all interactive elements
- [ ] Reduce Motion disables animations
- [ ] PrivacyInfo.xcprivacy present
- [ ] ITSAppUsesNonExemptEncryption set
- [ ] Launch screen (storyboard or static) — no black flash
- [ ] No private API usage (verify with `nm` or check)
- [ ] App thinning enabled (bitcode or asset catalogs)

### Nice-to-Have (not blocking TestFlight):
- [ ] Haptic feedback on key interactions
- [ ] Siri shortcut for "Continue my strategy session"
- [ ] Spotlight indexing for project names
- [ ] Handoff support (continue session on Mac/iPad)
- [ ] App Clip for quick demo

---

## 9. Key HIG Decisions

1. **Tab Bar over Sidebar.** iPhone uses Tab Bar at the bottom. Sidebar is an iPad/Mac pattern. No split views on iPhone — each tab is full-width.

2. **Settings as navigation push, not modal.** Standard iOS Settings pattern is a gear icon → push onto NavigationStack. Modals are for tasks with clear completion/ cancellation (camera, compose, authentication).

3. **SceneKit over ARKit.** 3D graph visualization is better served by SceneKit (full control, no world-tracking overhead) than ARKit. AR would add complexity with no user benefit for a graph viewer.

4. **Core Graphics over PDFKit for Strategy House.** Canvas rendering provides pixel-perfect control matching the web output. PDF generation could be added later as a non-bitmap export option.

5. **No custom navigation gestures.** Use system-provided swipe-back. Do not implement custom edge gestures that conflict with NavigationStack behavior.
