interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
}

const variantStyles: Record<string, { bg: string; text: string }> = {
  default: { bg: '#E5E7EB', text: '#374151' },
  success: { bg: '#D1FAE5', text: '#065F46' },
  warning: { bg: '#FEF3C7', text: '#92400E' },
  error: { bg: '#FEE2E2', text: '#991B1B' },
  info: { bg: '#DBEAFE', text: '#1E40AF' },
};

export default function Badge({ children, variant = 'default', size = 'sm' }: BadgeProps) {
  const s = variantStyles[variant];
  const px = size === 'sm' ? '6px' : '10px';
  const py = size === 'sm' ? '1px' : '3px';

  return (
    <span
      className="inline-flex items-center rounded-full font-medium"
      style={{
        backgroundColor: s.bg,
        color: s.text,
        fontSize: size === 'sm' ? 11 : 12,
        padding: `${py} ${px}`,
        lineHeight: 1.4,
      }}
    >
      {children}
    </span>
  );
}
