interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export default function Toggle({ checked, onChange, label, disabled }: ToggleProps) {
  return (
    <label
      className={`inline-flex items-center gap-3 ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      {label && <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className="relative inline-flex h-5 w-9 rounded-full transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--border-focus)]"
        style={{
          backgroundColor: checked ? '#2563EB' : 'var(--border-default)',
        }}
      >
        <span
          className="inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-200"
          style={{
            transform: checked ? 'translateX(18px)' : 'translateX(2px)',
            marginTop: 2,
          }}
        />
      </button>
    </label>
  );
}
