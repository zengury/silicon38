import { JsonAdapter } from '../../src/adapters/json-adapter';
import { ProtobufAdapter } from '../../src/adapters/protobuf-adapter';
import { ModbusAdapter } from '../../src/adapters/modbus-adapter';
import { BaseAdapter } from '../../src/adapters/base-adapter';
import type { NormalizedTelemetry } from '../../src/adapters/types';

describe('JsonAdapter', () => {
  const adapter = new JsonAdapter();

  const validPayload = {
    robotId: 'r-001',
    battery: 85.5,
    joints: { shoulder: 42.0, elbow: 38.5, wrist: 35.0 },
    cpu: 45.2,
    latency: 12,
    task: 'patrol-zone-a',
    latitude: 31.2304,
    longitude: 121.4737,
    status: 'online',
    ts: '2026-05-30T10:00:00.000Z',
  };

  it('normalizes a valid JSON payload', () => {
    const result = adapter.normalize(validPayload);

    expect(result.robot_id).toBe('r-001');
    expect(result.battery_level).toBe(85.5);
    expect(result.joint_temperatures).toEqual({ shoulder: 42.0, elbow: 38.5, wrist: 35.0 });
    expect(result.cpu_usage).toBe(45.2);
    expect(result.network_latency).toBe(12);
    expect(result.task).toBe('patrol-zone-a');
    expect(result.gps).toEqual({ latitude: 31.2304, longitude: 121.4737 });
    expect(result.status).toBe('online');
    expect(result.timestamp).toBe('2026-05-30T10:00:00.000Z');
  });

  it('generates timestamp when ts is missing', () => {
    const { ts, ...withoutTs } = validPayload;
    const result = adapter.normalize(withoutTs);
    expect(result.timestamp).toBeDefined();
    expect(new Date(result.timestamp).getTime()).toBeGreaterThan(0);
  });

  it('maps unknown status to error', () => {
    const result = adapter.normalize({ ...validPayload, status: 'unknown-state' });
    expect(result.status).toBe('error');
  });

  it('throws on null input', () => {
    expect(() => adapter.normalize(null)).toThrow('[json] Payload must be a JSON object');
  });

  it('throws on string input', () => {
    expect(() => adapter.normalize('not-an-object')).toThrow('[json] Payload must be a JSON object');
  });

  it('throws when a required field is missing', () => {
    const { battery, ...missing } = validPayload;
    expect(() => adapter.normalize(missing)).toThrow('[json] Missing required field: battery');
  });

  it('protocol is json', () => {
    expect(adapter.protocol).toBe('json');
  });
});

describe('ProtobufAdapter (stub)', () => {
  const adapter = new ProtobufAdapter();

  const validPayload = {
    robot_id: 'r-002',
    battery_pct: 92.0,
    joint_temp_c: { base: 40.0, arm: 36.0 },
    cpu_pct: 22.1,
    latency_ms: 8,
    task_name: 'inspect-area-b',
    lat: 39.9042,
    lng: 116.4074,
    status: 'online',
  };

  it('normalizes protobuf payload', () => {
    const result = adapter.normalize(validPayload);
    expect(result.robot_id).toBe('r-002');
    expect(result.battery_level).toBe(92.0);
    expect(result.joint_temperatures).toEqual({ base: 40.0, arm: 36.0 });
    expect(result.cpu_usage).toBe(22.1);
    expect(result.network_latency).toBe(8);
    expect(result.status).toBe('online');
  });

  it('throws on missing fields', () => {
    const { battery_pct, ...missing } = validPayload;
    expect(() => adapter.normalize(missing)).toThrow('Missing required field: battery_pct');
  });
});

describe('ModbusAdapter (stub)', () => {
  const adapter = new ModbusAdapter();

  const validPayload = {
    id: 'r-003',
    bat: 78.0,
    temp: 45.0,
    cpu: 67.0,
    latency: 25,
    task: 'charge-station',
    lat: 22.5431,
    lng: 114.0579,
    status: 1, // online
  };

  it('normalizes modbus payload', () => {
    const result = adapter.normalize(validPayload);
    expect(result.robot_id).toBe('r-003');
    expect(result.battery_level).toBe(78.0);
    expect(result.cpu_usage).toBe(67.0);
    expect(result.network_latency).toBe(25);
    expect(result.status).toBe('online'); // code 1 = online
  });

  it('maps status code 0 to offline', () => {
    const result = adapter.normalize({ ...validPayload, status: 0 });
    expect(result.status).toBe('offline');
  });

  it('maps status code 2 to error', () => {
    const result = adapter.normalize({ ...validPayload, status: 2 });
    expect(result.status).toBe('error');
  });

  it('maps status code 3 to maintenance', () => {
    const result = adapter.normalize({ ...validPayload, status: 3 });
    expect(result.status).toBe('maintenance');
  });
});

describe('BaseAdapter', () => {
  class TestAdapter extends BaseAdapter {
    readonly protocol = 'test';

    normalize(raw: unknown): NormalizedTelemetry {
      if (typeof raw !== 'object' || raw === null) throw new Error('not object');
      this.requireFields(raw as Record<string, unknown>, ['id', 'val']);
      return {
        robot_id: String((raw as any).id),
        battery_level: Number((raw as any).val),
        joint_temperatures: {},
        cpu_usage: 0,
        network_latency: 0,
        task: '',
        gps: { latitude: 0, longitude: 0 },
        status: 'online' as const,
        timestamp: this.now(),
      };
    }
  }

  it('requireFields throws on missing keys', () => {
    const adapter = new TestAdapter();
    expect(() => adapter.normalize({})).toThrow('Missing required field: id');
    expect(() => adapter.normalize({ id: 'x' })).toThrow('Missing required field: val');
  });

  it('now() returns ISO timestamp', () => {
    const adapter = new TestAdapter();
    const ts = (adapter as any).now();
    expect(ts).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });
});
