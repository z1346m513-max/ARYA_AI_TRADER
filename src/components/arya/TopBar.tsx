import { Bell, Settings, Minus, Square, X } from "lucide-react";
import { marketTickers } from "@/lib/arya-data";
import { DataStatusBadge, MOCK_META } from "@/components/arya/DataStatusBadge";

function Spark({ up }: { up: boolean }) {
  const d = up ? "M0,16 L10,11 L20,13 L30,6 L40,8 L50,2" : "M0,4 L10,8 L20,6 L30,12 L40,10 L50,16";
  return (
    <svg viewBox="0 0 50 18" className="h-4 w-12">
      <path d={d} fill="none" stroke={up ? "var(--bull)" : "var(--bear)"} strokeWidth={1.5} />
    </svg>
  );
}

export function TopBar() {
  return (
    <header className="flex items-center gap-3 border-b border-border bg-surface px-3 py-2">
      <div className="flex shrink-0 items-center gap-2.5 pl-2">
        <svg viewBox="0 0 40 32" className="h-7 w-9" aria-hidden>
          <path
            d="M20 3 L27 12 L38 8 L30 18 L20 29 L10 18 L2 8 L13 12 Z"
            fill="none"
            stroke="var(--primary)"
            strokeWidth={1.6}
            strokeLinejoin="round"
          />
          <path d="M20 9 L24 18 L20 24 L16 18 Z" fill="var(--primary)" opacity={0.9} />
        </svg>
        <div className="leading-none">
          <h1 className="text-lg font-bold tracking-wide">
            ARYA <span className="text-primary">AI TRADER</span>
          </h1>
          <p className="mt-1 num text-[9px] tracking-[0.18em] text-muted-foreground">
            AI POWERED MARKET ANALYSIS
          </p>
        </div>
      </div>

      <DataStatusBadge meta={MOCK_META} className="shrink-0" />

      <div className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto">
        {marketTickers.map((t) => (
          <div
            key={t.label}
            className="flex min-w-[152px] items-center justify-between gap-3 rounded-md border border-border bg-surface-2 px-3 py-1.5"
          >
            <div className="leading-tight">
              <p className="text-[11px] text-muted-foreground">{t.label}</p>
              <p className="num text-base font-semibold">{t.value}</p>
              <p className={`num text-[11px] ${t.up ? "text-bull" : "text-bear"}`}>{t.change}</p>
            </div>
            <Spark up={t.up} />
          </div>
        ))}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <div className="rounded-md border border-border bg-surface-2 px-3 py-1.5 text-center leading-tight">
          <p className="num text-sm font-semibold">10:30:45</p>
          <p className="num text-[10px] text-muted-foreground">2024/12/20</p>
        </div>
        <button className="grid size-8 place-items-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-foreground">
          <Bell className="size-4" />
        </button>
        <button className="grid size-8 place-items-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-foreground">
          <Settings className="size-4" />
        </button>
        <div className="flex items-center gap-1 pr-1 text-muted-foreground">
          <Minus className="size-4" />
          <Square className="size-3.5" />
          <X className="size-4" />
        </div>
      </div>
    </header>
  );
}