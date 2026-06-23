import { type ButtonHTMLAttributes } from 'react';

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function IconButton({ label, size = 'md', className = '', ...props }: IconButtonProps) {
  const s = size === 'sm' ? 32 : size === 'md' ? 40 : 48;

  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center rounded-lg transition-all
        hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-offset-2
        focus-visible:outline-[var(--border-focus)] active:scale-[0.95] ${className}`}
      style={{ width: s, height: s, minWidth: s, minHeight: s }}
      aria-label={label}
      title={label}
      {...props}
    />
  );
}
