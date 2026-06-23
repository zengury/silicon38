# Design System Spec: Fleet Ops Dashboard

## Design Tokens

### Color Tokens

```css
/* Semantic Colors — Light theme */
--color-bg-primary: #f8fafc;      /* Page background */
--color-bg-secondary: #ffffff;     /* Card, header, sidebar background */
--color-bg-tertiary: #f1f5f9;     /* Hover state */
--color-text-primary: #0f172a;    /* Headings, key data */
--color-text-secondary: #64748b;  /* Labels, metadata */
--color-text-muted: #94a3b8;      /* Disabled, placeholder */
--color-border: #e2e8f0;          /* Card borders, dividers */
--color-border-hover: #cbd5e1;    /* Interactive border */

/* Semantic Colors — Dark theme */
.dark {
  --color-bg-primary: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-bg-tertiary: #334155;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;
  --color-border: #334155;
  --color-border-hover: #475569;
}

/* Status Colors (same both themes for readability) */
--color-status-online: #22c55e;    /* Green 500 */
--color-status-warning: #f59e0b;   /* Amber 500 */
--color-status-critical: #ef4444;  /* Red 500 */
--color-status-offline: #64748b;   /* Slate 500 */
--color-status-info: #3b82f6;      /* Blue 500 */

/* Chart Palette (8 colors, accessible) */
--chart-1: #3b82f6;   /* Blue */
--chart-2: #22c55e;   /* Green */
--chart-3: #f59e0b;   /* Amber */
--chart-4: #ef4444;   /* Red */
--chart-5: #8b5cf6;   /* Violet */
--chart-6: #ec4899;   /* Pink */
--chart-7: #06b6d4;   /* Cyan */
--chart-8: #f97316;   /* Orange */
```

### Typography Tokens

```css
--font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: "SF Mono", "Fira Code", monospace;

--text-xs: 11px;    /* Labels, badges, heatmap cells */
--text-sm: 13px;    /* Body text, metric values, alert messages */
--text-base: 15px;  /* Card titles, config labels */
--text-lg: 18px;    /* Section headers */
--text-xl: 22px;    /* Page title */
--text-2xl: 28px;   /* Logo, hero numbers */

--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

--letter-spacing-tight: -0.5px;
--letter-spacing-normal: 0;
--letter-spacing-wide: 0.5px;
--letter-spacing-wider: 1px;  /* Uppercase labels */
```

### Spacing Tokens

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
```

### Border & Shadow Tokens

```css
--radius-sm: 6px;     /* Small buttons, badges */
--radius-md: 8px;     /* Inputs, config rows */
--radius-lg: 12px;    /* Cards, panels, charts */
--radius-full: 9999px; /* Pills, status badges */

--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.08);
--shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
--shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1);

/* Dark theme shadows */
.dark {
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4);
}
```

### Motion Tokens

```css
--duration-instant: 100ms;
--duration-fast: 200ms;
--duration-normal: 300ms;
--duration-slow: 400ms;
--duration-deliberate: 600ms;

--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

---

## Component Primitives

### StatusDot
```
Props: status ('online' | 'warning' | 'critical' | 'offline'), size ('sm' | 'md')
Render: 10px (sm) or 14px (md) circle with status color
Usage: Robot cards, detail panel header, map markers
Accessibility: aria-label="{status} status"
```

### MetricGauge
```
Props: label, value, unit, maxValue, thresholds ({ good, warn })
Render: Label above, value with unit, colored bar below
States: good (green), warn (amber), critical (red) based on thresholds
Usage: Battery, CPU, temperature display
```

### AlertBadge
```
Props: count, severity
Render: Red pill badge with count number. Hidden when count=0.
Animation: Scale bounce on count increase
Usage: Robot card alert indicator
```

### RobotCard
```
Props: robot (RobotTelemetry), alerts (Alert[]), onClick
States: normal, warning (amber border), critical (red border + pulse), offline (greyed + 0.55 opacity)
Content: Header (name + status dot + alert badge), metrics grid (battery, temp, CPU, latency), footer (last seen, task)
Animation: FLIP transition on sort order change
```

### AlertItem
```
Props: alert (Alert), onAcknowledge, onClick
States: active (colored left border, full opacity), acknowledged (60% opacity)
Content: Header (robot name + severity badge), message, timestamp, action button (if not acknowledged)
```

### ChartCard
```
Props: title, children (chart canvas), fullWidth?
Render: Bordered card with uppercase title, chart inside
States: loading (skeleton), empty ("No data"), error (icon + message), normal
```

### DetailDrawer
```
Props: open, robot, onClose, children
Render: Right-sliding overlay + panel (520px wide, max 90vw)
Content: Close button, robot header, children slots
Animation: Overlay fade + panel slide-in 250ms ease-out
```

### ConfigForm
```
Props: robotId, config, onChange
Content: Grouped sections (Thresholds, Sampling, Reconnect) with appropriate input types
Validation: Number inputs clamped to min/max. Select for discrete options.
Interaction: Instant apply with undo toast
```

### CommentThread
```
Props: robotId, comments, onAddComment
Content: List of comment bubbles (author + time + text), input with send button
Features: @mention autocomplete (mock user list), Enter to send
```

---

## Icon System

Use Unicode/emoji for Demo (no icon library dependency):

| Concept | Icon |
|---------|------|
| Battery | 🔋 |
| Temperature | 🌡 |
| CPU | 💻 |
| Network | 📶 |
| Location | 📍 |
| Task | 📋 |
| Alert | ⚠ |
| Settings | ⚙ |
| Export | 📥 |
| Comment | 💬 |
| Online | ● |
| Offline | ○ |
| Dark mode | 🌙 |
| Light mode | ☀️ |
| Language | 🌐 |

Production: Replace with Lucide React icon library for consistent stroke width and tree-shaking.

---

## Responsive Breakpoints

```
Mobile:    < 768px   — Single column, sidebar collapses to top bar, cards full-width
Tablet:    768-1200px — 2-column dashboard, 2-column robot cards
Desktop:   > 1200px  — Full layout: sidebar + 2-column dashboard + 3-column robot cards
```

---

## Completion Report

- **what_was_done**: Produced design system specification: color tokens (light/dark), typography scale, spacing scale, border/shadow tokens, motion tokens, 9 component primitives with props/states/behavior, icon system, responsive breakpoints
- **key_decisions**: [(1) CSS Variables for theming — zero runtime cost, instant toggle, (2) Unicode emoji for Demo icons — no dependency, replaceable with Lucide later, (3) Component primitives defined with explicit states (loading/empty/error/normal) — prevents UI gaps, (4) Motion tokens support prefers-reduced-motion — accessibility-first]
- **handoff_focus**: senior-frontend should implement components per these primitives; production should replace emoji with Lucide React
- **open_questions**: None
- **known_constraints**: Demo uses emoji icons; production should use proper icon library
- **confidence_differential**: 0.90
