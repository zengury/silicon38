/* ============================================
 * Mock Data Generator — Demo/development only
 * Mirrors the prototype's simulated data approach
 * ============================================ */

import type { SimulatedRobot, RobotTelemetry, Alert, AlertSeverity, RobotStatus } from '@/types';

const ROBOT_MODELS = ['X1-2000', 'Titan-5', 'Atlas-Pro', 'Sentinel-MK3'];
const ROBOT_NAMES = ['先锋', '猎鹰', '铁壁', '闪电', '磐石', '飞燕', '巨犀', '疾风', '天眼', '灵猫'];
const TASKS = ['仓库搬运', '设备巡检', '环境监测', '物料分拣', '焊接作业', '精密装配'];
const LOCATIONS = [
  { lat: 31.2304, lng: 121.4737 }, // Shanghai
  { lat: 31.2350, lng: 121.4800 },
  { lat: 31.2250, lng: 121.4700 },
  { lat: 31.2400, lng: 121.4650 },
  { lat: 31.2200, lng: 121.4850 },
  { lat: 31.2280, lng: 121.4780 },
  { lat: 31.2320, lng: 121.4680 },
  { lat: 31.2380, lng: 121.4820 },
  { lat: 31.2220, lng: 121.4750 },
  { lat: 31.2340, lng: 121.4720 },
];

const JOINT_NAMES = ['左肩', '右肩', '左肘', '右肘', '左腕', '右腕', '底座'];

function random(min: number, max: number): number {
  return Math.round((Math.random() * (max - min) + min) * 100) / 100;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function generateMockRobots(count: number): SimulatedRobot[] {
  return Array.from({ length: count }, (_, i) => {
    const robotId = `RBT-${String(i + 1).padStart(3, '0')}`;
    const batteryLevel = random(15, 100);
    const hasDisconnectedJoint = Math.random() < 0.05;
    const status: RobotStatus = hasDisconnectedJoint
      ? 'error'
      : batteryLevel < 20
        ? 'warning'
        : Math.random() < 0.1
          ? 'idle'
          : 'online';

    return {
      robotId,
      name: `${pick(ROBOT_NAMES)}-${i + 1}`,
      model: pick(ROBOT_MODELS),
      status,
      battery: {
        levelPercent: batteryLevel,
        voltage: random(18, 48),
        isCharging: status === 'idle' && batteryLevel < 50,
      },
      joints: JOINT_NAMES.map((name, ji) => ({
        jointId: `${robotId}-${name}`,
        temperatureCelsius: random(35, 85),
        isConnected: !(hasDisconnectedJoint && ji === 3),
        angleDegrees: random(-180, 180),
      })),
      cpu: {
        usagePercent: random(10, 95),
        temperatureCelsius: random(40, 90),
      },
      network: {
        latencyMs: random(5, 200),
        signalStrength: random(60, 100),
        isConnected: Math.random() > 0.05,
      },
      task: Math.random() < 0.2
        ? null
        : {
            taskId: `TASK-${random(1000, 9999)}`,
            name: pick(TASKS),
            state: pick(['queued', 'in_progress', 'completed'] as const),
            progressPercent: Math.round(random(0, 100)),
            startedAt: new Date(Date.now() - random(0, 3600000)).toISOString(),
            estimatedCompletionAt: null,
          },
      location: {
        latitude: LOCATIONS[i % LOCATIONS.length].lat + random(-0.005, 0.005),
        longitude: LOCATIONS[i % LOCATIONS.length].lng + random(-0.005, 0.005),
        altitudeMeters: random(0, 15),
      },
      lastSeenAt: new Date().toISOString(),
    };
  });
}

export function simulateTelemetryUpdate(robot: SimulatedRobot): RobotTelemetry {
  const d = 0.05; // Delta factor
  const now = new Date().toISOString();
  const batteryDelta = (Math.random() - 0.55) * 3;
  const newBattery = Math.max(0, Math.min(100, robot.battery.levelPercent + batteryDelta));

  return {
    robotId: robot.robotId,
    timestamp: now,
    battery: {
      levelPercent: newBattery,
      voltage: robot.battery.voltage + (Math.random() - 0.5) * 0.5,
      isCharging: robot.battery.isCharging && newBattery < 95,
    },
    joints: robot.joints.map((j) => ({
      ...j,
      temperatureCelsius: Math.max(30, Math.min(95, j.temperatureCelsius + (Math.random() - 0.5) * 2)),
    })),
    cpu: {
      usagePercent: Math.max(5, Math.min(100, robot.cpu.usagePercent + (Math.random() - 0.5) * 10)),
      temperatureCelsius: Math.max(35, Math.min(95, robot.cpu.temperatureCelsius + (Math.random() - 0.5) * 3)),
    },
    network: {
      latencyMs: Math.max(1, Math.min(500, robot.network.latencyMs + (Math.random() - 0.5) * 20)),
      signalStrength: Math.max(30, Math.min(100, robot.network.signalStrength + (Math.random() - 0.5) * 5)),
      isConnected: robot.network.isConnected,
    },
    task: robot.task
      ? {
          ...robot.task,
          progressPercent: Math.min(100, (robot.task.progressPercent || 0) + random(0, 5)),
        }
      : null,
    location: {
      latitude: robot.location.latitude + (Math.random() - 0.5) * 0.002,
      longitude: robot.location.longitude + (Math.random() - 0.5) * 0.002,
      altitudeMeters: robot.location.altitudeMeters,
    },
    metadata: {},
  };
}

export function generateMockAlerts(count: number): Alert[] {
  const severities: AlertSeverity[] = ['critical', 'warning', 'info'];
  const alertTemplates = [
    { msg: '机器人摔倒检测', ruleId: 'fall-detect-001' },
    { msg: '关节温度过高', ruleId: 'joint-temp-001' },
    { msg: '电量低于阈值', ruleId: 'battery-low-001' },
    { msg: 'CPU温度过高', ruleId: 'cpu-temp-001' },
    { msg: '网络延迟过高', ruleId: 'network-lat-001' },
    { msg: '关节断开连接', ruleId: 'joint-disc-001' },
  ];

  return Array.from({ length: count }, (_, i) => {
    const template = pick(alertTemplates);
    const severity = pick(severities);
    const triggeredAt = new Date(Date.now() - random(60000, 86400000)).toISOString();
    const acked = Math.random() < 0.4;

    return {
      alertId: `ALERT-${String(i + 1).padStart(4, '0')}`,
      robotId: `RBT-${String(Math.floor(Math.random() * 10) + 1).padStart(3, '0')}`,
      ruleId: template.ruleId,
      severity,
      message: template.msg,
      details: { value: random(0, 100) },
      triggeredAt,
      acknowledgedAt: acked ? new Date(Date.now() - random(0, 300000)).toISOString() : null,
      acknowledgedBy: acked ? `user-${Math.floor(Math.random() * 5) + 1}` : null,
      resolvedAt: null,
    };
  });
}

export function generateMockHistory(robotCount: number): Record<string, { timestamp: string; battery: number; cpu: number; temp: number }[]> {
  const history: Record<string, { timestamp: string; battery: number; cpu: number; temp: number }[]> = {};
  const now = Date.now();

  for (let r = 1; r <= robotCount; r++) {
    const robotId = `RBT-${String(r).padStart(3, '0')}`;
    const points: { timestamp: string; battery: number; cpu: number; temp: number }[] = [];
    let batt = random(70, 100);
    let cpu = random(10, 40);
    let temp = random(40, 60);

    // Generate 30 days of data points, one per hour
    for (let h = 720; h >= 0; h -= 1) {
      batt = Math.max(10, Math.min(100, batt + (Math.random() - 0.52) * 5));
      cpu = Math.max(5, Math.min(100, cpu + (Math.random() - 0.5) * 8));
      temp = Math.max(35, Math.min(90, temp + (Math.random() - 0.5) * 2));

      points.push({
        timestamp: new Date(now - h * 3600000).toISOString(),
        battery: Math.round(batt * 10) / 10,
        cpu: Math.round(cpu * 10) / 10,
        temp: Math.round(temp * 10) / 10,
      });
    }
    history[robotId] = points;
  }
  return history;
}

export function getSeverityColor(severity: AlertSeverity): string {
  switch (severity) {
    case 'critical': return '#EF4444';
    case 'warning': return '#F59E0B';
    case 'info': return '#3B82F6';
  }
}

export function getStatusColor(status: RobotStatus): string {
  switch (status) {
    case 'online': return '#10B981';
    case 'offline': return '#6B7280';
    case 'error': return '#EF4444';
    case 'warning': return '#F59E0B';
    case 'idle': return '#3B82F6';
    case 'charging': return '#8B5CF6';
  }
}

export function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return `${Math.floor(hours / 24)}天前`;
}
