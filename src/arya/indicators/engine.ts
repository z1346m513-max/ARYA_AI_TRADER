/**
 * Indicator engine (specification phase 3).
 *
 * Runs every *enabled* indicator over one candle series, preserves data
 * provenance end-to-end, and aggregates the results into per-category and
 * overall technical readings. It never invents values: an indicator without
 * enough bars reports NaN and is excluded from the aggregate.
 */
import { envelope, type DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Direction } from "@/arya/core/types";
import type { IndicatorsConfig } from "@/arya/config/schemas";
import { DEFAULT_INDICATORS } from "@/arya/config/defaults";
import { clamp01 } from "./math";
import { MOMENTUM_INDICATORS } from "./momentum";
import { TREND_INDICATORS } from "./trend";
import type { IndicatorCategory, IndicatorDefinition, IndicatorResult } from "./types";
import { VOLATILITY_INDICATORS } from "./volatility";
import { VOLUME_INDICATORS } from "./volume";

export const INDICATOR_DEFINITIONS: IndicatorDefinition[] = [
  ...TREND_INDICATORS,
  ...MOMENTUM_INDICATORS,
  ...VOLATILITY_INDICATORS,
  ...VOLUME_INDICATORS,
];

export const INDICATOR_REGISTRY: Record<string, IndicatorDefinition> = Object.fromEntries(
  INDICATOR_DEFINITIONS.map((d) => [d.id, d]),
);

export interface CategorySummary {
  category: IndicatorCategory;
  /** -100..100, negative is bearish. */
  score: number;
  signal: Direction;
  contributors: number;
}

export interface IndicatorReport {
  results: IndicatorResult[];
  categories: CategorySummary[];
  /** -100..100 weighted technical reading across all categories. */
  technicalScore: number;
  signal: Direction;
  /** 0..1 — share of enabled indicators that actually produced a value. */
  coverage: number;
  /** Ids skipped because the series was too short. */
  insufficient: string[];
}

const CATEGORY_ORDER: IndicatorCategory[] = ["trend", "momentum", "volatility", "volume"];

const directionSign = (d: Direction): number => (d === "bullish" ? 1 : d === "bearish" ? -1 : 0);

function toSignal(score: number): Direction {
  if (score > 8) return "bullish";
  if (score < -8) return "bearish";
  return "neutral";
}

/** Run all enabled indicators over a raw candle array. */
export function runIndicators(
  candles: Candle[],
  config: IndicatorsConfig = DEFAULT_INDICATORS,
): IndicatorReport {
  const results: IndicatorResult[] = [];
  const insufficient: string[] = [];
  const weights = new Map<string, number>();
  let enabledCount = 0;

  for (const def of INDICATOR_DEFINITIONS) {
    const cfg = config[def.id];
    if (!cfg || !cfg.enabled) continue;
    enabledCount++;
    const params = cfg.params ?? {};
    if (candles.length < def.minBars(params)) {
      insufficient.push(def.id);
      continue;
    }
    const result = def.compute({ candles, params });
    if (!Number.isFinite(result.value)) {
      insufficient.push(def.id);
      continue;
    }
    weights.set(def.id, cfg.weight ?? 0.5);
    results.push(result);
  }

  const categories: CategorySummary[] = CATEGORY_ORDER.map((category) => {
    const items = results.filter((r) => r.category === category);
    let num = 0;
    let den = 0;
    for (const r of items) {
      const w = weights.get(r.id) ?? 0.5;
      num += directionSign(r.signal) * r.strength * w;
      den += w;
    }
    const score = den ? (num / den) * 100 : 0;
    return { category, score: +score.toFixed(2), signal: toSignal(score), contributors: items.length };
  });

  // Volatility describes risk, not direction, so it does not vote on the
  // technical score; it only appears as its own category reading.
  const voting = categories.filter((c) => c.category !== "volatility" && c.contributors > 0);
  const technicalScore = voting.length
    ? +(voting.reduce((a, c) => a + c.score, 0) / voting.length).toFixed(2)
    : 0;

  return {
    results,
    categories,
    technicalScore,
    signal: toSignal(technicalScore),
    coverage: enabledCount ? clamp01(results.length / enabledCount) : 0,
    insufficient,
  };
}

/**
 * Envelope-preserving variant: the report inherits the provenance of the
 * candles it was computed from, so demo input can never surface as live output.
 */
export function analyzeSeries(
  input: DataEnvelope<Candle[]>,
  config: IndicatorsConfig = DEFAULT_INDICATORS,
): DataEnvelope<IndicatorReport> {
  const report = runIndicators(input.data, config);
  const quality = input.meta.quality * (0.4 + 0.6 * report.coverage);
  return envelope(report, {
    source: input.meta.source,
    providerId: input.meta.providerId,
    status: input.data.length === 0 ? "UNAVAILABLE" : input.meta.status,
    timestamp: input.meta.timestamp,
    quality,
    ...(report.coverage < 1
      ? { reason: `پوشش اندیکاتورها ${Math.round(report.coverage * 100)}٪ — داده‌ی تاریخی ناکافی` }
      : input.meta.reason
        ? { reason: input.meta.reason }
        : {}),
  });
}
