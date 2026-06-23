import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import type { RobotTelemetry, Alert, Comment, RobotStatus, SimulatedRobot } from '@/types';
import { generateMockRobots, simulateTelemetryUpdate, generateMockAlerts, generateMockHistory } from '@/lib/mockData';

/* ========== State Shape ========== */
interface RobotState {
  robots: SimulatedRobot[];
  selectedRobotId: string | null;
  alerts: Alert[];
  comments: Record<string, Comment[]>; // robotId → comments
  history: Record<string, { timestamp: string; battery: number; cpu: number; temp: number }[]>;
  fleetOverviewExpanded: boolean;
  timelineOpen: boolean;
  viewMode: 'overview' | 'detail' | 'timeline';
}

type RobotAction =
  | { type: 'TELEMETRY_UPDATE'; robotId: string; telemetry: RobotTelemetry }
  | { type: 'SELECT_ROBOT'; robotId: string }
  | { type: 'DESELECT_ROBOT' }
  | { type: 'ADD_ALERT'; alert: Alert }
  | { type: 'ACKNOWLEDGE_ALERT'; alertId: string; userId: string }
  | { type: 'ADD_COMMENT'; robotId: string; comment: Comment }
  | { type: 'MARK_HANDLING'; robotId: string; userId: string; isHandling: boolean }
  | { type: 'TOGGLE_FLEET_OVERVIEW' }
  | { type: 'TOGGLE_TIMELINE' }
  | { type: 'SET_VIEW_MODE'; mode: 'overview' | 'detail' | 'timeline' }
  | { type: 'UPDATE_ROBOT_STATUS'; robotId: string; status: RobotStatus };

function robotReducer(state: RobotState, action: RobotAction): RobotState {
  switch (action.type) {
    case 'TELEMETRY_UPDATE': {
      const updatedRobots = state.robots.map((r) => {
        if (r.robotId !== action.robotId) return r;
        const t = action.telemetry;
        return {
          ...r,
          battery: t.battery,
          joints: t.joints,
          cpu: t.cpu,
          network: t.network,
          task: t.task,
          location: t.location,
          lastSeenAt: t.timestamp,
          status: t.joints.some((j) => !j.isConnected)
            ? 'error'
            : t.battery.levelPercent < 20
              ? 'warning'
              : 'online',
        } as SimulatedRobot;
      });
      return { ...state, robots: updatedRobots };
    }
    case 'SELECT_ROBOT':
      return { ...state, selectedRobotId: action.robotId, viewMode: 'detail' };
    case 'DESELECT_ROBOT':
      return { ...state, selectedRobotId: null, viewMode: 'overview' };
    case 'ADD_ALERT':
      return { ...state, alerts: [action.alert, ...state.alerts].slice(0, 200) };
    case 'ACKNOWLEDGE_ALERT':
      return {
        ...state,
        alerts: state.alerts.map((a) =>
          a.alertId === action.alertId
            ? { ...a, acknowledgedAt: new Date().toISOString(), acknowledgedBy: action.userId }
            : a,
        ),
      };
    case 'ADD_COMMENT':
      return {
        ...state,
        comments: {
          ...state.comments,
          [action.robotId]: [...(state.comments[action.robotId] || []), action.comment],
        },
      };
    case 'MARK_HANDLING':
      return {
        ...state,
        comments: {
          ...state.comments,
          [action.robotId]: [
            ...(state.comments[action.robotId] || []),
            {
              commentId: `mark-${Date.now()}`,
              robotId: action.robotId,
              authorId: action.userId,
              authorName: 'Current User',
              content: action.isHandling ? '🚧 正在处理此机器人' : '✅ 已完成处理',
              mentions: [],
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
          ],
        },
      };
    case 'TOGGLE_FLEET_OVERVIEW':
      return { ...state, fleetOverviewExpanded: !state.fleetOverviewExpanded };
    case 'TOGGLE_TIMELINE':
      return { ...state, timelineOpen: !state.timelineOpen };
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.mode };
    case 'UPDATE_ROBOT_STATUS':
      return {
        ...state,
        robots: state.robots.map((r) =>
          r.robotId === action.robotId ? { ...r, status: action.status } : r,
        ),
      };
    default:
      return state;
  }
}

interface RobotContextValue extends RobotState {
  dispatch: React.Dispatch<RobotAction>;
  selectRobot: (id: string) => void;
  deselectRobot: () => void;
  toggleFleetOverview: () => void;
  toggleTimeline: () => void;
}

const RobotContext = createContext<RobotContextValue | null>(null);

export function RobotProvider({ children }: { children: React.ReactNode }) {
  const initialState: RobotState = {
    robots: generateMockRobots(10),
    selectedRobotId: null,
    alerts: generateMockAlerts(5),
    comments: {},
    history: generateMockHistory(10),
    fleetOverviewExpanded: true,
    timelineOpen: false,
    viewMode: 'overview',
  };

  const [state, dispatch] = useReducer(robotReducer, initialState);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Simulate real-time telemetry updates every 3 seconds
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      state.robots.forEach((robot) => {
        const updated = simulateTelemetryUpdate(robot);
        dispatch({ type: 'TELEMETRY_UPDATE', robotId: robot.robotId, telemetry: updated });
      });
    }, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const selectRobot = useCallback((id: string) => dispatch({ type: 'SELECT_ROBOT', robotId: id }), []);
  const deselectRobot = useCallback(() => dispatch({ type: 'DESELECT_ROBOT' }), []);
  const toggleFleetOverview = useCallback(() => dispatch({ type: 'TOGGLE_FLEET_OVERVIEW' }), []);
  const toggleTimeline = useCallback(() => dispatch({ type: 'TOGGLE_TIMELINE' }), []);

  return (
    <RobotContext.Provider
      value={{ ...state, dispatch, selectRobot, deselectRobot, toggleFleetOverview, toggleTimeline }}
    >
      {children}
    </RobotContext.Provider>
  );
}

export function useRobotContext() {
  const ctx = useContext(RobotContext);
  if (!ctx) throw new Error('useRobotContext must be used within RobotProvider');
  return ctx;
}
