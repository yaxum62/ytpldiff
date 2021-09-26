export namespace assert {
  export function notNull<T>(val: T | null | undefined): T {
    if (val === null || val === undefined) {
      throw new ReferenceError(`unexpected null/undefined value: ${val}`);
    }
    return val;
  }

  export function string(val: unknown): string {
    if (typeof val !== 'string') {
      throw new TypeError(`expect string, got ${typeof val}: ${val}`);
    }
    return val;
  }
}
