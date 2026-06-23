import { getStatusColor } from '@/lib/mockData';
import type { RobotStatus } from '@/types';

interface StatusIndicatorProps {
  status: RobotStatus;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  pulsing?: boolean;
}

const sizeMap = { sm: 8, md: 10, lg: 12 };

export default function StatusIndicator({ status, size = 'md', label, pulsing }: StatusIndicatorProps) {
  const s = sizeMap[size];
  const color = getStatusColor(status);
  return (
    <span className="inline-flex items-center gap-2" role="status" aria-label={label || status}>
      <span
        className={`inline-block rounded-full ${pulsing ? 'animate-pulse-dot' : ''}`}
        style={{ width: s, height: s, backgroundColor: color }}
      />
      {label && <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{label}</span>}
    </span>
  );
}
