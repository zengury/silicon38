import { AlertEngine, AlertRule, AlertEvent } from '../../src/alert/engine';
import type { NormalizedTelemetry } from '../../src/adapters/types';

function makeTelemetry(overrides: Partial<NormalizedTelemetry> = {}): NormalizedTelemetry {
  return {
    robot_id: 'r-test',
    battery_level: 50,
    joint_temperatures: { shoulder: 40, elbow: 35 },
    cpu_usage: 30,
    network_latency: 10,
    task: 'idle',
    gps: { latitude: 0, longitude: 0 },
    status: 'online',
    timestamp: '2026-05-30T10:00:00.000Z',
    ...overrides,
  };
}

function makeRule(overrides: Partial<AlertRule> = {}): AlertRule {
  return {
    id: 1,
    name: 'Low Battery',
    metric: 'battery_level',
    operator: '<',
    threshold: 20,
    targetValue: null,
    severity: 'warning',
    enabled: true,
    cooldownS: 300,
    escalateAfterS: null,
    ...overrides,
  };
}

describe('AlertEngine', () => {
  let engine: AlertEngine;

  beforeEach(() => {
    engine = new AlertEngine();
    engine.resetCooldowns();
  });

  describe('numeric rule evaluation', () => {
    it('fires when battery is below threshold', () => {
      const rule = makeRule({ metric: 'battery_level', operator: '<', threshold: 20 });
      const telemetry = makeTelemetry({ battery_level: 15 });
      const result = engine.evaluate(rule, telemetry);
      expect(result).not.toBeNull();
      expect(result!.severity).toBe('warning');
      expect(result!.robotId).toBe('r-test');
      expect(result!.message).toContain('Low Battery');
    });

    it('does not fire when battery is above threshold', () => {
      const rule = makeRule({ metric: 'battery_level', operator: '<', threshold: 20 });
      const telemetry = makeTelemetry({ battery_level: 85 });
      expect(engine.evaluate(rule, telemetry)).toBeNull();
    });

    it('fires when CPU is above threshold', () => {
      const rule = makeRule({ metric: 'cpu_usage', operator: '>', threshold: 90 });
      const telemetry = makeTelemetry({ cpu_usage: 95 });
      expect(engine.evaluate(rule, telemetry)).not.toBeNull();
    });

    it('does not fire when rule is disabled', () => {
      const rule = makeRule({ enabled: false });
      const telemetry = makeTelemetry({ battery_level: 15 });
      expect(engine.evaluate(rule, telemetry)).toBeNull();
    });
  });

  describe('status rule evaluation', () => {
    it('fires when status matches target', () => {
      const rule: AlertRule = {
        id: 2,
        name: 'Robot Error',
        metric: 'status',
        operator: '==',
        threshold: null,
        targetValue: 'error',
        severity: 'critical',
        enabled: true,
        cooldownS: 0,
        escalateAfterS: null,
      };
      const telemetry = makeTelemetry({ status: 'error' });
      const result = engine.evaluate(rule, telemetry);
      expect(result).not.toBeNull();
      expect(result!.severity).toBe('critical');
    });

    it('does not fire when status does not match', () => {
      const rule: AlertRule = {
        id: 2,
        name: 'Robot Error',
        metric: 'status',
        operator: '==',
        threshold: null,
        targetValue: 'error',
        severity: 'critical',
        enabled: true,
        cooldownS: 0,
        escalateAfterS: null,
      };
      const okTelemetry = makeTelemetry({ status: 'online' as const });
      expect(engine.evaluate(rule, okTelemetry)).toBeNull();
    });
  });

  describe('joint temperature max', () => {
    it('fires when max joint temperature exceeds threshold', () => {
      const rule: AlertRule = {
        id: 3,
        name: 'Joint Overheat',
        metric: 'joint_temperatures_max',
        operator: '>',
        threshold: 80,
        targetValue: null,
        severity: 'critical',
        enabled: true,
        cooldownS: 0,
        escalateAfterS: null,
      };
      const telemetry = makeTelemetry({
        joint_temperatures: { shoulder: 90, elbow: 70, wrist: 60 },
      });
      const result = engine.evaluate(rule, telemetry);
      expect(result).not.toBeNull();
      expect(result!.message).toContain('Overheat');
    });

    it('does not fire when all joint temps are below threshold', () => {
      const rule: AlertRule = {
        id: 3,
        name: 'Joint Overheat',
        metric: 'joint_temperatures_max',
        operator: '>',
        threshold: 80,
        targetValue: null,
        severity: 'critical',
        enabled: true,
        cooldownS: 0,
        escalateAfterS: null,
      };
      const telemetry = makeTelemetry({
        joint_temperatures: { shoulder: 40, elbow: 50 },
      });
      expect(engine.evaluate(rule, telemetry)).toBeNull();
    });
  });

  describe('cooldown', () => {
    it('does not re-fire within cooldown period', () => {
      const rule = makeRule({
        metric: 'battery_level',
        operator: '<',
        threshold: 20,
        cooldownS: 300,
      });
      const telemetry = makeTelemetry({ battery_level: 15 });

      // First fire
      expect(engine.evaluate(rule, telemetry)).not.toBeNull();
      // Second fire within cooldown
      expect(engine.evaluate(rule, telemetry)).toBeNull();
    });
  });

  describe('evaluateAll', () => {
    it('evaluates multiple rules and returns all fired', () => {
      const rules: AlertRule[] = [
        makeRule({ id: 1, metric: 'battery_level', operator: '<', threshold: 20 }),
        makeRule({ id: 2, metric: 'cpu_usage', operator: '>', threshold: 90 }),
      ];

      const telemetry = makeTelemetry({ battery_level: 10, cpu_usage: 95 });

      const results = engine.evaluateAll(rules, telemetry);
      expect(results).toHaveLength(2);
    });

    it('returns empty array when no rules fire', () => {
      const rules: AlertRule[] = [
        makeRule({ id: 1, metric: 'battery_level', operator: '<', threshold: 5 }),
      ];
      const telemetry = makeTelemetry({ battery_level: 50 });
      expect(engine.evaluateAll(rules, telemetry)).toHaveLength(0);
    });
  });
});
