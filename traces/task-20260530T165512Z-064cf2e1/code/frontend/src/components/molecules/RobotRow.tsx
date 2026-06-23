import StatusIndicator from '@/components/atoms/StatusIndicator';
import type { SimulatedRobot } from '@/types';

interface RobotRowProps {
  robot: SimulatedRobot;
  selected?: boolean;
  onClick?: () => void;
}

export default function RobotRow({ robot, selected, onClick }: RobotRowProps) {
  const maxJointTemp = Math.max(...robot.joints.map((j) => j.temperatureCelsius));
  const hasDisconnected = robot.joints.some((j) => !j.isConnected);

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors
        hover:bg-[var(--bg-hover)] border-b border-[var(--border-light)]
        ${selected ? 'bg-[var(--bg-selected)]' : ''}`}
      style={{
        background: selected ? 'var(--bg-selected)' : undefined,
        outline: robot.status === 'error' ? '1px solid var(--status-error)' : undefined,
      }}
    >
      <StatusIndicator status={robot.status} size="sm" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
            {robot.robotId}
          </span>
          <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>
            {robot.model}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-0.5 text-[11px]" style={{ color: 'var(--text-secondary)' }}>
          {/* Battery mini bar */}
          <span className="flex items-center gap-1">
            <svg width={10} height={10} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
              style={{ color: robot.battery.levelPercent < 20 ? 'var(--status-error)' : 'var(--status-online)' }}>
              <rect x="1" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2" fill="none" />
              <rect x="19" y="9" width="3" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none" />
              <rect x="3" y="8" width={14 * robot.battery.levelPercent / 100} height="8" rx="1" fill="currentColor" />
            </svg>
            {robot.battery.levelPercent.toFixed(0)}%
          </span>

          {/* Joint temp */}
          <span className="flex items-center gap-0.5">
            <svg width={10} height={10} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"
              style={{ color: maxJointTemp > 80 ? 'var(--status-error)' : 'var(--status-warning)' }}>
              <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
            </svg>
            {maxJointTemp.toFixed(0)}°
          </span>

          {/* Network */}
          <span className="flex items-center gap-0.5">
            <svg width={10} height={10} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path d="M5 12.55a11 11 0 0 1 14.08 0" />
              <path d="M1.42 9a16 16 0 0 1 21.16 0" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <circle cx="12" cy="20" r="1" fill="currentColor" />
            </svg>
            {robot.network.latencyMs.toFixed(0)}ms
          </span>
        </div>
      </div>

      {/* Disconnected joint indicator */}
      {hasDisconnected && (
        <span className="flex-shrink-0" title="关节失联">
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="var(--status-error)" strokeWidth={2}>
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </span>
      )}

      <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
        style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}
        aria-hidden="true">
        <polyline points="9 18 15 12 9 6" />
      </svg>
    </button>
  );
}
