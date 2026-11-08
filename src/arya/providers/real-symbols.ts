/** Instruments served by real providers. Browser-safe (no I/O). */
import type { Symbol } from "@/arya/core/types";

export interface RealSymbol extends Symbol {
  /** Provider-specific code: Binance pair or TSETMC instrument code. */
  code: string;
  providerId: "binance" | "tsetmc";
}

export const REAL_SYMBOLS: RealSymbol[] = [
  { id: "iran-equity:FOLD", ticker: "فولاد", name: "فولاد مبارکه اصفهان", market: "iran-equity", currency: "IRR", code: "46348559193224090", providerId: "tsetmc" },
  { id: "iran-equity:FMELI", ticker: "فملی", name: "ملی صنایع مس ایران", market: "iran-equity", currency: "IRR", code: "35425587644337450", providerId: "tsetmc" },
  { id: "iran-equity:KHODRO", ticker: "خودرو", name: "ایران خودرو", market: "iran-equity", currency: "IRR", code: "65883838195688438", providerId: "tsetmc" },
  { id: "iran-equity:SHEPNA", ticker: "شپنا", name: "پالایش نفت اصفهان", market: "iran-equity", currency: "IRR", code: "7745894403636165", providerId: "tsetmc" },
  { id: "iran-equity:VBMELLAT", ticker: "وبملت", name: "بانک ملت", market: "iran-equity", currency: "IRR", code: "778253364357513", providerId: "tsetmc" },
  { id: "iran-equity:SHASTA", ticker: "شستا", name: "سرمایه‌گذاری تامین اجتماعی", market: "iran-equity", currency: "IRR", code: "2400322364771558", providerId: "tsetmc" },
  { id: "crypto:BTCUSDT", ticker: "BTCUSDT", name: "Bitcoin / Tether", market: "crypto", currency: "USDT", code: "BTCUSDT", providerId: "binance" },
  { id: "crypto:ETHUSDT", ticker: "ETHUSDT", name: "Ethereum / Tether", market: "crypto", currency: "USDT", code: "ETHUSDT", providerId: "binance" },
  { id: "crypto:SOLUSDT", ticker: "SOLUSDT", name: "Solana / Tether", market: "crypto", currency: "USDT", code: "SOLUSDT", providerId: "binance" },
  { id: "crypto:BNBUSDT", ticker: "BNBUSDT", name: "BNB / Tether", market: "crypto", currency: "USDT", code: "BNBUSDT", providerId: "binance" },
];

export const findRealSymbol = (id: string) => REAL_SYMBOLS.find((s) => s.id === id);
