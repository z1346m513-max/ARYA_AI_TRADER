import { createOpenAI } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";

const RUN_ID = "X-Lovable-AIG-Run-ID";

const Trade = z.object({
  symbol: z.string().trim().min(1).max(32),
  side: z.enum(["long", "short"]),
  entry: z.number().finite().positive(),
  exit: z.number().finite().positive(),
  size: z.number().finite().positive().optional(),
  openedAt: z.string().max(40).optional(),
  closedAt: z.string().max(40).optional(),
  setup: z.string().max(120).optional(),
  note: z.string().max(1000).optional(),
});
const Body = z.object({ trades: z.array(Trade).min(3).max(200) });

const json = (status: number, message: string) =>
  new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "content-type": "application/json" },
  });

export async function handleTradeJournal(request: Request): Promise<Response> {
  const apiKey = process.env["LOVABLE_API_KEY"];
  if (!apiKey) return json(500, "کلید هوش مصنوعی پیکربندی نشده است.");

  let body: z.infer<typeof Body>;
  try {
    body = Body.parse(await request.json());
  } catch {
    return json(400, "ورودی نامعتبر است (حداقل ۳ معامله‌ی معتبر لازم است).");
  }

  const rows = body.trades.map((t) => {
    const pct = ((t.exit - t.entry) / t.entry) * 100 * (t.side === "long" ? 1 : -1);
    return { ...t, returnPct: +pct.toFixed(3) };
  });
  const wins = rows.filter((r) => r.returnPct > 0);
  const losses = rows.filter((r) => r.returnPct <= 0);
  const avg = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const summary = {
    trades: rows.length,
    winRatePct: +((wins.length / rows.length) * 100).toFixed(1),
    avgWinPct: +avg(wins.map((r) => r.returnPct)).toFixed(3),
    avgLossPct: +avg(losses.map((r) => r.returnPct)).toFixed(3),
  };
  const prompt = `Aggregate stats (computed): ${JSON.stringify(summary)}\nClosed trades (JSON, returnPct computed): ${JSON.stringify(rows)}`;

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

  let upstreamError: { status: number } | null = null;
  const result = streamText({
    model: provider.responses("openai/gpt-6-astra"),
    abortSignal: request.signal,
    system:
      "You are a trading-performance coach for the ARYA platform. Write in Persian (Farsi) with markdown headings and bullets. Analyze the trader's closed trades and notes. Sections: 1) خلاصه‌ی عملکرد, 2) الگوهای رفتاری تکرارشونده (e.g. revenge trading, early exits, cutting winners, overtrading, setup/symbol/side bias, emotional language in notes) — cite specific trades as evidence, 3) ریسک‌های قابل‌اقدام, 4) اقدامات پیشنهادی (concrete, measurable rules). Base everything strictly on the provided data; if evidence is weak, say so. End with a one-line disclaimer that this is not financial advice. Keep it under 400 words.",
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
      upstreamError = { status: (error as { statusCode?: number }).statusCode ?? 500 };
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
                : status === 403
                  ? "دسترسی به هوش مصنوعی مسدود است."
                  : "خطا در تحلیل ژورنال.";
          controller.enqueue(encoder.encode(`\n\n[[ERROR]] ${msg}`));
        }
      } catch {
        controller.enqueue(encoder.encode("\n\n[[ERROR]] خطا در تحلیل ژورنال."));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}
