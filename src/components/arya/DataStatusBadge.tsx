import { AlertTriangle, CircleSlash, FlaskConical, Radio } from "lucide-react";

import { STATUS_LABEL_FA, type DataMeta, type DataStatus } from "@/arya/core/data-envelope";

const STYLES: Record<DataStatus, { className: string; Icon: typeof Radio }> = {
  LIVE: { className: "border-bull/40 bg-bull/10 text-bull", Icon: Radio },
  DEMO: { className: "border-warning/40 bg-warning/10 text-warning", Icon: FlaskConical },
  STALE: { className: "border-border bg-surface-2 text-muted-foreground", Icon: AlertTriangle },
  UNAVAILABLE: { className: "border-bear/40 bg-bear/10 text-bear", Icon: CircleSlash },
};

/**
 * Mandatory provenance badge (specification rule 28). Any panel showing
 * numbers must render this so demo values can never pass as real data.
 */
export function DataStatusBadge({ meta, className = "" }: { meta: DataMeta; className?: string }) {
  const style = STYLES[meta.status];
  const Icon = style.Icon;
  const title = [
    `منبع: ${meta.source}`,
    `وضعیت: ${meta.status}`,
    `کیفیت: ${Math.round(meta.quality * 100)}%`,
    meta.reason ? `دلیل: ${meta.reason}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium ${style.className} ${className}`}
    >
      <Icon className="size-3" strokeWidth={2} />
      {STATUS_LABEL_FA[meta.status]}
      <span className="num opacity-70">· {meta.source}</span>
    </span>
  );
}

/** Shared meta for legacy panels still rendering seeded mock values. */
export const MOCK_META: DataMeta = {
  status: "DEMO",
  source: "Mock",
  providerId: "mock",
  timestamp: 0,
  quality: 0.5,
  reason: "داده‌ی نمایشی است و ارزش معاملاتی ندارد",
};
