import { ExternalLink, Sparkles } from "lucide-react";
import { recommendation, news } from "@/lib/arya-data";
import { DataStatusBadge, MOCK_META } from "@/components/arya/DataStatusBadge";

const toneClass: Record<string, string> = {
  info: "bg-bull/15 text-bull",
  bear: "bg-bear/15 text-bear",
  accent: "bg-accent/20 text-accent-foreground",
};

export function AiPanel() {
  return (
    <div className="flex flex-col gap-3">
      <section className="panel flex flex-col gap-3 p-4">
        <h2 className="flex items-center gap-1.5 text-[13px] font-semibold text-muted-foreground">
          <Sparkles className="size-3.5 text-primary" />
          پیشنهاد هوش مصنوعی
          <DataStatusBadge meta={MOCK_META} />
        </h2>

        <div className="rounded-lg border border-bull/40 bg-bull/10 py-5 text-center">
          <p className="text-2xl font-bold text-bull">{recommendation.action}</p>
          <p className="num mt-1 text-xs text-bull/80">با اعتبار {recommendation.confidence}%</p>
        </div>

        <dl className="flex flex-col gap-2 rounded-lg border border-border bg-surface-2 p-3">
          {recommendation.rows.map((r) => (
            <div key={r.label} className="flex items-center justify-between text-[12px]">
              <dt className="text-muted-foreground">{r.label}</dt>
              <dd className="flex items-center gap-3">
                <span className="num font-semibold">{r.value}</span>
                {r.delta && (
                  <span className={`num w-14 text-left ${r.up ? "text-bull" : "text-bear"}`}>{r.delta}</span>
                )}
              </dd>
            </div>
          ))}
        </dl>

        <ul className="flex flex-col gap-1.5 text-[11.5px] leading-relaxed text-muted-foreground">
          {recommendation.reasons.map((reason) => (
            <li key={reason} className="flex gap-1.5">
              <span className="mt-1.5 size-1 shrink-0 rounded-full bg-primary" />
              {reason}
            </li>
          ))}
        </ul>

        <button className="flex items-center justify-center gap-1.5 rounded-md border border-border py-2 text-[12px] text-accent-foreground transition-colors hover:bg-surface-2">
          توضیحات کامل تحلیل
          <ExternalLink className="size-3.5" />
        </button>
      </section>

      <section className="panel flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-[13px] font-semibold text-muted-foreground">اخبار و اطلاعیه‌های مهم</h2>
          <button className="text-[11px] text-primary hover:underline">مشاهده همه</button>
        </div>
        <ul className="flex flex-col">
          {news.map((n) => (
            <li
              key={n.time}
              className="flex items-center gap-3 border-b border-border/60 py-2.5 last:border-0"
            >
              <span className="num text-[11px] text-muted-foreground">{n.time}</span>
              <p className="min-w-0 flex-1 truncate text-[12px]">{n.text}</p>
              <span className={`rounded px-2 py-0.5 text-[10px] font-medium ${toneClass[n.tone]}`}>
                {n.tag}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}