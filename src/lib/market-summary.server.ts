import { createOpenAI } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";

import { findRealSymbol } from "@/arya/providers/real-symbols";
import { fetchRealCandles } from "@/arya/providers/real-providers";
import { TIMEFRAMES, type Candle } from "@/arya/core/types";

const RUN_ID = "X-Lovable-AIG-Run-ID";

const Body = z.object({
  mode: z.enum(["symbol", "ohlcv"]),
  symbolId: z.string().max(64).optional(),
  timeframe: z.enum(TIMEFRAMES),
  csv: z.string().max(200_000).optional(),
});

function parseCsv(csv: string): Candle[] {
  const rows = csv
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  const out: Candle[] = [];
  for (const row of rows) {
    const p = row.split(/[,;\t]/).map((s) => s.trim());
    if (p.length < 5) continue;
    // Accept "t,open,high,low,close[,volume]" or "open,high,low,close,volume"
    const nums = p.map(Number);
    const hasT = p.length >= 6;
    const [o, h, l, c, v] = hasT ? nums.slice(1) : nums;
    if ([o, h, l, c].some((n) => !Number.isFinite(n))) continue; // header row
    out.push({
      t: hasT ? Date.parse(p[0]!) || Number(p[0]) || out.length : out.length,
      open: o!,
      high: h!,
      low: l!,
      close: c!,
      volume: Number.isFinite(v) ? v! : 0,
    });
  }
  return out;
}

function stats(c: Candle[]) {
  const closes = c.map((x) => x.close);
  const last = closes.at(-1)!;
  const first = closes[0]!;
  const sma = (n: number) => {
    const s = closes.slice(-n);
    return s.reduce((a, b) => a + b, 0) / s.length;
  };
  let gain = 0;
  let loss = 0;
  const w = closes.slice(-15);
  for (let i = 1; i < w.length; i++) {
    const d = w[i]! - w[i - 1]!;
    if (d > 0) gain += d;
    else loss -= d;
  }
  const rsi = gain + loss === 0 ? 50 : 100 - 100 / (1 + gain / (loss || 1e-9));
  const trs = c.slice(-14).map((x, i, a) => {
    const prev = i > 0 ? a[i - 1]!.close : x.open;
    return Math.max(x.high - x.low, Math.abs(x.high - prev), Math.abs(x.low - prev));
  });
  const atr = trs.reduce((a, b) => a + b, 0) / trs.length;
  const r = (n: number) => +n.toPrecision(6);
  return {
    bars: c.length,
    last: r(last),
    changePct: r(((last - first) / first) * 100),
    high: r(Math.max(...c.map((x) => x.high))),
    low: r(Math.min(...c.map((x) => x.low))),
    sma20: r(sma(20)),
    sma50: r(sma(50)),
    rsi14: r(rsi),
    atr14: r(atr),
    atrPct: r((atr / last) * 100),
    recent: c.slice(-20).map((x) => [r(x.open), r(x.high), r(x.low), r(x.close), Math.round(x.volume)]),
  };
}

const json = (status: number, message: string) =>
  new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "content-type": "application/json" },
  });

export async function handleMarketSummary(request: Request): Promise<Response> {
  const apiKey = process.env["LOVABLE_API_KEY"];
  if (!apiKey) return json(500, "کلید هوش مصنوعی پیکربندی نشده است.");

  let body: z.infer<typeof Body>;
  try {
    body = Body.parse(await request.json());
  } catch {
    return json(400, "ورودی نامعتبر است.");
  }

  let candles: Candle[];
  let label: string;
  let provenance: string;
  if (body.mode === "symbol") {
    const sym = findRealSymbol(body.symbolId ?? "");
    if (!sym) return json(400, "نماد یافت نشد.");
    const series = await fetchRealCandles(sym.id, body.timeframe, 120);
    if (series.meta.status === "UNAVAILABLE" || !series.data.length) {
      return json(503, series.meta.reason ?? "دادهٔ واقعی در دسترس نیست.");
    }
    candles = series.data;
    label = `${sym.ticker} (${sym.name})`;
    provenance = `${series.meta.status}; source=${series.meta.source}; fetched=${new Date(series.meta.timestamp).toISOString()}; lastBar=${new Date(candles.at(-1)?.t ?? 0).toISOString()}. Historical OHLCV, not a live quote; do not claim current news or current trading price.`;
  } else {
    candles = parseCsv(body.csv ?? "");
    label = "User-supplied series";
    provenance = "USER-SUPPLIED";
  }
  if (candles.length < 20) return json(400, "حداقل ۲۰ کندل معتبر لازم است.");

  const s = stats(candles);
  const prompt = `Instrument: ${label}\nTimeframe: ${body.timeframe}\nData provenance: ${provenance}\nComputed stats (JSON): ${JSON.stringify(s)}\n("recent" = last 20 bars as [open,high,low,close,volume])`;

  let runId = request.headers.get(RUN_ID)?.trim() || undefined;
  const provider = createOpenAI({
    baseURL: "https://ai.gateway.lovable.dev/v1",
    apiKey,
    headers: { "Lovable-API-Key": apiKey, "X-Lovable-AIG-SDK": "vercel-ai-sdk" },
    fetch: async (input, init) => {
      const headers = new Headers(init?.headers);
      if (runId && !headers.has(RUN_ID)) headers.set(RUN_ID, runId);
      const res = await fetch(input, { ...init, headers });
      runId ??= res.headers.get(RUN_ID)?.trim() || undefined;
      return res;
    },
  });

  let upstreamError: { status: number; message: string } | null = null;
  const result = streamText({
    model: provider.responses("openai/gpt-6-astra"),
    abortSignal: request.signal,
    system:
      "You are a professional market analyst for the ARYA trading platform. Write in Persian (Farsi), concise and practical, using markdown headings and bullets. Sections: 1) وضعیت کلی بازار (trend, momentum, volatility), 2) سطوح کلیدی, 3) ریسک‌های معاملاتی, 4) سناریوها و شرایط ابطال. Base everything strictly on the provided numbers; never invent news or fundamentals. If provenance is DEMO, state clearly at the top that the data is demo and not suitable for real trading. End with a one-line disclaimer that this is not financial advice. Keep it under 350 words.",
    prompt,
    providerOptions: {
      openai: {
        forceReasoning: true,
        reasoningEffort: "low",
        reasoningSummary: "auto",
        store: false,
        include: ["reasoning.encrypted_content"],
      },
    },
    onError: ({ error }) => {
      const e = error as { statusCode?: number; message?: string };
      upstreamError = { status: e.statusCode ?? 500, message: e.message ?? "AI error" };
    },
  });

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of result.textStream) controller.enqueue(encoder.encode(chunk));
        if (upstreamError) {
          const { status } = upstreamError as { status: number };
          const msg =
            status === 402
              ? "اعتبار هوش مصنوعی تمام شده است. لطفاً اعتبار فضای کاری را افزایش دهید."
              : status === 429
                ? "تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
                : "خطا در تولید خلاصه.";
          controller.enqueue(encoder.encode(`\n\n[[ERROR]] ${msg}`));
        }
      } catch {
        controller.enqueue(encoder.encode("\n\n[[ERROR]] خطا در تولید خلاصه."));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}
