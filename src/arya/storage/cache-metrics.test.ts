import { describe, expect, it } from "vitest";

import { CacheMetrics } from "./cache-metrics";

describe("CacheMetrics", () => {
  it("starts empty with zero ratios", () => {
    const s = new CacheMetrics().snapshot();
    expect(s.totalLookups).toBe(0);
    expect(s.hitRatio).toBe(0);
  });

  it("counts hits, misses and stale separately", () => {
    const m = new CacheMetrics();
    m.recordHit({ market: "bourse", timeframe: "D" });
    m.recordHit();
    m.recordMiss({ market: "bourse" });
    m.recordMiss({ reason: "stale_ttl", timeframe: "D" });
    const s = m.snapshot();
    expect([s.hits, s.misses, s.stale, s.totalLookups]).toEqual([2, 1, 1, 4]);
    expect(s.hitRatio).toBe(0.5);
    expect(s.staleRatio).toBe(0.25);
    expect(s.byMarket['bourse']).toEqual({ hits: 1, misses: 1 });
    expect(s.byTimeframe['D']).toEqual({ hits: 1, stale: 1 });
    expect(s.byReason).toEqual({ fresh: 2, miss: 1, stale_ttl: 1 });
  });

  it("tracks saves, errors, force refresh outside lookups", () => {
    const m = new CacheMetrics();
    m.recordSave();
    m.recordError();
    m.recordForceRefresh({ market: "crypto" });
    const s = m.snapshot();
    expect(s.totalLookups).toBe(0);
    expect([s.saves, s.errors, s.forceRefresh]).toEqual([1, 1, 1]);
    expect(s.byMarket['crypto']).toEqual({ force_refresh: 1 });
  });

  it("snapshots are copies and reset clears state", () => {
    const m = new CacheMetrics();
    m.recordHit({ market: "fx" });
    const s = m.snapshot();
    s.byMarket['fx']!['hits'] = 99;
    expect(m.snapshot().byMarket['fx']!['hits']).toBe(1);
    let calls = 0;
    m.subscribe(() => calls++);
    m.reset();
    expect(m.snapshot().hits).toBe(0);
    expect(calls).toBe(1);
  });
});
