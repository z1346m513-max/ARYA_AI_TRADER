import { useMemo } from "react";

import { analyzeSeries, type CategorySummary, type IndicatorResult } from "@/arya/indicators";
import type { DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Direction } from "@/arya/core/types";
import { DEFAULT_CONFIG } from "@/arya/config";
import { DataStatusBadge } from "@/components/arya/DataStatusBadge";

const CATEGORY_FA: Record<CategorySummary["category"], string> = {
  trend: "روند",
  momentum: "مومنتوم",
  volatility: "نوسان",
  volume: "حجم",
};

const toneOf = (d: Direction): string =>
  d === "bullish" ? "var(--bull)" : d === "bearish" ? "var(--bear)" : "var(--neutral)";

const SIGNAL_FA: Record<Direction, string> = {
  bullish: "صعودی",
  bearish: "نزولی",
  neutral: "خنثی",
};

export function IndicatorPanel({ series }: { series: DataEnvelope<Candle[]> }) {
  const envelopeResult = useMemo(() => analyzeSeries(series, DEFAULT_CONFIG.indicators), [series]);

  const report = envelopeResult.data;
  if (series.data.length === 0) {
    return (
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2">
          <h3 className="text-[12px] font-semibold text-muted-foreground">موتور اندیکاتور</h3>
          <DataStatusBadge meta={series.meta} />
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground">داده در دسترس نیست — اندیکاتوری محاسبه نشد.</p>
      </div>
    );
  }

  return (
    <div className="border-t border-border p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-[12px] font-semibold text-muted-foreground">موتور اندیکاتور</h3>
        <DataStatusBadge meta={envelopeResult.meta} />
        <span className="num text-[11px]" style={{ color: toneOf(report.signal) }}>
          امتیاز تکنیکال: {report.technicalScore.toFixed(1)} · {SIGNAL_FA[report.signal]}
        </span>
        <span className="num mr-auto text-[10.5px] text-muted-foreground">
          پوشش {Math.round(report.coverage * 100)}٪ · {report.results.length} اندیکاتور فعال
        </span>
      </div>

      <div className="mb-2 grid grid-cols-2 gap-2 md:grid-cols-4">
        {report.categories.map((c) => (
          <div key={c.category} className="rounded-md border border-border bg-surface-2 px-2.5 py-2">
            <p className="text-[10.5px] text-muted-foreground">{CATEGORY_FA[c.category]}</p>
            <p className="num mt-1 text-[13px] font-semibold" style={{ color: toneOf(c.signal) }}>
              {c.contributors ? c.score.toFixed(1) : "—"}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {report.results.map((r: IndicatorResult) => (
          <div key={r.id} className="rounded-md border border-border bg-surface-2 px-2.5 py-2">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-medium">{r.label}</p>
              <span className="num text-[11px]" style={{ color: toneOf(r.signal) }}>
                {Number.isFinite(r.value) ? r.value.toLocaleString("en-US") : "—"}
              </span>
            </div>
            <p className="mt-1 text-[10.5px] text-muted-foreground">{r.note}</p>
            <div className="mt-1.5 h-1 rounded bg-border">
              <div
                className="h-1 rounded"
                style={{ width: `${Math.round(r.strength * 100)}%`, background: toneOf(r.signal) }}
              />
            </div>
          </div>
        ))}
      </div>

      {report.insufficient.length > 0 && (
        <p className="mt-2 text-[10.5px] text-muted-foreground">
          بدون داده‌ی کافی: {report.insufficient.join("، ")}
        </p>
      )}
    </div>
  );
}
