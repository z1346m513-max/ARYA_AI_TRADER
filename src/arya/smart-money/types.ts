/**
 * Smart Money Concepts — domain contracts (specification phase 4).
 *
 * Pure types shared by the structure, zone and liquidity detectors. No I/O,
 * no React: everything is computed from a plain candle array.
 */
import type { Candle, Direction } from "@/arya/core/types";

/** A confirmed pivot high/low used as the basis of market structure. */
export interface SwingPoint {
  /** Index in the source candle array. */
  index: number;
  /** Bar open time (epoch ms). */
  time: number;
  price: number;
  kind: "high" | "low";
}

export type StructureKind = "BOS" | "CHOCH";

/** A break of structure (continuation) or change of character (reversal). */
export interface StructureEvent {
  kind: StructureKind;
  direction: Exclude<Direction, "neutral">;
  /** Candle index where the break was confirmed by a close. */
  index: number;
  time: number;
  /** Swing level that was broken. */
  level: number;
  /** Close that confirmed the break. */
  closedAt: number;
  /** 0..1 conviction, based on how decisively the level was cleared. */
  strength: number;
}

/** An institutional order block: last opposing candle before an impulse. */
export interface OrderBlock {
  direction: Exclude<Direction, "neutral">;
  index: number;
  time: number;
  top: number;
  bottom: number;
  /** True while price has not traded back through the zone. */
  mitigated: boolean;
  /** 0..1 — impulse size relative to ATR. */
  strength: number;
}

/** A three-candle fair value gap (imbalance). */
export interface FairValueGap {
  direction: Exclude<Direction, "neutral">;
  index: number;
  time: number;
  top: number;
  bottom: number;
  /** Gap height as a fraction of price. */
  size: number;
  filled: boolean;
}

/** A liquidity pool formed by equal highs/lows (stop clusters). */
export interface LiquidityPool {
  side: "buy-side" | "sell-side";
  price: number;
  /** Number of swings forming the pool. */
  touches: number;
  /** Latest bar time contributing to the pool. */
  time: number;
  /** True once price has traded through the pool (a sweep). */
  swept: boolean;
}

export interface SmartMoneyReport {
  swings: SwingPoint[];
  structure: StructureEvent[];
  orderBlocks: OrderBlock[];
  fairValueGaps: FairValueGap[];
  liquidity: LiquidityPool[];
  /** Current structural bias derived from the most recent events. */
  bias: Direction;
  /** -100..100 smart-money reading; negative is bearish. */
  score: number;
  /** 0..1 — how much of the model could actually be computed. */
  coverage: number;
  /** Short Persian summary of the current structural picture. */
  note: string;
}

export interface SmartMoneyParams {
  /** Bars on each side required to confirm a pivot. */
  swingLookback: number;
  /** ATR period used to normalize impulses and zone sizes. */
  atrPeriod: number;
  /** Minimum impulse size (in ATR) for an order block to qualify. */
  minImpulseAtr: number;
  /** Minimum FVG height as a fraction of price. */
  minGapPct: number;
  /** Tolerance (fraction of price) for two swings to count as "equal". */
  equalTolerancePct: number;
  /** Maximum zones of each kind kept in the report (most recent first). */
  maxZones: number;
}

export const DEFAULT_SMART_MONEY_PARAMS: SmartMoneyParams = {
  swingLookback: 3,
  atrPeriod: 14,
  minImpulseAtr: 1.2,
  minGapPct: 0.0015,
  equalTolerancePct: 0.0015,
  maxZones: 8,
};

export interface SmartMoneyContext {
  candles: Candle[];
  params: SmartMoneyParams;
}
