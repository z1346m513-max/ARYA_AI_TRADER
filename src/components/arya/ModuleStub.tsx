import type { LucideIcon } from "lucide-react";
import { Construction } from "lucide-react";

import { unavailable } from "@/arya/core/data-envelope";
import { DataStatusBadge } from "@/components/arya/DataStatusBadge";

/**
 * Honest placeholder for a module whose engine is not built yet
 * (specification rules 28 and 38): it shows no numbers and states plainly
 * that no provider is connected, instead of faking output.
 */
export function ModuleStub({
  title,
  icon: Icon,
  phase,
  summary,
  scope,
}: {
  title: string;
  icon: LucideIcon;
  phase: string;
  summary: string;
  scope: string[];
}) {
  const meta = unavailable(null, "ARYA Core", "core", `${phase} پیاده‌سازی نشده است`).meta;

  return (
    <section className="panel flex flex-col gap-4 p-5">
      <header className="flex flex-wrap items-center gap-3">
        <span className="grid size-9 place-items-center rounded-md bg-primary/12 text-primary">
          <Icon className="size-4.5" strokeWidth={1.75} />
        </span>
        <h1 className="text-lg font-bold">{title}</h1>
        <DataStatusBadge meta={meta} />
        <span className="num rounded border border-border bg-surface-2 px-2 py-0.5 text-[10px] text-muted-foreground">
          {phase}
        </span>
      </header>

      <p className="max-w-3xl text-[13px] leading-relaxed text-muted-foreground">{summary}</p>

      <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
        <p className="flex items-center gap-2 text-[12.5px] font-semibold text-warning">
          <Construction className="size-4" />
          این ماژول هنوز موتور محاسباتی ندارد
        </p>
        <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
          طبق قاعده یکپارچگی داده، تا زمانی که محاسبات واقعی و Provider متصل نباشد هیچ عدد یا
          سیگنالی در این صفحه نمایش داده نمی‌شود.
        </p>
      </div>

      <div>
        <h2 className="mb-2 text-[13px] font-semibold text-muted-foreground">دامنه‌ی این ماژول</h2>
        <ul className="grid gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
          {scope.map((item) => (
            <li
              key={item}
              className="flex items-center gap-2 rounded-md border border-border bg-surface-2 px-3 py-2 text-[12px]"
            >
              <span className="size-1.5 shrink-0 rounded-full bg-primary" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
