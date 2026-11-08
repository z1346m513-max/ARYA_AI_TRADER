/**
 * Configuration schemas.
 *
 * Specification rules 5 and 6: nothing that a trader might reasonably want
 * to tune may be hard-coded. Every value below is user-overridable and
 * validated with zod before it reaches an engine.
 */
import { z } from "zod";

import { TIMEFRAMES } from "@/arya/core/types";

const positiveInt = z.number().int().positive();

/** Parameters are numeric and indicator-specific; validated per indicator. */
export const indicatorParamsSchema = z.record(z.string(), z.number());
export type IndicatorParams = z.infer<typeof indicatorParamsSchema>;

export const indicatorConfigSchema = z.object({
  id: z.string().min(1),
  enabled: z.boolean(),
  /** Relative influence of this indicator inside its own category (0..1). */
  weight: z.number().min(0).max(1),
  params: indicatorParamsSchema,
});
export type IndicatorConfig = z.infer<typeof indicatorConfigSchema>;

export const indicatorsConfigSchema = z.record(z.string(), indicatorConfigSchema);
export type IndicatorsConfig = z.infer<typeof indicatorsConfigSchema>;

/** The eight scoring pillars from specification rule 6. */
export const WEIGHT_KEYS = [
  "technical",
  "fundamental",
  "smartMoney",
  "codal",
  "news",
  "liquidity",
  "risk",
  "ai",
] as const;
export type WeightKey = (typeof WEIGHT_KEYS)[number];

export const weightsConfigSchema = z.object({
  technical: z.number().min(0).max(100),
  fundamental: z.number().min(0).max(100),
  smartMoney: z.number().min(0).max(100),
  codal: z.number().min(0).max(100),
  news: z.number().min(0).max(100),
  liquidity: z.number().min(0).max(100),
  risk: z.number().min(0).max(100),
  ai: z.number().min(0).max(100),
});
export type WeightsConfig = z.infer<typeof weightsConfigSchema>;

export const timeframeSchema = z.enum(TIMEFRAMES);

export const timeframesConfigSchema = z.object({
  /** Timeframes the analysis pipeline computes. */
  active: z.array(timeframeSchema).min(1),
  /** Higher-timeframe bias. */
  trend: timeframeSchema,
  /** Structure / setup timeframe. */
  structure: timeframeSchema,
  /** Momentum confirmation timeframe. */
  momentum: timeframeSchema,
  /** Execution timeframe. */
  entry: timeframeSchema,
});
export type TimeframesConfig = z.infer<typeof timeframesConfigSchema>;

export const REFRESH_INTERVALS_MS = {
  "1m": 60_000,
  "5m": 300_000,
  "10m": 600_000,
  "15m": 900_000,
  "30m": 1_800_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  manual: 0,
} as const;
export type RefreshInterval = keyof typeof REFRESH_INTERVALS_MS;

export const schedulerConfigSchema = z.object({
  interval: z.enum(Object.keys(REFRESH_INTERVALS_MS) as [RefreshInterval, ...RefreshInterval[]]),
  /** Pause polling when the tab is hidden. */
  pauseWhenHidden: z.boolean(),
  maxRetries: z.number().int().min(0).max(10),
  retryBackoffMs: positiveInt,
  /** Age after which LIVE data is downgraded to STALE. */
  staleAfterMs: positiveInt,
});
export type SchedulerConfig = z.infer<typeof schedulerConfigSchema>;

export const riskConfigSchema = z.object({
  /** Percentage of account risked per position. */
  riskPerTradePct: z.number().min(0.05).max(20),
  maxPortfolioRiskPct: z.number().min(0.1).max(100),
  maxPositions: positiveInt,
  minRiskReward: z.number().min(0.1).max(20),
  /** ATR multiple used for the default protective stop. */
  atrStopMultiple: z.number().min(0.1).max(10),
  maxDrawdownPct: z.number().min(1).max(100),
});
export type RiskConfig = z.infer<typeof riskConfigSchema>;

export const aiConfigSchema = z.object({
  enabled: z.boolean(),
  /** Below this confidence the engine must not emit a directional call. */
  minConfidence: z.number().min(0).max(100),
  /** Refuse to produce a recommendation from DEMO-only inputs. */
  requireRealData: z.boolean(),
});
export type AiConfig = z.infer<typeof aiConfigSchema>;

export const providersConfigSchema = z.object({
  /** Provider id used for OHLCV data. */
  market: z.string().min(1),
  news: z.string().min(1),
  codal: z.string().min(1),
  fundamental: z.string().min(1),
  /** Allow demo providers to fill gaps (clearly badged in the UI). */
  allowDemoFallback: z.boolean(),
  timeoutMs: positiveInt,
});
export type ProvidersConfig = z.infer<typeof providersConfigSchema>;

export const appConfigSchema = z.object({
  version: z.string().min(1),
  locale: z.enum(["fa-IR", "en-US"]),
  indicators: indicatorsConfigSchema,
  weights: weightsConfigSchema,
  timeframes: timeframesConfigSchema,
  scheduler: schedulerConfigSchema,
  risk: riskConfigSchema,
  ai: aiConfigSchema,
  providers: providersConfigSchema,
});
export type AppConfig = z.infer<typeof appConfigSchema>;
