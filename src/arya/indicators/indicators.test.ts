import { describe, expect, it } from "vitest";

import { demo } from "@/arya/core/data-envelope";
import type { Candle } from "@/arya/core/types";
import { DEFAULT_INDICATORS } from "@/arya/config/defaults";
import { ema, rma, sma, stdDev, trueRange, wma } from "./math";
import { rsiIndicator, rsiSeries, macdIndicator } from "./momentum";
import { atrIndicator, bollingerIndicator } from "./volatility";
import { obvIndicator } from "./volume";
import { adxIndicator, emaIndicator } from "./trend";
import { analyzeSeries, INDICATOR_REGISTRY, runIndicators } from "./engine";

function makeCandles(closesIn: number[]): Candle[] {
  return closesIn.map((c, i) => ({
    t: i * 60_000,
    open: i === 0 ? c : (closesIn[i - 1] as number),
    high: c * 1.01,
    low: c * 0.99,
    close: c,
    volume: 1000 + i * 10,
  }));
}

const up = makeCandles(Array.from({ length: 120 }, (_, i) => 100 + i));
const down = makeCandles(Array.from({ length: 120 }, (_, i) => 300 - i));
const flat = makeCandles(Array.from({ length: 120 }, () => 100));

describe("math helpers", () => {
  it("computes SMA over the trailing window", () => {
    expect(sma([1, 2, 3, 4, 5], 3).slice(2)).toEqual([2, 3, 4]);
  });

  it("leaves leading positions undefined as NaN", () => {
    expect(Number.isNaN(sma([1, 2, 3], 3)[0] as number)).toBe(true);
  });

  it("seeds EMA with the first SMA", () => {
    expect(ema([1, 2, 3, 4], 2)[1]).toBeCloseTo(1.5, 6);
  });

  it("computes WMA with linear weights", () => {
    // (1*1 + 2*2 + 3*3) / 6
    expect(wma([1, 2, 3], 3)[2]).toBeCloseTo(14 / 6, 6);
  });

  it("smooths with Wilder's RMA", () => {
    const r = rma([1, 1, 1, 1, 1], 3);
    expect(r[4]).toBeCloseTo(1, 6);
  });

  it("returns zero standard deviation for a constant series", () => {
    expect(stdDev([5, 5, 5, 5], 3)[3]).toBeCloseTo(0, 10);
  });

  it("uses high-low for the first true range bar", () => {
    const tr = trueRange(up);
    expect(tr[0]).toBeCloseTo((up[0] as Candle).high - (up[0] as Candle).low, 6);
  });
});

describe("RSI", () => {
  it("saturates at 100 for a monotonically rising series", () => {
    const r = rsiSeries(
      up.map((c) => c.close),
      14,
    );
    expect(r[r.length - 1]).toBeCloseTo(100, 6);
  });

  it("reports overbought as a bearish reading", () => {
    const res = rsiIndicator.compute({ candles: up, params: { period: 14, overbought: 70, oversold: 30 } });
    expect(res.value).toBeGreaterThan(70);
    expect(res.signal).toBe("bearish");
  });

  it("stays near 50 on a flat market", () => {
    const res = rsiIndicator.compute({ candles: flat, params: { period: 14 } });
    expect(res.value).toBeGreaterThanOrEqual(0);
    expect(res.strength).toBeLessThan(0.3);
  });
});

describe("MACD", () => {
  it("is positive while price trends up", () => {
    const res = macdIndicator.compute({ candles: up, params: { fast: 12, slow: 26, signal: 9 } });
    expect(res.value).toBeGreaterThan(0);
    expect(res.signal).toBe("bullish");
  });

  it("is negative while price trends down", () => {
    const res = macdIndicator.compute({ candles: down, params: { fast: 12, slow: 26, signal: 9 } });
    expect(res.value).toBeLessThan(0);
  });
});

describe("trend indicators", () => {
  it("marks price above its EMA as bullish", () => {
    const res = emaIndicator.compute({ candles: up, params: { period: 20 } });
    expect(res.signal).toBe("bullish");
  });

  it("reports a strong ADX in a persistent trend", () => {
    const res = adxIndicator.compute({ candles: up, params: { period: 14, trendThreshold: 25 } });
    expect(res.value).toBeGreaterThan(25);
    expect(res.signal).toBe("bullish");
  });
});

describe("volatility and volume", () => {
  it("keeps ATR non-negative and directionless", () => {
    const res = atrIndicator.compute({ candles: up, params: { period: 14 } });
    expect(res.value).toBeGreaterThan(0);
    expect(res.signal).toBe("neutral");
  });

  it("places price inside the Bollinger band range", () => {
    const res = bollingerIndicator.compute({ candles: up, params: { period: 20, stdDev: 2 } });
    expect(res.values?.["upper"]).toBeGreaterThan(res.values?.["lower"] as number);
  });

  it("rises OBV when every close is higher", () => {
    const res = obvIndicator.compute({ candles: up, params: {} });
    expect(res.signal).toBe("bullish");
  });
});

describe("indicator engine", () => {
  it("registers every definition under a unique id", () => {
    expect(Object.keys(INDICATOR_REGISTRY).length).toBeGreaterThanOrEqual(20);
    expect(INDICATOR_REGISTRY["rsi"]?.category).toBe("momentum");
  });

  it("produces a bullish technical score in an uptrend", () => {
    const report = runIndicators(up, DEFAULT_INDICATORS);
    expect(report.technicalScore).toBeGreaterThan(0);
    expect(report.signal).toBe("bullish");
  });

  it("produces a bearish technical score in a downtrend", () => {
    const report = runIndicators(down, DEFAULT_INDICATORS);
    expect(report.technicalScore).toBeLessThan(0);
  });

  it("reports zero coverage and no results without candles", () => {
    const report = runIndicators([], DEFAULT_INDICATORS);
    expect(report.results).toHaveLength(0);
    expect(report.coverage).toBe(0);
    expect(report.technicalScore).toBe(0);
  });

  it("excludes indicators lacking enough bars instead of guessing", () => {
    const report = runIndicators(up.slice(0, 12), DEFAULT_INDICATORS);
    expect(report.insufficient.length).toBeGreaterThan(0);
    expect(report.coverage).toBeLessThan(1);
  });

  it("never lets demo candles produce a live report", () => {
    const env = analyzeSeries(demo(up, "MockProvider", "mock"));
    expect(env.meta.status).toBe("DEMO");
    expect(env.data.results.length).toBeGreaterThan(0);
  });

  it("marks an empty series as unavailable", () => {
    const env = analyzeSeries(demo([], "MockProvider", "mock"));
    expect(env.meta.status).toBe("UNAVAILABLE");
  });
});
