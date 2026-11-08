/** Momentum indicators: RSI, MACD, Stochastic, CCI, ROC, MFI, Williams %R. */
import type { Candle, Direction } from "@/arya/core/types";
import { at, closes, clamp01, ema, highs, last, lows, prev, rma, sma, typicals } from "./math";
import { emptyResult, param, type IndicatorDefinition } from "./types";

/** Maps an oscillator reading to a direction using overbought/oversold bounds. */
function oscillatorSignal(value: number, oversold: number, overbought: number): Direction {
  if (value <= oversold) return "bullish";
  if (value >= overbought) return "bearish";
  return value > 50 ? "bullish" : value < 50 ? "bearish" : "neutral";
}

export function rsiSeries(values: readonly number[], period: number): number[] {
  const gains: number[] = [0];
  const losses: number[] = [0];
  for (let i = 1; i < values.length; i++) {
    const d = at(values, i) - at(values, i - 1);
    gains.push(d > 0 ? d : 0);
    losses.push(d < 0 ? -d : 0);
  }
  const avgGain = rma(gains, period);
  const avgLoss = rma(losses, period);
  return avgGain.map((g, i) => {
    const l = at(avgLoss, i);
    if (!Number.isFinite(g) || !Number.isFinite(l)) return Number.NaN;
    if (g === 0 && l === 0) return 50;
    if (l === 0) return 100;
    const rs = g / l;
    return 100 - 100 / (1 + rs);
  });
}

export const rsiIndicator: IndicatorDefinition = {
  id: "rsi",
  label: "RSI",
  category: "momentum",
  minBars: (p) => param(p, "period", 14) * 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 14);
    const overbought = param(params, "overbought", 70);
    const oversold = param(params, "oversold", 30);
    const series = rsiSeries(closes(candles), period);
    const value = last(series);
    if (!Number.isFinite(value)) return emptyResult({ id: "rsi", label: "RSI", category: "momentum" });
    const signal = oscillatorSignal(value, oversold, overbought);
    const extreme = value <= oversold || value >= overbought;
    return {
      id: "rsi",
      label: "RSI",
      category: "momentum",
      value: +value.toFixed(2),
      signal,
      strength: clamp01(Math.abs(value - 50) / 30) * (extreme ? 1 : 0.7),
      note:
        value >= overbought
          ? `اشباع خرید در ${value.toFixed(1)}`
          : value <= oversold
            ? `اشباع فروش در ${value.toFixed(1)}`
            : `مومنتوم ${value > 50 ? "مثبت" : "منفی"} در ${value.toFixed(1)}`,
      series: { rsi: series },
    };
  },
};

export const macdIndicator: IndicatorDefinition = {
  id: "macd",
  label: "MACD",
  category: "momentum",
  minBars: (p) => param(p, "slow", 26) + param(p, "signal", 9) + 5,
  compute: ({ candles, params }) => {
    const fast = param(params, "fast", 12);
    const slow = param(params, "slow", 26);
    const signalPeriod = param(params, "signal", 9);
    const c = closes(candles);
    const fastLine = ema(c, fast);
    const slowLine = ema(c, slow);
    const macd = fastLine.map((v, i) => v - at(slowLine, i));
    const valid = macd.filter((v) => Number.isFinite(v));
    const signalTail = ema(valid, signalPeriod);
    const offset = macd.length - valid.length;
    const signalLine: number[] = new Array(macd.length).fill(Number.NaN);
    signalTail.forEach((v, i) => {
      signalLine[i + offset] = v;
    });
    const hist = macd.map((v, i) => v - at(signalLine, i));

    const value = last(macd);
    const sig = last(signalLine);
    const h = last(hist);
    if (!Number.isFinite(h)) return emptyResult({ id: "macd", label: "MACD", category: "momentum" });
    const crossed = Number.isFinite(prev(hist)) && Math.sign(h) !== Math.sign(prev(hist));
    const price = last(c) || 1;
    const dirValue = Math.abs(h) / price > 1e-4 ? h : value;
    return {
      id: "macd",
      label: "MACD",
      category: "momentum",
      value: +value.toFixed(4),
      values: { signal: +sig.toFixed(4), histogram: +h.toFixed(4) },
      // When the histogram is numerically negligible the MACD line itself
      // carries the direction, otherwise the crossover dominates.
      signal: dirValue > 0 ? "bullish" : dirValue < 0 ? "bearish" : "neutral",
      strength: clamp01((Math.abs(h) / price) * 300 + (crossed ? 0.3 : 0.1)),
      note: crossed
        ? `تقاطع ${h > 0 ? "صعودی" : "نزولی"} خط سیگنال`
        : `هیستوگرام ${h > 0 ? "مثبت" : "منفی"}`,
      series: { macd, signal: signalLine, histogram: hist },
    };
  },
};

export const stochasticIndicator: IndicatorDefinition = {
  id: "stochastic",
  label: "استوکاستیک",
  category: "momentum",
  minBars: (p) => param(p, "k", 14) + param(p, "smooth", 3) + param(p, "d", 3),
  compute: ({ candles, params }) => {
    const kPeriod = param(params, "k", 14);
    const dPeriod = param(params, "d", 3);
    const smooth = param(params, "smooth", 3);
    const overbought = param(params, "overbought", 80);
    const oversold = param(params, "oversold", 20);
    const h = highs(candles);
    const l = lows(candles);
    const c = closes(candles);
    const rawK: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = kPeriod - 1; i < candles.length; i++) {
      const hh = Math.max(...h.slice(i - kPeriod + 1, i + 1));
      const ll = Math.min(...l.slice(i - kPeriod + 1, i + 1));
      rawK[i] = hh === ll ? 50 : ((at(c, i) - ll) / (hh - ll)) * 100;
    }
    const kLine = sma(rawK.map((v) => (Number.isFinite(v) ? v : 50)), smooth);
    const dLine = sma(kLine, dPeriod);
    const value = last(kLine);
    if (!Number.isFinite(value))
      return emptyResult({ id: "stochastic", label: "استوکاستیک", category: "momentum" });
    return {
      id: "stochastic",
      label: "استوکاستیک",
      category: "momentum",
      value: +value.toFixed(2),
      values: { d: +last(dLine).toFixed(2) },
      signal: oscillatorSignal(value, oversold, overbought),
      strength: clamp01(Math.abs(value - 50) / 40),
      note:
        value >= overbought
          ? `اشباع خرید ${value.toFixed(0)}`
          : value <= oversold
            ? `اشباع فروش ${value.toFixed(0)}`
            : `%K برابر ${value.toFixed(0)}`,
      series: { k: kLine, d: dLine },
    };
  },
};

export const cciIndicator: IndicatorDefinition = {
  id: "cci",
  label: "CCI",
  category: "momentum",
  minBars: (p) => param(p, "period", 20) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const tp = typicals(candles);
    const avg = sma(tp, period);
    const out: number[] = new Array(tp.length).fill(Number.NaN);
    for (let i = period - 1; i < tp.length; i++) {
      let dev = 0;
      for (let k = 0; k < period; k++) dev += Math.abs(at(tp, i - k) - at(avg, i));
      const md = dev / period;
      out[i] = md === 0 ? 0 : (at(tp, i) - at(avg, i)) / (0.015 * md);
    }
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "cci", label: "CCI", category: "momentum" });
    return {
      id: "cci",
      label: "CCI",
      category: "momentum",
      value: +value.toFixed(2),
      signal: value > 100 ? "bullish" : value < -100 ? "bearish" : value > 0 ? "bullish" : "bearish",
      strength: clamp01(Math.abs(value) / 200),
      note: `CCI برابر ${value.toFixed(0)}`,
      series: { cci: out },
    };
  },
};

export const rocIndicator: IndicatorDefinition = {
  id: "roc",
  label: "نرخ تغییر",
  category: "momentum",
  minBars: (p) => param(p, "period", 12) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 12);
    const c = closes(candles);
    const out = c.map((v, i) => (i >= period && at(c, i - period) ? ((v - at(c, i - period)) / at(c, i - period)) * 100 : Number.NaN));
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "roc", label: "نرخ تغییر", category: "momentum" });
    return {
      id: "roc",
      label: "نرخ تغییر",
      category: "momentum",
      value: +value.toFixed(2),
      signal: value > 0.2 ? "bullish" : value < -0.2 ? "bearish" : "neutral",
      strength: clamp01(Math.abs(value) / 8),
      note: `تغییر ${value.toFixed(2)}٪ در ${period} کندل اخیر`,
      series: { roc: out },
    };
  },
};

export const mfiIndicator: IndicatorDefinition = {
  id: "mfi",
  label: "MFI",
  category: "momentum",
  minBars: (p) => param(p, "period", 14) + 3,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 14);
    const overbought = param(params, "overbought", 80);
    const oversold = param(params, "oversold", 20);
    const tp = typicals(candles);
    const out: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = period; i < candles.length; i++) {
      let pos = 0;
      let neg = 0;
      for (let k = i - period + 1; k <= i; k++) {
        const flow = at(tp, k) * (candles[k] as Candle).volume;
        if (at(tp, k) > at(tp, k - 1)) pos += flow;
        else if (at(tp, k) < at(tp, k - 1)) neg += flow;
      }
      out[i] = neg === 0 ? 100 : 100 - 100 / (1 + pos / neg);
    }
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "mfi", label: "MFI", category: "momentum" });
    return {
      id: "mfi",
      label: "MFI",
      category: "momentum",
      value: +value.toFixed(2),
      signal: oscillatorSignal(value, oversold, overbought),
      strength: clamp01(Math.abs(value - 50) / 35),
      note: `جریان نقدینگی ${value.toFixed(0)}`,
      series: { mfi: out },
    };
  },
};

export const williamsRIndicator: IndicatorDefinition = {
  id: "williamsR",
  label: "ویلیامز %R",
  category: "momentum",
  minBars: (p) => param(p, "period", 14) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 14);
    const h = highs(candles);
    const l = lows(candles);
    const c = closes(candles);
    const out: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = period - 1; i < candles.length; i++) {
      const hh = Math.max(...h.slice(i - period + 1, i + 1));
      const ll = Math.min(...l.slice(i - period + 1, i + 1));
      out[i] = hh === ll ? -50 : ((hh - at(c, i)) / (hh - ll)) * -100;
    }
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "williamsR", label: "ویلیامز %R", category: "momentum" });
    return {
      id: "williamsR",
      label: "ویلیامز %R",
      category: "momentum",
      value: +value.toFixed(2),
      signal: value <= -80 ? "bullish" : value >= -20 ? "bearish" : value > -50 ? "bullish" : "bearish",
      strength: clamp01(Math.abs(value + 50) / 40),
      note: `%R برابر ${value.toFixed(0)}`,
      series: { williamsR: out },
    };
  },
};

export const MOMENTUM_INDICATORS = [
  rsiIndicator,
  macdIndicator,
  stochasticIndicator,
  cciIndicator,
  rocIndicator,
  mfiIndicator,
  williamsRIndicator,
];
