# Prototype: Robot Fleet Monitoring Dashboard — UI Layout Evaluation

## Prototype Profile

- **Type**: UI Prototype (sub-shape B — new page, no existing frontend codebase)
- **File**: `prototype/dashboard-prototype.html`
- **How to run**: Open `traces/task-20260530T165512Z-064cf2e1/prototype/dashboard-prototype.html` in any modern browser. No build step, no server, no npm install.
- **Framing**: This is THROWAWAY code. All data is simulated. ECharts via CDN. No React, no TypeScript, no build pipeline — the prototype exists to answer one question, not to be promoted.

## Question Answered

> **What layout and interaction model works best for a robot fleet monitoring dashboard rated for 10 robots, with real-time metrics, alarms, collaboration, and configuration — before committing to a React component architecture?**

## Three Variants

Toggle via `?variant=A|B|C` URL param or the floating bottom bar (← → arrow keys or click).

### Variant A — Grid Dashboard
- **Layout**: 3-column CSS grid. Cards for battery ring chart, CPU trend line, heatmap scatter, alarm list, collaboration panel, quick actions.
- **Philosophy**: Single-glance overview. All critical info visible without scrolling. Matches the UX wireframe directly.
- **Strengths**: Familiar monitoring-dashboard pattern (Grafana/Datadog style). Good information density. Drag handles indicated on every card.
- **Weaknesses**: Little room for detail on any one robot. Alarms share equal weight with charts — easy to miss.

### Variant B — Sidebar Command Center
- **Layout**: Left sidebar lists all robots with status dots. Main area shows selected robot detail: 4 metric cards, 30-day history chart, alarm list filtered for that robot, collaboration, and config shortcuts.
- **Philosophy**: Operator drill-down. The sidebar is the index; the main area is the detail panel. Good for an operator actively managing specific robots.
- **Strengths**: Excellent for focused troubleshooting. Robot-level context is clear. Metric cards give instant numeric reads. Sidebar scales to more robots.
- **Weaknesses**: Fleet-level overview is lost. The operator must scroll the sidebar and click to see each robot. Battery distribution and heatmap are missing.

### Variant C — Timeline / Feed
- **Layout**: Left column is an event feed (alarms, status changes, config edits, collaboration in chronological order). Right area has 2×2 grid of charts and panels.
- **Philosophy**: Activity-stream-centric. The feed tells the story; charts provide context. Good for catching what just changed.
- **Strengths**: The feed is naturally attention-grabbing. Operators see the narrative ("robot fell → engineer acknowledged → resolved"). Collaboration messages interleaved with events.
- **Weaknesses**: Feed can get noisy with 10+ robots generating events. Charts are smaller. Hard to compare multiple robots side-by-side.

## Finding

**The answer is a hybrid: Variant B's sidebar with Variant A's overview charts, controlled by a toggle.**

- Variant B (Sidebar Command Center) is the strongest for the operator's primary workflow: selecting a robot and seeing its detail. The left-sidebar pattern is standard for operational tools and scales better as robot count grows.
- Variant A (Grid Dashboard) provides essential fleet-level awareness that Variant B lacks. The battery ring chart and heatmap answer "is the fleet healthy?" in one glance.
- Variant C (Timeline) is valuable as a secondary view — it captures the chronological narrative that engineers need for post-incident review — but should not be the primary dashboard.

**Recommended composition**:
1. **Primary layout**: Variant B sidebar + detail area (the default view with robot list)
2. **Overview toggle**: A top-bar button that temporarily expands Variant A-style grid charts (battery ring, heatmap, CPU trend) *above* the detail area or as a collapsible section. This gives both fleet-level and robot-level awareness without switching pages.
3. **Timeline as a tab**: The feed column from Variant C lives behind a "Timeline" tab or drawer — available but not the default.

## What This Prototype Does NOT Tell Us

| Gap | Why not tested | How to test later |
|-----|---------------|-------------------|
| Performance with 100+ robots | Prototype simulates 10 robots with no real data pipeline | Load test with actual WebSocket stream at scale |
| Drag-and-drop persistence | Drag handles are visual-only; react-grid-layout not integrated | Build a real React grid layout, test save/restore across sessions |
| Real-time chart animation with live data | Charts update on 3s interval but do not stream-animate | Test ECharts `appendData` with real WebSocket at 1s sample rate |
| Accessibility (screen reader, keyboard nav) | No ARIA labels, no focus management | Apply WCAG 2.1 AA to the winning variant |
| Mobile/tablet responsiveness | Designed for desktop 1440px+ | Test responsive breakpoints against the PRD's "out of scope" for mobile |
| Actual i18n integration | Strings are embedded in JS object, not react-i18next resource files | Integrate with react-i18next, validate Chinese/English coverage |
| Map with real tiles vs scatter plot | Heatmap uses scatter plot on coordinates, not a real map provider | Integrate AMap / Leaflet / Mapbox with robot GPS positions |
| PDF/Excel export accuracy | Export buttons are stubs | Test Puppeteer PDF rendering and exceljs output with real chart data |

## Shortcuts Explicitly Labeled

| Shortcut | Where | Why |
|----------|-------|-----|
| All robot data fabricated in-memory | `generateRobots()` | Testing layout, not data accuracy |
| ECharts via CDN | `<script src="cdn.jsdelivr.net">` | No bundler, no npm, no build step |
| No React or TypeScript | Entire file is vanilla JS | Prototype answers layout question, not framework choice |
| Dark theme via CSS variables toggle, no context provider | `toggleTheme()` | Testing color scheme, not architecture |
| i18n via embedded JS object | `i18n` const | Testing bilingual UI, not i18n infrastructure |
| Alarm banner is hardcoded to RBT-003 | `alarmBanner` HTML | Testing alarm UI placement, not alarm engine |
| History data is random walk | `generateHistory()` | Testing chart rendering, not actual time-series |
| "Send message" buttons are alert() stubs | Multiple `onclick="alert(...)"` | Testing layout of collaboration panel, not WebSocket messaging |
| Drag handles are visual only (⠿) | Card headers | Testing the concept of draggable layout, not react-grid-layout |
| Scatter plot instead of real map | Heatmap chart | Testing robot position visualization, not map integration |
| No error handling, no loading states | Entire file | Demo path only — error states are a separate design question |

## Recommended Next Step

**Proceed** — with the hybrid layout (Variant B sidebar + Variant A overview + Timeline tab). The prototype has reduced uncertainty about the dashboard layout. The next node should build the React component architecture for this composition.

Specifically:
1. Implement the sidebar robot list with status indicators and click-to-select
2. Build the 4-metric-card header for the selected robot
3. Create a collapsible "Fleet Overview" section with battery ring chart and heatmap
4. Add a "Timeline" drawer/tab with event feed
5. Integrate react-grid-layout for the dashboard grid cards
6. Wire WebSocket data to charts with `appendData` for live updates
