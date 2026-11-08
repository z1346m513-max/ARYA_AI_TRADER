import { Upload } from "lucide-react";
import { useEffect, useState } from "react";

import { envelope, type DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle } from "@/arya/core/types";
import { candlesFromSnapshots, parseMarketWatch, type DailySnapshot } from "@/arya/providers/marketwatch-import";
import { listSnapshots, onSnapshotsChange, saveSnapshot } from "@/arya/storage/daily-store";

export function useSnapshots() {
  const [snaps, setSnaps] = useState<DailySnapshot[]>([]);
  useEffect(() => {
    const load = () => void listSnapshots().then(setSnaps).catch(() => setSnaps([]));
    load();
    return onSnapshotsChange(load);
  }, []);
  return snaps;
}

/** Real (manually uploaded) history for one ticker, labelled as not live. */
export function storedEnvelope(snaps: DailySnapshot[], ticker: string): DataEnvelope<Candle[]> | null {
  const candles = candlesFromSnapshots(snaps, ticker);
  if (!candles.length) return null;
  return envelope(candles, {
    source: "فایل دیده‌بان TSETMC (بارگذاری دستی)",
    providerId: "tsetmc-file",
    status: "STALE",
    quality: 0.9,
    timestamp: candles.at(-1)!.t,
    reason: `${candles.length} روز معاملاتی از فایل‌های بارگذاری‌شده — داده‌ی زنده نیست`,
  });
}

export function DailyUpload() {
  const snaps = useSnapshots();
  const [msg, setMsg] = useState("");
  async function onFiles(files: FileList | null) {
    if (!files) return;
    const { default: readXlsx } = await import("read-excel-file/browser");
    for (const f of Array.from(files)) {
      try {
        const out = (await readXlsx(f)) as unknown as Array<unknown[] | { data: unknown[][] }>;
        const first = out[0];
        const rows = first && !Array.isArray(first) && "data" in first ? first.data : (out as unknown[][]);
        const s = parseMarketWatch(rows, f.name);
        await saveSnapshot(s);
        setMsg(`${s.jalali}: ${Object.keys(s.bars).length} نماد ذخیره شد`);
      } catch (e) {
        setMsg(`${f.name}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
  }
  const days = [...snaps].sort((a, b) => a.t - b.t);
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-border px-3 py-1.5 text-[11px]">
      <label className="flex cursor-pointer items-center gap-1 rounded border border-border bg-surface-2 px-2 py-1 hover:text-primary">
        <Upload className="size-3.5" /> بارگذاری دیده‌بان روزانه (xlsx)
        <input type="file" accept=".xlsx" multiple className="hidden" onChange={(e) => void onFiles(e.target.files)} />
      </label>
      <span className="text-muted-foreground">
        حافظه: {days.length} روز{days.length ? ` (${days[0]!.jalali} تا ${days.at(-1)!.jalali})` : ""}
      </span>
      {msg && <span className="text-primary">{msg}</span>}
    </div>
  );
}
