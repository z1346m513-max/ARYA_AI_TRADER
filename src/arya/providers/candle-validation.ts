import type { Candle } from "@/arya/core/types";

/** Reject invalid provider bars rather than manufacturing replacements. */
export function validCandle(c: Candle): boolean {
  return [c.t, c.open, c.high, c.low, c.close, c.volume].every(Number.isFinite)
    && c.t > 0 && c.low > 0 && c.open > 0 && c.close > 0
    && c.volume >= 0 && c.high >= Math.max(c.open, c.close)
    && c.low <= Math.min(c.open, c.close) && c.high >= c.low;
}

export function cleanCandles(candles: Candle[]): Candle[] {
  const unique = new Map<number, Candle>();
  for (const candle of candles) if (validCandle(candle)) unique.set(candle.t, candle);
  return [...unique.values()].sort((a, b) => a.t - b.t);
}