import { BaseAdapter } from './base-adapter';
import type { NormalizedTelemetry } from './types';

/**
 * Adapter Registry — hot-plug capable.
 *
 * Call `register()` at startup (or when a new robot type is added) to
 * associate a protocol name with its adapter instance.  New adapters
 * are added by writing ONE new file and calling `registry.register(...)`
 * — no core code changes required.
 *
 * Call `normalize(protocol, raw)` to convert raw payload data into
 * the unified `NormalizedTelemetry` schema.
 */
export class AdapterRegistry {
  private adapters = new Map<string, BaseAdapter>();

  /** Register a new adapter instance. */
  register(adapter: BaseAdapter): void {
    const proto = adapter.protocol.toLowerCase();
    if (this.adapters.has(proto)) {
      throw new Error(
        `Adapter already registered for protocol: ${proto}`,
      );
    }
    this.adapters.set(proto, adapter);
  }

  /** Unregister an adapter (e.g. for hot-reload). */
  unregister(protocol: string): boolean {
    return this.adapters.delete(protocol.toLowerCase());
  }

  /** List all registered protocol names. */
  listProtocols(): string[] {
    return Array.from(this.adapters.keys());
  }

  /**
   * Normalize raw payload data using the adapter registered for `protocol`.
   *
   * @throws if no adapter is registered for the protocol
   */
  normalize(protocol: string, raw: unknown): NormalizedTelemetry {
    const adapter = this.adapters.get(protocol.toLowerCase());
    if (!adapter) {
      throw new Error(
        `No adapter registered for protocol: ${protocol}`,
      );
    }
    return adapter.normalize(raw);
  }
}

/** Singleton instance for the application. */
export const registry = new AdapterRegistry();
