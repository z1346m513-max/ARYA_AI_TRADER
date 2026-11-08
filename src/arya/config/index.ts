/**
 * Runtime configuration store.
 *
 * Merges user overrides over `DEFAULT_CONFIG`, validates the result, and
 * persists to localStorage when available. Framework-agnostic: the UI reads
 * it through a thin hook.
 */
import { DEFAULT_CONFIG } from "./defaults";
import { appConfigSchema, type AppConfig } from "./schemas";

const STORAGE_KEY = "arya.config.v1";

type DeepPartial<T> = { [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K] };
export type ConfigPatch = DeepPartial<AppConfig>;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Recursive merge; arrays are replaced, not concatenated. */
export function mergeConfig<T>(base: T, patch: unknown): T {
  if (!isPlainObject(patch) || !isPlainObject(base)) return (patch === undefined ? base : patch) as T;
  const out: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(patch)) {
    out[key] = isPlainObject(value) ? mergeConfig(out[key], value) : value;
  }
  return out as T;
}

export interface ConfigLoadResult {
  config: AppConfig;
  /** True when stored overrides were rejected and defaults were used. */
  fellBack: boolean;
  errors: string[];
}

/** Validate an arbitrary patch against the schema, on top of defaults. */
export function resolveConfig(patch: unknown, base: AppConfig = DEFAULT_CONFIG): ConfigLoadResult {
  const merged = mergeConfig(base, patch);
  const parsed = appConfigSchema.safeParse(merged);
  if (parsed.success) return { config: parsed.data, fellBack: false, errors: [] };
  return {
    config: base,
    fellBack: true,
    errors: parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`),
  };
}

function storage(): Storage | null {
  try {
    if (typeof window === "undefined") return null;
    return window.localStorage;
  } catch {
    return null;
  }
}

export function loadConfig(): ConfigLoadResult {
  const store = storage();
  if (!store) return { config: DEFAULT_CONFIG, fellBack: false, errors: [] };
  const raw = store.getItem(STORAGE_KEY);
  if (!raw) return { config: DEFAULT_CONFIG, fellBack: false, errors: [] };
  try {
    return resolveConfig(JSON.parse(raw));
  } catch (error) {
    return {
      config: DEFAULT_CONFIG,
      fellBack: true,
      errors: [error instanceof Error ? error.message : "Invalid stored configuration"],
    };
  }
}

export function saveConfig(config: AppConfig): boolean {
  const store = storage();
  if (!store) return false;
  try {
    store.setItem(STORAGE_KEY, JSON.stringify(config));
    return true;
  } catch {
    return false;
  }
}

export function clearConfig(): void {
  storage()?.removeItem(STORAGE_KEY);
}

export { DEFAULT_CONFIG };
export * from "./schemas";
export * from "./weights";
