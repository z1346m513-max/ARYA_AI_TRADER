import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

import type { Candle as CoreCandle, Timeframe } from "@/arya/core/types";
import { REAL_SYMBOLS, findRealSymbol } from "@/arya/providers/real-symbols";
import { DataStatusBadge } from "@/components/arya/DataStatusBadge";
import { useMarketCandles } from "@/hooks/use-market-candles";
import type { Candle as ChartCandle } from "@/lib/arya-data";
import { CandleChart } from "./CandleChart";
import snapshot from "@/arya/providers/tse-snapshot-1405-08-11.json";

const TSE_SNAPSHOT = snapshot as Record<string, { open: number; high: number; low: number; close: number; changePct: number; volume: number }>;
import { IndicatorPanel } from "./IndicatorPanel";
import { SmartMoneyPanel } from "./SmartMoneyPanel";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D", "1W"];

function sma(values: number[], i: number, n: number): number {
  const from = Math.max(0, i - n + 1);
  const slice = values.slice(from, i + 1);
  return slice.reduce((a, b) => a + b, 0) / slice.length;
}

function toChart(candles: CoreCandle[]): ChartCandle[] {
  const closes = candles.map((c) => c.close);
  let gain = 0;
  let loss = 0;
  return candles.map((c, i) => {
    if (i > 0) {
      const d = closes[i]! - closes[i - 1]!;
      gain = (gain * 13 + Math.max(d, 0)) / 14;
      loss = (loss * 13 + Math.max(-d, 0)) / 14;
    }
    const rsi = loss === 0 ? (gain === 0 ? 50 : 100) : 100 - 100 / (1 + gain / loss);
    return {
      ...c,
      label: new Date(c.t).toISOString().slice(0, 10),
      ma20: sma(closes, i, 20),
      ma50: sma(closes, i, 50),
      rsi,
    };
  });
}

const fmt = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: n < 10 ? 4 : 2 });

export function ChartPanel() {
  const [symbolId, setSymbolId] = useState("iran-equity:FOLD");
  const [tf, setTf] = useState<Timeframe>("1D");
  const sym = findRealSymbol(symbolId)!;
  const effectiveTf: Timeframe = sym.providerId === "tsetmc" ? "1D" : tf;
  const env = useMarketCandles(symbolId, effectiveTf, 240);
  const chart = useMemo(() => (env && env.data.length > 1 ? toChart(env.data.slice(-120)) : []), [env]);

  const last = env?.data.at(-1);
  const prev = env?.data.at(-2);
  const pct = last && prev ? ((last.close - prev.close) / prev.close) * 100 : 0;

  return (
    <section className="panel flex min-w-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-2">
        <h2 className="text-[13px] font-semibold text-muted-foreground">تحلیل تکنیکال</h2>
        {env && <DataStatusBadge meta={env.meta} />}
        <select
          value={symbolId}
          onChange={(e) => setSymbolId(e.target.value)}
          className="mr-auto rounded border border-border bg-surface-2 px-2 py-1 text-[12px]"
        >
          <optgroup label="بورس تهران">
            {REAL_SYMBOLS.filter((s) => s.market === "iran-equity").map((s) => (
              <option key={s.id} value={s.id}>{s.ticker} — {s.name}</option>
            ))}
          </optgroup>
          <optgroup label="رمزارز">
            {REAL_SYMBOLS.filter((s) => s.market === "crypto").map((s) => (
              <option key={s.id} value={s.id}>{s.ticker}</option>
            ))}
          </optgroup>
        </select>
      </div>

      <div className="flex items-center gap-1 border-b border-border px-3 py-1.5">
        {TIMEFRAMES.map((t) => {
          const disabled = sym.providerId === "tsetmc" && t !== "1D";
          return (
            <button
              key={t}
              disabled={disabled}
              onClick={() => setTf(t)}
              className={`num rounded px-2 py-1 text-[11px] transition-colors disabled:opacity-30 ${
                effectiveTf === t ? "bg-surface-2 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          );
        })}
        {sym.providerId === "tsetmc" && (
          <span className="mr-2 text-[10.5px] text-muted-foreground">بورس تهران فقط روزانه</span>
        )}
      </div>

      <div className="flex min-w-0 flex-1 flex-col px-3 pb-2 pt-2">
        {!env ? (
          <div className="flex h-64 items-center justify-center gap-2 text-[12px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> در حال دریافت داده‌ی واقعی…
          </div>
        ) : env.data.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-2 text-center">
            <p className="text-[13px] font-semibold text-bear">اتصال زنده در دسترس نیست</p>
            <p className="max-w-md text-[11px] text-muted-foreground">{env.meta.reason}</p>
            {TSE_SNAPSHOT[symbolId] && (() => {
              const s = TSE_SNAPSHOT[symbolId]!;
              return (
                <div className="mt-2 rounded border border-border bg-surface-2 px-4 py-2 text-[11.5px]">
                  <p className="mb-1 text-muted-foreground">آخرین دیده‌بان بازار (فایل TSETMC · ۱۴۰۵/۰۸/۱۱) — نه زنده</p>
                  <p className="num">
                    پایانی {fmt(s.close)} <span className={s.changePct >= 0 ? "text-bull" : "text-bear"}>({s.changePct}%)</span>
                    {" "}· O{fmt(s.open)} H{fmt(s.high)} L{fmt(s.low)} · حجم {fmt(s.volume)}
                  </p>
                </div>
              );
            })()}
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11.5px]">
              <span className="font-semibold">{sym.ticker} · {effectiveTf}</span>
              {last && (
                <span className="num text-muted-foreground">
                  O{fmt(last.open)} H{fmt(last.high)} L{fmt(last.low)} C{fmt(last.close)}
                </span>
              )}
              <span className={`num ${pct >= 0 ? "text-bull" : "text-bear"}`}>
                {pct >= 0 ? "+" : ""}{pct.toFixed(2)}%
              </span>
              {last && (
                <span className="num text-muted-foreground">
                  {new Date(last.t).toISOString().slice(0, 16).replace("T", " ")} UTC
                </span>
              )}
            </div>
            <div className="mt-1 min-h-0 flex-1">
              <CandleChart data={chart} />
            </div>
          </>
        )}
      </div>

      {env && <IndicatorPanel series={env} />}
      {env && <SmartMoneyPanel series={env} />}
    </section>
  );
}
