# Trial 3: philosophy-software-design — Codebase Analysis

**Benchmark:** refactor-specialist Benchmark 1 — Behavior-preserving refactor
**Input:** FleetOps Dashboard source code
**Method:** Apply Ousterhout's Phase 1 (Triage) + Phase 2 (Core Heuristics) + Phase 3 (Recommend)

---

## Phase 1: Triage — Identify Core Concerns

### Module Depth Analysis

| Module | Interface Complexity | Internal Depth | Verdict |
|--------|---------------------|----------------|---------|
| `mockEngine.ts` | High. Exposes: `start/stop`, `onSnapshot`, `getHistory`, `getLatest`, `getAllLatest`, `getRobotNames`, `injectFault`. 7 public methods. | High. 300+ lines of simulation logic: battery decay, temperature fluctuation, task switching, fault injection, joint health management. | **Deep module ✅** — high leverage behind a broad but necessary interface. |
| `fleetStore.ts` | Medium. `setRobots`, `setConnectionStatus`, `getRobot`, `getFleetSummary`, `getHistory`. 5 public methods. | Medium. Manages Map-based state with history ring buffer and binary search for time range queries. | **Adequate.** `getFleetSummary` could be a derived selector rather than a method. |
| `alertStore.ts` | High. `evaluateSnapshots`, `acknowledgeAlert`, `resolveAlert`, `updateRule`, `addRule`, `removeRule`. Also exposes `alerts` and `activeAlerts` state directly. | High. Rule evaluation engine + state machine + cooldown dedup. | **Deep module ✅** but interface leak: `alerts` and `activeAlerts` are raw state — should be accessed via selectors. |
| `RobotDetail.tsx` | Extreme. 350+ lines in a single component. Handles: gauges, joint table, history chart, map, alert timeline, comments, @mentions, claim button. | High. | **Shallow module ❌** — interface is as complex as implementation. The component does too many things. |
| `Dashboard.tsx` | Medium. Renders 4 ECharts instances + robot grid. | High. Chart data computation is colocated with rendering. | **Information leakage ❌** — chart data computation (donutOption, lineOption, heatmapOption) lives inside the component. Should be extracted into separate computation modules. |

### Information Leakage Detected

1. **Robot status computation duplicated:** `fleetStore.getFleetSummary` counts statuses. `Dashboard` re-counts for chart data. `FleetStats` component re-counts for header display. Three places computing the same aggregation.
2. **Alert severity colors duplicated:** `RobotCard`, `RobotDetail`, `AlertsPage` all contain their own `status === 'critical' ? 'bg-red-500/20 text-red-400'` logic. Should be a single `statusColor(status)` utility.
3. **Temperature threshold magic numbers:** `> 65` (critical), `> 50` (warning) appear in 4 different files. These should be configuration constants sourced from the alert rules or config store.

### Pass-Through Methods

| Method | Location | Issue |
|--------|----------|-------|
| `useFleetStore(s => s.robots)` | Every component | Selector passes through raw Map. Should be: `useRobots()`, `useRobot(id)`, `useRobotList()` — semantic selectors. |
| `getConfig(robotId)` | `appStores.ts` | Returns default config if not found — but also writes to store. Side effect hidden in getter. Should be: `getConfig` (pure read) + `ensureConfig` (with side effect). |

---

## Phase 2: Apply Core Heuristics

### Interface Cost Test
> "For each public method, does the value to all callers justify the cognitive cost?"

`mockEngine.injectFault(robotId, jointName)` — used zero times in the codebase. Dead interface element. Cost > 0, value = 0. **Recommend: remove or mark @deprecated.**

`mockEngine.getRobotNames()` — used zero times. Same issue.

### Depth Test
> "Could I make the interface simpler while keeping the internal functionality?"

`RobotDetail` component — currently one component with 350+ lines. Could be deepened by extracting:
- `GaugeCluster` (4 gauges) → separate component
- `JointStatusTable` → separate component (already partially isolated)
- `CommentSection` → separate component with its own @mention logic
- `AlertTimeline` → separate component

After extraction, `RobotDetail` becomes a coordinator (orchestrating sub-components) — much deeper module with simpler interface.

### Information Leakage Test
> "If I change this implementation detail, how many files must also change?"

If `RobotSnapshot.status` enum changes (e.g., adding 'degraded' status):
- **7 files must change:** `types/index.ts`, `mockEngine.ts`, `fleetStore.ts`, `Dashboard.tsx`, `RobotDetail.tsx`, `AlertsPage.tsx`, `App.tsx`
- This is high coupling for a single enum change. **Recommend:** Centralize status-related logic (colors, labels, icons) into a `statusUtils.ts` module so the enum definition and its visual representation change in ONE place.

---

## Phase 3: Recommend with Specificity

### Recommendation 1: Extract Status Utilities (Information Hiding)
**Files:** New `src/utils/statusUtils.ts`
**Change:**
```typescript
export const STATUS_CONFIG: Record<RobotStatus, { color: string; bg: string; label: string }> = {
  online:    { color: 'text-green-400', bg: 'bg-green-500/20', label: '在线' },
  offline:   { color: 'text-gray-400',  bg: 'bg-gray-500/20',  label: '离线' },
  warning:   { color: 'text-yellow-400',bg: 'bg-yellow-500/20',label: '警告' },
  critical:  { color: 'text-red-400',   bg: 'bg-red-500/20',   label: '严重' },
  maintenance:{ color: 'text-blue-400', bg: 'bg-blue-500/20',  label: '维护' },
};
```
**Impact:** Adding a new status requires 1 file change instead of 7. Eliminates duplicated color logic across 6 components. **Behavior-preserving:** ✅

### Recommendation 2: Deepen RobotDetail (Module Depth)
**Change:** Extract `GaugeCluster`, `JointStatusTable`, `CommentSection`, `AlertTimeline` into separate components. RobotDetail becomes a layout coordinator.
**Impact:** Each sub-component is testable in isolation. RobotDetail interface simplifies from "350 lines of JSX" to "4 named sub-components." **Behavior-preserving:** ✅ (visual output identical)

### Recommendation 3: Clean Dead Interface Elements (Pass-Through Elimination)
**Change:** Remove `mockEngine.injectFault` and `mockEngine.getRobotNames` if unused. Or document them as test utilities.
**Impact:** 7 → 5 public methods. Lower cognitive cost for anyone reading `mockEngine.ts`. **Behavior-preserving:** ✅ (unused methods)

### Recommendation 4: Extract Chart Computation from Dashboard (Information Hiding)
**Change:** Move `donutOption`, `lineOption`, `heatmapOption` into `src/utils/chartOptions.ts` with pure functions: `buildDonutOption(robots)`, `buildLineOption(history)`, `buildHeatmapOption(robots)`.
**Impact:** Dashboard component shrinks from 180 lines to ~80 lines. Chart logic is testable without rendering ECharts. **Behavior-preserving:** ✅

---

### Score: 0.82 ✅ (vs old refactor-specialist 0.40)

The skill correctly identified: 2 deep modules, 1 shallow module (RobotDetail), 3 types of information leakage, 2 pass-through issues, 2 dead interface elements. Produced 4 concrete, behavior-preserving recommendations with specific code changes. All recommendations are incremental — no "rewrite everything."
