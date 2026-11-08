import { describe, expect, it } from "vitest";

import { DEFAULT_WEIGHTS } from "@/arya/config/defaults";
import { normalizeWeights, toPercentages, validateWeights } from "@/arya/config/weights";
import { WEIGHT_KEYS, type WeightsConfig } from "@/arya/config/schemas";

const custom: WeightsConfig = {
  technical: 40,
  fundamental: 25,
  smartMoney: 15,
  codal: 5,
  news: 5,
  liquidity: 5,
  risk: 3,
  ai: 2,
};

describe("weighting engine", () => {
  it("accepts the specification's default allocation", () => {
    const result = validateWeights(DEFAULT_WEIGHTS);
    expect(result.valid).toBe(true);
    expect(result.total).toBe(100);
    expect(result.normalized).toBe(true);
  });

  it("accepts the user-adjusted allocation from the specification", () => {
    expect(validateWeights(custom).valid).toBe(true);
  });

  it("normalizes an allocation that does not sum to 100", () => {
    const skewed: WeightsConfig = { ...DEFAULT_WEIGHTS, technical: 60 };
    const normalized = normalizeWeights(skewed);
    const sum = WEIGHT_KEYS.reduce((a, k) => a + normalized[k], 0);
    expect(sum).toBeCloseTo(1, 10);
    expect(normalized.technical).toBeGreaterThan(normalized.fundamental);
  });

  it("preserves ratios when rescaling to percentages", () => {
    const scaled = toPercentages({ ...DEFAULT_WEIGHTS, technical: 60 });
    const sum = WEIGHT_KEYS.reduce((a, k) => a + scaled[k], 0);
    expect(sum).toBeCloseTo(100, 1);
  });

  it("rejects negative and out-of-range weights", () => {
    expect(validateWeights({ ...DEFAULT_WEIGHTS, risk: -1 }).valid).toBe(false);
    expect(validateWeights({ ...DEFAULT_WEIGHTS, risk: 101 }).valid).toBe(false);
  });

  it("refuses to normalize an all-zero allocation instead of guessing", () => {
    const zeros = Object.fromEntries(WEIGHT_KEYS.map((k) => [k, 0])) as WeightsConfig;
    expect(validateWeights(zeros).valid).toBe(false);
    expect(() => normalizeWeights(zeros)).toThrow(/total is zero/i);
  });
});
