import { ChevronDown, Pause, Play, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { cacheMetrics, type CacheMetricsSnapshot } from "@/arya/storage/cache-metrics";

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

function Kpi({ label, value, tone = "" }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="rounded border border-border bg-surface-2 p-2">
      <div className="text-[10.5px] text-muted-foreground">{label}</div>
      <div className={`num text-[15px] font-semibold ${tone}`}>{value}</div>
    </div>
  );
}

function Ratio({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="w-14 text-muted-foreground">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded bg-surface-2">
        <div className={`h-full ${tone}`} style={{ width: pct(value) }} />
      </div>
      <span className="num w-12 text-left">{pct(value)}</span>
    </div>
  );
}

/**
 * Collapsible cache-metrics dock (web port of the Qt CacheMetricsDock).
 * Auto-refresh pauses when collapsed, manually paused, or the tab is hidden.
 */
export function CacheMetricsDock({ refreshMs = 2000 }: { refreshMs?: number }) {
  const [snap, setSnap] = useState<CacheMetricsSnapshot | null>(null);
  const [open, setOpen] = useState(true);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [status, setStatus] = useState("آماده");

  const refresh = useCallback(() => setSnap(cacheMetrics.snapshot()), []);
  const running = open && !paused && !hidden;

  useEffect(() => {
    const onVis = () => setHidden(document.hidden);
    onVis();
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  useEffect(() => {
    refresh();
    if (!running) return;
    const id = window.setInterval(refresh, refreshMs);
    return () => window.clearInterval(id);
  }, [running, refresh, refreshMs]);

  useEffect(() => {
    setStatus(!open ? "داک بسته شد — به‌روزرسانی متوقف" : paused ? "متوقف (دستی)" : hidden ? "تب مخفی — متوقف" : "در حال به‌روزرسانی زنده");
  }, [open, paused, hidden]);

  const s = snap;
  const markets = s ? Object.entries(s.byMarket) : [];

  return (
    <section className="panel flex flex-col">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <button onClick={() => setOpen((o) => !o)} className="flex items-center gap-1.5 text-[13px] font-semibold text-muted-foreground hover:text-foreground">
          <ChevronDown className={`size-4 transition-transform ${open ? "" : "-rotate-90"}`} />
          متریک‌های کش
        </button>
        <span className={`rounded px-1.5 py-0.5 text-[10px] ${running ? "bg-bull/10 text-bull" : "bg-surface-2 text-muted-foreground"}`}>
          {running ? "زنده" : "متوقف"}
        </span>
        <div className="mr-auto flex items-center gap-1">
          <button title={paused ? "ادامه" : "توقف"} onClick={() => setPaused((p) => !p)} className="rounded p-1 text-muted-foreground hover:text-primary">
            {paused ? <Play className="size-3.5" /> : <Pause className="size-3.5" />}
          </button>
          <button title="بازنشانی" onClick={() => { cacheMetrics.reset(); refresh(); }} className="rounded p-1 text-muted-foreground hover:text-primary">
            <RotateCcw className="size-3.5" />
          </button>
        </div>
      </header>

      {open && s && (
        <div className="flex flex-col gap-3 p-4">
          {s.totalLookups === 0 && (
            <p className="text-[11.5px] text-muted-foreground">
              هنوز هیچ درخواستی به کش ثبت نشده است. شمارنده‌ها با اتصال Provider واقعی پر می‌شوند.
            </p>
          )}
          <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
            <Kpi label="Hit Ratio" value={pct(s.hitRatio)} tone="text-bull" />
            <Kpi label="برخورد" value={s.hits} />
            <Kpi label="عدم برخورد" value={s.misses} tone="text-bear" />
            <Kpi label="کهنه" value={s.stale} tone="text-warning" />
            <Kpi label="ذخیره" value={s.saves} />
            <Kpi label="خطا" value={s.errors} tone="text-bear" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Ratio label="Hit" value={s.hitRatio} tone="bg-bull" />
            <Ratio label="Miss" value={s.missRatio} tone="bg-bear" />
            <Ratio label="Stale" value={s.staleRatio} tone="bg-warning" />
          </div>
          {markets.length > 0 && (
            <table className="w-full text-[11.5px]">
              <thead className="text-muted-foreground">
                <tr><th className="text-right font-normal">بازار</th><th>Hit</th><th>Miss</th><th>Stale</th><th>Save</th><th>Err</th></tr>
              </thead>
              <tbody className="num text-center">
                {markets.map(([k, v]) => (
                  <tr key={k} className="border-t border-border/60">
                    <td className="py-1 text-right">{k}</td>
                    <td>{v['hits'] ?? 0}</td><td>{v['misses'] ?? 0}</td><td>{v['stale'] ?? 0}</td><td>{v['saves'] ?? 0}</td><td>{v['errors'] ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <footer className="border-t border-border px-4 py-1 text-[10.5px] text-muted-foreground">
        وضعیت: {status}{s ? <span className="num"> · {s.snapshotAt}</span> : null}
      </footer>
    </section>
  );
}
