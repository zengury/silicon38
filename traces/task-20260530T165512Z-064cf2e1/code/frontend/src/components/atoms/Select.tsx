import { type SelectHTMLAttributes } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export default function Select({ label, options, className = '', ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </label>
      )}
      <select
        className={`rounded-lg border px-3 py-2 text-sm
          bg-[var(--bg-input)] border-[var(--border-default)]
          text-[var(--text-primary)] focus:border-[var(--border-focus)] focus:ring-1 focus:ring-[var(--border-focus)]
          outline-none transition-colors ${className}`}
        style={{ height: 40 }}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
