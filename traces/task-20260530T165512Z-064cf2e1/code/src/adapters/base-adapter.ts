import { NormalizedTelemetry } from './types';

/**
 * Abstract base class for all protocol adapters.
 *
 * Every adapter extends this class and implements `normalize()`.
 * The base class provides:
 *  - protocol identification (used by the registry)
 *  - a shared method for timestamp generation
 *  - a common field-validation guard
 */
export abstract class BaseAdapter {
  /** Protocol name this adapter handles (e.g. "json", "protobuf", "modbus") */
  abstract readonly protocol: string;

  /**
   * Parse and normalize raw incoming data into the unified schema.
   *
   * Implementations MUST throw if required fields cannot be extracted.
   */
  abstract normalize(raw: unknown): NormalizedTelemetry;

  /**
   * Convenience: generate an ISO-8601 timestamp for "now".
   */
  protected now(): string {
    return new Date().toISOString();
  }

  /**
   * Guard: throws if any of the given keys is missing or nullish in `obj`.
   * Call this in normalize() to enforce required fields.
   */
  protected requireFields(
    obj: Record<string, unknown>,
    keys: string[],
  ): void {
    for (const key of keys) {
      if (obj[key] === undefined || obj[key] === null) {
        throw new Error(
          `[${this.protocol}] Missing required field: ${key}`,
        );
      }
    }
  }
}
