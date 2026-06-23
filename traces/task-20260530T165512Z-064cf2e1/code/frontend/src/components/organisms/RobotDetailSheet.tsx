import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import MetricValue from '@/components/atoms/MetricValue';
import StatusIndicator from '@/components/atoms/StatusIndicator';
import Badge from '@/components/atoms/Badge';
import Button from '@/components/atoms/Button';
import CpuTempLineChart from '@/components/organisms/CpuTempLineChart';

export default function RobotDetailSheet() {
  const { t } = useTranslation();
  const { robots, selectedRobotId, deselectRobot } = useRobotContext();

  const robot = robots.find((r) => r.robotId === selectedRobotId);

  if (!robot) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-tertiary)' }}>
        <div className="text-center">
          <svg width={48} height={48} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="mx-auto mb-3 opacity-30">
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <circle cx="12" cy="12" r="4" />
            <line x1="12" y1="2" x2="12" y2="6" />
            <line x1="12" y1="18" x2="12" y2="22" />
          </svg>
          <p className="text-sm">{t('common.noData')}</p>
        </div>
      </div>
    );
  }

  const maxJointTemp = Math.max(...robot.joints.map((j) => j.temperatureCelsius));
  const hasDisconnected = robot.joints.some((j) => !j.isConnected);

  return (
    <div className="flex-1 overflow-y-auto" role="region" aria-label={`${robot.robotId} 详情`}>
      {/* Robot header */}
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={deselectRobot} icon={
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <polyline points="15 18 9 12 15 6" />
            </svg>
          }>
            {t('common.back')}
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold font-mono" style={{ color: 'var(--text-primary)' }}>{robot.robotId}</h2>
              <StatusIndicator status={robot.status} label={t(`status.${robot.status}`)} />
            </div>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{robot.name} · {robot.model}</p>
          </div>
        </div>
        {robot.task && (
          <Badge variant="info">{robot.task.name} ({robot.task.progressPercent}%)</Badge>
        )}
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4 p-6">
        <div className="card p-4">
          <MetricValue
            value={robot.battery.levelPercent}
            label={t('metrics.battery')}
            unit={t('metrics.batteryUnit')}
            alert={robot.battery.levelPercent < 20}
            trend={robot.battery.levelPercent < 20 ? 'down' : 'stable'}
            trendValue={robot.battery.isCharging ? t('status.charging') : undefined}
          />
        </div>
        <div className="card p-4">
          <MetricValue
            value={maxJointTemp}
            label={t('metrics.temperature')}
            unit={t('metrics.temperatureUnit')}
            alert={maxJointTemp > 80}
            trend={maxJointTemp > 80 ? 'up' : 'stable'}
          />
        </div>
        <div className="card p-4">
          <MetricValue
            value={robot.cpu.usagePercent}
            label={t('metrics.cpu')}
            unit={t('metrics.cpuUnit')}
            alert={robot.cpu.temperatureCelsius > 85}
          />
        </div>
        <div className="card p-4">
          <MetricValue
            value={robot.network.latencyMs}
            label={t('metrics.network')}
            unit={t('metrics.networkUnit')}
            alert={robot.network.latencyMs > 500}
            trend={robot.network.latencyMs > 300 ? 'up' : 'stable'}
          />
        </div>
      </div>

      {/* Joint status and charts */}
      <div className="grid grid-cols-3 gap-4 px-6">
        {/* Joints table */}
        <div className="card">
          <div className="px-4 py-3 border-b text-sm font-semibold" style={{ borderColor: 'var(--border-light)' }}>
            关节状态
          </div>
          <div className="p-3 space-y-1">
            {robot.joints.map((joint) => (
              <div key={joint.jointId} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-[var(--bg-hover)]">
                <div className="flex items-center gap-2">
                  <StatusIndicator
                    status={joint.isConnected ? 'online' : 'error'}
                    size="sm"
                  />
                  <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                    {joint.jointId.split('-').pop()}
                  </span>
                </div>
                <span
                  className="text-xs font-mono tabular-nums"
                  style={{ color: joint.temperatureCelsius > 80 ? 'var(--status-error)' : 'var(--text-secondary)' }}
                >
                  {joint.temperatureCelsius.toFixed(1)}°C
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* History chart */}
        <div className="col-span-2">
          <CpuTempLineChart robotId={robot.robotId} compact />
        </div>
      </div>

      {/* Location */}
      <div className="px-6 py-4">
        <div className="card p-4">
          <h4 className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('metrics.location')}
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <MetricValue value={robot.location.latitude} label="纬度" precision={4} />
            <MetricValue value={robot.location.longitude} label="经度" precision={4} />
            <MetricValue value={robot.location.altitudeMeters} label={t('metrics.altitude')} unit="m" precision={1} />
          </div>
        </div>
      </div>

      {/* Spacer */}
      <div className="h-8" />
    </div>
  );
}
