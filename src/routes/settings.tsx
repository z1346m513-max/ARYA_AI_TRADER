import { createFileRoute } from "@tanstack/react-router";
import { Settings as SettingsIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { DEFAULT_CONFIG, loadConfig, type AppConfig } from "@/arya/config";
import { WEIGHT_KEYS } from "@/arya/config/schemas";
import { WEIGHT_LABEL_FA, toPercentages, validateWeights } from "@/arya/config/weights";
import { AppShell } from "@/components/arya/AppShell";
import { CacheMetricsDock } from "@/components/arya/CacheMetricsDock";

const title = "تنظیمات | آریا";
const description = "پیکربندی اندیکاتورها، وزن تحلیل‌ها، تایم‌فریم‌ها، زمان‌بندی به‌روزرسانی و پارامترهای ریسک.";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SettingsPage,
});

function Panel({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <section className="panel flex flex-col gap-3 p-4">
      <h2 className="text-[13px] font-semibold text-muted-foreground">{heading}</h2>
      {children}
    </section>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 py-1.5 text-[12px] last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="num font-semibold">{value}</span>
    </div>
  );
}

function SettingsPage() {
  // Stored overrides live in localStorage, so read them after hydration.
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const result = loadConfig();
    setConfig(result.config);
    setErrors(result.errors);
  }, []);

  const weights = toPercentages(config.weights);
  const weightCheck = validateWeights(config.weights);
  const enabledIndicators = Object.values(config.indicators).filter((i) => i.enabled);

  return (
    <AppShell>
      <div className="flex flex-col gap-3">
        <header className="flex flex-wrap items-center gap-3">
          <span className="grid size-9 place-items-center rounded-md bg-primary/12 text-primary">
            <SettingsIcon className="size-4.5" strokeWidth={1.75} />
          </span>
          <h1 className="text-lg font-bold">تنظیمات</h1>
          <span className="num rounded border border-border bg-surface-2 px-2 py-0.5 text-[10px] text-muted-foreground">
            نسخه پیکربندی {config.version}
          </span>
        </header>

        {errors.length > 0 && (
          <div className="rounded-lg border border-bear/40 bg-bear/10 p-3 text-[12px] text-bear">
            پیکربندی ذخیره‌شده نامعتبر بود و مقادیر پیش‌فرض بارگذاری شد: {errors.join(" · ")}
          </div>
        )}

        <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-[12px] leading-relaxed text-muted-foreground">
          موتور پیکربندی ساخته و اعتبارسنجی شده است و مقادیر زیر واقعاً از همان موتور خوانده
          می‌شوند. فرم‌های ویرایش در فاز ۳ به همین مقادیر متصل می‌شوند.
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <Panel heading={`وزن تحلیل‌ها (جمع: ${weightCheck.total}٪)`}>
            <ul className="flex flex-col gap-2.5">
              {WEIGHT_KEYS.map((key) => (
                <li key={key}>
                  <div className="flex items-baseline justify-between text-[12px]">
                    <span>{WEIGHT_LABEL_FA[key]}</span>
                    <span className="num text-muted-foreground">{weights[key]}٪</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-2">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${weights[key]}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel heading="تایم‌فریم‌ها">
            <div className="flex flex-wrap gap-1.5">
              {config.timeframes.active.map((tf) => (
                <span
                  key={tf}
                  className="num rounded border border-primary/40 bg-primary/10 px-2 py-1 text-[11px] text-primary"
                >
                  {tf}
                </span>
              ))}
            </div>
            <div>
              <Row label="روند (بالاترین)" value={config.timeframes.trend} />
              <Row label="ساختار" value={config.timeframes.structure} />
              <Row label="مومنتوم" value={config.timeframes.momentum} />
              <Row label="ورود" value={config.timeframes.entry} />
            </div>
          </Panel>

          <Panel heading="زمان‌بندی به‌روزرسانی">
            <Row label="بازه به‌روزرسانی" value={config.scheduler.interval} />
            <Row label="توقف در تب پنهان" value={config.scheduler.pauseWhenHidden ? "بله" : "خیر"} />
            <Row label="حداکثر تلاش مجدد" value={config.scheduler.maxRetries} />
            <Row label="فاصله تلاش مجدد" value={`${config.scheduler.retryBackoffMs} ms`} />
            <Row label="آستانه کهنگی داده" value={`${config.scheduler.staleAfterMs / 60000} دقیقه`} />
          </Panel>

          <Panel heading="مدیریت ریسک">
            <Row label="ریسک هر معامله" value={`${config.risk.riskPerTradePct}٪`} />
            <Row label="حداکثر ریسک سبد" value={`${config.risk.maxPortfolioRiskPct}٪`} />
            <Row label="حداکثر تعداد موقعیت" value={config.risk.maxPositions} />
            <Row label="حداقل نسبت ریسک به بازده" value={config.risk.minRiskReward} />
            <Row label="ضریب ATR حد ضرر" value={config.risk.atrStopMultiple} />
            <Row label="حداکثر افت سرمایه" value={`${config.risk.maxDrawdownPct}٪`} />
          </Panel>

          <Panel heading="Providerها">
            <Row label="داده بازار" value={config.providers.market} />
            <Row label="اخبار" value={config.providers.news} />
            <Row label="کدال" value={config.providers.codal} />
            <Row label="بنیادی" value={config.providers.fundamental} />
            <Row label="مهلت پاسخ" value={`${config.providers.timeoutMs} ms`} />
            <Row label="استفاده از داده نمایشی" value={config.providers.allowDemoFallback ? "مجاز" : "غیرمجاز"} />
          </Panel>

          <Panel heading={`اندیکاتورها (${enabledIndicators.length} فعال از ${Object.keys(config.indicators).length})`}>
            <ul className="flex max-h-[280px] flex-col gap-1 overflow-y-auto">
              {Object.values(config.indicators).map((ind) => (
                <li
                  key={ind.id}
                  className="flex items-center justify-between rounded-md border border-border bg-surface-2 px-2.5 py-1.5 text-[11.5px]"
                >
                  <span className="flex items-center gap-2">
                    <span
                      className={`size-1.5 rounded-full ${ind.enabled ? "bg-bull" : "bg-muted-foreground/40"}`}
                    />
                    <span className="num">{ind.id}</span>
                  </span>
                  <span className="num text-[11px] text-muted-foreground">
                    {Object.entries(ind.params)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(" · ") || "—"}
                  </span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
        <CacheMetricsDock />
      </div>
    </AppShell>
  );
}
