/**
 * ARYA AI TRADER — core domain types.
 *
 * This module is pure TypeScript: no React, no browser globals, no I/O.
 * Every engine (technical, analysis, scoring, risk, backtest) builds on
 * these types so the core stays portable and testable in isolation.
 */

/** Supported analysis timeframes, ordered from fastest to slowest. */
export const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"] as const;
export type Timeframe = (typeof TIMEFRAMES)[number];

/** Approximate duration of one bar, in milliseconds. */
export const TIMEFRAME_MS: Record<Timeframe, number> = {
  "1m": 60_000,
  "5m": 300_000,
  "15m": 900_000,
  "30m": 1_800_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1D": 86_400_000,
  "1W": 604_800_000,
  "1M": 2_592_000_000,
};

/** Market classes the platform is designed to support. */
export const MARKETS = ["iran-equity", "crypto", "forex", "commodity", "index"] as const;
export type Market = (typeof MARKETS)[number];

/** A tradable instrument. */
export interface Symbol {
  /** Stable internal id, e.g. `iran-equity:FOLD`. */
  id: string;
  /** Exchange ticker, e.g. `FOLD`, `BTCUSDT`. */
  ticker: string;
  /** Display name, may be localized. */
  name: string;
  market: Market;
  currency: string;
}

/** A single OHLCV bar. `t` is a Unix epoch in milliseconds (bar open time). */
export interface Candle {
  t: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** An OHLCV series for one symbol on one timeframe. */
export interface Series {
  symbolId: string;
  timeframe: Timeframe;
  candles: Candle[];
}

/** Direction shared by indicators, patterns and structure events. */
export type Direction = "bullish" | "bearish" | "neutral";

/** Final action vocabulary used by the scoring and recommendation engines. */
export const ACTIONS = ["STRONG_BUY", "BUY", "WATCH", "NEUTRAL", "SELL", "STRONG_SELL"] as const;
export type Action = (typeof ACTIONS)[number];
