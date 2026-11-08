/**
 * Parser for the TSETMC "MarketWatchPlus" daily Excel export (دیده‌بان بازار).
 * Pure: takes the sheet as rows of cells, returns one validated bar per symbol.
 */
import type { Candle } from "@/arya/core/types";
import { validCandle } from "./candle-validation";

export interface DailySnapshot {
  /** Jalali date as written in the file, e.g. 1405/08/11. */
  jalali: string;
  /** Bar time (UTC midnight of the Gregorian trading day). */
  t: number;
  /** ticker → [open, high, low, close, volume] */
  bars: Record<string, [number, number, number, number, number]>;
}

export const normalizeTicker = (s: string) =>
  s.replace(/ي/g, "ی").replace(/ك/g, "ک").replace(/\u200c/g, "").trim();

/** Jalali → Gregorian (standard arithmetic algorithm). */
export function jalaliToGregorian(jy: number, jm: number, jd: number): [number, number, number] {
  jy += 1595;
  let days = -355668 + 365 * jy + Math.floor(jy / 33) * 8 + Math.floor(((jy % 33) + 3) / 4) + jd
    + (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
  let gy = 400 * Math.floor(days / 146097);
  days %= 146097;
  if (days > 36524) {
    gy += 100 * Math.floor(--days / 36524);
    days %= 36524;
    if (days >= 365) days++;
  }
  gy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) {
    gy += Math.floor((days - 1) / 365);
    days = (days - 1) % 365;
  }
  let gd = days + 1;
  const leap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0;
  const ml = [0, 31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm = 1;
  for (; gm <= 12 && gd > ml[gm]!; gm++) gd -= ml[gm]!;
  return [gy, gm, gd];
}

const num = (v: unknown) => (typeof v === "number" ? v : Number(String(v ?? "").replace(/,/g, "")));

export function parseMarketWatch(rows: unknown[][], fileName = ""): DailySnapshot {
  const text = rows.slice(0, 5).map((r) => r.map(String).join(" ")).join(" ") + " " + fileName;
  const m = text.match(/(1[34]\d\d)[/_-](\d{1,2})[/_-](\d{1,2})/);
  if (!m) throw new Error("تاریخ معاملات در فایل پیدا نشد");
  const [gy, gm, gd] = jalaliToGregorian(+m[1]!, +m[2]!, +m[3]!);
  const headerIdx = rows.findIndex((r) => normalizeTicker(String(r[0] ?? "")) === "نماد");
  if (headerIdx < 0) throw new Error("این فایل دیده‌بان بازار (MarketWatchPlus) نیست");
  const bars: DailySnapshot["bars"] = {};
  for (const r of rows.slice(headerIdx + 1)) {
    const ticker = normalizeTicker(String(r[0] ?? ""));
    if (!ticker) continue;
    // columns: 3 volume, 6 first, 10 closing, 13 low, 14 high
    const c: Candle = { t: 1, open: num(r[6]), high: num(r[14]), low: num(r[13]), close: num(r[10]), volume: num(r[3]) };
    if (c.volume > 0 && validCandle(c)) bars[ticker] = [c.open, c.high, c.low, c.close, c.volume];
  }
  if (!Object.keys(bars).length) throw new Error("هیچ ردیف معتبری در فایل نبود");
  return { jalali: `${m[1]}/${m[2]!.padStart(2, "0")}/${m[3]!.padStart(2, "0")}`, t: Date.UTC(gy, gm - 1, gd), bars };
}

/** Build a candle history for one ticker from stored daily snapshots. */
export function candlesFromSnapshots(snaps: DailySnapshot[], ticker: string): Candle[] {
  const key = normalizeTicker(ticker);
  return snaps
    .flatMap((s) => {
      const b = s.bars[key];
      return b ? [{ t: s.t, open: b[0], high: b[1], low: b[2], close: b[3], volume: b[4] }] : [];
    })
    .sort((a, b) => a.t - b.t);
}
