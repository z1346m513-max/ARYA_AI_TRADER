/** Trend indicators: moving averages, SuperTrend, ADX. */
import type { Candle, Direction } from "@/arya/core/types";
import {
  at,
  closes,
  clamp01,
  ema,
  highs,
  last,
  lows,
  normalizedSlope,
  prev,
  rma,
  sma,
  trueRange,
  wma,
} from "./math";
import { emptyResult, param, type IndicatorDefinition, type IndicatorResult } from "./types";

function maResult(
  id: string,
  label: string,
  line: number[],
  price: number,
  period: number,
): IndicatorResult {
  const value = last(line);
  if (!Number.isFinite(value)) return emptyResult({ id, label, category: "trend" });
  const distance = (price - value) / value;
  const slope = normalizedSlope(line, Math.min(period, line.length - 1), value);
  const direction: Direction = distance > 0.002 ? "bullish" : distance < -0.002 ? "bearish" : "neutral";
  const strength = clamp01(Math.abs(distance) * 20 + Math.abs(slope) * 200);
  return {
    id,
    label,
    category: "trend",
    value: +value.toFixed(4),
    signal: direction,
    strength,
    note:
      direction === "bullish"
        ? `قیمت ${(distance * 100).toFixed(2)}٪ بالای میانگین ${period} دوره‌ای است`
        : direction === "bearish"
          ? `قیمت ${(Math.abs(distance) * 100).toFixed(2)}٪ زیر میانگین ${period} دوره‌ای است`
          : `قیمت روی میانگین ${period} دوره‌ای در نوسان است`,
    series: { line },
  };
}

export const smaIndicator: IndicatorDefinition = {
  id: "sma",
  label: "میانگین متحرک ساده",
  category: "trend",
  minBars: (p) => param(p, "period", 50) + 1,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 50);
    return maResult("sma", "میانگین متحرک ساده", sma(closes(candles), period), last(closes(candles)), period);
  },
};

export const emaIndicator: IndicatorDefinition = {
  id: "ema",
  label: "میانگین متحرک نمایی",
  category: "trend",
  minBars: (p) => param(p, "period", 20) + 1,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    return maResult("ema", "میانگین متحرک نمایی", ema(closes(candles), period), last(closes(candles)), period);
  },
};

export const wmaIndicator: IndicatorDefinition = {
  id: "wma",
  label: "میانگین متحرک وزنی",
  category: "trend",
  minBars: (p) => param(p, "period", 20) + 1,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    return maResult("wma", "میانگین متحرک وزنی", wma(closes(candles), period), last(closes(candles)), period);
  },
};

/** ATR-based SuperTrend with proper band locking. */
export const supertrendIndicator: IndicatorDefinition = {
  id: "supertrend",
  label: "سوپرترند",
  category: "trend",
  minBars: (p) => param(p, "period", 10) * 3,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 10);
    const mult = param(params, "multiplier", 3);
    const atr = rma(trueRange(candles), period);
    const line: number[] = new Array(candles.length).fill(Number.NaN);
    const dir: number[] = new Array(candles.length).fill(Number.NaN);
    let upper = Number.NaN;
    let lower = Number.NaN;
    let trend = 1;

    for (let i = 0; i < candles.length; i++) {
      const c = candles[i] as Candle;
      const a = at(atr, i);
      if (!Number.isFinite(a)) continue;
      const mid = (c.high + c.low) / 2;
      const rawUpper = mid + mult * a;
      const rawLower = mid - mult * a;
      const p = candles[i - 1];
      upper = Number.isFinite(upper) && p && (rawUpper < upper || p.close > upper) ? Math.min(rawUpper, upper) : rawUpper;
      lower = Number.isFinite(lower) && p && (rawLower > lower || p.close < lower) ? Math.max(rawLower, lower) : rawLower;
      if (c.close > upper) trend = 1;
      else if (c.close < lower) trend = -1;
      dir[i] = trend;
      line[i] = trend === 1 ? lower : upper;
    }

    const value = last(line);
    if (!Number.isFinite(value)) return emptyResult({ id: "supertrend", label: "سوپرترند", category: "trend" });
    const price = last(closes(candles));
    const bull = last(dir) === 1;
    const flipped = last(dir) !== prev(dir);
    return {
      id: "supertrend",
      label: "سوپرترند",
      category: "trend",
      value: +value.toFixed(4),
      signal: bull ? "bullish" : "bearish",
      strength: clamp01(Math.abs(price - value) / value * 12 + (flipped ? 0.35 : 0.2)),
      note: flipped
        ? `تغییر فاز سوپرترند به ${bull ? "صعودی" : "نزولی"}`
        : `روند ${bull ? "صعودی" : "نزولی"} با حد ${value.toFixed(0)}`,
      series: { line, direction: dir },
    };
  },
};

/** ADX with +DI/-DI (Wilder). */
export const adxIndicator: IndicatorDefinition = {
  id: "adx",
  label: "ADX",
  category: "trend",
  minBars: (p) => param(p, "period", 14) * 3,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 14);
    const threshold = param(params, "trendThreshold", 25);
    const h = highs(candles);
    const l = lows(candles);
    const plusDM: number[] = [0];
    const minusDM: number[] = [0];
    for (let i = 1; i < candles.length; i++) {
      const up = at(h, i) - at(h, i - 1);
      const down = at(l, i - 1) - at(l, i);
      plusDM.push(up > down && up > 0 ? up : 0);
      minusDM.push(down > up && down > 0 ? down : 0);
    }
    const atr = rma(trueRange(candles), period);
    const pdi = rma(plusDM, period).map((v, i) => (at(atr, i) ? (v / at(atr, i)) * 100 : Number.NaN));
    const mdi = rma(minusDM, period).map((v, i) => (at(atr, i) ? (v / at(atr, i)) * 100 : Number.NaN));
    const dx = pdi.map((v, i) => {
      const m = at(mdi, i);
      const sum = v + m;
      return sum ? (Math.abs(v - m) / sum) * 100 : Number.NaN;
    });
    const adx = rma(
      dx.map((v) => (Number.isFinite(v) ? v : 0)),
      period,
    );

    const value = last(adx);
    if (!Number.isFinite(value)) return emptyResult({ id: "adx", label: "ADX", category: "trend" });
    const bull = last(pdi) > last(mdi);
    const trending = value >= threshold;
    return {
      id: "adx",
      label: "ADX",
      category: "trend",
      value: +value.toFixed(2),
      values: { plusDI: +last(pdi).toFixed(2), minusDI: +last(mdi).toFixed(2) },
      signal: trending ? (bull ? "bullish" : "bearish") : "neutral",
      strength: clamp01((value - 15) / 35) * (trending ? 1 : 0.4),
      note: trending
        ? `روند ${bull ? "صعودی" : "نزولی"} با قدرت ${value.toFixed(0)}`
        : `بازار بدون روند مشخص (ADX ${value.toFixed(0)})`,
      series: { adx, plusDI: pdi, minusDI: mdi },
    };
  },
};

export const TREND_INDICATORS = [smaIndicator, emaIndicator, wmaIndicator, supertrendIndicator, adxIndicator];
