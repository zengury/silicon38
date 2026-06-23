# Design System: 机器人车队运维监控面板 (Robot Fleet Ops Dashboard)

> Source: UX Design Spec (3 personas, 3 journey maps) · Dark-optimized fleet monitoring context
> Target: Web (React SPA) · WCAG AA minimum · Dark-first design

---

## 1. Design Tokens

### 1.1 Color Palette — Dark Mode (Default)

```css
:root {
  /* ── Surface ── */
  --color-surface-0: #0a0e14;       /* deepest bg (sidebar, modal backdrop) */
  --color-surface-1: #111820;       /* main content bg */
  --color-surface-2: #182230;       /* card, panel bg */
  --color-surface-3: #1f2a3a;       /* elevated surface (hover, dropdown) */
  --color-surface-4: #283548;       /* highest elevation */

  /* ── Border ── */
  --color-border-default: #1f2f44;
  --color-border-emphasis: #304560;
  --color-border-focus: #39bae6;    /* cyan focus ring */

  /* ── Text ── */
  --color-text-primary: #e6edf3;
  --color-text-secondary: #8b9bb4;
  --color-text-tertiary: #5c6e84;
  --color-text-disabled: #3d4f64;
  --color-text-link: #59c2ff;
  --color-text-inverse: #0a0e14;

  /* ── Status (operational context — same meaning in both themes) ── */
  --color-status-online: #26d96c;
  --color-status-online-bg: rgba(38, 217, 108, 0.12);
  --color-status-offline: #5c6e84;
  --color-status-offline-bg: rgba(92, 110, 132, 0.12);
  --color-status-error: #ff6b6b;
  --color-status-error-bg: rgba(255, 107, 107, 0.12);
  --color-status-delayed: #ffaa33;
  --color-status-delayed-bg: rgba(255, 170, 51, 0.12);
  --color-status-unknown: #8b9bb4;
  --color-status-unknown-bg: rgba(139, 155, 180, 0.08);

  /* ── Severity (alert context) ── */
  --color-severity-critical: #ff4444;
  --color-severity-critical-bg: rgba(255, 68, 68, 0.15);
  --color-severity-warning: #ffb224;
  --color-severity-warning-bg: rgba(255, 178, 36, 0.15);
  --color-severity-info: #39bae6;
  --color-severity-info-bg: rgba(57, 186, 230, 0.12);

  /* ── Brand / Accent ── */
  --color-accent-primary: #39bae6;   /* cyan — primary CTAs, focus, active */
  --color-accent-primary-hover: #59c2ff;
  --color-accent-primary-active: #2b9ec4;
  --color-accent-primary-bg: rgba(57, 186, 230, 0.10);

  --color-accent-secondary: #7c5cfc; /* violet — secondary actions, charts */
  --color-accent-secondary-hover: #9678ff;
  --color-accent-secondary-bg: rgba(124, 92, 252, 0.10);

  /* ── Data Visualization (accessible colorblind-safe palette) ── */
  --color-chart-1: #39bae6;   /* cyan */
  --color-chart-2: #ffb224;   /* amber */
  --color-chart-3: #26d96c;   /* green */
  --color-chart-4: #ff6b6b;   /* red */
  --color-chart-5: #7c5cfc;   /* violet */
  --color-chart-6: #ff8f40;   /* orange */
  --color-chart-grid: #1f2f44;
  --color-chart-label: #8b9bb4;

  /* ── Semantic Backgrounds ── */
  --color-bg-danger: rgba(255, 68, 68, 0.08);
  --color-bg-success: rgba(38, 217, 108, 0.08);
  --color-bg-info: rgba(57, 186, 230, 0.08);
  --color-bg-warning: rgba(255, 178, 36, 0.08);
}
```

### 1.2 Color Palette — Light Mode

```css
[data-theme="light"] {
  --color-surface-0: #f0f2f5;
  --color-surface-1: #f8f9fb;
  --color-surface-2: #ffffff;
  --color-surface-3: #ebedf0;
  --color-surface-4: #dfe2e6;

  --color-border-default: #d1d5db;
  --color-border-emphasis: #9ca3af;
  --color-border-focus: #0d7eb3;

  --color-text-primary: #111820;
  --color-text-secondary: #4b5563;
  --color-text-tertiary: #9ca3af;
  --color-text-disabled: #c4c9ce;
  --color-text-link: #0d7eb3;
  --color-text-inverse: #f8f9fb;

  /* Status colors adjusted for light background legibility */
  --color-status-online: #16803c;
  --color-status-online-bg: rgba(22, 128, 60, 0.08);
  --color-status-offline: #6b7280;
  --color-status-offline-bg: rgba(107, 114, 128, 0.08);
  --color-status-error: #dc2626;
  --color-status-error-bg: rgba(220, 38, 38, 0.08);
  --color-status-delayed: #d97706;
  --color-status-delayed-bg: rgba(217, 119, 6, 0.08);

  --color-severity-critical: #dc2626;
  --color-severity-critical-bg: rgba(220, 38, 38, 0.10);
  --color-severity-warning: #d97706;
  --color-severity-warning-bg: rgba(217, 119, 6, 0.10);
  --color-severity-info: #0d7eb3;
  --color-severity-info-bg: rgba(13, 126, 179, 0.08);

  --color-accent-primary: #0d7eb3;
  --color-accent-primary-hover: #0a6c99;
  --color-accent-primary-bg: rgba(13, 126, 179, 0.08);
  --color-accent-secondary: #6d28d9;
  --color-accent-secondary-hover: #5b21b6;

  --color-chart-grid: #d1d5db;
  --color-chart-label: #4b5563;
}
```

### 1.3 Typography

```css
:root {
  /* ── Font Families ── */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  --font-display: 'Inter', sans-serif;  /* same family, different weight for headings */

  /* ── Font Sizes ── */
  --text-2xs: 0.625rem;    /* 10px — micro labels, chart axis */
  --text-xs: 0.75rem;      /* 12px — secondary labels, badges */
  --text-sm: 0.8125rem;    /* 13px — body small, table cells */
  --text-base: 0.9375rem;  /* 15px — body default */
  --text-md: 1.0625rem;    /* 17px — emphasized body */
  --text-lg: 1.25rem;      /* 20px — section headers */
  --text-xl: 1.5rem;       /* 24px — page titles */
  --text-2xl: 1.875rem;    /* 30px — dashboard hero metrics */
  --text-3xl: 2.5rem;      /* 40px — big numbers (fleet count) */

  /* ── Font Weights ── */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* ── Line Heights ── */
  --leading-tight: 1.2;    /* headings, big numbers */
  --leading-normal: 1.5;   /* body text */
  --leading-relaxed: 1.7;  /* long-form content */

  /* ── Letter Spacing ── */
  --tracking-tight: -0.02em;  /* large headings */
  --tracking-normal: 0;
  --tracking-wide: 0.05em;    /* uppercase labels */
  --tracking-mono: 0;         /* monospace values */
}
```

### 1.4 Spacing

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* Layout */
  --sidebar-width: 260px;
  --sidebar-collapsed: 64px;
  --topbar-height: 56px;
  --content-max-width: 1440px;
  --card-min-width: 280px;
}
```

### 1.5 Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}
```

### 1.6 Shadows (Dark Theme)

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6);

  --shadow-focus: 0 0 0 3px var(--color-border-focus);
}
```

### 1.7 Motion

```css
:root {
  --motion-fast: 150ms ease;
  --motion-normal: 250ms ease;
  --motion-slow: 400ms ease;
  --motion-spring: 300ms cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Reduced motion */
  @media (prefers-reduced-motion: reduce) {
    --motion-fast: 0ms;
    --motion-normal: 0ms;
    --motion-slow: 0ms;
    --motion-spring: 0ms;
  }
}
```

---

## 2. Component Specifications

### 2.1 StatusDot

Renders a robot's connection status as a pulsing dot indicator.

| Property | Token | Value |
|----------|-------|-------|
| Size | — | 10px diameter |
| Online color | `--color-status-online` | Green, subtle pulse animation (opacity 1→0.6) |
| Offline color | `--color-status-offline` | Gray, static |
| Error color | `--color-status-error` | Red, fast pulse (opacity 1→0.4, 500ms) |
| Delayed color | `--color-status-delayed` | Amber, slow pulse |
| Label | `--text-xs`, `--color-text-secondary` | Optional text beside dot |
| Pulse animation | `--motion-slow` (online), `--motion-fast` (error) | CSS keyframe opacity pulse |
| Focus | 4px ring `--color-border-focus` | Only when interactive (clickable) |
| Reduced motion | `prefers-reduced-motion` → static | Pulse disabled |

**States**:
- `default` — colored dot per status, with pulse if online/error
- `with-label` — dot + text on right, `--space-2` gap
- `interactive` — clickable, cursor pointer, focus ring on keyboard

---

### 2.2 RobotCard

Dashboard card representing a single robot in the fleet overview grid.

| Property | Token | Value |
|----------|-------|-------|
| Surface | `--color-surface-2` | Card background |
| Border | `--color-border-default` | 1px border |
| Radius | `--radius-lg` | 12px |
| Shadow | `--shadow-sm` | Rest state |
| Shadow hover | `--shadow-md` | Hover state |
| Width | `--card-min-width` (280px) min, fluid max | Grid auto-fill |
| Padding | `--space-4` | Internal spacing |
| Header | StatusDot + robot name (`--text-base`, `--font-semibold`) + last-seen time (`--text-xs`, `--color-text-tertiary`) | Top row |
| Body | Battery bar (h), CPU gauge (h), Task status tag | Middle row — `--space-2` gap |
| Click action | Navigate to `/robot/:id` | Entire card clickable |

**States**:
- `default` — as above
- `hover` — border `--color-border-emphasis`, shadow elevates, cursor pointer
- `focus` — `--shadow-focus` ring
- `loading` — skeleton shimmer animation, content replaced with placeholder blocks
- `error-state` — card tinted with `--color-status-error-bg`, status shows "Error"

---

### 2.3 SeverityBadge

Indicates alert severity level on alert rows and notifications.

| Property | Token | Value |
|----------|-------|-------|
| Size | `--text-2xs` (10px), height 20px | Compact inline badge |
| Critical bg | `--color-severity-critical-bg` | Red-tinted background |
| Critical text | `--color-severity-critical` | Red text |
| Warning bg | `--color-severity-warning-bg` | Amber-tinted |
| Warning text | `--color-severity-warning` | Amber text |
| Info bg | `--color-severity-info-bg` | Blue-tinted |
| Info text | `--color-severity-info` | Blue text |
| Icon | Exclamation triangle (critical), warning triangle (warning), info circle (info) | Left of label, 12px |
| Font | `--font-medium`, uppercase, `--tracking-wide` | All-caps label |
| Radius | `--radius-full` | Pill shape |
| Padding | `--space-1` h, `--space-1` v (2px 4px) | Compact |

**States**: No interactive states — display only.

---

### 2.4 MetricGauge

Semi-circular gauge for displaying real-time metrics (battery, CPU, memory).

| Property | Token | Value |
|----------|-------|-------|
| Size | 120px × 60px | Semi-circle arc |
| Arc stroke | 6px | Thick enough to read at a glance |
| Track color | `--color-surface-4` | Background arc |
| Value color | Dynamic: green (>60%), amber (30-60%), red (<30%) | Gradient stops at threshold |
| Center label | Value: `--text-xl`, unit: `--text-xs`, `--color-text-secondary` | Stacked vertically |
| Min/Max labels | `--text-2xs`, `--color-text-tertiary` | Ends of arc |
| Animation | `--motion-normal` | Value changes animate smoothly |
| Threshold markers | Small dots at 25%, 50%, 75% | Optional — configurable per gauge type |

**Variants**:
- `gauge-battery` — reads 0-100%, color transitions at 20%/50%
- `gauge-cpu` — reads 0-100%, no color bands (higher is worse context-dependent)
- `gauge-memory` — reads 0-100%, color transitions at 70%/90%

**States**:
- `normal` — current value animated
- `no-data` — arc greyed out, center shows "--"
- `loading` — shimmer on arc

---

### 2.5 TimeSeriesChart

Interactive time-series line chart for history exploration.

| Property | Token | Value |
|----------|-------|-------|
| Library | — | Recharts or visx (React) |
| Height | 300px default, 500px full-panel | Responsive |
| Grid | `--color-chart-grid`, 1px dashed | Horizontal gridlines only |
| Axis labels | `--text-xs`, `--color-chart-label` | X: time, Y: metric value |
| Line width | 2px | Visible at small sizes |
| Line colors | `--color-chart-1` through `--color-chart-6` | Per metric |
| Tooltip | `--color-surface-3`, `--shadow-md`, `--radius-md` | On hover, shows all series values at timestamp |
| Gap handling | Dashed line across gap, shaded gap region `rgba(255,107,107,0.08)` | Gap > 2× expected interval |
| Zoom/Pan | Brush zoom (bottom mini-chart), drag to pan | Standard chart interaction |
| Threshold lines | Horizontal dashed lines at alert thresholds, colored by severity | Optional overlay |
| Loading | Skeleton bars at varied widths | Before data arrives |

**States**:
- `default` — renders data
- `no-data` — empty state: "No telemetry data for selected range" with calendar icon
- `loading` — skeleton
- `comparing` — 2+ lines with legend, dual Y-axis if metrics differ in unit
- `error` — "Failed to load data. Retry?" with button

---

### 2.6 AlertToast

Slide-in notification for new alerts. Stacks from top-right, auto-dismisses.

| Property | Token | Value |
|----------|-------|-------|
| Position | Fixed top-right, 16px margin | Stacked vertically |
| Width | 380px max | Reasonable on desktop |
| Surface | `--color-surface-3` | Elevated |
| Border-left | 4px solid severity color | Visual severity indicator |
| Shadow | `--shadow-lg` | Floating appearance |
| Anim in | Slide from right + fade, `--motion-spring` | 300ms spring enter |
| Anim out | Fade out, `--motion-normal` | 250ms fade exit |
| Content | SeverityBadge + alert title (`--text-sm`, `--font-medium`) + robot name (`--text-xs`, `--color-text-secondary`) + timestamp (`--text-2xs`) + action buttons | Stacked |
| Auto-dismiss | 8s for warning, 15s for info, no auto-dismiss for critical | Configurable |
| Sound | Web Audio API: 250Hz 200ms pulse (critical), 440Hz 100ms (warning) | Only if tab focused |

**Actions**:
- Acknowledge: mark alert seen, changes state, removes from unread count
- Jump to robot: navigates to `/robot/:id`
- Dismiss: closes toast, dismisses alert if critical (otherwise snoozes 5 min)

**States**:
- `entering` — slide-in animation
- `visible` — fully shown
- `exiting` — fade-out, removed from DOM after animation
- `pinned` — user hovered, auto-dismiss timer paused

---

### 2.7 DataTable

Sortable, filterable table for alert lists, robot lists, config history.

| Property | Token | Value |
|----------|-------|-------|
| Header bg | `--color-surface-3` | Sticky header |
| Row bg | `--color-surface-2` | Default row |
| Row hover | `--color-surface-3` | Slight elevation |
| Row striped | Even rows: `--color-surface-1` with 50% opacity | For readability on wide tables |
| Border | `--color-border-default`, horizontal only | Clean look |
| Cell padding | `--space-3` h, `--space-2` v | Comfortable density |
| Header font | `--text-xs`, `--font-semibold`, `--color-text-secondary`, uppercase, `--tracking-wide` | Distinct from data |
| Cell font | `--text-sm`, `--font-normal` | Data values |
| Monospace cells | Numeric/ID columns: `--font-mono`, tabular-nums | Aligned numbers |
| Sort indicator | ▲/▼ icon beside header, `--color-accent-primary` for active sort | Click column header to sort |
| Empty state | "No data" message with relevant icon, `--text-md`, `--color-text-tertiary`, centered | Friendly empty |
| Loading | Skeleton rows (5 rows, striped pattern) | Placeholder |
| Pagination | Bottom: "Showing X-Y of Z" + prev/next buttons | `--space-4` padding |

**Variants**:
- `compact` — `--space-2` padding, `--text-xs` cells (for high-density monitoring views)
- `expandable` — row click expands detail panel below

---

### 2.8 Sidebar

Collapsible navigation sidebar with fleet status summary.

| Property | Token | Value |
|----------|-------|-------|
| Width | `--sidebar-width` (260px) expanded, `--sidebar-collapsed` (64px) collapsed | CSS transition |
| Bg | `--color-surface-0` | Deepest surface |
| Border | Right: `--color-border-default` | Separator |
| Logo | Top: org logo + "FleetOps" title (collapsed: logo only) | Brand area |
| Nav items | Icon + label (`--text-sm`, `--color-text-secondary`), active: `--color-accent-primary` bg + border-left | 7 items |
| Fleet summary | Bottom: "3 Online / 1 Offline / 0 Error" compact view | Collapsed: count badges only |
| User | Bottom-most: avatar + name + role, collapsed: avatar only | Identity area |
| Collapse toggle | Chevron icon at bottom, `--motion-normal` rotate + width transition | Keyboard: Ctrl+B |
| Mobile | Overlay drawer, backdrop `rgba(0,0,0,0.5)`, swipe-to-close | Below 768px |

**States**:
- `expanded` — full width, labels visible
- `collapsed` — icons only, labels on tooltip hover
- `mobile-open` — full overlay
- `mobile-closed` — hidden

---

### 2.9 TopBar

Top navigation bar with search, alert badge, theme toggle, user menu.

| Property | Token | Value |
|----------|-------|-------|
| Height | `--topbar-height` (56px) | Fixed height |
| Bg | `--color-surface-1` | With bottom border |
| Border | Bottom: `--color-border-default` | Separator |
| Content (L→R) | Hamburger (mobile), Search input, Alert bell + count badge, Theme toggle, User dropdown | Full-width flex |
| Search | 240px width, `--radius-md`, `--color-surface-3` bg, placeholder: "Search robots..." | Keyboard: / focuses |
| Alert bell | Icon + badge (count, `--radius-full`, `--color-severity-critical`) | Pulse animation on new alert |
| Theme toggle | Sun/Moon icon, `--motion-normal` rotation | Keyboard: Ctrl+Shift+T |
| User menu | Avatar + ▼ icon → dropdown: name, role, settings, logout | Click/focus |
| Mobile hamburger | Visible < 768px, toggles sidebar overlay | Standard hamburger icon |

---

### 2.10 MapMarker

Map marker for robot position on Leaflet/Maplibre map.

| Property | Token | Value |
|----------|-------|-------|
| Shape | Circle (12px) + direction arrow (8px) | Circle + triangle |
| Online color | `--color-status-online`, white arrow | Green circle |
| Offline color | `--color-status-offline` | Gray circle |
| Error color | `--color-status-error`, pulse animation | Red circle |
| Clustered | `--color-accent-primary` circle with count in white `--font-mono` `--text-xs` | Blue cluster marker |
| Popup | Robot name + status + battery + last seen, "View Details" link | Standard Leaflet popup |
| Trail | Fading polyline (last 10 positions), opacity 0.8→0.1 | Map layer |
| Interpolation | Smooth movement between position updates, `--motion-slow` linear | CSS transition on marker position |

---

## 3. Layout Grid

### 3.1 Fleet Overview Layout

```
┌─────────────────────────────────────────────────┐
│ TopBar                                          │
├────────┬────────────────────────────────────────┤
│        │  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│        │  │ Fleet    │ │ Battery  │ │ CPU    │ │
│        │  │ Status   │ │ Trend    │ │ Trend  │ │
│ Sidebar│  │ Ring     │ │ Chart    │ │ Chart  │ │
│        │  └──────────┘ └──────────┘ └────────┘ │
│        │  ┌──────────────────────────────────┐  │
│        │  │ Robot Card Grid (auto-fill)      │  │
│        │  │ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │  │
│        │  │ │   │ │   │ │   │ │   │ │   │  │  │
│        │  │ └───┘ └───┘ └───┘ └───┘ └───┘  │  │
│        │  └──────────────────────────────────┘  │
│        │  ┌──────────────────────────────────┐  │
│        │  │ Map View (optional, toggled)     │  │
│        │  └──────────────────────────────────┘  │
└────────┴────────────────────────────────────────┘
```

### 3.2 Robot Detail Layout

```
┌─────────────────────────────────────────────────┐
│ TopBar                                          │
├────────┬────────────────────────────────────────┤
│        │  ← Back to Fleet    Robot Name · Status │
│        │  ┌────────┬────────┬────────┐          │
│ Sidebar│  │Battery │ CPU    │ Memory │          │
│        │  │ Gauge  │ Gauge  │ Gauge  │          │
│        │  └────────┴────────┴────────┘          │
│        │  ┌──────────────┐ ┌──────────────┐     │
│        │  │ Joint Temps  │ │ GPS/Map      │     │
│        │  │ Heatmap Grid │ │ Mini Map     │     │
│        │  └──────────────┘ └──────────────┘     │
│        │  ┌──────────────────────────────────┐  │
│        │  │ Time-series Chart (full width)   │  │
│        │  └──────────────────────────────────┘  │
│        │  ┌──────────────┐ ┌──────────────┐     │
│        │  │ Alert History│ │ Comments     │     │
│        │  └──────────────┘ └──────────────┘     │
└────────┴────────────────────────────────────────┘
```

---

## 4. Interaction Patterns

### 4.1 Real-time Updates

- **Data flow**: WebSocket → Zustand store → selective React re-render
- **Update frequency**: Throttled to 2 FPS (500ms) for visual display; store keeps latest
- **Visual cue**: Changed values flash briefly with `--color-accent-primary-bg` overlay, fade over 1s
- **Stale indicator**: If no update for > 30s, card border turns `--color-status-delayed`, tooltip shows "Last update: Xs ago"

### 4.2 Alert Flow

```
Alert triggered (pipeline) → WS push → Zustand store → 
  ├─ Badge count increment (topbar bell)
  ├─ Toast notification (top-right)
  ├─ Sound alert (if tab focused, severity-dependent)
  └─ Browser notification (if tab backgrounded)

User actions:
  Acknowledge → PUT /api/alerts/:id/acknowledge → WS broadcast → remove from unread
  Jump to robot → navigate to /robot/:id, scroll to alert section
  Dismiss → PUT /api/alerts/:id/dismiss (critical) or snooze (warning/info)
```

### 4.3 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+Shift+T` | Toggle theme |
| `Esc` | Close modal/drawer/dropdown |
| `←→` | Navigate between robot cards in grid |
| `Tab` | Move through interactive elements in natural order |
| `Enter` | Open selected robot / Confirm action |

### 4.4 Loading States

- **Skeleton screens**: Replaces content with shape-matched pulsating placeholders. Color: `--color-surface-3` → `--color-surface-4` pulse.
- **Progressive loading**: Critical data (status, alerts) loads first; charts and history load second.
- **Stale-while-revalidate**: Show cached data while fetching fresh, transition with fade on update.

---

## 5. Accessibility Requirements (WCAG AA)

| Requirement | Implementation |
|-------------|---------------|
| Color contrast | All text-to-background ≥ 4.5:1 (normal), ≥ 3:1 (large). Status dots supplemented with icons/text. |
| Focus indicators | `--shadow-focus` on all interactive elements. Visible focus ring on keyboard navigation. |
| Screen reader | `aria-label` on icon-only buttons, `aria-live="polite"` on status updates, `role="alert"` on critical toasts |
| Keyboard | All functionality accessible via keyboard. No keyboard traps. |
| Reduced motion | `prefers-reduced-motion` disables all animations, pulses, and transitions |
| Text scaling | Layout works at 200% zoom without horizontal scroll |
| Data visualization | Chart data available in adjacent table for screen readers. Color not the sole differentiator. |

---

## Completion Report

**what_was_done**: Designed complete design system for Robot Fleet Ops Dashboard — 7 color categories (97 tokens), typography scale, spacing system, 10 component specs, 2 page layouts, interaction patterns, and WCAG AA accessibility requirements. Dark-first with light mode variant.

**key_decisions**:
- **decision**: Dark-first design language
  **rationale**: Ops dashboard viewed for long shifts; dark reduces eye strain. Light mode provided as secondary option via `prefers-color-scheme` detection.
- **decision**: Monospace for all numeric data values
  **rationale**: Tabular alignment critical for scanning metrics across robots. JetBrains Mono with `tabular-nums` ensures vertical alignment without pixel-level CSS hacks.
- **decision**: 10 component specs focusing on ops-unique patterns
  **rationale**: Standard components (button, input, modal) use Radix UI primitives; only dashboard-specific components (StatusDot, RobotCard, MetricGauge, SeverityBadge, AlertToast, DataTable, MapMarker) receive custom specs.
- **decision**: Colorblind-safe chart palette
  **rationale**: 8% of male population affected. Palette selected from ColorBrewer qualitative set, supplemented with pattern differentiation as fallback.

**handoff_focus**: senior-frontend should implement I-020 (shell) using these tokens and component specs as the single source of truth. All 10 components rely on CSS custom properties defined here. epic-design can use motion tokens and chart styling for scroll-driven reveals.

**open_questions**:
- Should the chart library be Recharts (simpler) or visx (more flexible)? Recommendation: start with Recharts, migrate if needed

**known_constraints**:
- All token values are CSS custom properties — no build-time theme compilation needed
- Component specs assume React + TypeScript; framework-agnostic where possible
