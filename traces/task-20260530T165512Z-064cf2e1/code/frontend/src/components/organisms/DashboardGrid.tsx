import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import BatteryRingChart from '@/components/organisms/BatteryRingChart';
import CpuTempLineChart from '@/components/organisms/CpuTempLineChart';
import GeoHeatmap from '@/components/organisms/GeoHeatmap';
import AlertListPanel from '@/components/organisms/AlertListPanel';
import CollaborationPanel from '@/components/organisms/CollaborationPanel';
import ConfigPanel from '@/components/organisms/ConfigPanel';

export default function DashboardGrid() {
  const { t } = useTranslation();
  const { robots, selectedRobotId } = useRobotContext();

  const onlineCount = useMemo(() => robots.filter((r) => r.status === 'online').length, [robots]);
  const errorCount = useMemo(() => robots.filter((r) => r.status === 'error').length, [robots]);
  const warningCount = useMemo(() => robots.filter((r) => r.status === 'warning').length, [robots]);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {/* Summary bar */}
      <div className="flex items-center gap-6 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{t('common.fleet')}:</span>
          <span className="metric-value text-base">{robots.length}</span>
          <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{t('common.robots')}</span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-online)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>{t('status.online')}: {onlineCount}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-warning)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>{t('status.warning')}: {warningCount}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-error)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>{t('status.error')}: {errorCount}</span>
          </span>
        </div>
      </div>

      {/* Charts row — Fleet overview (Variant A style grid) */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <BatteryRingChart robots={robots} />
        <CpuTempLineChart />
        <GeoHeatmap robots={robots} />
      </div>

      {/* Bottom row — Alerts + Collaboration + Config (Variant B detail area) */}
      <div className="grid grid-cols-3 gap-4" style={{ minHeight: 420 }}>
        <AlertListPanel />
        {selectedRobotId ? (
          <>
            <CollaborationPanel />
            <ConfigPanel />
          </>
        ) : (
          <>
            <div className="card flex items-center justify-center" style={{ color: 'var(--text-tertiary)' }}>
              <p className="text-sm">选择机器人后协作</p>
            </div>
            <div className="card flex items-center justify-center" style={{ color: 'var(--text-tertiary)' }}>
              <p className="text-sm">选择机器人后配置</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
