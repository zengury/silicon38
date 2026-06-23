import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@/components/atoms/Button';
import ThresholdRow from '@/components/molecules/ThresholdRow';
import Select from '@/components/atoms/Select';
import { useRobotContext } from '@/contexts/RobotContext';

export default function ConfigPanel() {
  const { t } = useTranslation();
  const { selectedRobotId } = useRobotContext();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [thresholds, setThresholds] = useState({
    batteryLowPercent: 20,
    jointTemperatureHighCelsius: 80,
    cpuTemperatureHighCelsius: 85,
    networkLatencyHighMs: 500,
    tiltAngleDegrees: 45,
  });

  const [samplingMs, setSamplingMs] = useState(1000);
  const [reconnect, setReconnect] = useState({ maxRetries: 5, baseDelayMs: 1000, backoffMultiplier: 2 });

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    // Simulate API call
    await new Promise((r) => setTimeout(r, 800));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  if (!selectedRobotId) {
    return (
      <div className="card flex items-center justify-center p-8">
        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>选择机器人后配置</p>
      </div>
    );
  }

  return (
    <div className="card flex flex-col" role="region" aria-label={t('config.title')}>
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
          {t('config.title')} — <span className="font-mono">{selectedRobotId}</span>
        </h3>
        <div className="flex items-center gap-2">
          {saved && (
            <span className="text-xs font-medium" style={{ color: 'var(--status-online)' }}>
              {t('config.saved')} ✓
            </span>
          )}
          <Button
            size="sm"
            onClick={handleSave}
            loading={saving}
            disabled={saving}
          >
            {saving ? t('config.saving') : t('config.save')}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Alert Thresholds */}
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('config.alertThresholds')}
          </h4>
          <div className="space-y-1">
            <ThresholdRow
              label={t('config.batteryLowThreshold')}
              value={thresholds.batteryLowPercent}
              onChange={(v) => setThresholds({ ...thresholds, batteryLowPercent: v })}
              min={5} max={50} unit="%"
            />
            <ThresholdRow
              label={t('config.jointTempHighThreshold')}
              value={thresholds.jointTemperatureHighCelsius}
              onChange={(v) => setThresholds({ ...thresholds, jointTemperatureHighCelsius: v })}
              min={50} max={120} unit="°C"
            />
            <ThresholdRow
              label={t('config.cpuTempHighThreshold')}
              value={thresholds.cpuTemperatureHighCelsius}
              onChange={(v) => setThresholds({ ...thresholds, cpuTemperatureHighCelsius: v })}
              min={60} max={110} unit="°C"
            />
            <ThresholdRow
              label={t('config.networkLatencyHighThreshold')}
              value={thresholds.networkLatencyHighMs}
              onChange={(v) => setThresholds({ ...thresholds, networkLatencyHighMs: v })}
              min={100} max={2000} step={50} unit="ms"
            />
            <ThresholdRow
              label={t('config.tiltAngleThreshold')}
              value={thresholds.tiltAngleDegrees}
              onChange={(v) => setThresholds({ ...thresholds, tiltAngleDegrees: v })}
              min={10} max={90} unit="°"
            />
          </div>
        </section>

        {/* Sampling Frequency */}
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('config.samplingFrequency')}
          </h4>
          <Select
            value={String(samplingMs)}
            onChange={(e) => setSamplingMs(Number(e.target.value))}
            options={[
              { value: '1000', label: `1 ${t('config.samplesPerSecond')}` },
              { value: '2000', label: '0.5 (2s)' },
              { value: '5000', label: '0.2 (5s)' },
              { value: '10000', label: '0.1 (10s)' },
              { value: '30000', label: '30s' },
            ]}
          />
        </section>

        {/* Reconnect Strategy */}
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('config.reconnectStrategy')}
          </h4>
          <ThresholdRow
            label={t('config.maxRetries')}
            value={reconnect.maxRetries}
            onChange={(v) => setReconnect({ ...reconnect, maxRetries: v })}
            min={1} max={20} unit=""
          />
          <ThresholdRow
            label={t('config.baseDelay')}
            value={reconnect.baseDelayMs}
            onChange={(v) => setReconnect({ ...reconnect, baseDelayMs: v })}
            min={100} max={10000} step={100} unit="ms"
          />
          <ThresholdRow
            label={t('config.backoffMultiplier')}
            value={reconnect.backoffMultiplier}
            onChange={(v) => setReconnect({ ...reconnect, backoffMultiplier: v })}
            min={1} max={5} step={0.5} unit="x"
          />
        </section>
      </div>
    </div>
  );
}
