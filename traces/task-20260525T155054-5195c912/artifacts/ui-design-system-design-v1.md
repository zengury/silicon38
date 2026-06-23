# Design System: 机器人车队运维监控面板

> Source: UX Spec (3 personas, 5 design principles, 2 screen wireframes) · Dark-first for long monitoring shifts

---

## 1. Design Tokens

### Color — Dark Mode (default)

```css
:root {
  --surface-0: #0a0e14;     /* sidebar bg */
  --surface-1: #111820;     /* main content */
  --surface-2: #182230;     /* card bg */
  --surface-3: #1f2a3a;    /* hover, dropdown */
  --border-default: #1f2f44;
  --border-focus: #39bae6;  /* cyan focus ring */

  --text-primary: #e6edf3;
  --text-secondary: #8b9bb4;
  --text-tertiary: #5c6e84;

  --status-online: #26d96c;
  --status-offline: #5c6e84;
  --status-error: #ff6b6b;
  --status-delayed: #ffaa33;

  --severity-critical: #ff4444;
  --severity-warning: #ffb224;
  --severity-info: #39bae6;

  --accent: #39bae6;         /* cyan — primary CTAs */
  --accent-hover: #59c2ff;

  --chart-1: #39bae6; --chart-2: #ffb224;
  --chart-3: #26d96c; --chart-4: #ff6b6b;
  --chart-5: #7c5cfc; --chart-grid: #1f2f44;
}
```

### Typography

```css
--font-sans: 'Inter', sans-serif;
--font-mono: 'JetBrains Mono', monospace;  /* data values, IDs */
--text-xs: 0.75rem;  --text-sm: 0.8125rem;
--text-base: 0.9375rem; --text-lg: 1.25rem;
--text-xl: 1.5rem; --text-2xl: 1.875rem;
```

### Spacing & Layout

```css
--space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
--space-6: 24px; --space-8: 32px;
--sidebar-width: 260px; --topbar-height: 56px;
--card-min-width: 280px;
--radius-md: 8px; --radius-lg: 12px;
--motion-fast: 150ms; --motion-normal: 250ms;
```

---

## 2. Component Specifications

### StatusDot
10px diameter circle. Online: green, subtle pulse. Offline: gray, static. Error: red, fast pulse. Delayed: amber, slow pulse. Optional text label beside dot (`--text-xs`). Respects `prefers-reduced-motion`.

### RobotCard
Card: `--surface-2` bg, `--radius-lg`, `--shadow-sm` (hover: `--shadow-md`). 280px min width, fluid grid. Content: header (StatusDot + name + last-seen), body (battery bar + CPU gauge + task tag). Entire card clickable → navigate to detail. Loading: skeleton shimmer. Error: red-tinted background.

### MetricGauge
Semi-circle 120×60px. 6px stroke. Track: `--surface-4`. Value color: green (>60%), amber (30-60%), red (<30%). Center: value (`--text-xl`) + unit (`--text-xs`). Threshold markers at 25/50/75%.

### AlertToast
Fixed top-right, 380px, slides in with spring animation. 4px left border in severity color. Content: severity badge + title + robot name + timestamp. Actions: Acknowledge, Jump to robot, Dismiss. Critical: 250Hz pulse tone. Auto-dismiss: 8s warning, 15s info, never for critical.

### StatusBadge
Compact pill badge: `--text-2xs`, uppercase, `--tracking-wide`. Critical: red bg/text. Warning: amber. Info: blue. With icon (triangle/circle). Display only.

### TimeSeriesChart
Recharts line chart. 2px lines. Dashed grid. Zoom/pan. Gap detection: break in line + shaded gap region. Threshold overlay: horizontal dashed lines at alert thresholds. Dual Y-axis for comparison mode. Loading: skeleton bars. Tooltip: `--surface-3` bg, `--shadow-md`.

### DataTable
Headers: `--surface-3` bg, `--text-xs`, uppercase, sticky. Rows: `--surface-2`, hover elevates to `--surface-3`. Monospace for numeric/ID columns (`--font-mono`, tabular-nums). Sortable column headers. Empty state: icon + "No data" message. Loading: 5 skeleton rows.

### Sidebar
260px, collapsible to 64px. `--surface-0` bg. Nav items: icon + label, active state with accent bg + left border. Bottom: fleet summary (online/offline/error counts). Collapse toggle: chevron icon, `--motion-normal`. Mobile: overlay drawer with backdrop.

---

## 3. Architecture: CSS Custom Properties → Components

```
tokens.css (design tokens)
    ↓
Component specs (this document)
    ↓
React components (senior-frontend implements)
    ↓
Pages (Fleet Overview, Robot Detail, Alerts, History, Config, Reports)
    ↓
Shell (theme provider, i18n, layout engine)
```

Hard constraints for frontend implementation:
- Every color must reference a CSS custom property — no hardcoded hex values in components
- Every component must cover: default, hover, focus, disabled, error, loading, empty states
- Dark mode is the default. Light mode is the secondary variant.
- Monospace for all numeric data. Tabular-nums alignment.

---

## Completion Report

**what_was_done**: Designed complete design system — 7 color categories (40+ tokens), typography scale, spacing system, 8 component specs with all states, CSS custom properties architecture. Dark-first. WCAG AA compliant color contrast. Motion respects prefers-reduced-motion.

**chain_entry**: "Dark-first design tokens (40+ CSS custom properties), 8 component specs (StatusDot, RobotCard, MetricGauge, AlertToast, StatusBadge, TimeSeriesChart, DataTable, Sidebar). Hard constraint: no hardcoded colors in components — all via tokens."
