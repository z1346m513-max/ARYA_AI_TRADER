import { useRef, useState } from "react";
import { Loader2, Sparkles, Square } from "lucide-react";

import { REAL_SYMBOLS, findRealSymbol } from "@/arya/providers/real-symbols";
import { Button } from "@/components/ui/button";
import { TIMEFRAMES, type Timeframe } from "@/arya/core/types";

type Mode = "symbol" | "ohlcv";

const SAMPLE = "date,open,high,low,close,volume\n2026-01-01,100,104,99,103,12000\n...";

export function MarketSummaryTool() {
  const [mode, setMode] = useState<Mode>("symbol");
  const [symbolId, setSymbolId] = useState("iran-equity:FOLD");
  const [timeframe, setTimeframe] = useState<Timeframe>("1D");
  const [csv, setCsv] = useState("");
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function run() {
    setOutput("");
    setError("");
    setLoading(true);
    const ac = new AbortController();
    abortRef.current = ac;
    try {
      const res = await fetch("/api/market-summary", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ mode, symbolId, timeframe: mode === "symbol" && findRealSymbol(symbolId)?.providerId === "tsetmc" ? "1D" : timeframe, csv }),
        signal: ac.signal,
      });
      if (!res.ok || !res.body) {
        const j = (await res.json().catch(() => ({}))) as { error?: string };
        setError(j.error ?? "خطا در ارتباط با سرور.");
        return;
      }
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let text = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += dec.decode(value, { stream: true });
        const idx = text.indexOf("[[ERROR]]");
        if (idx >= 0) {
          setOutput(text.slice(0, idx).trim());
          setError(text.slice(idx + 9).trim());
        } else setOutput(text);
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") setError("خطا در ارتباط با سرور.");
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  const field = "rounded-md border border-border bg-surface-2 px-3 py-2 text-[13px] outline-none focus:border-primary";

  return (
    <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
      <section className="panel flex flex-col gap-3 p-4">
        <h2 className="flex items-center gap-1.5 text-[14px] font-semibold">
          <Sparkles className="size-4 text-primary" /> خلاصه‌ی بازار با هوش مصنوعی
        </h2>
        <div className="grid grid-cols-2 gap-1 rounded-md border border-border p-1 text-[12px]">
          {(["symbol", "ohlcv"] as Mode[]).map((m) => (
            <Button variant="ghost"
              key={m}
              onClick={() => setMode(m)}
              className={`rounded py-1.5 ${mode === m ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-surface-2"}`}
            >
              {m === "symbol" ? "نماد" : "داده‌ی OHLCV"}
            </Button>
          ))}
        </div>

        {mode === "symbol" ? (
          <label className="flex flex-col gap-1 text-[12px] text-muted-foreground">
            نماد (دادهٔ واقعی)
            <select className={field} value={symbolId} onChange={(e) => { setSymbolId(e.target.value); if (findRealSymbol(e.target.value)?.providerId === "tsetmc") setTimeframe("1D"); }}>
              {REAL_SYMBOLS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.ticker} — {s.name}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <label className="flex flex-col gap-1 text-[12px] text-muted-foreground">
            CSV: تاریخ، باز، بالا، پایین، بسته، حجم (حداقل ۲۰ ردیف)
            <textarea
              dir="ltr"
              rows={9}
              className={`${field} num font-mono text-[11px]`}
              placeholder={SAMPLE}
              value={csv}
              onChange={(e) => setCsv(e.target.value)}
            />
          </label>
        )}

        <label className="flex flex-col gap-1 text-[12px] text-muted-foreground">
          بازه‌ی زمانی
          <select className={field} value={timeframe} onChange={(e) => setTimeframe(e.target.value as Timeframe)}>
            {TIMEFRAMES.map((t) => (
              <option key={t} value={t} disabled={mode === "symbol" && findRealSymbol(symbolId)?.providerId === "tsetmc" && t !== "1D"}>
                {t}
              </option>
            ))}
          </select>
        </label>

        {loading ? (
          <Button variant="outline"
            onClick={() => abortRef.current?.abort()}
            className="flex items-center justify-center gap-1.5 rounded-md border border-border py-2 text-[13px] hover:bg-surface-2"
          >
            <Square className="size-3.5" /> توقف
          </Button>
        ) : (
          <Button
            onClick={run}
            disabled={mode === "ohlcv" && !csv.trim()}
            className="flex items-center justify-center gap-1.5 rounded-md bg-primary py-2 text-[13px] font-semibold text-primary-foreground disabled:opacity-50"
          >
            <Sparkles className="size-3.5" /> تولید خلاصه
          </Button>
        )}
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          {mode === "symbol" ? "منبع: TSETMC برای بورس تهران، Binance برای رمزارز. دادهٔ تاریخی، نه قیمت لحظه‌ای." : "منبع: داده‌های واردشده توسط شما؛ صحت آن‌ها مستقل تأیید نشده است."}
        </p>
      </section>

      <section className="panel min-h-[320px] p-4">
        {error && <p className="mb-3 rounded-md border border-bear/40 bg-bear/10 p-2 text-[12px] text-bear">{error}</p>}
        {loading && !output && (
          <p className="flex items-center gap-2 text-[13px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> در حال تحلیل…
          </p>
        )}
        {output ? (
          <div className="whitespace-pre-wrap text-[13px] leading-7">{output}</div>
        ) : (
          !loading && !error && <p className="text-[13px] text-muted-foreground">خلاصه اینجا نمایش داده می‌شود.</p>
        )}
      </section>
    </div>
  );
}
