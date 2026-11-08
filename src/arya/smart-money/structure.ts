/**
 * Market structure: swing detection, BOS and CHOCH.
 *
 * A swing is a fractal pivot confirmed by `lookback` bars on each side.
 * A break of a swing high in an up-trend is a BOS (continuation); the first
 * break against the prevailing direction is a CHOCH (change of character).
 */
import type { Candle } from "@/arya/core/types";

import type { StructureEvent, SwingPoint } from "./types";

/** Confirmed fractal pivots, ordered by index. */
export function findSwings(candles: readonly Candle[], lookback: number): SwingPoint[] {
  const out: SwingPoint[] = [];
  const n = candles.length;
  const k = Math.max(1, Math.floor(lookback));
  if (n < k * 2 + 1) return out;

  for (let i = k; i < n - k; i++) {
    const c = candles[i] as Candle;
    let isHigh = true;
    let isLow = true;
    for (let j = i - k; j <= i + k; j++) {
      if (j === i) continue;
      const o = candles[j] as Candle;
      if (o.high >= c.high) isHigh = false;
      if (o.low <= c.low) isLow = false;
      if (!isHigh && !isLow) break;
    }
    if (isHigh) out.push({ index: i, time: c.t, price: c.high, kind: "high" });
    else if (isLow) out.push({ index: i, time: c.t, price: c.low, kind: "low" });
  }
  return out;
}

/**
 * Walk the series forward and emit a structure event each time a close
 * clears the most recent confirmed swing on either side.
 */
export function findStructureEvents(
  candles: readonly Candle[],
  swings: readonly SwingPoint[],
  atr: readonly number[],
): StructureEvent[] {
  const events: StructureEvent[] = [];
  if (swings.length === 0) return events;

  let lastHigh: SwingPoint | undefined;
  let lastLow: SwingPoint | undefined;
  let trend: "bullish" | "bearish" | undefined;
  let si = 0;

  for (let i = 0; i < candles.length; i++) {
    // A pivot is only usable once its right-hand confirmation bars exist.
    while (si < swings.length && (swings[si] as SwingPoint).index < i) {
      const s = swings[si] as SwingPoint;
      if (s.kind === "high") lastHigh = s;
      else lastLow = s;
      si++;
    }

    const c = candles[i] as Candle;
    const scale = Number.isFinite(atr[i]) && (atr[i] as number) > 0 ? (atr[i] as number) : c.close * 0.01;

    if (lastHigh && c.close > lastHigh.price && lastHigh.index < i) {
      const kind = trend === "bearish" ? "CHOCH" : "BOS";
      events.push({
        kind,
        direction: "bullish",
        index: i,
        time: c.t,
        level: lastHigh.price,
        closedAt: c.close,
        strength: Math.min(1, (c.close - lastHigh.price) / scale),
      });
      trend = "bullish";
      lastHigh = undefined;
      continue;
    }

    if (lastLow && c.close < lastLow.price && lastLow.index < i) {
      const kind = trend === "bullish" ? "CHOCH" : "BOS";
      events.push({
        kind,
        direction: "bearish",
        index: i,
        time: c.t,
        level: lastLow.price,
        closedAt: c.close,
        strength: Math.min(1, (lastLow.price - c.close) / scale),
      });
      trend = "bearish";
      lastLow = undefined;
    }
  }

  return events;
}
