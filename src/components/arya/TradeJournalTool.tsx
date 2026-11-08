import { useRef, useState } from "react";
import { Loader2, NotebookPen, Square } from "lucide-react";

const SAMPLE =
  "symbol,side,entry,exit,size,opened,closed,setup,note\nFOLD,long,1000,960,100,2026-01-02,2026-01-03,breakout,ورود عجولانه بعد از ضرر قبلی\n...";

interface Trade {
  symbol: string;
  side: "long" | "short";
  entry: number;
  exit: number;
  size?: number | undefined;
  openedAt?: string | undefined;
  closedAt?: string | undefined;
  setup?: string | undefined;
  note?: string | undefined;
}

function parse(csv: string): Trade[] {
  const out: Trade[] = [];
  for (const line of csv.split(/\r?\n/)) {
    const p = line.split(/[,\t;]/).map((s) => s.trim());
    if (p.length < 4) continue;
    const side = p[1]!.toLowerCase();
    const s = side === "short" || side === "sell" || side === "فروش" ? "short" : side === "long" || side === "buy" || side === "خرید" ? "long" : null;
    const entry = Number(p[2]);
    const exit = Number(p[3]);
    if (!s || !(entry > 0) || !(exit > 0)) continue;
    const size = Number(p[4]);
    out.push({
      symbol: p[0]!.slice(0, 32),
      side: s,
      entry,
      exit,
      size: size > 0 ? size : undefined,
      openedAt: p[5] || undefined,
      closedAt: p[6] || undefined,
      setup: p[7]?.slice(0, 120) || undefined,
      note: p.slice(8).join(", ").slice(0, 1000) || undefined,
    });
  }
  return out;
}

export function TradeJournalTool() {
  const [csv, setCsv] = useState("");
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const trades = parse(csv);

  async function run() {
    setOutput("");
    setError("");
    if (trades.length < 3) return setError("حداقل ۳ معامله‌ی معتبر لازم است.");
    setLoading(true);
    const ac = new AbortController();
    abortRef.current = ac;
    try {
      const res = await fetch("/api/trade-journal", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ trades: trades.slice(0, 200) }),
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
    <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
      <section className="panel flex flex-col gap-3 p-4">
        <h2 className="flex items-center gap-1.5 text-[14px] font-semibold">
          <NotebookPen className="size-4 text-primary" /> تحلیل ژورنال معاملات با هوش مصنوعی
        </h2>
        <label className="flex flex-col gap-1 text-[12px] text-muted-foreground">
          هر خط یک معامله‌ی بسته‌شده: نماد، جهت (long/short)، ورود، خروج، حجم، تاریخ باز، تاریخ بسته، ستاپ، یادداشت
          <textarea dir="ltr" rows={11} className={`${field} num font-mono text-[11px]`} placeholder={SAMPLE} value={csv} onChange={(e) => setCsv(e.target.value)} />
        </label>
        <p className="text-[11px] text-muted-foreground">معاملات معتبر شناسایی‌شده: {trades.length}</p>
        {loading ? (
          <button onClick={() => abortRef.current?.abort()} className="flex items-center justify-center gap-1.5 rounded-md border border-border py-2 text-[13px] hover:bg-surface-2">
            <Square className="size-3.5" /> توقف
          </button>
        ) : (
          <button onClick={run} disabled={trades.length < 3} className="flex items-center justify-center gap-1.5 rounded-md bg-primary py-2 text-[13px] font-semibold text-primary-foreground disabled:opacity-50">
            <NotebookPen className="size-3.5" /> شناسایی الگوها و ریسک‌ها
          </button>
        )}
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
          !loading && !error && <p className="text-[13px] text-muted-foreground">الگوهای رفتاری و ریسک‌ها اینجا نمایش داده می‌شود.</p>
        )}
      </section>
    </div>
  );
}
