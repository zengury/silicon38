import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import Badge from '@/components/atoms/Badge';
import { getSeverityColor, formatDate } from '@/lib/mockData';
import type { AlertSeverity, Alert } from '@/types';

const severityVariant: Record<AlertSeverity, 'error' | 'warning' | 'info'> = {
  critical: 'error',
  warning: 'warning',
  info: 'info',
};

/* Merge alerts and comments into a single chronological feed */
interface TimelineEvent {
  id: string;
  type: 'alert' | 'comment' | 'status_change';
  timestamp: string;
  robotId: string;
  content: string;
  severity?: AlertSeverity;
  author?: string;
}

export default function TimelineDrawer() {
  const { t } = useTranslation();
  const { alerts, comments, toggleTimeline } = useRobotContext();

  // Build timeline events from alerts + comments
  const events: TimelineEvent[] = [
    ...alerts.map((a) => ({
      id: a.alertId,
      type: 'alert' as const,
      timestamp: a.triggeredAt,
      robotId: a.robotId,
      content: a.message,
      severity: a.severity,
      acknowledged: !!a.acknowledgedAt,
    })),
    ...Object.values(comments).flat().map((c) => ({
      id: c.commentId,
      type: 'comment' as const,
      timestamp: c.createdAt,
      robotId: c.robotId,
      content: c.content,
      author: c.authorName,
    })),
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <div
      className="fixed right-0 top-0 h-full w-80 shadow-2xl border-l z-[var(--z-overlay)] animate-slide-down flex flex-col"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-light)',
      }}
      role="complementary"
      aria-label={t('common.timeline')}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
          {t('common.timeline')}
        </h3>
        <button
          onClick={toggleTimeline}
          className="p-1 rounded hover:bg-[var(--bg-hover)]"
          aria-label={t('common.close')}
        >
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-sm" style={{ color: 'var(--text-tertiary)' }}>
            {t('common.noData')}
          </div>
        ) : (
          <div className="relative pl-8 pr-4 py-4">
            {/* Vertical line */}
            <div
              className="absolute left-5 top-0 bottom-0 w-px"
              style={{ backgroundColor: 'var(--border-light)' }}
            />

            {events.map((event) => (
              <div key={event.id} className="relative mb-4 last:mb-0">
                {/* Timeline dot */}
                <div
                  className="absolute -left-5 mt-1 rounded-full border-2"
                  style={{
                    width: 10,
                    height: 10,
                    backgroundColor: 'var(--bg-card)',
                    borderColor:
                      event.type === 'alert'
                        ? getSeverityColor(event.severity || 'info')
                        : event.type === 'comment'
                          ? '#8B5CF6'
                          : '#2563EB',
                  }}
                />

                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-medium" style={{ color: 'var(--text-link)' }}>
                      {event.robotId}
                    </span>
                    {event.type === 'alert' && event.severity && (
                      <Badge variant={severityVariant[event.severity]} size="sm">
                        {t(`alerts.severity.${event.severity}`)}
                      </Badge>
                    )}
                    {event.type === 'comment' && (
                      <Badge size="sm">留言</Badge>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                    {event.content}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>
                      {formatDate(event.timestamp)}
                    </span>
                    {event.author && (
                      <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>
                        — {event.author}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
