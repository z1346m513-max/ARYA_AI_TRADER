/**
 * Contract every indicator implementation follows.
 *
 * An indicator never decides anything on its own: it reports a normalized
 * signal + strength and the scoring engine combines them using the weights
 * from the config engine.
 */
import type { Candle, Direction } from "@/arya/core/types";

export type IndicatorCategory = "trend" | "momentum" | "volatility" | "volume";

export interface IndicatorResult {
  /** Config id, e.g. `rsi`. */
  id: string;
  /** Localized label for the UI. */
  label: string;
  category: IndicatorCategory;
  /** Primary numeric reading (last bar), NaN when not computable. */
  value: number;
  /** Extra named readings, e.g. `{ signal, histogram }`. */
  values?: Record<string, number>;
  signal: Direction;
  /** 0..1 conviction of the signal, independent of the indicator weight. */
  strength: number;
  /** Short Persian explanation of the current reading. */
  note: string;
  /** Full computed series, for charting. */
  series?: Record<string, number[]>;
}

export interface IndicatorContext {
  candles: Candle[];
  params: Record<string, number>;
}

export interface IndicatorDefinition {
  id: string;
  label: string;
  category: IndicatorCategory;
  /** Minimum number of candles required to produce a value. */
  minBars: (params: Record<string, number>) => number;
  compute: (ctx: IndicatorContext) => IndicatorResult;
}

export function param(params: Record<string, number>, key: string, fallback: number): number {
  const v = params[key];
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

export function emptyResult(
  def: Pick<IndicatorDefinition, "id" | "label" | "category">,
  note = "داده کافی برای محاسبه وجود ندارد",
): IndicatorResult {
  return {
    id: def.id,
    label: def.label,
    category: def.category,
    value: Number.NaN,
    signal: "neutral",
    strength: 0,
    note,
  };
}
