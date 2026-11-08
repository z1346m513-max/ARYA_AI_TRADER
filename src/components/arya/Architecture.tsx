import { Check } from "lucide-react";
import { architecture, infrastructure } from "@/lib/arya-data";

const features = [
  "ماژولار و قابل توسعه",
  "پلاگین محور (Plugin System)",
  "قابل ارتقا به نسخه‌ی سازمانی",
  "امن، سریع و پایدار",
];

export function Architecture() {
  return (
    <section className="panel p-5" aria-labelledby="arch-title">
      <h2 id="arch-title" className="text-center text-lg font-bold text-primary">
        معماری پروژه ARYA AI TRADER
      </h2>

      <div className="mt-5 grid grid-cols-1 items-start gap-3 lg:grid-cols-4 xl:grid-cols-8">
        {architecture.map((layer) => (
          <div
            key={layer.id}
            className={`rounded-lg border bg-surface-2/60 p-3 ${layer.id === "4" ? "xl:col-span-2" : ""}`}
            style={{ borderColor: `color-mix(in oklch, ${layer.accent} 45%, transparent)` }}
          >
            <h3 className="mb-2.5 text-center text-[12.5px] font-semibold" style={{ color: layer.accent }}>
              {layer.title}
            </h3>
            <div className="flex flex-col gap-2.5">
              {layer.groups.map((group, gi) => (
                <div key={gi}>
                  {group.title && (
                    <p className="mb-1.5 text-center text-[11px] text-muted-foreground">{group.title}</p>
                  )}
                  <ul
                    className={`grid gap-1.5 ${
                      layer.id === "4" ? "grid-cols-2 sm:grid-cols-3" : "grid-cols-1"
                    }`}
                  >
                    {group.items.map((item) => (
                      <li
                        key={item}
                        className="num rounded border border-border bg-surface px-2 py-1.5 text-center text-[11px] text-foreground/90"
                      >
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 grid items-stretch gap-3 lg:grid-cols-[1fr_auto]">
        <div className="rounded-lg border border-border bg-surface-2/60 p-3">
          <h3 className="mb-2.5 text-center text-[12.5px] font-semibold text-muted-foreground">
            ۸. لایه زیرساخت
          </h3>
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
            {infrastructure.map((item) => (
              <li
                key={item}
                className="num rounded border border-border bg-surface px-2 py-2 text-center text-[11px]"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center gap-5 rounded-lg border border-primary/30 bg-surface-2/60 p-4">
          <svg viewBox="0 0 40 32" className="h-12 w-14 shrink-0" aria-hidden>
            <path
              d="M20 3 L27 12 L38 8 L30 18 L20 29 L10 18 L2 8 L13 12 Z"
              fill="none"
              stroke="var(--primary)"
              strokeWidth={1.6}
              strokeLinejoin="round"
            />
            <path d="M20 9 L24 18 L20 24 L16 18 Z" fill="var(--primary)" />
          </svg>
          <ul className="flex flex-col gap-1.5">
            {features.map((f) => (
              <li key={f} className="flex items-center gap-2 text-[12px]">
                <Check className="size-3.5 text-bull" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}