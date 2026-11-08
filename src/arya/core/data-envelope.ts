/**
 * Data integrity layer.
 *
 * Specification rule 28: no demo, mock or synthetic value may ever be shown
 * as real data. Every piece of data crossing a module boundary therefore
 * travels inside a `DataEnvelope` carrying its provenance, and the UI is
 * required to surface that provenance.
 */

export type DataStatus =
  /** Fetched from a real provider and fresh. */
  | "LIVE"
  /** Generated locally for development/demo purposes. Never real. */
  | "DEMO"
  /** Real, but older than the acceptable age for its timeframe. */
  | "STALE"
  /** No usable data — provider missing, failed, or not implemented. */
  | "UNAVAILABLE";

export interface DataMeta {
  /** Human-readable provider name, e.g. `MockProvider`. */
  source: string;
  /** Stable provider id, e.g. `mock`. */
  providerId: string;
  /** Epoch milliseconds at which the data was produced or fetched. */
  timestamp: number;
  status: DataStatus;
  /** 0..1 confidence in completeness/accuracy of the payload. */
  quality: number;
  /** Populated for UNAVAILABLE/STALE to explain the degradation. */
  reason?: string;
}

export interface DataEnvelope<T> {
  data: T;
  meta: DataMeta;
}

function clamp01(n: number): number {
  if (Number.isNaN(n)) return 0;
  return Math.min(1, Math.max(0, n));
}

/** Wrap a payload with explicit provenance. */
export function envelope<T>(
  data: T,
  meta: Omit<DataMeta, "timestamp" | "quality"> & Partial<Pick<DataMeta, "timestamp" | "quality">>,
): DataEnvelope<T> {
  return {
    data,
    meta: {
      source: meta.source,
      providerId: meta.providerId,
      status: meta.status,
      timestamp: meta.timestamp ?? Date.now(),
      quality: clamp01(meta.quality ?? (meta.status === "LIVE" ? 1 : 0.5)),
      ...(meta.reason === undefined ? {} : { reason: meta.reason }),
    },
  };
}

/** Convenience constructor for locally generated demo payloads. */
export function demo<T>(
  data: T,
  source: string,
  providerId: string,
  timestamp?: number,
): DataEnvelope<T> {
  return envelope(data, {
    source,
    providerId,
    status: "DEMO",
    quality: 0.5,
    ...(timestamp === undefined ? {} : { timestamp }),
  });
}

/** Convenience constructor for the "we have nothing" case. */
export function unavailable<T>(
  fallback: T,
  source: string,
  providerId: string,
  reason: string,
): DataEnvelope<T> {
  return envelope(fallback, {
    source,
    providerId,
    status: "UNAVAILABLE",
    quality: 0,
    reason,
  });
}

/**
 * Downgrade a LIVE envelope to STALE once it exceeds `maxAgeMs`.
 * DEMO and UNAVAILABLE envelopes are returned untouched — a demo value does
 * not become "more real" or "less real" with age.
 */
export function withFreshness<T>(
  env: DataEnvelope<T>,
  maxAgeMs: number,
  now: number = Date.now(),
): DataEnvelope<T> {
  if (env.meta.status !== "LIVE") return env;
  const age = now - env.meta.timestamp;
  if (age <= maxAgeMs) return env;
  return {
    data: env.data,
    meta: {
      ...env.meta,
      status: "STALE",
      quality: clamp01(env.meta.quality * 0.5),
      reason: `Data is ${Math.round(age / 1000)}s old (limit ${Math.round(maxAgeMs / 1000)}s)`,
    },
  };
}

/** True only for data safe to present as real market information. */
export function isReal<T>(env: DataEnvelope<T>): boolean {
  return env.meta.status === "LIVE" || env.meta.status === "STALE";
}

/**
 * Combine provenance from several inputs. The result is never more
 * trustworthy than its weakest input, and quality is the minimum.
 */
export function combineMeta(metas: DataMeta[], source: string, providerId: string): DataMeta {
  if (metas.length === 0) {
    return {
      source,
      providerId,
      timestamp: Date.now(),
      status: "UNAVAILABLE",
      quality: 0,
      reason: "No inputs",
    };
  }
  const rank: Record<DataStatus, number> = { UNAVAILABLE: 0, DEMO: 1, STALE: 2, LIVE: 3 };
  let worst: DataStatus = "LIVE";
  let quality = 1;
  let timestamp = Number.POSITIVE_INFINITY;
  for (const m of metas) {
    if (rank[m.status] < rank[worst]) worst = m.status;
    quality = Math.min(quality, m.quality);
    timestamp = Math.min(timestamp, m.timestamp);
  }
  return { source, providerId, timestamp, status: worst, quality: clamp01(quality) };
}

/** Localized (fa-IR) label for each status, for UI badges. */
export const STATUS_LABEL_FA: Record<DataStatus, string> = {
  LIVE: "زنده",
  DEMO: "نمایشی",
  STALE: "قدیمی",
  UNAVAILABLE: "بدون داده",
};
