import type { NormalizedTelemetry } from '../adapters/types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface AlertRule {
  id: number;
  name: string;
  metric: string;
  operator: '<' | '>' | '==' | '!=' | '>=' | '<=';
  threshold: number | null;
  targetValue: string | null;
  severity: AlertSeverity;
  enabled: boolean;
  cooldownS: number;
  escalateAfterS: number | null;
}

export interface AlertEvent {
  ruleId: number;
  robotId: string;
  metric: string;
  value: string;
  severity: AlertSeverity;
  message: string;
  firedAt: string;
}

// ---------------------------------------------------------------------------
// Rule evaluation helpers
// ---------------------------------------------------------------------------

function evaluateNumeric(
  value: number,
  operator: AlertRule['operator'],
  threshold: number,
): boolean {
  switch (operator) {
    case '<':  return value < threshold;
    case '>':  return value > threshold;
    case '<=': return value <= threshold;
    case '>=': return value >= threshold;
    case '==': return value === threshold;
    case '!=': return value !== threshold;
    default:   return false;
  }
}

function evaluateStatus(
  status: string,
  operator: AlertRule['operator'],
  target: string | null,
): boolean {
  if (target === null) return false;
  if (operator === '==') return status === target;
  if (operator === '!=') return status !== target;
  return false;
}

/** Extract a metric value from normalized telemetry. */
function getMetricValue(telemetry: NormalizedTelemetry, metric: string): number | string | null {
  switch (metric) {
    case 'battery_level':       return telemetry.battery_level;
    case 'cpu_usage':           return telemetry.cpu_usage;
    case 'network_latency':     return telemetry.network_latency;
    case 'status':              return telemetry.status;
    case 'joint_temperatures_max': {
      const temps = Object.values(telemetry.joint_temperatures);
      return temps.length > 0 ? Math.max(...temps) : null;
    }
    default: return null;
  }
}

// ---------------------------------------------------------------------------
// Alert Engine
// ---------------------------------------------------------------------------

export class AlertEngine {
  /**
   * Cooldown map: `${ruleId}:${robotId}` → last fire timestamp (ms).
   * In production this would live in Redis.
   */
  private cooldowns = new Map<string, number>();

  /**
   * Evaluate a single rule against a telemetry sample.
   * Returns an AlertEvent if the rule fires, or null.
   */
  evaluate(rule: AlertRule, telemetry: NormalizedTelemetry): AlertEvent | null {
    if (!rule.enabled) return null;

    const value = getMetricValue(telemetry, rule.metric);
    if (value === null) return null;

    let triggered = false;

    if (typeof value === 'number' && rule.threshold !== null) {
      triggered = evaluateNumeric(value, rule.operator, rule.threshold);
    } else if (typeof value === 'string' && rule.targetValue !== null) {
      triggered = evaluateStatus(value, rule.operator, rule.targetValue);
    }

    if (!triggered) return null;

    // Cooldown check
    const cooldownKey = `${rule.id}:${telemetry.robot_id}`;
    const now = Date.now();
    const lastFire = this.cooldowns.get(cooldownKey);

    if (lastFire && now - lastFire < rule.cooldownS * 1000) {
      return null; // still in cooldown
    }

    this.cooldowns.set(cooldownKey, now);

    return {
      ruleId: rule.id,
      robotId: telemetry.robot_id,
      metric: rule.metric,
      value: String(value),
      severity: rule.severity,
      message: this.buildMessage(rule, telemetry, value),
      firedAt: new Date().toISOString(),
    };
  }

  /**
   * Evaluate all rules against one telemetry sample.
   */
  evaluateAll(rules: AlertRule[], telemetry: NormalizedTelemetry): AlertEvent[] {
    return rules
      .map((rule) => this.evaluate(rule, telemetry))
      .filter((e): e is AlertEvent => e !== null);
  }

  /** Reset cooldowns (useful for testing or post-deploy). */
  resetCooldowns(): void {
    this.cooldowns.clear();
  }

  private buildMessage(
    rule: AlertRule,
    t: NormalizedTelemetry,
    value: number | string,
  ): string {
    return `[${rule.name}] Robot ${t.robot_id}: ${rule.metric} is ${value} ` +
      `(${rule.operator} ${rule.threshold ?? rule.targetValue}) — severity: ${rule.severity}`;
  }
}
