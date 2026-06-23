import type { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
}

export default function StatCard({ title, children, className = '', actions, loading, error, onRetry }: StatCardProps) {
  return (
    <div
      className={`card p-4 flex flex-col gap-3 ${className}`}
      role="region"
      aria-label={title}
      aria-busy={loading}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</h3>
        {actions}
      </div>
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--border-default)] border-t-primary" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center gap-2 py-4 text-center">
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>加载失败</span>
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
      ) : (
        children
      )}
    </div>
  );
}
