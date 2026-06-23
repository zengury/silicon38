import { useMemo } from 'react';
import type { ReactNode } from 'react';

interface MetricValueProps {
  value: number;
  label: string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  alert?: boolean;
  precision?: number;
  className?: string;
  icon?: ReactNode;
}

export default function MetricValue({
  value,
  label,
  unit = '',
  trend,
  trendValue,
  alert,
  precision = 1,
  className = '',
  icon,
}: MetricValueProps) {
  const trendArrow = useMemo(() => {
    if (!trend || trend === 'stable') return null;
    return trend === 'up' ? '↑' : '↓';
  }, [trend]);

  const trendColor = trend === 'up' ? 'var(--status-warning)' : 'var(--status-online)';

  return (
    <dl
      className={`flex flex-col gap-1 ${className}`}
      style={{
        color: alert ? 'var(--status-error)' : undefined,
      }}
    >
      <dt className="text-xs font-medium flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
        {icon && <span className="flex-shrink-0">{icon}</span>}
        {label}
      </dt>
      <dd className="metric-value flex items-baseline gap-1">
        <span>{value.toFixed(precision)}</span>
        {unit && (
          <span className="text-sm font-normal" style={{ color: 'var(--text-tertiary)' }}>
            {unit}
          </span>
        )}
      </dd>
      {trendValue && (
        <dd className="text-xs flex items-center gap-1" style={{ color: trendColor }}>
          <span aria-label={trend === 'up' ? '上升' : '下降'}>{trendArrow}</span>
          <span>{trendValue}</span>
        </dd>
      )}
    </dl>
  );
}
