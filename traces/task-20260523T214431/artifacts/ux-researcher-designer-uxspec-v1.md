# Strategy Canvas iOS — UX Research Synthesis & Design Specification

**Date:** 2026-05-23  
**Status:** Design Specification for Implementation

---

## User Personas

### Persona 1: Alex the Strategy Practitioner

**Archetype:** Power User  
**Quote:** "I think about strategy between meetings. I need it in my pocket."

**Demographics:**
- Age: 28–45
- Role: Startup founder, consultant, or product lead
- Tech proficiency: High
- Primary device: iPhone (daily) + MacBook

**Goals:**
- Continue strategic sessions started on desktop while mobile
- Capture strategic insights during walks or commutes
- Share Strategy House diagrams in presentations and board meetings
- Track multiple strategic decisions across projects

**Frustrations:**
- Can't access the tool when away from desk
- Web version is unusable on iPhone (pinch-zoom, 3D graph crashes)
- Strategic ideas evaporate when not captured quickly

**Design Implications:**
→ Optimize for quick session resumption (last project loads instantly)
→ Prioritize chat input with minimal friction
→ Graph viewing must be fluid on mobile GPU
→ Export to Photos/Share Sheet is essential for presentations

---

### Persona 2: Jordan the Decision Explorer

**Archetype:** Consumer User  
**Quote:** "I have a big life decision. I want to talk it through."

**Demographics:**
- Age: 22–60
- Role: Individual facing a major decision (career change, relocation, investment)
- Tech proficiency: Moderate
- Primary device: iPhone only

**Goals:**
- Work through a single strategic decision with AI coaching
- Understand the process without reading documentation
- See a clear visual output (diagram) that makes sense

**Frustrations:**
- Overwhelmed by too many panels or options
- Doesn't know where to start
- Wants the app to feel like talking to a wise friend, not a corporate tool

**Design Implications:**
→ Default onboarding: open to chat immediately, no settings required (use preconfigured backend)
→ Progressive disclosure: only show advanced features (project management, multi-project) when needed
→ The first experience must work with zero configuration (demo mode or default backend)

---

### Persona 3: Taylor the Team Lead

**Archetype:** Business User  
**Quote:** "I need our team's strategy visualized before the board meeting."

**Demographics:**
- Age: 30–50
- Role: Team lead, director, VP
- Tech proficiency: Moderate
- Primary device: iPhone + iPad

**Goals:**
- Generate polished strategy diagrams for stakeholder presentations
- Run strategic sessions with team inputs (typed in chat)
- Export Strategy House as a shareable image

**Frustrations:**
- Can't get a clean PNG export from the web on mobile
- Wants to annotate or highlight specific nodes
- Needs the output to look "consulting-firm grade"

**Design Implications:**
→ Strategy House export is a first-class feature, not an afterthought
→ High-resolution PNG with proper typography
→ Share Sheet integration (Save to Photos, AirDrop, Messages, Email)

---

## Journey Map: First-Time User to Strategy House Export

```
STAGE 1: DISCOVERY                  STAGE 2: ONBOARDING              STAGE 3: FIRST CONVERSATION
─────────────────────────────────   ─────────────────────────────   ──────────────────────────────
ACTIONS:                            ACTIONS:                         ACTIONS:
• Install via TestFlight link       • Tap app icon                  • Type: "I'm considering..."
• Wait for install                  • See config screen             • Read AI coach response
                                    • Enter backend URL + API key   • Continue dialogue
                                    • Tap "Connect"                 • See graph nodes appear
                                                                    
TOUCHPOINTS:                        TOUCHPOINTS:                    TOUCHPOINTS:
• TestFlight app                    • Settings screen               • Chat input (keyboard)
• App Store Connect email           • Connection status indicator   • Chat bubbles
                                                                    • Graph badge (node count)
                                                                    
EMOTIONS: 😊 Excited                EMOTIONS: 😤 Slight friction    EMOTIONS: 🤯 Delighted
─────────────────────────────────   ─────────────────────────────   ──────────────────────────────
PAIN POINTS:                        PAIN POINTS:                    PAIN POINTS:
• Finding the TestFlight link       • "Where's my API key?"        • Typing on mobile keyboard
• Waiting for review approval       • Typing long URL on phone     • Waiting for AI response
                                                                    
OPPORTUNITIES:                      OPPORTUNITIES:                  OPPORTUNITIES:
• Clear install instructions        • Paste from clipboard detect   • Quick-reply suggestions
• Public TestFlight link            • Default backend option        • Voice input (dictation)


STAGE 4: GRAPH EXPLORATION          STAGE 5: STRATEGY HOUSE          STAGE 6: SHARING
─────────────────────────────────   ─────────────────────────────   ──────────────────────────────
ACTIONS:                            ACTIONS:                         ACTIONS:
• Swipe to Graph tab               • Tap "Generate Strategy House" • Tap Share button
• Pinch-zoom, orbit camera          • Review diagram                • Select destination
• Tap a node to fly to it           • Read golden phrases           • Send to team/stakeholder
• Rotate, explore relationships     • Read named concepts
                                                                    
TOUCHPOINTS:                        TOUCHPOINTS:                    TOUCHPOINTS:
• 3D SceneKit view                  • ScrollView with canvas        • iOS Share Sheet
• Node tap gesture                  • Generate button               • Export confirmation
• Camera controls (gestures)        • Download button
                                                                    
EMOTIONS: 😎 Satisfied              EMOTIONS: 🎉 Proud               EMOTIONS: 💪 Empowered
─────────────────────────────────   ─────────────────────────────   ──────────────────────────────
PAIN POINTS:                        PAIN POINTS:                    PAIN POINTS:
• Small nodes hard to tap           • Rendering time on old phones  • Export quality expectations
• 3D navigation learning curve     • Scroll gesture conflicts      • Large PNG file size
                                                                    
OPPORTUNITIES:                      OPPORTUNITIES:                  OPPORTUNITIES:
• Haptic feedback on tap            • Progress indicator             • Compression options
• Double-tap to zoom to fit         • Background rendering           • Share as PDF option
• Legend overlay tap-to-filter      • Auto-generate on milestone    • Copy golden phrase to clipboard
```

---

## Interaction Design: Screen Architecture

### Screen 1: Chat (Primary Tab)
```
┌─────────────────────────┐
│ ← Projects   Strategy Canvas │  ← Navigation bar
├─────────────────────────┤
│                         │
│  ┌──────────────────┐   │
│  │ Coach: I hear    │   │  ← Chat bubble (left-aligned)
│  │ you're facing... │   │
│  └──────────────────┘   │
│                         │
│       ┌──────────────────┐
│       │ User: I'm       │  ← Chat bubble (right-aligned)
│       │ considering...  │
│       └──────────────────┘
│                         │
│  ... (scrollable)       │
│                         │
│  ○ ○ ○  (thinking)      │  ← Thinking indicator
│                         │
├─────────────────────────┤
│ [Type your message...]  │  ← Input bar, fixed at bottom
│              [Send]     │     Above keyboard when active
└─────────────────────────┘
│  Chat  │ Graph │ Analysis │  ← Tab Bar (SF Symbols)
```

### Screen 2: Graph (Secondary Tab)
```
┌─────────────────────────┐
│ ← Chat    Graph    Nodes: 12 │
├─────────────────────────┤
│                         │
│     [3D SceneKit]       │  ← Full-height SceneKit view
│     • • • • •          │     Orbit camera (drag = rotate)
│       •   •            │     Pinch = zoom
│         •  •           │     Single tap node = fly-to + select
│      •     •           │
│    •  • •  •           │
│                         │
├─────────────────────────┤
│ ● Goal ●Option ●Risk...│  ← Horizontal scroll legend
│ 3     5       2         │     Tap to filter/highlight
└─────────────────────────┘
│  Chat  │ Graph │ Analysis │
```

### Screen 3: Analysis (Third Tab)
```
┌─────────────────────────┐
│ ← Graph   Analysis       │
├─────────────────────────┤
│ Stage: Converge / 收敛   │
│ Confidence: ████████ 72% │
│                         │
│ Golden Phrases          │
│ ┌─────────────────────┐ │
│ │ "先验证，后投入..."  │ │
│ └─────────────────────┘ │
│                         │
│ Named Concepts          │
│ [假设缺口] [轻量验证]    │
│                         │
│ ┌─────────────────────┐ │
│ │                     │ │
│ │  [Generate          │ │
│ │   Strategy House]   │ │  ← CTA button (prominent)
│ │                     │ │
│ └─────────────────────┘ │
│                         │
│ [Strategy House Preview]│  ← Once generated, shows scrollable PNG
│ [Share] [Regenerate]    │
└─────────────────────────┘
│  Chat  │ Graph │ Analysis │
```

### Screen 4: Settings (Modal)
```
┌─────────────────────────┐
│ Cancel    Settings   Done │
├─────────────────────────┤
│ Backend URL             │
│ ┌─────────────────────┐ │
│ │ https://strategy... │ │  ← Text field with paste detection
│ └─────────────────────┘ │
│                         │
│ API Key                 │
│ ┌─────────────────────┐ │
│ │ sk-•••••••••••••••• │ │  ← Secure field with reveal toggle
│ └─────────────────────┘ │
│                         │
│ Model                   │
│ ○ DeepSeek Chat         │  ← Picker
│ ○ DeepSeek Reasoner     │
│                         │
│ [Test Connection]       │  ← Validates URL + API key
│                         │
│ Connection: 🟢 Online   │
│                         │
│ ─────────────────────   │
│ App Version: 1.0 (42)   │
└─────────────────────────┘
```

---

## Edge Cases & Error States

| Scenario | Behavior |
|----------|----------|
| No internet on launch | Show cached data, disable chat, show "Offline — connect to continue" banner |
| Connection drops mid-conversation | Show "Reconnecting..." indicator, queue last message for retry |
| Backend returns error | Show error bubble in chat: "The coach is having trouble. Tap to retry." |
| Invalid API key | Settings shows ❌ error state, Test Connection fails with descriptive message |
| Empty graph (no nodes yet) | Graph tab shows placeholder: "Start a conversation to build your strategy graph" |
| Very large graph (50+ nodes) | SceneKit level-of-detail: distant nodes become small dots, labels hidden below certain zoom |
| Strategy House generation fails | Show error toast, regenerate button remains available |
| First launch (no projects) | Create default "My Strategy" project, open chat immediately |
| Keyboard covers input | Input bar rises with keyboard (iOS standard behavior) |
| Copy/paste URL with trailing slash | Auto-trim trailing slash from backend URL |
| Rapid message sending | Disable Send button while waiting for response, queue messages |

---

## Usability Heuristics Assessment

| Heuristic | Status | Notes |
|-----------|--------|-------|
| Visibility of system status | ✅ | Connection indicator, thinking dots, stage badge, confidence bar |
| Match between system and real world | ✅ | "Chat" tab mirrors messaging apps, "Strategy House" = familiar consulting metaphor |
| User control and freedom | ✅ | Cancel settings, back navigation, swipe between tabs |
| Consistency and standards | ✅ | Tab Bar (standard iOS), NavigationStack, SF Symbols, standard gestures |
| Error prevention | ✅ | Disable send during thinking, trim URLs, validate API key format |
| Recognition rather than recall | ✅ | Legend shows node types/colors inline, tabs are self-describing |
| Flexibility and efficiency | ✅ | Quick-reply suggestions, dictation support, tab bar shortcuts |
| Aesthetic and minimalist design | ✅ | 3-tab structure vs 5-panel desktop — reduced for mobile focus |
| Help users recognize and recover | ✅ | Error messages are actionable, retry buttons available |
| Help and documentation | ⚠️ | No in-app help yet — acceptable for TestFlight beta with known user base |

---

## Key UX Decisions

1. **3 tabs, not 5 panels.** Mobile screens are too narrow for side-by-side panels. Chat is the primary interaction; Graph and Analysis are secondary views accessed via tabs. The project sidebar becomes a sheet overlay when needed (less frequent interaction).

2. **Settings first-run, not every launch.** After initial configuration, the app remembers backend URL and API key. Only show settings when connection fails or user explicitly navigates there.

3. **Chat-first onboarding.** When a new project is created, open directly to the chat tab. The graph and analysis tabs show placeholder content until the first conversation generates nodes.

4. **SceneKit over WebView.** A WebView wrapping the web app would be lazy but produces poor mobile UX (scaling issues, broken gestures, no haptics). Native SceneKit rendering of the 3D graph provides proper iOS interaction patterns.

5. **No AI on device.** The backend handles all LLM processing. The client is a presenter, not a processor. This is a deliberate scope decision for v1, consistent with the existing web/desktop architecture.

---

## Open Questions

1. **Default backend for new users?** Should the app ship with a preconfigured public backend URL for demo/onboarding, or require configuration from the start?
2. **TestFlight group size?** Private (25 testers) or public link (up to 10,000)?
3. **App Store Connect team access?** Who has the Apple Developer account with the `com.strategiccanvas.ios` bundle ID?
