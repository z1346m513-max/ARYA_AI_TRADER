import { useMemo } from "react";

import type { DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Direction } from "@/arya/core/types";
import { analyzeSmartMoney } from "@/arya/smart-money";
import { DataStatusBadge } from "@/components/arya/DataStatusBadge";


const toneOf = (d: Direction): string =>
  d === "bullish" ? "var(--bull)" : d === "bearish" ? "var(--bear)" : "var(--neutral)";

const DIR_FA: Record<Direction, string> = {
  bullish: "صعودی",
  bearish: "نزولی",
  neutral: "خنثی",
};

const num = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });

function Section({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-surface-2 p-2.5">
      <div className="mb-1.5 flex items-center justify-between">
        <p className="text-[11px] font-semibold">{title}</p>
        <span className="num text-[10.5px] text-muted-foreground">{count}</span>
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Empty() {
  return <p className="text-[10.5px] text-muted-foreground">موردی یافت نشد</p>;
}

export function SmartMoneyPanel({ series }: { series: DataEnvelope<Candle[]> }) {
  const env = useMemo(() => analyzeSmartMoney(series), [series]);
  if (series.data.length === 0) return null;

  const r = env.data;
  const structure = r.structure.slice(-6).reverse();
  const blocks = r.orderBlocks.filter((b) => !b.mitigated).slice(-6).reverse();
  const gaps = r.fairValueGaps.filter((g) => !g.filled).slice(-6).reverse();
  const pools = r.liquidity.slice(0, 6);

  return (
    <div className="border-t border-border p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-[12px] font-semibold text-muted-foreground">موتور Smart Money</h3>
        <DataStatusBadge meta={env.meta} />
        <span className="num text-[11px]" style={{ color: toneOf(r.bias) }}>
          امتیاز اسمارت‌مانی: {r.score.toFixed(1)} · {DIR_FA[r.bias]}
        </span>
        <span className="num mr-auto text-[10.5px] text-muted-foreground">
          پوشش {Math.round(r.coverage * 100)}٪ · {r.swings.length} سوئینگ
        </span>
      </div>

      <p className="mb-2 text-[10.5px] text-muted-foreground">{r.note}</p>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <Section title="BOS / CHOCH" count={r.structure.length}>
          {structure.length === 0 && <Empty />}
          {structure.map((e) => (
            <div key={`${e.kind}-${e.index}`} className="flex items-center justify-between text-[10.5px]">
              <span style={{ color: toneOf(e.direction) }}>
                {e.kind} {DIR_FA[e.direction]}
              </span>
              <span className="num text-muted-foreground">
                {num(e.level)} · {Math.round(e.strength * 100)}٪
              </span>
            </div>
          ))}
        </Section>

        <Section title="اردربلاک فعال" count={blocks.length}>
          {blocks.length === 0 && <Empty />}
          {blocks.map((b) => (
            <div key={`ob-${b.index}`} className="flex items-center justify-between text-[10.5px]">
              <span style={{ color: toneOf(b.direction) }}>{DIR_FA[b.direction]}</span>
              <span className="num text-muted-foreground">
                {num(b.bottom)} – {num(b.top)}
              </span>
            </div>
          ))}
        </Section>

        <Section title="گپ ارزش منصفانه (FVG)" count={gaps.length}>
          {gaps.length === 0 && <Empty />}
          {gaps.map((g) => (
            <div key={`fvg-${g.index}`} className="flex items-center justify-between text-[10.5px]">
              <span style={{ color: toneOf(g.direction) }}>{DIR_FA[g.direction]}</span>
              <span className="num text-muted-foreground">
                {num(g.bottom)} – {num(g.top)} · {(g.size * 100).toFixed(2)}٪
              </span>
            </div>
          ))}
        </Section>

        <Section title="نقدینگی" count={r.liquidity.length}>
          {pools.length === 0 && <Empty />}
          {pools.map((p, i) => (
            <div key={`lq-${i}`} className="flex items-center justify-between text-[10.5px]">
              <span style={{ color: p.side === "buy-side" ? "var(--bull)" : "var(--bear)" }}>
                {p.side === "buy-side" ? "سمت خرید" : "سمت فروش"}
                {p.swept ? " (جاروشده)" : ""}
              </span>
              <span className="num text-muted-foreground">
                {num(p.price)} · {p.touches}×
              </span>
            </div>
          ))}
        </Section>
      </div>
    </div>
  );
}
