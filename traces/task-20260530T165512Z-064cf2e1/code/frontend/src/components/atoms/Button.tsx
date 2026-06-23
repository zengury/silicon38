import { type ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantClasses: Record<string, string> = {
  primary: 'text-white hover:opacity-90',
  secondary: 'text-[var(--text-primary)] hover:opacity-90',
  ghost: 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]',
  danger: 'text-white hover:opacity-90',
};

const sizeHeights = { sm: 32, md: 40, lg: 48 };

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, icon, children, className = '', style, disabled, ...props }, ref) => {
    const bgColor =
      variant === 'primary'
        ? '#2563EB'
        : variant === 'danger'
          ? '#EF4444'
          : variant === 'secondary'
            ? 'var(--bg-hover)'
            : 'transparent';

    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all
          focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--border-focus)]
          active:scale-[0.98] ${variantClasses[variant]} ${className}`}
        style={{
          backgroundColor: bgColor,
          height: sizeHeights[size],
          paddingLeft: size === 'sm' ? 12 : size === 'md' ? 16 : 20,
          paddingRight: size === 'sm' ? 12 : size === 'md' ? 16 : 20,
          fontSize: 14,
          opacity: disabled || loading ? 0.5 : 1,
          cursor: disabled || loading ? 'not-allowed' : 'pointer',
          ...style,
        }}
        disabled={disabled || loading}
        aria-disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <svg className="animate-spin" width={16} height={16} viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
            <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
          </svg>
        ) : icon ? (
          <span aria-hidden="true">{icon}</span>
        ) : null}
        {children}
      </button>
    );
  },
);

Button.displayName = 'Button';
export default Button;
