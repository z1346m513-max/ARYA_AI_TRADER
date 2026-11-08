import { sectionScores, recommendation } from "@/lib/arya-data";
import { DataStatusBadge, MOCK_META } from "@/components/arya/DataStatusBadge";

const R = 46;
const C = 2 * Math.PI * R;

export function ScorePanel() {
  const pct = recommendation.overallScore / 100;

  return (
    <section className="panel flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-[13px] font-semibold text-muted-foreground">امتیاز جامع</h2>
        <DataStatusBadge meta={MOCK_META} />
      </div>

      <div className="flex flex-col items-center gap-2">
        <div className="relative">
          <svg viewBox="0 0 120 120" className="size-[118px] -rotate-90">
            <circle cx="60" cy="60" r={R} fill="none" stroke="var(--surface-2)" strokeWidth={9} />
            <circle
              cx="60"
              cy="60"
              r={R}
              fill="none"
              stroke="var(--bull)"
              strokeWidth={9}
              strokeLinecap="round"
              strokeDasharray={`${C * pct} ${C}`}
            />
          </svg>
          <div className="absolute inset-0 grid place-content-center text-center">
            <p className="num text-3xl font-bold leading-none">{recommendation.overallScore}</p>
            <p className="num text-[11px] text-muted-foreground">/100</p>
          </div>
        </div>
        <span className="rounded-md bg-bull px-3 py-1 text-xs font-bold text-bull-foreground">
          سیگنال: {recommendation.action}
        </span>
      </div>

      <ul className="flex flex-col gap-2.5">
        {sectionScores.map((s) => (
          <li key={s.key} className="flex items-center gap-2.5">
            <span
              className="grid size-6 shrink-0 place-items-center rounded-md text-[10px] font-bold"
              style={{
                backgroundColor: `color-mix(in oklch, var(--${s.tone}) 22%, transparent)`,
                color: `var(--${s.tone})`,
              }}
            >
              {s.score}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between">
                <span className="text-[12px]">{s.label}</span>
                <span className="num text-[11px] text-muted-foreground">{s.score}/100</span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${s.score}%`, backgroundColor: `var(--${s.tone})` }}
                />
              </div>
            </div>
          </li>
        ))}
      </ul>

      <p className="num mt-auto text-[11px] text-muted-foreground">آخرین به‌روزرسانی: 10:30</p>
    </section>
  );
}