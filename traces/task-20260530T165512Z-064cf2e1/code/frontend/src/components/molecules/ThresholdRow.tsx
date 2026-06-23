import Slider from '@/components/atoms/Slider';

interface ThresholdRowProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit: string;
  lowIsBad?: boolean;
}

export default function ThresholdRow({ label, value, onChange, min, max, step, unit, lowIsBad }: ThresholdRowProps) {
  return (
    <div className="py-2">
      <Slider value={value} onChange={onChange} min={min} max={max} step={step} label={label} unit={unit} />
      <div className="flex justify-between mt-1">
        <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>
          {min}{unit}
        </span>
        <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>
          {max}{unit}
        </span>
      </div>
    </div>
  );
}
