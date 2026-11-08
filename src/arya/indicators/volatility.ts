/** Volatility indicators: ATR, Bollinger, Keltner, Donchian, StdDev. */
import { at, closes, clamp01, ema, highs, last, lows, prev, rma, sma, stdDev, trueRange } from "./math";
import { emptyResult, param, type IndicatorDefinition } from "./types";

export const atrIndicator: IndicatorDefinition = {
  id: "atr",
  label: "ATR",
  category: "volatility",
  minBars: (p) => param(p, "period", 14) * 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 14);
    const series = rma(trueRange(candles), period);
    const value = last(series);
    if (!Number.isFinite(value)) return emptyResult({ id: "atr", label: "ATR", category: "volatility" });
    const price = last(closes(candles)) || 1;
    const pct = (value / price) * 100;
    return {
      id: "atr",
      label: "ATR",
      category: "volatility",
      value: +value.toFixed(4),
      values: { pct: +pct.toFixed(2) },
      // Volatility is risk information, not a directional signal.
      signal: "neutral",
      strength: clamp01(pct / 6),
      note: `نوسان میانگین ${pct.toFixed(2)}٪ از قیمت`,
      series: { atr: series },
    };
  },
};

export const bollingerIndicator: IndicatorDefinition = {
  id: "bollinger",
  label: "باند بولینگر",
  category: "volatility",
  minBars: (p) => param(p, "period", 20) + 5,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const mult = param(params, "stdDev", 2);
    const c = closes(candles);
    const mid = sma(c, period);
    const sd = stdDev(c, period);
    const upper = mid.map((m, i) => m + mult * at(sd, i));
    const lower = mid.map((m, i) => m - mult * at(sd, i));
    const width = mid.map((m, i) => (m ? ((at(upper, i) - at(lower, i)) / m) * 100 : Number.NaN));
    const price = last(c);
    const u = last(upper);
    const l = last(lower);
    if (!Number.isFinite(u)) return emptyResult({ id: "bollinger", label: "باند بولینگر", category: "volatility" });
    const pctB = u === l ? 0.5 : (price - l) / (u - l);
    const squeezing = Number.isFinite(prev(width, 5)) && last(width) < prev(width, 5);
    return {
      id: "bollinger",
      label: "باند بولینگر",
      category: "volatility",
      value: +pctB.toFixed(3),
      values: { upper: +u.toFixed(2), lower: +l.toFixed(2), width: +last(width).toFixed(2) },
      signal: pctB > 1 ? "bearish" : pctB < 0 ? "bullish" : pctB > 0.5 ? "bullish" : "bearish",
      strength: clamp01(Math.abs(pctB - 0.5) * 1.6),
      note: squeezing ? "فشردگی باندها؛ احتمال انفجار نوسان" : `موقعیت قیمت در باند: ${(pctB * 100).toFixed(0)}٪`,
      series: { upper, middle: mid, lower, width },
    };
  },
};

export const keltnerIndicator: IndicatorDefinition = {
  id: "keltner",
  label: "کانال کلتنر",
  category: "volatility",
  minBars: (p) => param(p, "period", 20) + 5,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const mult = param(params, "multiplier", 2);
    const c = closes(candles);
    const mid = ema(c, period);
    const atr = rma(trueRange(candles), period);
    const upper = mid.map((m, i) => m + mult * at(atr, i));
    const lower = mid.map((m, i) => m - mult * at(atr, i));
    const price = last(c);
    if (!Number.isFinite(last(upper)))
      return emptyResult({ id: "keltner", label: "کانال کلتنر", category: "volatility" });
    const pos = (price - last(lower)) / (last(upper) - last(lower));
    return {
      id: "keltner",
      label: "کانال کلتنر",
      category: "volatility",
      value: +pos.toFixed(3),
      values: { upper: +last(upper).toFixed(2), lower: +last(lower).toFixed(2) },
      signal: pos > 0.5 ? "bullish" : "bearish",
      strength: clamp01(Math.abs(pos - 0.5) * 1.6),
      note: `موقعیت قیمت در کانال: ${(pos * 100).toFixed(0)}٪`,
      series: { upper, middle: mid, lower },
    };
  },
};

export const donchianIndicator: IndicatorDefinition = {
  id: "donchian",
  label: "کانال دونچیان",
  category: "volatility",
  minBars: (p) => param(p, "period", 20) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const h = highs(candles);
    const l = lows(candles);
    const upper: number[] = new Array(candles.length).fill(Number.NaN);
    const lower: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = period - 1; i < candles.length; i++) {
      upper[i] = Math.max(...h.slice(i - period + 1, i + 1));
      lower[i] = Math.min(...l.slice(i - period + 1, i + 1));
    }
    const price = last(closes(candles));
    if (!Number.isFinite(last(upper)))
      return emptyResult({ id: "donchian", label: "کانال دونچیان", category: "volatility" });
    const breakoutUp = price >= last(upper);
    const breakoutDown = price <= last(lower);
    const pos = (price - last(lower)) / (last(upper) - last(lower) || 1);
    return {
      id: "donchian",
      label: "کانال دونچیان",
      category: "volatility",
      value: +pos.toFixed(3),
      values: { upper: +last(upper).toFixed(2), lower: +last(lower).toFixed(2) },
      signal: breakoutUp ? "bullish" : breakoutDown ? "bearish" : pos > 0.5 ? "bullish" : "bearish",
      strength: clamp01(breakoutUp || breakoutDown ? 0.9 : Math.abs(pos - 0.5) * 1.4),
      note: breakoutUp
        ? `شکست سقف ${period} کندلی`
        : breakoutDown
          ? `شکست کف ${period} کندلی`
          : `قیمت داخل کانال ${period} کندلی`,
      series: { upper, lower },
    };
  },
};

export const stdDevIndicator: IndicatorDefinition = {
  id: "stdDev",
  label: "انحراف معیار",
  category: "volatility",
  minBars: (p) => param(p, "period", 20) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const series = stdDev(closes(candles), period);
    const value = last(series);
    if (!Number.isFinite(value))
      return emptyResult({ id: "stdDev", label: "انحراف معیار", category: "volatility" });
    const price = last(closes(candles)) || 1;
    return {
      id: "stdDev",
      label: "انحراف معیار",
      category: "volatility",
      value: +value.toFixed(4),
      signal: "neutral",
      strength: clamp01((value / price) * 40),
      note: `پراکندگی قیمت ${((value / price) * 100).toFixed(2)}٪`,
      series: { stdDev: series },
    };
  },
};

export const VOLATILITY_INDICATORS = [
  atrIndicator,
  bollingerIndicator,
  keltnerIndicator,
  donchianIndicator,
  stdDevIndicator,
];
