/**
 * MockProvider — deterministic synthetic data for development only.
 *
 * Everything it returns is stamped `DEMO`. It exists so the UI and the
 * engines can be built and tested before real adapters land; it must never
 * be blended with real provider output.
 */
import { demo, type DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Market, Symbol, Timeframe } from "@/arya/core/types";
import { TIMEFRAME_MS } from "@/arya/core/types";

import type {
  MarketDataProvider,
  OhlcvRequest,
  ProviderInfo,
  QuoteSnapshot,
} from "./base";

const INFO: ProviderInfo = {
  id: "mock",
  name: "MockProvider",
  kind: "demo",
  markets: ["iran-equity", "crypto", "forex", "index"],
  description: "داده‌های شبیه‌سازی‌شده و تکرارپذیر برای توسعه — داده واقعی بازار نیست.",
};

export const MOCK_SYMBOLS: Symbol[] = [
  { id: "iran-equity:FOLD", ticker: "فولاد", name: "فولاد مبارکه اصفهان", market: "iran-equity", currency: "IRR" },
  { id: "iran-equity:KHODRO", ticker: "خودرو", name: "ایران خودرو", market: "iran-equity", currency: "IRR" },
  { id: "iran-equity:SHEPNA", ticker: "شپنا", name: "پالایش نفت اصفهان", market: "iran-equity", currency: "IRR" },
  { id: "iran-equity:VBMELLAT", ticker: "وبملت", name: "بانک ملت", market: "iran-equity", currency: "IRR" },
  { id: "crypto:BTCUSDT", ticker: "BTCUSDT", name: "Bitcoin / Tether", market: "crypto", currency: "USDT" },
  { id: "crypto:ETHUSDT", ticker: "ETHUSDT", name: "Ethereum / Tether", market: "crypto", currency: "USDT" },
  { id: "forex:EURUSD", ticker: "EURUSD", name: "Euro / US Dollar", market: "forex", currency: "USD" },
];

const BASE_PRICE: Record<string, number> = {
  "iran-equity:FOLD": 4600,
  "iran-equity:KHODRO": 2350,
  "iran-equity:SHEPNA": 8100,
  "iran-equity:VBMELLAT": 3450,
  "crypto:BTCUSDT": 64000,
  "crypto:ETHUSDT": 3100,
  "forex:EURUSD": 1.09,
};

/** Deterministic PRNG so a symbol always renders the same demo series. */
function mulberry32(seed: number) {
  let s = seed;
  return () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seedOf(key: string): number {
  return [...key].reduce((a, c) => a + c.charCodeAt(0) * 31, 7);
}

/**
 * Generate a reproducible OHLCV series. `endTime` is fixed by the caller so
 * output stays deterministic (no `Date.now()` at module scope).
 */
export function generateCandles(
  symbolId: string,
  timeframe: Timeframe,
  count: number,
  endTime: number,
): Candle[] {
  const rnd = mulberry32(seedOf(`${symbolId}:${timeframe}`));
  const step = TIMEFRAME_MS[timeframe];
  const base = BASE_PRICE[symbolId] ?? 1000;
  const out: Candle[] = [];
  let price = base;

  for (let i = 0; i < count; i++) {
    const drift = Math.sin(i / 11) * 0.006 + Math.sin(i / 29) * 0.004 + 0.0009;
    const shock = (rnd() - 0.5) * 0.022;
    const open = price;
    const close = Math.max(base * 0.2, open * (1 + drift + shock));
    const high = Math.max(open, close) * (1 + rnd() * 0.008);
    const low = Math.min(open, close) * (1 - rnd() * 0.008);
    out.push({
      t: endTime - (count - 1 - i) * step,
      open,
      high,
      low,
      close,
      volume: Math.round(rnd() * 40_000 + 8_000),
    });
    price = close;
  }
  return out;
}

export class MockProvider implements MarketDataProvider {
  readonly info = INFO;

  constructor(private readonly now: () => number = () => Date.now()) {}

  async health(): Promise<DataEnvelope<{ ok: boolean }>> {
    return demo({ ok: true }, INFO.name, INFO.id, this.now());
  }

  async listSymbols(market?: Market): Promise<DataEnvelope<Symbol[]>> {
    const list = market ? MOCK_SYMBOLS.filter((s) => s.market === market) : MOCK_SYMBOLS;
    return demo(list, INFO.name, INFO.id, this.now());
  }

  async getQuote(symbolId: string): Promise<DataEnvelope<QuoteSnapshot | null>> {
    const now = this.now();
    const candles = generateCandles(symbolId, "1D", 2, now);
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2];
    if (!last || !prev) return demo(null, INFO.name, INFO.id, now);
    return demo(
      {
        symbolId,
        price: last.close,
        changePct: ((last.close - prev.close) / prev.close) * 100,
        volume: last.volume,
        updatedAt: last.t,
      },
      INFO.name,
      INFO.id,
      now,
    );
  }

  async getOhlcv(request: OhlcvRequest): Promise<DataEnvelope<Candle[]>> {
    const now = this.now();
    const limit = Math.max(1, Math.min(request.limit, 2000));
    return demo(
      generateCandles(request.symbolId, request.timeframe, limit, now),
      INFO.name,
      INFO.id,
      now,
    );
  }
}
