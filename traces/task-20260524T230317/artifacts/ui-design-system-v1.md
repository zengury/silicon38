# Design System Spec — HR Assistant

## Design Philosophy: Louis Kahn's "Three Rooms" Applied to Software

> *"Light is data. How it must reach the person defines the structure."* — Kimbell

### Kimbell Principle → Information Architecture
Messages arrive at the reader as light arrives at art: even, never as glare. The assistant's response is the artwork. Everything else — sidebar, header, right panel — is the reflector, the slit, the ceiling that shapes arrival. Structure must serve how information reaches the person.

**Design rule:** Every UI element must answer: "Does this make the response clearer to read, or does it merely occupy space?" If the latter, remove it.

### Esherick Principle → Module Depth
Interfaces face two ways: outward to the world (API, data), inward to the person (reading experience). The depth of each component is where these two are reconciled, out of sight.

**Design rule:** The person sees clean surface. Complexity (API calls, state management, RAG logic) lives behind seams. Never expose implementation to the user.

### Salk Principle → Subtraction of Chrome
The empty state is the Salk plaza: a vast, serene emptiness that tells the person "this matters." One line of water (a single prompt), the ocean beyond (the assistant's potential).

**Design rule:** Empty state shows ONLY the question input. No sidebar. No header. No tabs. The question is the act. Everything else is secondary.

---

## Design Tokens

### Color System — "Silken Stone" Palette

```yaml
colors:
  # Primary — Indigo family, the "architect's signature"
  primary:
    50:  "#eef2ff"   # background tint
    100: "#e0e7ff"   # selected state bg
    200: "#c7d2fe"   # hover border
    300: "#a5b4fc"   # focus ring
    400: "#818cf8"   # secondary accent
    500: "#6366f1"   # primary action, brand
    600: "#4f46e5"   # hover state
    700: "#4338ca"   # text on light bg
    800: "#3730a3"   # dark mode accent
    900: "#312e81"   # dark mode bg tint

  # Neutral — The "concrete" palette
  neutral:
    50:  "#f8fafc"   # page background
    100: "#f1f5f9"   # card hover
    200: "#e2e8f0"   # border
    300: "#cbd5e1"   # muted text
    400: "#94a3b8"   # placeholder
    500: "#64748b"   # secondary text
    600: "#475569"   # dark mode text
    700: "#334155"   # dark mode card
    800: "#1e293b"   # dark mode surface
    900: "#0f172a"   # dark mode background

  # Semantic
  success: "#22c55e"  # connection dot
  error:   "#ef4444"  # error states
  warning: "#f59e0b"  # medium priority

  # Message bubbles
  user_bubble_bg:    "{primary.500}"
  user_bubble_text:  "#ffffff"
  ai_bubble_bg:      "{neutral.50}"    # light mode
  ai_bubble_bg_dark: "{neutral.800}"   # dark mode
  ai_bubble_border:  "{neutral.200}"
```

### Typography — "Quiet Reading" Scale

```yaml
typography:
  font_family:
    base: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    mono: "'SF Mono', 'Fira Code', 'JetBrains Mono', monospace"

  scale:
    xs:    "0.70rem"   # timestamps, meta
    sm:    "0.82rem"   # sidebar items, skill cards
    base:  "0.92rem"   # body text, message content
    lg:    "1.05rem"   # message headings
    xl:    "1.25rem"   # empty state heading
    2xl:   "1.50rem"   # (reserved — not used to keep quiet presence)

  weight:
    normal: 400
    medium: 500
    semibold: 600

  line_height:
    tight:   1.3    # headings
    relaxed: 1.65   # message body
    loose:   1.75   # long-form reading
```

### Spacing — "Breathing Room" Scale

```yaml
spacing:
  xs:  "0.25rem"  # icon gaps
  sm:  "0.50rem"  # inline gaps
  md:  "0.75rem"  # card padding
  lg:  "1.00rem"  # section gaps
  xl:  "1.50rem"  # message gaps
  2xl: "2.00rem"  # empty state margins
  3xl: "3.00rem"  # page padding
```

### Border Radius — "Soft Architecture"

```yaml
radius:
  sm:   "0.375rem"  # checkboxes, badges
  md:   "0.625rem"  # cards, input fields
  lg:   "0.875rem"  # message bubbles
  xl:   "1.125rem"  # panels, large containers
  full: "9999px"    # avatars, pills
```

### Shadows — "Depth Without Drama"

```yaml
shadows:
  sm:  "0 1px 2px rgba(0,0,0,0.04)"
  md:  "0 2px 4px rgba(0,0,0,0.06)"
  lg:  "0 4px 12px rgba(0,0,0,0.08)"
  # Note: No heavy shadows. Kahn's light is even, not dramatic.
```

### Motion — "Gravity, Not Theatre"

```yaml
motion:
  duration:
    instant: 100ms   # hover color changes
    quick:   200ms   # panel open/close
    natural: 300ms   # sidebar slide
    slow:    500ms   # message appear (subtle, barely perceptible)

  easing:
    default: "cubic-bezier(0.4, 0, 0.2, 1)"   # standard ease-out
    decelerate: "cubic-bezier(0, 0, 0.2, 1)"   # enter
    accelerate: "cubic-bezier(0.4, 0, 1, 1)"   # exit
```

---

## Component Specifications

### EmptyState (Salk Plaza)
```
Purpose: First impression — the question is the act
States: default
Layout: Centered, vertically and horizontally
Content:
  - Large wave emoji (👋) — warm but minimal
  - Heading: "管理问题，我来帮你想" (Managerial questions, I'll help you think)
  - Subtitle: One line — quiet, no marketing
  - Quick questions: 4 pill buttons, arranged horizontally, wrapping
  - No sidebar, no header, no panel visible

Accessibility: Focus ring on quick questions, aria-label on emoji
```

### ChatInput (The Threshold)
```
Purpose: Where voice meets the assistant — the most important seam
States: default, focused, disabled (loading), empty (send disabled)
Layout: Bottom-anchored, max-w-3xl centered
Content:
  - Textarea: auto-resize, min 1 row, max 6 rows
  - Send button: right-aligned, icon only (Send icon)
  - Footer: single line disclaimer text

Behavior:
  - Enter sends / Shift+Enter newline
  - Focus ring: primary.300 with 2px offset
  - Disabled: opacity-40, cursor-not-allowed
  - Auto-scrolls messages up on expand

Accessibility:
  - aria-label: "输入管理问题"
  - Send button: aria-label "发送消息"
  - Keyboard: Enter sends (announced by aria-live region)
```

### ChatMessage (The Artwork)
```
Purpose: The response is the art — nothing competes with it
States: user-message, ai-message, ai-loading (typing indicator)
Layout: Row with avatar + bubble, max-w-[75%]
  - User: Right-aligned, primary color
  - AI: Left-aligned, card with subtle border

AI Bubble:
  - Background: white (light) / neutral.800 (dark)
  - Border: neutral.200 (light) / neutral.700 (dark)
  - Padding: lg (1rem) horizontal, md (0.75rem) vertical
  - Border-radius: lg, with bottom-left at sm (speech tail)
  - Shadow: sm — barely there

Markdown rendering:
  - h3: primary color, medium weight
  - code: monospace, neutral background pill
  - pre: padded block with overflow-x auto
  - ul/ol: proper indent, spacing between items

Timestamps: xs size, neutral.400 color, 4px below bubble

Accessibility:
  - role="article" on AI messages
  - aria-label distinguishing user vs assistant
```

### Sidebar (The Reflector)
```
Purpose: Navigation — always visible but never loud
States: open (mobile overlay), closed (mobile), persistent (desktop)
Layout: Fixed left, 280px wide, full height
Content:
  - Brand: gradient text, HOM subtitle
  - New Chat button: full width, primary color, always visible
  - Chat list: scrollable, each item shows title + delete (on hover)
  - Footer: skills count + Grove credit

Behavior:
  - Mobile: overlay with backdrop blur, closes on select
  - Desktop: persistent, never collapsible
  - Active chat: primary.50 bg, primary.700 text, medium weight
  - Delete button: hidden by default, appears on row hover

Accessibility:
  - nav element with aria-label "对话历史"
  - Chat items: role="button", aria-current when active
  - New Chat: aria-label "开始新对话"
```

### RightPanel (The Organizer)
```
Purpose: Reference — skills used + action items
States: skills-tab, todos-tab, hidden
Layout: Right side, 280px wide, only visible when content exists

Skills tab:
  - Card per skill: name (medium), category (small, primary color), description (2-line clamp)
  - Empty: "对话后将显示相关管理技能"

Todos tab:
  - Checkbox items with strikethrough on check
  - Priority badge: high (red), medium (amber), low (green)
  - Timeframe text: small, neutral color
  - Empty: "对话后将生成行动建议"

Behavior:
  - Tab toggle: pill-style buttons
  - Todo check: smooth strikethrough animation (200ms)
  - Empty state: neutral text, no icon

Accessibility:
  - role="complementary"
  - Tabs: role="tablist", aria-selected
  - Todos: role="checkbox", aria-checked
```

### Header (The Slit)
```
Purpose: Minimal presence — status only
States: default
Layout: Horizontal bar, full width
Content:
  - Left: Connection dot (green pulsing) + "智能 HR 顾问"
  - Right: Theme toggle (sun/moon icon)

Behavior:
  - Mobile: Menu button added to left (hamburger → X)
  - Theme toggle: instant transition (100ms), no animation

Accessibility:
  - Theme toggle: aria-label "切换深色模式" / "切换浅色模式"
```

### TypingIndicator
```
Purpose: Signal that the assistant is composing
States: active
Layout: Same as AI message layout (avatar + bubble)
Animation: 3 dots, staggered bounce, primary color at 40% opacity

Accessibility:
  - aria-label "AI 正在回复..."
  - aria-live="polite"
```

---

## Design Token Output (Tailwind Config)

```javascript
// tailwind.config.js extension
{
  theme: {
    extend: {
      colors: {
        primary: { /* indigo scale as above */ },
        neutral: { /* slate scale as above */ },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["'SF Mono'", "'Fira Code'", "'JetBrains Mono'", "monospace"],
      },
      fontSize: {
        'xs': ['0.70rem', { lineHeight: '1.4' }],
        'sm': ['0.82rem', { lineHeight: '1.5' }],
        'base': ['0.92rem', { lineHeight: '1.65' }],
        'lg': ['1.05rem', { lineHeight: '1.5' }],
        'xl': ['1.25rem', { lineHeight: '1.4' }],
      },
      borderRadius: {
        'bubble': '0.875rem',
        'card': '0.625rem',
        'panel': '1.125rem',
      },
      boxShadow: {
        'surface': '0 1px 2px rgba(0,0,0,0.04)',
        'card': '0 2px 4px rgba(0,0,0,0.06)',
        'elevated': '0 4px 12px rgba(0,0,0,0.08)',
      },
      transitionDuration: {
        'quick': '100ms',
        'natural': '200ms',
        'slide': '300ms',
      },
    },
  },
}
```

---

## Accessibility Checklist

- [x] All interactive elements have focus rings (primary.300, 2px offset)
- [x] Color contrast: primary.500 on white = 4.62:1 (passes AA for text > 18px)
- [x] All emoji have aria-labels
- [x] Tab panels use role="tablist" pattern
- [x] Messages use role="article" or role="log"
- [x] Theme respects prefers-color-scheme and allows manual override
- [x] Typing indicator has aria-live="polite"
- [x] No content disappears on 200% zoom
- [x] Touch targets minimum 44x44px (send button: 40px → adjust to 44px)
