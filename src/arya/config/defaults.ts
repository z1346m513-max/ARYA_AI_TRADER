/**
 * Default configuration.
 *
 * These are starting points, not constants — every value here is editable by
 * the user and persisted over the defaults at runtime.
 */
import {
  appConfigSchema,
  type AppConfig,
  type IndicatorsConfig,
  type WeightsConfig,
} from "./schemas";

export const DEFAULT_INDICATORS: IndicatorsConfig = {
  // Trend
  sma: { id: "sma", enabled: true, weight: 0.5, params: { period: 50 } },
  ema: { id: "ema", enabled: true, weight: 1, params: { period: 20 } },
  wma: { id: "wma", enabled: false, weight: 0.4, params: { period: 20 } },
  vwma: { id: "vwma", enabled: false, weight: 0.5, params: { period: 20 } },
  hma: { id: "hma", enabled: false, weight: 0.5, params: { period: 21 } },
  kama: { id: "kama", enabled: false, weight: 0.5, params: { period: 10, fast: 2, slow: 30 } },
  supertrend: { id: "supertrend", enabled: true, weight: 0.9, params: { period: 10, multiplier: 3 } },
  ichimoku: {
    id: "ichimoku",
    enabled: false,
    weight: 0.7,
    params: { conversion: 9, base: 26, spanB: 52, displacement: 26 },
  },
  psar: { id: "psar", enabled: false, weight: 0.5, params: { step: 0.02, max: 0.2 } },
  adx: { id: "adx", enabled: true, weight: 0.8, params: { period: 14, trendThreshold: 25 } },

  // Momentum
  rsi: { id: "rsi", enabled: true, weight: 1, params: { period: 14, overbought: 70, oversold: 30 } },
  macd: { id: "macd", enabled: true, weight: 1, params: { fast: 12, slow: 26, signal: 9 } },
  stochastic: {
    id: "stochastic",
    enabled: true,
    weight: 0.6,
    params: { k: 14, d: 3, smooth: 3, overbought: 80, oversold: 20 },
  },
  cci: { id: "cci", enabled: false, weight: 0.5, params: { period: 20 } },
  roc: { id: "roc", enabled: false, weight: 0.4, params: { period: 12 } },
  mfi: { id: "mfi", enabled: true, weight: 0.6, params: { period: 14, overbought: 80, oversold: 20 } },
  williamsR: { id: "williamsR", enabled: false, weight: 0.4, params: { period: 14 } },
  tsi: { id: "tsi", enabled: false, weight: 0.4, params: { long: 25, short: 13, signal: 13 } },
  ultimateOscillator: {
    id: "ultimateOscillator",
    enabled: false,
    weight: 0.4,
    params: { short: 7, medium: 14, long: 28 },
  },

  // Volatility
  atr: { id: "atr", enabled: true, weight: 0.8, params: { period: 14 } },
  bollinger: { id: "bollinger", enabled: true, weight: 0.7, params: { period: 20, stdDev: 2 } },
  keltner: { id: "keltner", enabled: false, weight: 0.5, params: { period: 20, multiplier: 2 } },
  donchian: { id: "donchian", enabled: false, weight: 0.5, params: { period: 20 } },
  stdDev: { id: "stdDev", enabled: false, weight: 0.3, params: { period: 20 } },

  // Volume
  obv: { id: "obv", enabled: true, weight: 0.7, params: {} },
  vwap: { id: "vwap", enabled: true, weight: 0.7, params: { period: 20 } },
  cmf: { id: "cmf", enabled: false, weight: 0.5, params: { period: 20 } },
  adLine: { id: "adLine", enabled: false, weight: 0.4, params: {} },
  volumeOscillator: {
    id: "volumeOscillator",
    enabled: false,
    weight: 0.4,
    params: { fast: 5, slow: 20 },
  },
  nvi: { id: "nvi", enabled: false, weight: 0.3, params: {} },
  pvi: { id: "pvi", enabled: false, weight: 0.3, params: {} },
};

/** Specification rule 6 sample allocation — user-editable. */
export const DEFAULT_WEIGHTS: WeightsConfig = {
  technical: 30,
  fundamental: 20,
  smartMoney: 15,
  codal: 10,
  news: 10,
  liquidity: 5,
  risk: 5,
  ai: 5,
};

export const DEFAULT_CONFIG: AppConfig = appConfigSchema.parse({
  version: "0.2.0",
  locale: "fa-IR",
  indicators: DEFAULT_INDICATORS,
  weights: DEFAULT_WEIGHTS,
  timeframes: {
    active: ["15m", "1h", "4h", "1D", "1W"],
    trend: "1W",
    structure: "1D",
    momentum: "4h",
    entry: "1h",
  },
  scheduler: {
    interval: "15m",
    pauseWhenHidden: true,
    maxRetries: 3,
    retryBackoffMs: 2_000,
    staleAfterMs: 20 * 60_000,
  },
  risk: {
    riskPerTradePct: 1,
    maxPortfolioRiskPct: 6,
    maxPositions: 10,
    minRiskReward: 1.5,
    atrStopMultiple: 2,
    maxDrawdownPct: 20,
  },
  ai: {
    enabled: true,
    minConfidence: 55,
    requireRealData: true,
  },
  providers: {
    market: "mock",
    news: "none",
    codal: "none",
    fundamental: "none",
    allowDemoFallback: true,
    timeoutMs: 10_000,
  },
} satisfies AppConfig);
