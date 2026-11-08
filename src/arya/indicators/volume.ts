/** Volume indicators: OBV, VWAP, CMF, A/D line, volume oscillator. */
import type { Candle } from "@/arya/core/types";
import { at, closes, clamp01, last, normalizedSlope, sma, typicals, volumes } from "./math";
import { emptyResult, param, type IndicatorDefinition } from "./types";

export const obvIndicator: IndicatorDefinition = {
  id: "obv",
  label: "OBV",
  category: "volume",
  minBars: () => 20,
  compute: ({ candles }) => {
    if (candles.length < 20) return emptyResult({ id: "obv", label: "OBV", category: "volume" });
    const out: number[] = [0];
    for (let i = 1; i < candles.length; i++) {
      const c = candles[i] as Candle;
      const p = candles[i - 1] as Candle;
      const prevVal = at(out, i - 1);
      out.push(c.close > p.close ? prevVal + c.volume : c.close < p.close ? prevVal - c.volume : prevVal);
    }
    const scale = Math.max(1, Math.abs(last(out)) || 1);
    const slope = normalizedSlope(out, Math.min(14, out.length - 1), scale);
    const priceSlope = normalizedSlope(closes(candles), Math.min(14, candles.length - 1), last(closes(candles)) || 1);
    const divergence = Math.sign(slope) !== 0 && Math.sign(slope) !== Math.sign(priceSlope);
    return {
      id: "obv",
      label: "OBV",
      category: "volume",
      value: +last(out).toFixed(0),
      signal: slope > 0 ? "bullish" : slope < 0 ? "bearish" : "neutral",
      strength: clamp01(Math.abs(slope) * 40 + (divergence ? 0.25 : 0)),
      note: divergence
        ? "واگرایی حجم با قیمت"
        : `جریان حجم ${slope > 0 ? "مثبت" : "منفی"} در ۱۴ کندل اخیر`,
      series: { obv: out },
    };
  },
};

export const vwapIndicator: IndicatorDefinition = {
  id: "vwap",
  label: "VWAP",
  category: "volume",
  minBars: (p) => param(p, "period", 20) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const tp = typicals(candles);
    const v = volumes(candles);
    const out: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = period - 1; i < candles.length; i++) {
      let pv = 0;
      let vol = 0;
      for (let k = i - period + 1; k <= i; k++) {
        pv += at(tp, k) * at(v, k);
        vol += at(v, k);
      }
      out[i] = vol ? pv / vol : Number.NaN;
    }
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "vwap", label: "VWAP", category: "volume" });
    const price = last(closes(candles));
    const distance = (price - value) / value;
    return {
      id: "vwap",
      label: "VWAP",
      category: "volume",
      value: +value.toFixed(2),
      signal: distance > 0.001 ? "bullish" : distance < -0.001 ? "bearish" : "neutral",
      strength: clamp01(Math.abs(distance) * 25),
      note: `قیمت ${(distance * 100).toFixed(2)}٪ ${distance >= 0 ? "بالای" : "زیر"} VWAP`,
      series: { vwap: out },
    };
  },
};

export const cmfIndicator: IndicatorDefinition = {
  id: "cmf",
  label: "CMF",
  category: "volume",
  minBars: (p) => param(p, "period", 20) + 2,
  compute: ({ candles, params }) => {
    const period = param(params, "period", 20);
    const mfv = candles.map((c) => {
      const range = c.high - c.low;
      if (!range) return 0;
      return ((c.close - c.low - (c.high - c.close)) / range) * c.volume;
    });
    const out: number[] = new Array(candles.length).fill(Number.NaN);
    for (let i = period - 1; i < candles.length; i++) {
      let num = 0;
      let den = 0;
      for (let k = i - period + 1; k <= i; k++) {
        num += at(mfv, k);
        den += (candles[k] as Candle).volume;
      }
      out[i] = den ? num / den : Number.NaN;
    }
    const value = last(out);
    if (!Number.isFinite(value)) return emptyResult({ id: "cmf", label: "CMF", category: "volume" });
    return {
      id: "cmf",
      label: "CMF",
      category: "volume",
      value: +value.toFixed(3),
      signal: value > 0.05 ? "bullish" : value < -0.05 ? "bearish" : "neutral",
      strength: clamp01(Math.abs(value) * 4),
      note: `جریان پول ${value > 0 ? "ورودی" : "خروجی"} با شدت ${Math.abs(value).toFixed(2)}`,
      series: { cmf: out },
    };
  },
};

export const adLineIndicator: IndicatorDefinition = {
  id: "adLine",
  label: "خط انباشت/توزیع",
  category: "volume",
  minBars: () => 20,
  compute: ({ candles }) => {
    if (candles.length < 20)
      return emptyResult({ id: "adLine", label: "خط انباشت/توزیع", category: "volume" });
    const out: number[] = [];
    let acc = 0;
    for (const c of candles) {
      const range = c.high - c.low;
      acc += range ? ((c.close - c.low - (c.high - c.close)) / range) * c.volume : 0;
      out.push(acc);
    }
    const slope = normalizedSlope(out, Math.min(14, out.length - 1), Math.max(1, Math.abs(last(out)) || 1));
    return {
      id: "adLine",
      label: "خط انباشت/توزیع",
      category: "volume",
      value: +last(out).toFixed(0),
      signal: slope > 0 ? "bullish" : slope < 0 ? "bearish" : "neutral",
      strength: clamp01(Math.abs(slope) * 35),
      note: slope > 0 ? "فاز انباشت" : "فاز توزیع",
      series: { adLine: out },
    };
  },
};

export const volumeOscillatorIndicator: IndicatorDefinition = {
  id: "volumeOscillator",
  label: "نوسان‌گر حجم",
  category: "volume",
  minBars: (p) => param(p, "slow", 20) + 2,
  compute: ({ candles, params }) => {
    const fast = param(params, "fast", 5);
    const slow = param(params, "slow", 20);
    const v = volumes(candles);
    const f = sma(v, fast);
    const s = sma(v, slow);
    const out = f.map((x, i) => (at(s, i) ? ((x - at(s, i)) / at(s, i)) * 100 : Number.NaN));
    const value = last(out);
    if (!Number.isFinite(value))
      return emptyResult({ id: "volumeOscillator", label: "نوسان‌گر حجم", category: "volume" });
    return {
      id: "volumeOscillator",
      label: "نوسان‌گر حجم",
      category: "volume",
      value: +value.toFixed(2),
      // Volume expansion confirms the move, it does not choose its direction.
      signal: "neutral",
      strength: clamp01(Math.abs(value) / 60),
      note: `حجم ${value >= 0 ? "بالاتر" : "پایین‌تر"} از میانگین به میزان ${Math.abs(value).toFixed(0)}٪`,
      series: { volumeOscillator: out },
    };
  },
};

export const VOLUME_INDICATORS = [
  obvIndicator,
  vwapIndicator,
  cmfIndicator,
  adLineIndicator,
  volumeOscillatorIndicator,
];
