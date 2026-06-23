import { AdapterRegistry, registry } from '../../src/adapters/registry';
import { JsonAdapter } from '../../src/adapters/json-adapter';
import { ProtobufAdapter } from '../../src/adapters/protobuf-adapter';
import { BaseAdapter } from '../../src/adapters/base-adapter';
import type { NormalizedTelemetry } from '../../src/adapters/types';

describe('AdapterRegistry', () => {
  let reg: AdapterRegistry;

  beforeEach(() => {
    reg = new AdapterRegistry();
  });

  it('registers an adapter and lists it', () => {
    reg.register(new JsonAdapter());
    expect(reg.listProtocols()).toContain('json');
  });

  it('normalizes through registered adapter', () => {
    reg.register(new JsonAdapter());

    const result = reg.normalize('json', {
      robotId: 'r-99',
      battery: 100,
      joints: {},
      cpu: 10,
      latency: 5,
      task: 'idle',
      latitude: 0,
      longitude: 0,
      status: 'online',
    });

    expect(result.robot_id).toBe('r-99');
    expect(result.battery_level).toBe(100);
  });

  it('throws when no adapter registered for protocol', () => {
    expect(() => reg.normalize('unknown', {})).toThrow('No adapter registered for protocol: unknown');
  });

  it('prevents duplicate registration', () => {
    reg.register(new JsonAdapter());
    expect(() => reg.register(new JsonAdapter())).toThrow('Adapter already registered for protocol: json');
  });

  it('unregisters adapters', () => {
    reg.register(new JsonAdapter());
    expect(reg.listProtocols()).toHaveLength(1);
    reg.unregister('json');
    expect(reg.listProtocols()).toHaveLength(0);
  });

  it('is case-insensitive for protocol names', () => {
    reg.register(new JsonAdapter());
    const result = reg.normalize('JSON', {
      robotId: 'r-caps',
      battery: 50,
      joints: {},
      cpu: 10,
      latency: 5,
      task: 'idle',
      latitude: 0,
      longitude: 0,
      status: 'online',
    });
    expect(result.robot_id).toBe('r-caps');
  });

  it('supports hot-plug: add new adapter without changing registry code', () => {
    class CustomAdapter extends BaseAdapter {
      readonly protocol = 'custom';
      normalize(_raw: unknown): NormalizedTelemetry {
        return {
          robot_id: 'custom-bot',
          battery_level: 99,
          joint_temperatures: {},
          cpu_usage: 1,
          network_latency: 1,
          task: 'custom',
          gps: { latitude: 0, longitude: 0 },
          status: 'online' as const,
          timestamp: this.now(),
        };
      }
    }

    // Hot-plug: just register the new adapter
    reg.register(new CustomAdapter());
    expect(reg.listProtocols()).toContain('custom');

    const result = reg.normalize('custom', {});
    expect(result.robot_id).toBe('custom-bot');
    expect(result.battery_level).toBe(99);
  });
});

describe('Global registry singleton', () => {
  it('is an instance of AdapterRegistry', () => {
    expect(registry).toBeInstanceOf(AdapterRegistry);
  });
});
