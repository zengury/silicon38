# Architecture Decision Record: Robot Fleet Ops Dashboard

## 1. System Context

```
┌──────────────────────────────────────────────────────────────────┐
│                        Browser (React 18 + TS)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │RobotCard │ │Detail    │ │Config    │           │
│  │Overview  │ │ Grid     │ │Panel     │ │Panel     │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └─────────────┴────────────┴─────────────┘                 │
│                         │ Zustand Store                          │
│  ┌──────────────────────┼──────────────────────────────────┐    │
│  │ DataNormalizer │ AlertEngine │ WebSocketManager         │    │
│  └──────────────────────┴────────────┴──────────────────────┘    │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │ WebSocket (JSON frames)
                  ┌───────┴────────┐
                  │  Mock Server   │  ← Demo: client-side mock
                  │  (future: real │     Production: Go/Node WS server
                  │   WS gateway)  │     + InfluxDB/TimescaleDB
                  └────────────────┘
```

## 2. Component Architecture

### 2.1 Core Modules (Deep Modules)

#### DataNormalizer — Schema Registry + Adapter Pipeline

```
                    ┌──────────────────┐
 raw data ─────────►│  FormatDetector  │──► identifies format (json-a | json-b | proto-like)
                    └──────┬───────────┘
                           │ format tag
                    ┌──────▼───────────┐
                    │  AdapterRegistry │──► looks up adapter by format
                    │  {               │
                    │   'json-a':      │
                    │     JsonAAdapter,│
                    │   'json-b':      │
                    │     JsonBAdapter,│
                    │   'proto-like':  │
                    │     ProtoAdapter │
                    │  }               │
                    └──────┬───────────┘
                           │ adapter instance
                    ┌──────▼───────────┐
                    │  Adapter.normalize(raw) ──► RobotTelemetry
                    │  • field renaming        │
                    │  • unit conversion       │
                    │  • default fill          │
                    │  • type coercion         │
                    └──────────────────────────┘
```

**Interface**:
```typescript
interface DataNormalizer {
  registerAdapter(format: string, adapter: TelemetryAdapter): void;
  normalize(raw: unknown, format: string): RobotTelemetry;
}

interface TelemetryAdapter {
  readonly format: string;
  normalize(raw: Record<string, unknown>): RobotTelemetry;
}
```

**Rationale**: Adapter pattern allows adding new robot formats without touching existing code. Schema Registry is a simple Map — no DI framework needed for Demo. Each adapter is independently testable.

**Alternatives rejected**:
- Single `if/else` chain in normalize() — doesn't scale beyond 3 formats
- JSON Schema validation (Ajv) — adds runtime dependency, overkill for Demo where we control mock data
- Protobuf.js full runtime — Demo uses JSON representation of protobuf; full parsing deferred to P2

#### AlertEngine — Rule Evaluator

```
 RobotTelemetry ──────► RuleEvaluator
                         │
                         │ rules: AlertRule[]
                         │ dedupWindow: 300000ms
                         │
                         ├──► Rule: "battery.level < threshold"
                         │      severity: WARNING
                         │
                         ├──► Rule: "status == FALLEN"
                         │      severity: CRITICAL
                         │
                         └──► Rule: "joints[*].communication == LOST"
                                severity: CRITICAL
                         │
                    ┌────▼──────────────────┐
                    │  Dedup + Lifecycle     │
                    │  • same robot+type →   │
                    │    skip if < 5min      │
                    │  • new alert → emit    │
                    │  • resolved → update   │
                    └────────────────────────┘
                              │
                              ▼
                         Alert[]
```

**Interface**:
```typescript
interface AlertEngine {
  setRules(rules: AlertRule[]): void;
  evaluate(telemetry: RobotTelemetry): Alert[];
  acknowledge(alertId: string): void;
  resolve(alertId: string): void;
  getActiveAlerts(): Alert[];
}

interface AlertRule {
  id: string;
  metric: string;        // dot-path: "battery.level"
  operator: '<' | '>' | '==' | '!=' | 'includes';
  threshold: number | string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  messageTemplate: string;
}
```

**Rationale**: Rules are plain objects — no DSL, no expression parser. For Demo's 3 rules, this is sufficient. Rules reference metrics by dot-path (`battery.level`), which lodash `get()` resolves. Config panel writes directly to rules array.

**Alternatives rejected**:
- Expression engine (JEXL, JSONLogic) — overkill for 3 simple rules
- State machine for alert lifecycle — Demo scope = acknowledge/resolve, no escalation. Keep simple.

#### WebSocketManager — Connection + Reconnection

```
                    ┌────────────────────────┐
 connect(url) ─────►│  WebSocketManager       │
                    │                         │
                    │  ws: WebSocket          │
                    │  reconnectDelay: 1000ms │
                    │  maxRetries: 10         │
                    │  retryCount: 0          │
                    │                         │
                    │  onMessage → Dispatch   │
                    │  onClose  → Reconnect   │
                    │  onError  → Reconnect   │
                    └────────┬───────────────┘
                             │
                    ┌────────▼────────────┐
                    │  Topic Subscribers   │
                    │  topic: callback[]   │
                    │  "telemetry": [fn1,  │
                    │                fn2]  │
                    └─────────────────────┘
```

**Interface**:
```typescript
interface WebSocketManager {
  connect(url: string): void;
  disconnect(): void;
  subscribe(topic: string, handler: (data: unknown) => void): () => void;
  send(topic: string, data: unknown): void;
}
```

**Rationale**: Topic-based pub/sub over a single WS connection. Each subscriber returns an unsubscribe function (clean React useEffect integration). Exponential backoff: 1s → 2s → 4s → 8s → cap at 30s.

**Alternatives rejected**:
- Socket.io — adds protocol overhead, Demo doesn't need rooms/namespaces
- SSE (Server-Sent Events) — unidirectional, can't send config changes back
- Multiple WS connections — unnecessary, single connection with topic multiplexing is simpler

### 2.2 State Management — Zustand Store

```typescript
interface FleetStore {
  // Data
  robots: Map<string, RobotState>;
  alerts: Alert[];
  
  // Config
  configs: Map<string, RobotConfig>;
  
  // UI
  ui: {
    theme: 'dark' | 'light';
    language: 'zh-CN' | 'en-US';
    layout: LayoutItem[];
    selectedRobotId: string | null;
    sidebarOpen: boolean;
  };
  
  // Collaboration
  comments: Map<string, Comment[]>;
  
  // Actions
  updateTelemetry(telemetry: RobotTelemetry): void;
  addAlert(alert: Alert): void;
  acknowledgeAlert(id: string): void;
  updateConfig(robotId: string, config: Partial<RobotConfig>): void;
  addComment(robotId: string, comment: Comment): void;
  setTheme(theme: 'dark' | 'light'): void;
  setLanguage(lang: 'zh-CN' | 'en-US'): void;
}
```

**Rationale**: Zustand chosen over Redux (too much boilerplate for Demo) and Jotai (atomic model doesn't fit hierarchical fleet data as cleanly). Zustand's `subscribeWithSelector` enables efficient per-robot subscriptions.

### 2.3 UI Component Tree

```
<App>
  <ThemeProvider>            ← CSS Variables + Tailwind dark:
    <I18nProvider>           ← react-i18next
      <LayoutShell>          ← Header + Sidebar + Main
        <Header>
          <LogoTile />
          <FleetStatusBadge />  ← "5/6 online"
          <ThemeToggle />
          <LanguageToggle />
          <LayoutPresets />     ← Compact | Relaxed | Focus
        </Header>
        <Sidebar>
          <AlertPanel>          ← Active alerts list
            <AlertItem />       ← severity icon + message + ack button
          </AlertPanel>
        </Sidebar>
        <Main>
          <ReactGridLayout>
            <DashboardOverview>     ← Charts row
              <FleetDonutChart />
              <BatteryTrendLine />
              <JointTempHeatmap />
              <RobotMap />
            </DashboardOverview>
            <RobotCardGrid>         ← Cards grid
              <RobotCard />         ← ×6
            </RobotCardGrid>
          </ReactGridLayout>
        </Main>
        <RobotDetailDrawer>         ← Slide-out panel
          <SensorTable />
          <HistoryChart />
          <CommentThread />
          <OwnershipBadge />
        </RobotDetailDrawer>
        <ConfigPanel>               ← Modal/slide-out
          <ThresholdForm />
          <SamplingForm />
          <ReconnectForm />
        </ConfigPanel>
      </LayoutShell>
    </I18nProvider>
  </ThemeProvider>
</App>
```

### 2.4 Data Flow (Runtime)

```
[WebSocket message arrives]
        │
        ▼
WebSocketManager.onMessage(topic="telemetry", rawData)
        │
        ▼
DataNormalizer.normalize(rawData, detectFormat(rawData))
        │
        ▼
  RobotTelemetry { robotId, battery, joints, cpu, ... }
        │
        ├──────────────────────────────────┐
        ▼                                  ▼
AlertEngine.evaluate(telemetry)     Store.updateTelemetry(telemetry)
        │                                  │
        ▼                                  ▼
  Alert[] ──► Store.addAlert()      React re-render subscribed components
                                          │
                    ┌─────────────────────┼──────────────────┐
                    ▼                     ▼                  ▼
            RobotCard updates    Dashboard charts    AlertPanel badge
            (battery bar,       re-render with       count updates
             status dot)         new data point
```

### 2.5 Unified Data Schema

```typescript
interface RobotTelemetry {
  robotId: string;
  timestamp: number;  // Unix ms

  battery: {
    level: number;         // 0-100 (%)
    voltage: number;       // volts
    temperature: number;   // celsius
  };

  joints: JointState[];

  cpu: {
    usage: number;         // 0-100 (%)
    temperature: number;   // celsius
  };

  network: {
    latency: number;       // ms
    rssi: number;          // dBm, -30 to -90
  };

  task: {
    id: string;
    name: string;
    progress: number;      // 0-100 (%)
  };

  location: {
    lat: number;
    lng: number;
    alt?: number;
  };

  status: 'ONLINE' | 'OFFLINE' | 'ERROR' | 'FALLEN';
  statusDetail?: string;
}

interface JointState {
  name: string;            // "left_shoulder_pitch"
  temperature: number;     // celsius
  torque: number;          // Nm
  velocity: number;        // rad/s
  position: number;        // rad
  communication: 'OK' | 'LOST' | 'DEGRADED';
}
```

**Unit normalization decisions**:
- Temperature: always **Celsius** (convert Fahrenheit if adapter receives it)
- Battery level: always **percentage 0-100** (convert from voltage if needed)
- Latency: always **milliseconds**
- Angles: always **radians**
- Timestamp: always **Unix milliseconds**

## 3. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | React 18 + TypeScript 5 | Ubiquitous, Vite for build speed |
| State | Zustand 4 | Lightweight, selector-based subscriptions |
| Charts | Recharts 2 | React-native, composable, supports donut/line/heatmap |
| Map | Leaflet + react-leaflet | Lightweight, no API key needed, OpenStreetMap tiles |
| Styling | Tailwind CSS 3 + CSS Variables | Utility-first + theme token system |
| i18n | react-i18next | Standard, key-based translation |
| Drag layout | react-grid-layout | Stable, responsive breakpoints |
| CSV export | PapaParse | Reliable CSV generation |
| Icons | Lucide React | Tree-shakeable, consistent style |
| Build | Vite 5 | Fast HMR, TypeScript native |

**Rejected alternatives**:
- Next.js — SSR adds complexity for a real-time dashboard that is purely client-side
- D3.js — too low-level for Demo charts; Recharts provides sufficient customization
- Mapbox GL — requires API key; Leaflet with OSM is free and sufficient for marker display
- Redux Toolkit — boilerplate overhead not justified for this app's state complexity
- Ant Design / MUI — heavy; Tailwind + custom components gives more control for the Demo's visual identity

## 4. Cross-Cutting Concerns

### 4.1 Theme System
```
:root {
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f8fafc;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;
  --color-accent: #3b82f6;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-critical: #ef4444;
  --color-border: #e2e8f0;
  --chart-colors: #3b82f6,#22c55e,#f59e0b,#ef4444,#8b5cf6,#ec4899;
}

.dark {
  --color-bg-primary: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-border: #334155;
  /* accent/success/warning/critical remain same for readability */
}
```
Tailwind `dark:` variants reference these CSS variables. Charts read `--chart-colors` for consistent palette.

### 4.2 Performance Strategies

| Concern | Strategy |
|---------|----------|
| Frequent re-renders (telemetry every 1s × 6 robots) | Zustand selectors + `React.memo` on RobotCard |
| Chart re-render on every data point | Recharts animation disabled; only last 60 points rendered |
| Heatmap color computation | Pre-compute normalized values, avoid per-pixel JS |
| 30-day history rendering | Downsample to max 500 points for chart display |
| WebSocket message parsing | `DataNormalizer` runs synchronously in WS message handler |

### 4.3 Error States

| Component | Loading | Empty | Error | Offline |
|-----------|---------|-------|-------|---------|
| RobotCardGrid | Skeleton cards (6) | "No robots connected" illustration | "Data stream error — retrying..." banner | Greyed out cards + "Reconnecting" spinner |
| Dashboard charts | Skeleton chart shapes | "Waiting for data..." placeholder | Chart area with error icon | Last known data with "stale" watermark |
| AlertPanel | Spinner | "No active alerts" ✅ | "Alert system paused" | — |
| ConfigPanel | Form skeleton | — | "Failed to save — retry?" | — |

### 4.4 Mock Data Strategy

Mock server is a client-side module that:
1. Maintains 6 `RobotSimulator` instances, each with a unique "personality":
   - Robot-01: Normal operation, slight temp drift
   - Robot-02: Intermittent network issues (latency spikes)
   - Robot-03: High joint temps on shoulder (approaching threshold)
   - Robot-04: Battery draining faster than others
   - Robot-05: All nominal — baseline reference
   - Robot-06: Occasionally goes OFFLINE for 10-30 seconds
2. Emits telemetry frames via a `MockWebSocket` class (implements same EventTarget interface)
3. `injectAnomaly(robotId, type)` for demo purposes — triggers fall/joint-loss/low-battery
4. Historical data: pre-generate 30 days × 1 sample/min = 43,200 points per robot, stored as compressed JSON arrays

## 5. Module Dependency Map

```
DataNormalizer  ◄── no dependencies
AlertEngine     ◄── no dependencies (takes RobotTelemetry as input)
MockDataGen     ◄── DataNormalizer (produces normalized data)
WebSocketMgr    ◄── none (mock implements same interface)
Store           ◄── none (stores everything)
RobotCard       ◄── Store (selects single robot)
Dashboard       ◄── Store (selects all robots + aggregates)
DetailPanel     ◄── Store (selects single robot + comments)
ConfigPanel     ◄── Store (reads/writes configs)
AlertPanel      ◄── Store (selects alerts)
HistoryChart    ◄── Store (selects historical data)
LayoutShell     ◄── Store (reads/writes UI state)
```

All UI components are leaf nodes. No component imports another component's internals. Shared UI primitives (Badge, StatusDot, MetricGauge) go in `components/ui/`.

## 6. Project Structure

```
src/
├── core/
│   ├── data-normalizer/
│   │   ├── DataNormalizer.ts
│   │   ├── adapters/
│   │   │   ├── JsonAAdapter.ts
│   │   │   ├── JsonBAdapter.ts
│   │   │   └── ProtoAdapter.ts
│   │   └── schema.ts          # RobotTelemetry type
│   ├── alert-engine/
│   │   ├── AlertEngine.ts
│   │   └── rules.ts           # default rules
│   ├── websocket/
│   │   ├── WebSocketManager.ts
│   │   └── MockWebSocket.ts   # Demo mock
│   └── mock/
│       ├── RobotSimulator.ts
│       ├── mock-data-generator.ts
│       └── historical-data.ts
├── store/
│   ├── fleetStore.ts          # Zustand store
│   └── selectors.ts
├── components/
│   ├── ui/                    # Shared primitives
│   │   ├── Badge.tsx
│   │   ├── StatusDot.tsx
│   │   └── MetricGauge.tsx
│   ├── dashboard/
│   │   ├── FleetDonutChart.tsx
│   │   ├── BatteryTrendLine.tsx
│   │   ├── JointTempHeatmap.tsx
│   │   └── RobotMap.tsx
│   ├── fleet/
│   │   ├── RobotCardGrid.tsx
│   │   └── RobotCard.tsx
│   ├── detail/
│   │   ├── RobotDetailDrawer.tsx
│   │   ├── SensorTable.tsx
│   │   ├── HistoryChart.tsx
│   │   └── CommentThread.tsx
│   ├── alerts/
│   │   ├── AlertPanel.tsx
│   │   └── AlertItem.tsx
│   ├── config/
│   │   └── ConfigPanel.tsx
│   └── shell/
│       ├── LayoutShell.tsx
│       ├── Header.tsx
│       └── Sidebar.tsx
├── i18n/
│   ├── index.ts
│   ├── zh-CN.json
│   └── en-US.json
├── theme/
│   ├── tokens.css
│   └── ThemeProvider.tsx
├── App.tsx
└── main.tsx
```

## Completion Report

- **what_was_done**: Produced complete architecture design: system context, component architecture with interfaces, data flow, unified schema, technology stack with rationale, theme system, error states, mock data strategy, dependency map, and project structure
- **key_decisions**: [(1) Adapter pattern for data normalization — extensible, testable, (2) Plain rule objects for alert engine — no DSL overhead for 3 rules, (3) Zustand over Redux — simpler subscription model for real-time data, (4) Client-side mock WS — enables Demo without backend, (5) CSS Variables for theming — zero runtime cost, (6) Leaflet over Mapbox — no API key needed]
- **handoff_focus**: UI nodes should implement components per the component tree; senior-frontend should follow the project structure and interface contracts; caveman already flagged mock data generator interface — addressed in section 4.4
- **open_questions**: None blocking
- **known_constraints**: Demo is client-side only; all mock data generated in browser; production would separate WS server, time-series DB, and auth
- **confidence_differential**: 0.92
