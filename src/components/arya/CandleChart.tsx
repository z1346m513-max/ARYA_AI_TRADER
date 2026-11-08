import type { Candle } from "@/lib/arya-data";

type Props = { data: Candle[] };

const W = 1000;
const H = 300;
const RSI_H = 90;
const PAD_R = 56;

export function CandleChart({ data }: Props) {
  const highs = data.map((d) => d.high);
  const lows = data.map((d) => d.low);
  const max = Math.max(...highs) * 1.01;
  const min = Math.min(...lows) * 0.99;
  const plotW = W - PAD_R;
  const step = plotW / data.length;
  const bw = Math.max(2, step * 0.55);

  const y = (v: number) => H - ((v - min) / (max - min)) * H;
  const x = (i: number) => i * step + step / 2;

  const line = (key: "ma20" | "ma50") =>
    data.map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d[key]).toFixed(1)}`).join(" ");

  const rsiY = (v: number) => RSI_H - (v / 100) * RSI_H;
  const rsiPath = data
    .map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${rsiY(d.rsi).toFixed(1)}`)
    .join(" ");

  const gridValues = Array.from({ length: 6 }, (_, i) => min + ((max - min) / 5) * i);

  return (
    <div className="flex flex-col gap-1" dir="ltr">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-[280px] w-full" preserveAspectRatio="none">
        {gridValues.map((v) => (
          <g key={v}>
            <line
              x1={0}
              x2={plotW}
              y1={y(v)}
              y2={y(v)}
              stroke="var(--grid-line)"
              strokeWidth={1}
              strokeDasharray="3 6"
              vectorEffect="non-scaling-stroke"
            />
          </g>
        ))}
        <path d={line("ma50")} fill="none" stroke="var(--chart-4)" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />
        <path d={line("ma20")} fill="none" stroke="var(--primary)" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />
        {data.map((d, i) => {
          const up = d.close >= d.open;
          const color = up ? "var(--bull)" : "var(--bear)";
          const top = y(Math.max(d.open, d.close));
          const bottom = y(Math.min(d.open, d.close));
          return (
            <g key={d.t}>
              <line
                x1={x(i)}
                x2={x(i)}
                y1={y(d.high)}
                y2={y(d.low)}
                stroke={color}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
              <rect
                x={x(i) - bw / 2}
                y={top}
                width={bw}
                height={Math.max(1, bottom - top)}
                fill={up ? color : "transparent"}
                stroke={color}
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            </g>
          );
        })}
        <line
          x1={0}
          x2={plotW}
          y1={y(data[data.length - 1]?.close ?? 0)}
          y2={y(data[data.length - 1]?.close ?? 0)}
          stroke="var(--bull)"
          strokeDasharray="4 4"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
      </svg>

      <div className="relative">
        <span className="absolute right-1 top-0 num text-[10px] text-muted-foreground">RSI 14</span>
        <svg viewBox={`0 0 ${W} ${RSI_H}`} className="h-[76px] w-full" preserveAspectRatio="none">
          {[30, 50, 70].map((v) => (
            <line
              key={v}
              x1={0}
              x2={plotW}
              y1={rsiY(v)}
              y2={rsiY(v)}
              stroke="var(--grid-line)"
              strokeDasharray={v === 50 ? "2 8" : "3 6"}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          ))}
          <path d={rsiPath} fill="none" stroke="var(--chart-4)" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />
        </svg>
      </div>

      <div className="flex justify-between border-t border-border pt-1.5 num text-[10px] text-muted-foreground">
        {["مرداد", "شهریور", "مهر", "آبان", "آذر", "دی"].map((m) => (
          <span key={m}>{m}</span>
        ))}
      </div>
    </div>
  );
}