import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import Badge from '@/components/atoms/Badge';
import Button from '@/components/atoms/Button';
import { getSeverityColor, formatDate } from '@/lib/mockData';
import type { AlertSeverity, Alert } from '@/types';

const severityVariant: Record<AlertSeverity, 'error' | 'warning' | 'info'> = {
  critical: 'error',
  warning: 'warning',
  info: 'info',
};

export default function AlertListPanel() {
  const { t } = useTranslation();
  const { alerts, dispatch } = useRobotContext();
  const [filter, setFilter] = useState<'all' | 'active' | 'acknowledged'>('all');

  const filtered = alerts.filter((a) => {
    if (filter === 'active') return !a.acknowledgedAt;
    if (filter === 'acknowledged') return !!a.acknowledgedAt;
    return true;
  });

  function handleAcknowledge(alert: Alert) {
    dispatch({ type: 'ACKNOWLEDGE_ALERT', alertId: alert.alertId, userId: 'current-user' });
  }

  const tabs = [
    { key: 'all', label: t('alerts.allAlerts') },
    { key: 'active', label: t('alerts.active') },
    { key: 'acknowledged', label: t('alerts.acknowledged') },
  ] as const;

  return (
    <div className="card flex flex-col h-full" role="region" aria-label={t('alerts.title')}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{t('alerts.title')}</h3>
        <Badge variant="error">{alerts.filter((a) => !a.acknowledgedAt).length}</Badge>
      </div>

      {/* Filter tabs */}
      <div className="flex border-b" style={{ borderColor: 'var(--border-light)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className="flex-1 py-2 text-xs font-medium transition-colors border-b-2"
            style={{
              color: filter === tab.key ? 'var(--text-link)' : 'var(--text-tertiary)',
              borderColor: filter === tab.key ? '#2563EB' : 'transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-sm" style={{ color: 'var(--text-tertiary)' }}>
            {t('alerts.noAlerts')}
          </div>
        ) : (
          filtered.map((alert) => (
            <div
              key={alert.alertId}
              className="flex items-start gap-3 px-4 py-3 border-b transition-colors hover:bg-[var(--bg-hover)]"
              style={{
                borderColor: 'var(--border-light)',
                borderLeft: `3px solid ${getSeverityColor(alert.severity)}`,
                opacity: alert.acknowledgedAt ? 0.6 : 1,
              }}
            >
              {/* Severity dot */}
              <span
                className="flex-shrink-0 mt-1 rounded-full"
                style={{ width: 8, height: 8, backgroundColor: getSeverityColor(alert.severity) }}
                aria-hidden="true"
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {alert.robotId}
                  </span>
                  <Badge variant={severityVariant[alert.severity]} size="sm">
                    {t(`alerts.severity.${alert.severity}`)}
                  </Badge>
                </div>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {alert.message}
                </p>
                <p className="text-[10px] mt-1" style={{ color: 'var(--text-tertiary)' }}>
                  {formatDate(alert.triggeredAt)}
                </p>
              </div>

              {!alert.acknowledgedAt && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAcknowledge(alert)}
                  className="flex-shrink-0"
                  style={{ fontSize: 11, padding: '2px 8px', height: 28 }}
                >
                  {t('alerts.acknowledge')}
                </Button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
