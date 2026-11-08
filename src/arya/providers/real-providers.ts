/**
 * Real market data adapters (Binance public market data, TSETMC).
 * Pure fetch — runs on the server. Failures degrade to UNAVAILABLE; nothing
 * is ever synthesised.
 */
import { envelope, unavailable, type DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Timeframe } from "@/arya/core/types";
import { findRealSymbol } from "./real-symbols";
import { cleanCandles } from "./candle-validation";

const BINANCE_INTERVAL: Record<Timeframe, string> = {
  "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1D": "1d", "1W": "1w", "1M": "1M",
};

async function fetchWithTimeout(url: string, ms: number, init?: RequestInit): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

export async function binanceCandles(pair: string, tf: Timeframe, limit: number): Promise<DataEnvelope<Candle[]>> {
  const url = `https://data-api.binance.vision/api/v3/klines?symbol=${encodeURIComponent(pair)}&interval=${BINANCE_INTERVAL[tf]}&limit=${limit}`;
  try {
    const res = await fetchWithTimeout(url, 10_000);
    if (!res.ok) return unavailable([], "Binance", "binance", `Binance HTTP ${res.status}`);
    const payload: unknown = await res.json();
    if (!Array.isArray(payload)) return unavailable([], "Binance", "binance", "پاسخ منبع معتبر نیست");
    const rows = payload.filter((r): r is unknown[] => Array.isArray(r));
    const candles = cleanCandles(rows.map((r) => ({
      t: Number(r[0]), open: Number(r[1]), high: Number(r[2]), low: Number(r[3]), close: Number(r[4]), volume: Number(r[5]),
    })));
    if (!candles.length) return unavailable([], "Binance", "binance", "کندل معتبر دریافت نشد");
    return envelope(candles, { source: "Binance", providerId: "binance", status: "LIVE", quality: 1 });
  } catch (e) {
    return unavailable([], "Binance", "binance", `اتصال به Binance ناموفق: ${e instanceof Error ? e.message : String(e)}`);
  }
}

interface TseDaily {
  dEven: number; priceFirst: number; priceMax: number; priceMin: number; pClosing: number; qTotTran5J: number;
}

const TSETMC_HOSTS = ["https://cdn.tsetmc.com", "https://cdn2.tsetmc.com", "http://cdn.tsetmc.com"];

async function fetchTsetmcJson(path: string): Promise<{ closingPriceDaily?: TseDaily[] }> {
  let last = "unknown";
  for (const host of TSETMC_HOSTS) {
    try {
      const res = await fetchWithTimeout(`${host}${path}`, 8_000, {
        headers: { Accept: "application/json", "User-Agent": "Mozilla/5.0", Referer: "https://www.tsetmc.com/" },
      });
      if (res.ok) return (await res.json()) as { closingPriceDaily?: TseDaily[] };
      last = `HTTP ${res.status}`;
    } catch (e) {
      last = e instanceof Error ? e.message : String(e);
    }
  }
  throw new Error(last);
}

export async function tsetmcCandles(insCode: string, tf: Timeframe, limit: number): Promise<DataEnvelope<Candle[]>> {
  if (tf !== "1D") return unavailable([], "TSETMC", "tsetmc", "بورس تهران فقط داده‌ی روزانه (1D) ارائه می‌دهد");
  try {
    const json = await fetchTsetmcJson(`/api/ClosingPrice/GetClosingPriceDailyList/${insCode}/${limit}`);
    const rows = (json.closingPriceDaily ?? []).filter((r) => r.qTotTran5J > 0);
    if (!rows.length) return unavailable([], "TSETMC", "tsetmc", "TSETMC داده‌ای برنگرداند");
    const candles = cleanCandles(rows
      .map((r) => {
        const s = String(r.dEven);
        const t = Date.UTC(+s.slice(0, 4), +s.slice(4, 6) - 1, +s.slice(6, 8));
        return { t, open: r.priceFirst, high: r.priceMax, low: r.priceMin, close: r.pClosing, volume: r.qTotTran5J };
      })
      .sort((a, b) => a.t - b.t));
    if (!candles.length) return unavailable([], "TSETMC", "tsetmc", "کندل معتبر دریافت نشد");
    return envelope(candles, { source: "TSETMC", providerId: "tsetmc", status: "LIVE", quality: 0.95 });
  } catch (e) {
    return unavailable([], "TSETMC", "tsetmc", `اتصال به بورس تهران (TSETMC) ناموفق: ${e instanceof Error ? e.message : String(e)}`);
  }
}

export async function fetchRealCandles(symbolId: string, tf: Timeframe, limit: number): Promise<DataEnvelope<Candle[]>> {
  const sym = findRealSymbol(symbolId);
  if (!sym) return unavailable([], "—", "none", `منبع واقعی برای ${symbolId} تعریف نشده`);
  const n = Math.max(10, Math.min(limit, 1000));
  return sym.providerId === "binance" ? binanceCandles(sym.code, tf, n) : tsetmcCandles(sym.code, tf, n);
}
