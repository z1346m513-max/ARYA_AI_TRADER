/**
 * OHLCV cache metrics: hit/miss/stale counters and ratios.
 * Port of the Python `arya.storage.cache_metrics` module. No provider or
 * indicator dependencies; a process-wide instance is exported.
 */
export type DimCounts = Record<string, number>;

export interface CacheMetricsSnapshot {
  hits: number;
  misses: number;
  stale: number;
  forceRefresh: number;
  saves: number;
  errors: number;
  totalLookups: number;
  hitRatio: number;
  missRatio: number;
  staleRatio: number;
  byReason: Record<string, number>;
  byMarket: Record<string, DimCounts>;
  byTimeframe: Record<string, DimCounts>;
  startedAt: string;
  snapshotAt: string;
}

interface Dims {
  market?: string;
  timeframe?: string;
}

const isoNow = (now: () => number) => new Date(now()).toISOString().replace(/\.\d{3}Z$/, "Z");
const round6 = (n: number) => Math.round(n * 1e6) / 1e6;

export class CacheMetrics {
  private startedAt: string;
  private hits = 0;
  private misses = 0;
  private stale = 0;
  private forceRefresh = 0;
  private saves = 0;
  private errors = 0;
  private byReason: Record<string, number> = {};
  private byMarket: Record<string, DimCounts> = {};
  private byTimeframe: Record<string, DimCounts> = {};
  private listeners = new Set<() => void>();

  constructor(private readonly now: () => number = Date.now) {
    this.startedAt = isoNow(now);
  }

  recordHit({ reason = "fresh", ...d }: Dims & { reason?: string } = {}) {
    this.hits++;
    this.bumpReason(reason);
    this.bumpDims(d, "hits");
    this.emit();
  }

  /** Pure miss, or a stale record counted as an operational miss. */
  recordMiss({ reason = "miss", ...d }: Dims & { reason?: string } = {}) {
    const isStale = reason.startsWith("stale");
    if (isStale) this.stale++;
    else this.misses++;
    this.bumpReason(reason);
    this.bumpDims(d, isStale ? "stale" : "misses");
    this.emit();
  }

  recordForceRefresh(d: Dims = {}) {
    this.forceRefresh++;
    this.bumpReason("force_refresh");
    this.bumpDims(d, "force_refresh");
    this.emit();
  }

  recordSave(d: Dims = {}) {
    this.saves++;
    this.bumpDims(d, "saves");
    this.emit();
  }

  recordError({ reason = "error", ...d }: Dims & { reason?: string } = {}) {
    this.errors++;
    this.bumpReason(reason);
    this.bumpDims(d, "errors");
    this.emit();
  }

  snapshot(): CacheMetricsSnapshot {
    const total = this.hits + this.misses + this.stale;
    const r = (n: number) => (total ? round6(n / total) : 0);
    const clone = (s: Record<string, DimCounts>) =>
      Object.fromEntries(Object.entries(s).map(([k, v]) => [k, { ...v }]));
    return {
      hits: this.hits,
      misses: this.misses,
      stale: this.stale,
      forceRefresh: this.forceRefresh,
      saves: this.saves,
      errors: this.errors,
      totalLookups: total,
      hitRatio: r(this.hits),
      missRatio: r(this.misses),
      staleRatio: r(this.stale),
      byReason: { ...this.byReason },
      byMarket: clone(this.byMarket),
      byTimeframe: clone(this.byTimeframe),
      startedAt: this.startedAt,
      snapshotAt: isoNow(this.now),
    };
  }

  hitRatio() {
    return this.snapshot().hitRatio;
  }

  reset() {
    this.startedAt = isoNow(this.now);
    this.hits = this.misses = this.stale = this.forceRefresh = this.saves = this.errors = 0;
    this.byReason = {};
    this.byMarket = {};
    this.byTimeframe = {};
    this.emit();
  }

  subscribe(fn: () => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit() {
    this.listeners.forEach((fn) => fn());
  }
  private bumpReason(reason: string) {
    this.byReason[reason] = (this.byReason[reason] ?? 0) + 1;
  }
  private bumpDims(d: Dims, field: string) {
    const bump = (store: Record<string, DimCounts>, key?: string) => {
      if (!key) return;
      const b = (store[key] ??= {});
      b[field] = (b[field] ?? 0) + 1;
    };
    bump(this.byMarket, d.market);
    bump(this.byTimeframe, d.timeframe);
  }
}

/** Process-wide instance shared by providers and UI. */
export const cacheMetrics = new CacheMetrics();
