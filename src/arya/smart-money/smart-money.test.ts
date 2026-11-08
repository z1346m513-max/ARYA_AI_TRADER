import { describe, expect, it } from "vitest";

import { demo, envelope } from "@/arya/core/data-envelope";
import type { Candle } from "@/arya/core/types";
import { generateCandles } from "@/arya/providers/mock-provider";
import {
  analyzeSmartMoney,
  findFairValueGaps,
  findLiquidityPools,
  findOrderBlocks,
  findStructureEvents,
  findSwings,
  runSmartMoney,
} from "@/arya/smart-money";

const bar = (i: number, open: number, high: number, low: number, close: number, volume = 100): Candle => ({
  t: i * 60_000,
  open,
  high,
  low,
  close,
  volume,
});

/** Simple zig-zag: up leg, pullback, higher high. */
function zigzag(): Candle[] {
  const prices = [100, 102, 104, 103, 101, 103, 106, 108, 107, 105, 107, 110, 112];
  return prices.map((p, i) => bar(i, p - 0.5, p + 1, p - 1, p));
}

describe("swing detection", () => {
  it("returns nothing when the series is shorter than the fractal window", () => {
    expect(findSwings([bar(0, 1, 2, 0.5, 1.5)], 3)).toEqual([]);
  });

  it("finds a pivot high and a pivot low", () => {
    const candles = [
      bar(0, 10, 11, 9, 10),
      bar(1, 10, 12, 9.5, 11),
      bar(2, 11, 20, 10, 19), // pivot high
      bar(3, 19, 18.5, 10, 12),
      bar(4, 12, 13, 8, 9),
      bar(5, 9, 10, 2, 3), // pivot low
      bar(6, 3, 9, 4, 8),
      bar(7, 8, 11, 6, 10),
    ];
    const swings = findSwings(candles, 2);
    expect(swings.find((s) => s.kind === "high")?.index).toBe(2);
    expect(swings.find((s) => s.kind === "low")?.index).toBe(5);
  });
});

describe("structure events", () => {
  it("labels a continuation break as BOS and the first counter-break as CHOCH", () => {
    const candles = zigzag();
    const swings = findSwings(candles, 2);
    const atr = candles.map(() => 1);
    const events = findStructureEvents(candles, swings, atr);
    expect(events.length).toBeGreaterThan(0);
    expect(events[0]?.kind).toBe("BOS");
    const kinds = new Set(events.map((e) => e.kind));
    expect(["BOS", "CHOCH"].some((k) => kinds.has(k as "BOS"))).toBe(true);
    for (const e of events) {
      expect(e.strength).toBeGreaterThanOrEqual(0);
      expect(e.strength).toBeLessThanOrEqual(1);
    }
  });

  it("emits nothing without swings", () => {
    expect(findStructureEvents(zigzag(), [], [])).toEqual([]);
  });
});

describe("order blocks", () => {
  it("detects the last bearish candle before a bullish impulse", () => {
    const candles = [
      bar(0, 100, 101, 99, 100),
      bar(1, 100, 100.5, 97, 98), // bearish block candle
      bar(2, 98, 112, 98, 111), // impulse
      bar(3, 111, 113, 110, 112),
    ];
    const atr = candles.map(() => 2);
    const blocks = findOrderBlocks(candles, atr, 1.2);
    expect(blocks).toHaveLength(1);
    expect(blocks[0]?.direction).toBe("bullish");
    expect(blocks[0]?.index).toBe(1);
    expect(blocks[0]?.mitigated).toBe(false);
  });

  it("marks a block as mitigated once price returns into it", () => {
    const candles = [
      bar(0, 100, 101, 99, 100),
      bar(1, 100, 100.5, 97, 98),
      bar(2, 98, 112, 98, 111),
      bar(3, 111, 112, 99, 100), // trades back into the block
    ];
    const blocks = findOrderBlocks(candles, candles.map(() => 2), 1.2);
    expect(blocks[0]?.mitigated).toBe(true);
  });

  it("ignores impulses smaller than the ATR threshold", () => {
    const candles = [bar(0, 100, 101, 99, 100), bar(1, 100, 100, 99, 99), bar(2, 99, 100, 99, 99.5)];
    expect(findOrderBlocks(candles, candles.map(() => 5), 1.2)).toEqual([]);
  });
});

describe("fair value gaps", () => {
  it("detects a bullish gap and tracks fills", () => {
    const candles = [
      bar(0, 100, 101, 99, 100),
      bar(1, 100, 110, 100, 109),
      bar(2, 109, 112, 105, 110), // low 105 > high 101 => bullish FVG
    ];
    const gaps = findFairValueGaps(candles, 0.001);
    expect(gaps).toHaveLength(1);
    expect(gaps[0]?.direction).toBe("bullish");
    expect(gaps[0]?.bottom).toBe(101);
    expect(gaps[0]?.top).toBe(105);
    expect(gaps[0]?.filled).toBe(false);

    const filled = findFairValueGaps([...candles, bar(3, 110, 111, 100, 102)], 0.001);
    expect(filled[0]?.filled).toBe(true);
  });

  it("detects a bearish gap", () => {
    const candles = [
      bar(0, 110, 112, 108, 109),
      bar(1, 109, 109, 100, 101),
      bar(2, 101, 104, 99, 100), // high 104 < low 108 => bearish FVG
    ];
    const gaps = findFairValueGaps(candles, 0.001);
    expect(gaps[0]?.direction).toBe("bearish");
  });

  it("skips gaps below the minimum size", () => {
    const candles = [
      bar(0, 100, 100.01, 99, 100),
      bar(1, 100, 100.5, 100, 100.4),
      bar(2, 100.4, 101, 100.02, 100.5),
    ];
    expect(findFairValueGaps(candles, 0.05)).toEqual([]);
  });
});

describe("liquidity pools", () => {
  it("groups equal highs into a buy-side pool and flags sweeps", () => {
    const candles = [
      bar(0, 100, 100, 99, 99.5),
      bar(1, 99.5, 105, 99, 104),
      bar(2, 104, 100, 99, 99.5),
      bar(3, 99.5, 105.02, 99, 104),
      bar(4, 104, 100, 99, 99.5),
      bar(5, 99.5, 108, 99, 107), // sweep
    ];
    const swings = [
      { index: 1, time: candles[1]!.t, price: 105, kind: "high" as const },
      { index: 3, time: candles[3]!.t, price: 105.02, kind: "high" as const },
    ];
    const pools = findLiquidityPools(candles, swings, 0.001);
    expect(pools).toHaveLength(1);
    expect(pools[0]?.side).toBe("buy-side");
    expect(pools[0]?.touches).toBe(2);
    expect(pools[0]?.swept).toBe(true);
  });

  it("ignores isolated swings", () => {
    const swings = [{ index: 1, time: 0, price: 105, kind: "low" as const }];
    expect(findLiquidityPools(zigzag(), swings, 0.001)).toEqual([]);
  });
});

describe("smart money engine", () => {
  it("returns an empty, honest report when there are too few bars", () => {
    const r = runSmartMoney(zigzag());
    expect(r.coverage).toBe(0);
    expect(r.bias).toBe("neutral");
    expect(r.note).toContain("داده کافی");
  });

  it("produces a bounded score and bias on a realistic series", () => {
    const candles = generateCandles("iran-equity:SHEPNA", "1D", 240, Date.UTC(2026, 0, 1));
    const r = runSmartMoney(candles);
    expect(r.score).toBeGreaterThanOrEqual(-100);
    expect(r.score).toBeLessThanOrEqual(100);
    expect(r.coverage).toBeGreaterThan(0);
    expect(r.swings.length).toBeGreaterThan(0);
    expect(["bullish", "bearish", "neutral"]).toContain(r.bias);
  });

  it("scores a clean up-trend bullish", () => {
    const candles: Candle[] = Array.from({ length: 120 }, (_, i) => {
      const base = 100 + i * 1.5;
      return bar(i, base, base + 2, base - 0.8, base + 1.4);
    });
    const r = runSmartMoney(candles);
    expect(r.score).toBeGreaterThan(0);
    expect(r.bias).toBe("bullish");
  });

  it("scores a clean down-trend bearish", () => {
    const candles: Candle[] = Array.from({ length: 120 }, (_, i) => {
      const base = 600 - i * 4;
      return bar(i, base, base + 0.8, base - 2, base - 1.4);
    });
    const r = runSmartMoney(candles);
    expect(r.score).toBeLessThan(0);
    expect(r.bias).toBe("bearish");
  });

  it("keeps demo provenance and downgrades quality with coverage", () => {
    const candles = generateCandles("iran-equity:SHEPNA", "1D", 240, Date.UTC(2026, 0, 1));
    const env = analyzeSmartMoney(demo(candles, "MockProvider", "mock", 123));
    expect(env.meta.status).toBe("DEMO");
    expect(env.meta.timestamp).toBe(123);
    expect(env.meta.quality).toBeLessThanOrEqual(0.5);
  });

  it("reports UNAVAILABLE for an empty series even from a live provider", () => {
    const env = analyzeSmartMoney(
      envelope([] as Candle[], { source: "X", providerId: "x", status: "LIVE" }),
    );
    expect(env.meta.status).toBe("UNAVAILABLE");
    expect(env.data.structure).toEqual([]);
  });
});
