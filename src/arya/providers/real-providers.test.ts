import { afterEach, describe, expect, it, vi } from "vitest";
import { binanceCandles, fetchRealCandles, tsetmcCandles } from "./real-providers";

afterEach(() => vi.unstubAllGlobals());

describe("real data integrity", () => {
  it("never substitutes generated candles for a failed Tehran request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await tsetmcCandles("46348559193224090", "1D", 20);
    expect(result.meta.status).toBe("UNAVAILABLE");
    expect(result.data).toEqual([]);
  });
  it("rejects invalid Binance bars instead of labelling them live", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([[1700000000000, "10", "5", "8", "12", "100"]]))));
    const result = await binanceCandles("BTCUSDT", "1D", 20);
    expect(result.meta.status).toBe("UNAVAILABLE");
    expect(result.data).toEqual([]);
  });
  it("keeps real valid Binance prices unchanged", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([[1700000000000, "10", "13", "8", "12", "100"]]))));
    const result = await binanceCandles("BTCUSDT", "1D", 20);
    expect(result.meta.providerId).toBe("binance");
    expect(result.data[0]?.close).toBe(12);
  });
  it("does not guess a source for unsupported instruments", async () => {
    const result = await fetchRealCandles("forex:UNKNOWN", "1D", 20);
    expect(result.data).toEqual([]);
    expect(result.meta.status).toBe("UNAVAILABLE");
  });
});