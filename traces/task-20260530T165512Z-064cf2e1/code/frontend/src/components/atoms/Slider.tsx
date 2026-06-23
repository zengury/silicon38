interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  label?: string;
  unit?: string;
}

export default function Slider({ value, onChange, min, max, step = 1, label, unit }: SliderProps) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        {label && <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>}
        <span className="text-xs font-mono tabular-nums" style={{ color: 'var(--text-primary)' }}>
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--border-focus)]"
        style={{
          background: `linear-gradient(to right, #2563EB ${pct}%, var(--border-light) ${pct}%)`,
          accentColor: '#2563EB',
        }}
      />
    </div>
  );
}
