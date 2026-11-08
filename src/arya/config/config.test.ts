import { describe, expect, it } from "vitest";

import { DEFAULT_CONFIG, resolveConfig, mergeConfig } from "@/arya/config";
import { appConfigSchema } from "@/arya/config/schemas";

describe("config engine", () => {
  it("ships defaults that satisfy the schema", () => {
    expect(appConfigSchema.safeParse(DEFAULT_CONFIG).success).toBe(true);
  });

  it("exposes the specification's default indicator parameters", () => {
    expect(DEFAULT_CONFIG.indicators["ema"]?.params["period"]).toBe(20);
    expect(DEFAULT_CONFIG.indicators["rsi"]?.params).toMatchObject({
      period: 14,
      overbought: 70,
      oversold: 30,
    });
    expect(DEFAULT_CONFIG.indicators["macd"]?.params).toMatchObject({
      fast: 12,
      slow: 26,
      signal: 9,
    });
    expect(DEFAULT_CONFIG.indicators["atr"]?.params["period"]).toBe(14);
  });

  it("deep-merges a partial user patch without dropping siblings", () => {
    const merged = mergeConfig(DEFAULT_CONFIG, { risk: { riskPerTradePct: 2 } });
    expect(merged.risk.riskPerTradePct).toBe(2);
    expect(merged.risk.maxPositions).toBe(DEFAULT_CONFIG.risk.maxPositions);
  });

  it("accepts a valid override", () => {
    const result = resolveConfig({ scheduler: { interval: "5m" } });
    expect(result.fellBack).toBe(false);
    expect(result.config.scheduler.interval).toBe("5m");
  });

  it("falls back to defaults and reports errors on invalid input", () => {
    const result = resolveConfig({ risk: { riskPerTradePct: 500 } });
    expect(result.fellBack).toBe(true);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.config.risk.riskPerTradePct).toBe(DEFAULT_CONFIG.risk.riskPerTradePct);
  });

  it("rejects an unknown timeframe", () => {
    expect(resolveConfig({ timeframes: { trend: "2h" } }).fellBack).toBe(true);
  });
});
