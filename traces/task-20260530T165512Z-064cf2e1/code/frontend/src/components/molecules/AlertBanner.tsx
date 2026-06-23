import { useEffect, useState } from 'react';
import type { AlertSeverity } from '@/types';
import { getSeverityColor } from '@/lib/mockData';

interface AlertBannerProps {
  message: string;
  severity: AlertSeverity;
  robotId?: string;
  onAcknowledge?: () => void;
  onDismiss?: () => void;
  onViewDetails?: () => void;
  autoDismissMs?: number;
}

export default function AlertBanner({
  message,
  severity,
  robotId,
  onAcknowledge,
  onDismiss,
  onViewDetails,
  autoDismissMs,
}: AlertBannerProps) {
  const [visible, setVisible] = useState(true);
  const [dismissing, setDismissing] = useState(false);

  const bgColor =
    severity === 'critical' ? '#FEE2E2' : severity === 'warning' ? '#FEF3C7' : '#DBEAFE';
  const borderColor = getSeverityColor(severity);
  const textColor =
    severity === 'critical' ? '#991B1B' : severity === 'warning' ? '#92400E' : '#1E40AF';

  useEffect(() => {
    if (autoDismissMs) {
      const t = setTimeout(() => handleDismiss(), autoDismissMs);
      return () => clearTimeout(t);
    }
  }, [autoDismissMs]);

  function handleDismiss() {
    setDismissing(true);
    setTimeout(() => {
      setVisible(false);
      onDismiss?.();
    }, 150);
  }

  if (!visible) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`flex items-center gap-3 px-4 py-3 border-l-4 rounded-r-lg animate-slide-down
        ${dismissing ? 'opacity-0 transition-opacity duration-150' : ''}`}
      style={{ backgroundColor: bgColor, borderColor, color: textColor }}
    >
      {/* Severity icon */}
      <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        {severity === 'critical' ? (
          <path d="M12 2L2 22h20L12 2zm0 4v6m0 4h.01" />
        ) : severity === 'warning' ? (
          <>
            <path d="M12 2L2 22h20L12 2z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </>
        ) : (
          <>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </>
        )}
      </svg>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">
          {robotId && <span className="font-mono mr-2">{robotId}</span>}
          {message}
        </p>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {onViewDetails && (
          <button onClick={onViewDetails} className="text-xs underline hover:opacity-80">
            查看详情
          </button>
        )}
        {onAcknowledge && (
          <button
            onClick={onAcknowledge}
            className="text-xs px-2 py-1 rounded border font-medium hover:opacity-80"
            style={{ borderColor: 'currentColor' }}
          >
            确认
          </button>
        )}
        <button onClick={handleDismiss} className="p-1 rounded hover:bg-black/10" aria-label="关闭">
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
