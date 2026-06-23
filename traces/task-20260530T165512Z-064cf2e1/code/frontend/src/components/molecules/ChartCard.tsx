import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  loading?: boolean;
  error?: boolean;
  empty?: boolean;
  onRetry?: () => void;
  onRefresh?: () => void;
  collapsed?: boolean;
  collapseHeight?: number;
}

export default function ChartCard({
  title,
  children,
  className = '',
  actions,
  loading,
  error,
  empty,
  onRetry,
  onRefresh,
  collapsed,
  collapseHeight = 48,
}: ChartCardProps) {
  return (
    <div
      className={`card ${className}`}
      role="region"
      aria-label={title}
      aria-busy={loading}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</h3>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors"
              aria-label="刷新"
              title="刷新"
            >
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M1 4v6h6M23 20v-6h-6" />
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
              </svg>
            </button>
          )}
          {actions}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: collapsed ? collapseHeight : 320 }}>
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--border-default)] border-t-primary" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center gap-3" style={{ height: collapsed ? collapseHeight : 320 }}>
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>数据加载失败</span>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs font-medium px-3 py-1 rounded"
              style={{ color: 'var(--text-link)' }}
            >
              重试
            </button>
          )}
        </div>
      ) : empty ? (
        <div className="flex items-center justify-center" style={{ height: collapsed ? collapseHeight : 320 }}>
          <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>暂无数据</span>
        </div>
      ) : collapsed ? (
        <div style={{ height: collapseHeight }}>{children}</div>
      ) : (
        <div style={{ height: 320 }}>{children}</div>
      )}
    </div>
  );
}
