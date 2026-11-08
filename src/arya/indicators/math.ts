/**
 * Pure numeric helpers shared by every indicator.
 * No I/O, no React, fully deterministic and testable.
 */
import type { Candle } from "@/arya/core/types";

export const at = (xs: readonly number[], i: number): number => xs[i] ?? Number.NaN;
export const last = (xs: readonly number[]): number => (xs.length ? (xs[xs.length - 1] as number) : Number.NaN);
export const prev = (xs: readonly number[], back = 1): number =>
  xs.length > back ? (xs[xs.length - 1 - back] as number) : Number.NaN;

export const closes = (c: readonly Candle[]): number[] => c.map((x) => x.close);
export const highs = (c: readonly Candle[]): number[] => c.map((x) => x.high);
export const lows = (c: readonly Candle[]): number[] => c.map((x) => x.low);
export const volumes = (c: readonly Candle[]): number[] => c.map((x) => x.volume);
export const typicals = (c: readonly Candle[]): number[] => c.map((x) => (x.high + x.low + x.close) / 3);

export function clamp(n: number, min: number, max: number): number {
  if (!Number.isFinite(n)) return min;
  return Math.min(max, Math.max(min, n));
}

export const clamp01 = (n: number): number => clamp(n, 0, 1);

/** Simple moving average; leading positions are NaN. */
export function sma(values: readonly number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(Number.NaN);
  if (period <= 0) return out;
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += at(values, i);
    if (i >= period) sum -= at(values, i - period);
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

/** Exponential moving average seeded with the first SMA value. */
export function ema(values: readonly number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(Number.NaN);
  if (period <= 0 || values.length < period) return out;
  const k = 2 / (period + 1);
  let acc = 0;
  for (let i = 0; i < period; i++) acc += at(values, i);
  let e = acc / period;
  out[period - 1] = e;
  for (let i = period; i < values.length; i++) {
    e = at(values, i) * k + e * (1 - k);
    out[i] = e;
  }
  return out;
}

/** Wilder's smoothing (used by RSI, ATR, ADX). */
export function rma(values: readonly number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(Number.NaN);
  if (period <= 0 || values.length < period) return out;
  let acc = 0;
  for (let i = 0; i < period; i++) acc += at(values, i);
  let r = acc / period;
  out[period - 1] = r;
  for (let i = period; i < values.length; i++) {
    r = (r * (period - 1) + at(values, i)) / period;
    out[i] = r;
  }
  return out;
}

/** Linear weighted moving average. */
export function wma(values: readonly number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(Number.NaN);
  if (period <= 0) return out;
  const denom = (period * (period + 1)) / 2;
  for (let i = period - 1; i < values.length; i++) {
    let acc = 0;
    for (let k = 0; k < period; k++) acc += at(values, i - period + 1 + k) * (k + 1);
    out[i] = acc / denom;
  }
  return out;
}

/** Rolling population standard deviation. */
export function stdDev(values: readonly number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(Number.NaN);
  const means = sma(values, period);
  for (let i = period - 1; i < values.length; i++) {
    const m = at(means, i);
    let acc = 0;
    for (let k = 0; k < period; k++) {
      const d = at(values, i - k) - m;
      acc += d * d;
    }
    out[i] = Math.sqrt(acc / period);
  }
  return out;
}

/** True range per bar; the first bar uses high-low. */
export function trueRange(candles: readonly Candle[]): number[] {
  return candles.map((c, i) => {
    if (i === 0) return c.high - c.low;
    const p = candles[i - 1] as Candle;
    return Math.max(c.high - c.low, Math.abs(c.high - p.close), Math.abs(c.low - p.close));
  });
}

/** Slope of a value series over `lookback` bars, normalized by price scale. */
export function normalizedSlope(values: readonly number[], lookback: number, scale: number): number {
  const a = prev(values, lookback);
  const b = last(values);
  if (!Number.isFinite(a) || !Number.isFinite(b) || !scale) return 0;
  return (b - a) / lookback / scale;
}
