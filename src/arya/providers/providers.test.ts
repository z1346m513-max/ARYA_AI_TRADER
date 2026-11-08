import { describe, expect, it } from "vitest";

import { isReal } from "@/arya/core/data-envelope";
import { MockProvider, generateCandles } from "@/arya/providers/mock-provider";
import { getMarketProvider, listMarketProviders, safeProviderCall } from "@/arya/providers/registry";

const FIXED_NOW = 1_700_000_000_000;
const provider = new MockProvider(() => FIXED_NOW);

describe("MockProvider", () => {
  it("declares itself a demo source", () => {
    expect(provider.info.kind).toBe("demo");
  });

  it("stamps every payload as DEMO, never real", async () => {
    const symbols = await provider.listSymbols();
    const ohlcv = await provider.getOhlcv({ symbolId: "crypto:BTCUSDT", timeframe: "1D", limit: 10 });
    const quote = await provider.getQuote("crypto:BTCUSDT");
    for (const env of [symbols.meta, ohlcv.meta, quote.meta].map((meta) => ({ data: null, meta }))) {
      expect(env.meta.status).toBe("DEMO");
      expect(isReal(env)).toBe(false);
    }
  });

  it("produces reproducible series for the same symbol and timeframe", () => {
    const a = generateCandles("iran-equity:FOLD", "1D", 50, FIXED_NOW);
    const b = generateCandles("iran-equity:FOLD", "1D", 50, FIXED_NOW);
    expect(a).toEqual(b);
    expect(generateCandles("crypto:BTCUSDT", "1D", 50, FIXED_NOW)).not.toEqual(a);
  });

  it("produces internally consistent OHLC bars on an ascending time axis", () => {
    const candles = generateCandles("iran-equity:FOLD", "1h", 120, FIXED_NOW);
    expect(candles).toHaveLength(120);
    for (let i = 0; i < candles.length; i++) {
      const c = candles[i]!;
      expect(c.high).toBeGreaterThanOrEqual(Math.max(c.open, c.close));
      expect(c.low).toBeLessThanOrEqual(Math.min(c.open, c.close));
      expect(c.volume).toBeGreaterThan(0);
      if (i > 0) expect(c.t).toBeGreaterThan(candles[i - 1]!.t);
    }
    expect(candles[candles.length - 1]!.t).toBe(FIXED_NOW);
  });

  it("filters symbols by market", async () => {
    const crypto = await provider.listSymbols("crypto");
    expect(crypto.data.every((s) => s.market === "crypto")).toBe(true);
    expect(crypto.data.length).toBeGreaterThan(0);
  });

  it("caps absurd limits instead of allocating unbounded arrays", async () => {
    const env = await provider.getOhlcv({ symbolId: "crypto:ETHUSDT", timeframe: "1D", limit: 99_999 });
    expect(env.data.length).toBe(2000);
  });
});

describe("provider registry", () => {
  it("registers the mock provider by default", () => {
    expect(getMarketProvider("mock")).toBeDefined();
    expect(listMarketProviders().length).toBeGreaterThan(0);
  });

  it("returns UNAVAILABLE instead of throwing when a provider keeps failing", async () => {
    let attempts = 0;
    const env = await safeProviderCall<number[]>(
      "FlakyProvider",
      "flaky",
      [],
      async () => {
        attempts++;
        throw new Error("boom");
      },
      { timeoutMs: 50, retries: 2, backoffMs: 1, sleep: async () => {} },
    );
    expect(attempts).toBe(3);
    expect(env.meta.status).toBe("UNAVAILABLE");
    expect(env.meta.reason).toBe("boom");
    expect(env.data).toEqual([]);
  });

  it("recovers when a later attempt succeeds", async () => {
    let attempts = 0;
    const env = await safeProviderCall<number[]>(
      "FlakyProvider",
      "flaky",
      [],
      async () => {
        attempts++;
        if (attempts < 2) throw new Error("transient");
        return { data: [1], meta: { source: "F", providerId: "flaky", timestamp: 1, status: "LIVE", quality: 1 } };
      },
      { timeoutMs: 50, retries: 3, backoffMs: 1, sleep: async () => {} },
    );
    expect(env.meta.status).toBe("LIVE");
    expect(env.data).toEqual([1]);
  });

  it("times out a hanging provider", async () => {
    const env = await safeProviderCall<null>(
      "HangingProvider",
      "hang",
      null,
      () => new Promise(() => {}),
      { timeoutMs: 10, retries: 0, backoffMs: 1, sleep: async () => {} },
    );
    expect(env.meta.status).toBe("UNAVAILABLE");
    expect(env.meta.reason).toMatch(/timeout/i);
  });
});
