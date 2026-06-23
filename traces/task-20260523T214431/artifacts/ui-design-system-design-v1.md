# Strategy Canvas iOS — Design System Specification

**Source:** UX spec + Apple HIG guidelines + existing web design language  
**Status:** Constrains `senior-frontend` and `epic-design`

---

## 1. Design Token Architecture

### Color Tokens

#### Semantic Colors (iOS system — dynamic Light/Dark)

```json
{
  "colors": {
    "background": {
      "primary": { "light": "systemBackground", "dark": "systemBackground" },
      "secondary": { "light": "systemGray6", "dark": "systemGray6" },
      "tertiary": { "light": "systemGray5", "dark": "systemGray5" }
    },
    "text": {
      "primary": { "light": "label", "dark": "label" },
      "secondary": { "light": "secondaryLabel", "dark": "secondaryLabel" },
      "tertiary": { "light": "tertiaryLabel", "dark": "tertiaryLabel" },
      "inverse": { "light": "white", "dark": "white" }
    },
    "accent": {
      "primary": { "light": "systemBlue", "dark": "systemBlue" },
      "success": { "light": "systemGreen", "dark": "systemGreen" },
      "warning": { "light": "systemOrange", "dark": "systemOrange" },
      "error": { "light": "systemRed", "dark": "systemRed" }
    },
    "separator": { "light": "separator", "dark": "separator" }
  }
}
```

#### Brand Colors — Node Types (14 types, fixed across platforms)

```json
{
  "nodeColors": {
    "goal":        "#FFD700",
    "position":    "#4A90D9",
    "option":      "#50C878",
    "mechanism":   "#7E57C2",
    "resource":    "#9B59B6",
    "constraint":  "#E74C3C",
    "evidence":    "#26A69A",
    "tension":     "#FF6B35",
    "assumption":  "#F39C12",
    "risk":        "#C0392B",
    "signal":      "#00BCD4",
    "action":      "#66BB6A",
    "pattern":     "#EC407A",
    "stakeholder":"#8D6E63"
  }
}
```

**Emissive intensity (SceneKit):** `confidence × 0.55` in Light Mode, `confidence × 0.40` in Dark Mode (reduced to avoid eye strain).

---

### Typography Tokens

```json
{
  "typography": {
    "display": {
      "largeTitle": { "size": 34, "weight": "bold", "style": ".largeTitle" },
      "title1":     { "size": 28, "weight": "regular", "style": ".title" }
    },
    "heading": {
      "title2":     { "size": 22, "weight": "regular", "style": ".title2" },
      "title3":     { "size": 20, "weight": "semibold", "style": ".title3" }
    },
    "body": {
      "body":       { "size": 17, "weight": "regular", "style": ".body" },
      "callout":    { "size": 16, "weight": "regular", "style": ".callout" },
      "subhead":    { "size": 15, "weight": "regular", "style": ".subheadline" },
      "footnote":   { "size": 13, "weight": "regular", "style": ".footnote" }
    },
    "caption": {
      "caption1":   { "size": 12, "weight": "regular", "style": ".caption" },
      "caption2":   { "size": 11, "weight": "medium", "style": ".caption2" }
    },
    "custom": {
      "goldenPhrase": { "size": 20, "weight": "semibold", "style": ".title3", "italic": true },
      "nodeLabel":    { "size": 14, "weight": "bold", "style": ".caption", "scaledMetric": true },
      "houseTitle":   { "size": 18, "weight": "bold", "style": ".title3" },
      "stageBadge":   { "size": 14, "weight": "medium", "style": ".subheadline" }
    }
  }
}
```

All text uses SF Pro (system default). No custom fonts needed. All sizes use Dynamic Type via `Font.system(_:design:)` with text styles for automatic scaling.

---

### Spacing Tokens (8pt grid)

```json
{
  "spacing": {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "xxl": 24,
    "xxxl": 32,
    "section": 40
  }
}
```

**Additional rules:**
- Screen horizontal margins: 16pt (`spacing.lg`)
- Card internal padding: 12pt (`spacing.md`)
- Chat bubble padding: 12pt horizontal, 8pt vertical
- Tab bar: system default
- Minimum tap target: 44×44pt (override with `.frame(minWidth: 44, minHeight: 44)`)

---

### Corner Radius Tokens

```json
{
  "radius": {
    "sm": 6,
    "md": 10,
    "lg": 16,
    "pill": 9999,
    "chatBubble": 12
  }
}
```

---

### Motion Tokens

```json
{
  "motion": {
    "duration": {
      "instant": 0.1,
      "fast": 0.2,
      "normal": 0.3,
      "slow": 0.5,
      "flyTo": 1.0
    },
    "easing": {
      "default": "easeInOut",
      "spring": { "response": 0.35, "dampingFraction": 0.7 }
    }
  }
}
```

**Respect Reduced Motion:** When `UIAccessibility.isReduceMotionEnabled`:
- Disable graph auto-rotation and camera fly-to animations
- Replace animated transitions with crossfade (0.1s)
- Springs → instantaneous .snappy

---

## 2. Component Specifications

### Component 1: ChatBubble

| State | Visual | Behavior |
|-------|--------|----------|
| Default (user) | Blue fill (`systemBlue`), white text, right-aligned, radius 12pt, max width 75% | — |
| Default (coach) | Gray fill (`systemGray5`), label text, left-aligned, radius 12pt, max width 75% | — |
| Loading/Thinking | 3 animated dots (`.spring` bounce), gray fill, left-aligned | Animates while waiting for response |
| Error | Red border (`systemRed`), gray fill, retry button (blue link text) | Tap "Retry" resends last message |
| Accessibility | Label: "{Speaker}: {message text}" | VoiceOver reads speaker + content |

**Implementation pattern (SwiftUI):**
```
ChatBubble(speaker: .user, text: message, status: .sent)
ChatBubble(speaker: .coach, text: message, status: .received)
ChatBubble(speaker: .coach, text: nil, status: .thinking)
ChatBubble(speaker: .coach, text: message, status: .error(retryAction))
```

---

### Component 2: GraphNode (SceneKit)

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Sphere radius = `max(0.6, min(1.5, weight × 0.6))`, colored per node type, emissive at `confidence × 0.55` | Orbits in force layout |
| Selected | Sphere scale 1.3×, outer glow ring (emission intensity +0.3), label fully visible | Camera flies to node |
| Hover (not used on iOS) | N/A | — |
| Disabled (invalidated) | Reduced opacity 0.3, desaturated color | Still visible, not interactive |
| Accessibility | Label: "[label], [node_type], confidence [X]%" | Via rotor or node selector list |

**Hit region:** Transparent `SCNPlane` (44×44pt projected size) placed at node position, billboarded. The visual sphere can be smaller (12pt min radius) but the hit plane always respects 44pt minimum.

---

### Component 3: ConfidenceBar

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Horizontal bar: gray track (`.systemGray5`), colored fill (blue→green gradient), percentage label | Fill animates with `.spring` on change |
| Low (<30%) | Red fill | Warning indicator |
| Medium (30-70%) | Orange fill | Progress indicator |
| High (>70%) | Green fill | Confidence indicator |

---

### Component 4: StageBadge

| Stage | Label | Color |
|-------|-------|-------|
| explore | "Explore / 探索" | `systemBlue` |
| converge | "Converge / 收敛" | `systemTeal` |
| stress_test | "Stress Test / 压力测试" | `systemOrange` |
| commit | "Commit / 决策" | `systemGreen` |
| review | "Review / 回顾" | `systemPurple` |

Rounded pill shape (`.capsule`), 6pt horizontal padding, `.subheadline` font, white text on colored background.

---

### Component 5: GoldenPhrase

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Italic `.title3`, left border accent (gold: `#FFD700`), 12pt padding | Static display |
| Accessibility | Reads as "Golden phrase: [text]" | — |

---

### Component 6: StrategyHouseCanvas

| State | Visual | Behavior |
|-------|--------|----------|
| Empty | Placeholder icon (🏛️) + "Complete your conversation, then generate" + node count | Button disabled if nodes count = 0 |
| Generating | Progress spinner + "Generating..." | Button disabled, async Core Graphics render |
| Generated | Scrollable PNG, download + share buttons | PNG at @3x device resolution |
| Error | Error icon + "Generation failed" + Retry button | — |

---

### Component 7: ConnectionIndicator

| State | Visual | Behavior |
|-------|--------|----------|
| Connected | Green dot (`.systemGreen`), pulse animation on reconnection | — |
| Connecting | Yellow dot, spinning | During WebSocket handshake |
| Disconnected | Red dot (`.systemRed`) | — |
| Error | Red dot + "Tap to retry" | Tapping opens settings |

Located in status bar area (top of Chat tab) and Settings screen.

---

### Component 8: ProjectCard (in Sidebar)

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Row: project name, node count, date | Tap to select |
| Active | Highlighted background (`.systemBlue.opacity(0.1)`), blue left border | Currently active |
| Editing | TextField replaces name, auto-focus | Blur or Enter commits rename |
| Deleting | Swipe-to-delete with confirmation | "Delete Project?" alert |

---

## 3. Interaction State Matrix

| Component | Default | Tap | Long Press | Swipe | Animation |
|-----------|---------|-----|------------|-------|-----------|
| ChatBubble | Static | n/a | Copy text | n/a | Appear: slide up + fade |
| GraphNode | Orbiting | Select + fly-to | n/a | n/a | Fly-to: 1s easeInOut |
| SendButton | Enabled | Send + haptic | n/a | n/a | Scale 0.9 then spring back |
| GenerateBtn | Enabled | Generate + haptic success | n/a | n/a | Progress spinner → fade in PNG |
| ConfidenceBar | Colored fill | n/a | n/a | n/a | Fill: 0.3s spring on change |
| TabItem | SF Symbol | Switch tab | n/a | n/a | Crossfade (0.15s) |
| ProjectCard | Tap to select | Select + switch | n/a | Delete | Slide to delete |
| ConnectionDot | State color | n/a | n/a | n/a | Pulse on reconnect |

---

## 4. Accessibility Requirements Matrix

| Element | `.accessibilityLabel` | `.accessibilityHint` | `.accessibilityTraits` |
|---------|----------------------|---------------------|----------------------|
| Chat input | "Message input" | "Type your question, then double-tap to send" | `.searchField` |
| Send button | "Send message" | "Sends your message to the AI coach" | `.button` |
| Graph node | "[label], [type], confidence [X]%" | "Double-tap to select and fly to this node" | `.button` |
| Tab: Chat | "Chat, tab 1 of 3" | — | `.tab` |
| Tab: Graph | "Graph, tab 2 of 3" | — | `.tab` |
| Tab: Analysis | "Analysis, tab 3 of 3" | — | `.tab` |
| Generate button | "Generate Strategy House" | "Creates a visual diagram" | `.button` |
| Connection dot | "Connected" / "Disconnected" | — | `.image` |
| Golden phrase | "Golden phrase" | "[reads text]" | `.staticText` |
| Confidence bar | "Confidence [X] percent" | — | `.staticText` |
| Stage badge | "[Stage name]" | — | `.staticText` |

---

## 5. Cross-Platform Consistency Notes

The iOS design system inherits from the web app's visual language but adapts to iOS conventions:
- **Preserved:** Node color palette (14 types), Strategy House layout algorithm, golden phrase styling, bilingual labels (En/Zh), stage naming
- **Adapted:** Navigation (Tab Bar vs side-by-side panels), typography (SF Pro vs system fonts), spacing (iOS native vs CSS), interaction gestures (touch vs mouse)
- **New:** Haptic feedback, Safe Area handling, Dynamic Type, VoiceOver, Keychain storage

---

## 6. Iconography

All icons use SF Symbols (iOS 17+):

| Context | Symbol Name | Usage |
|---------|-------------|-------|
| Chat tab | `bubble.left.and.bubble.right` | Tab bar item |
| Graph tab | `point.3.connected.trianglepath.dotted` | Tab bar item |
| Analysis tab | `chart.bar.doc.horizontal` | Tab bar item |
| Projects | `folder` | Toolbar button |
| Settings | `gearshape` | Toolbar button |
| Send | `arrow.up.circle.fill` | Chat send button |
| Share | `square.and.arrow.up` | Strategy House share |
| Generate | `wand.and.stars` | Generate Strategy House |
| Download | `arrow.down.circle` | Download PNG |
| Add | `plus` | New project |
| Delete | `trash` | Delete project |
| Connection | `circle.fill` (green/red) | Status indicator |
| Thinking | `ellipsis` (animated) | AI thinking state |
| Retry | `arrow.clockwise` | Error retry |
| Microphone | `mic` | Dictation |
| Dark Mode | `moon` / `sun.max` | Theme toggle |
