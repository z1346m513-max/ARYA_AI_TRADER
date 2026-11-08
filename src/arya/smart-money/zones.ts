/**
 * Zone detection: order blocks, fair value gaps and liquidity pools.
 */
import type { Candle } from "@/arya/core/types";

import type { FairValueGap, LiquidityPool, OrderBlock, SwingPoint } from "./types";

/**
 * Order block = last opposing candle before an impulse that is at least
 * `minImpulseAtr` ATRs in size. The block is "mitigated" once price trades
 * back into it after formation.
 */
export function findOrderBlocks(
  candles: readonly Candle[],
  atr: readonly number[],
  minImpulseAtr: number,
): OrderBlock[] {
  const out: OrderBlock[] = [];
  for (let i = 1; i < candles.length; i++) {
    const c = candles[i] as Candle;
    const p = candles[i - 1] as Candle;
    const a = Number.isFinite(atr[i]) && (atr[i] as number) > 0 ? (atr[i] as number) : Number.NaN;
    if (!Number.isFinite(a)) continue;
    const move = c.close - c.open;
    const impulse = Math.abs(move) / a;
    if (impulse < minImpulseAtr) continue;

    const bullish = move > 0;
    // The prior candle must be the opposite colour to qualify as a block.
    const priorBearish = p.close < p.open;
    if (bullish !== priorBearish) continue;

    const top = Math.max(p.open, p.close, p.high);
    const bottom = Math.min(p.open, p.close, p.low);
    let mitigated = false;
    for (let j = i + 1; j < candles.length; j++) {
      const f = candles[j] as Candle;
      if (bullish ? f.low <= top : f.high >= bottom) {
        mitigated = true;
        break;
      }
    }

    out.push({
      direction: bullish ? "bullish" : "bearish",
      index: i - 1,
      time: p.t,
      top,
      bottom,
      mitigated,
      strength: Math.min(1, impulse / (minImpulseAtr * 2.5)),
    });
  }
  return out;
}

/** Three-candle imbalance: candle i-2 high < candle i low (bullish), or vice versa. */
export function findFairValueGaps(candles: readonly Candle[], minGapPct: number): FairValueGap[] {
  const out: FairValueGap[] = [];
  for (let i = 2; i < candles.length; i++) {
    const a = candles[i - 2] as Candle;
    const m = candles[i - 1] as Candle;
    const c = candles[i] as Candle;
    const ref = m.close || c.close;
    if (!ref) continue;

    if (c.low > a.high) {
      const size = (c.low - a.high) / ref;
      if (size >= minGapPct) {
        out.push({
          direction: "bullish",
          index: i - 1,
          time: m.t,
          top: c.low,
          bottom: a.high,
          size,
          filled: candles.slice(i + 1).some((f) => f.low <= a.high),
        });
      }
    } else if (c.high < a.low) {
      const size = (a.low - c.high) / ref;
      if (size >= minGapPct) {
        out.push({
          direction: "bearish",
          index: i - 1,
          time: m.t,
          top: a.low,
          bottom: c.high,
          size,
          filled: candles.slice(i + 1).some((f) => f.high >= a.low),
        });
      }
    }
  }
  return out;
}

/**
 * Liquidity pools: clusters of swings at (almost) the same price. Equal highs
 * hold buy-side liquidity, equal lows hold sell-side liquidity.
 */
export function findLiquidityPools(
  candles: readonly Candle[],
  swings: readonly SwingPoint[],
  tolerancePct: number,
): LiquidityPool[] {
  const pools: LiquidityPool[] = [];

  for (const kind of ["high", "low"] as const) {
    const points = swings.filter((s) => s.kind === kind);
    const used = new Set<number>();
    for (let i = 0; i < points.length; i++) {
      if (used.has(i)) continue;
      const base = points[i] as SwingPoint;
      const group = [base];
      for (let j = i + 1; j < points.length; j++) {
        if (used.has(j)) continue;
        const other = points[j] as SwingPoint;
        if (Math.abs(other.price - base.price) / (base.price || 1) <= tolerancePct) {
          group.push(other);
          used.add(j);
        }
      }
      if (group.length < 2) continue;
      used.add(i);

      const price = group.reduce((a, s) => a + s.price, 0) / group.length;
      const lastIndex = Math.max(...group.map((s) => s.index));
      const lastTime = Math.max(...group.map((s) => s.time));
      const after = candles.slice(lastIndex + 1);
      pools.push({
        side: kind === "high" ? "buy-side" : "sell-side",
        price: +price.toFixed(6),
        touches: group.length,
        time: lastTime,
        swept: after.some((c) => (kind === "high" ? c.high > price : c.low < price)),
      });
    }
  }

  return pools.sort((a, b) => b.time - a.time);
}
