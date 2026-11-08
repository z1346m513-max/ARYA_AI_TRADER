/**
 * Weight validation and normalization (specification rule 6).
 *
 * Users may enter any non-negative numbers. The scoring engine always
 * consumes normalized weights that sum to exactly 1.
 */
import { WEIGHT_KEYS, weightsConfigSchema, type WeightKey, type WeightsConfig } from "./schemas";

export interface WeightValidation {
  valid: boolean;
  total: number;
  /** True when the raw input already sums to 100 (within tolerance). */
  normalized: boolean;
  errors: string[];
}

const TOLERANCE = 0.01;

export function validateWeights(input: unknown): WeightValidation {
  const parsed = weightsConfigSchema.safeParse(input);
  if (!parsed.success) {
    return {
      valid: false,
      total: 0,
      normalized: false,
      errors: parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`),
    };
  }
  const total = WEIGHT_KEYS.reduce((sum, key) => sum + parsed.data[key], 0);
  const errors: string[] = [];
  if (total <= 0) errors.push("Sum of weights must be greater than zero.");
  return {
    valid: errors.length === 0,
    total,
    normalized: Math.abs(total - 100) < TOLERANCE,
    errors,
  };
}

/**
 * Scale weights so they sum to 1. Throws when the total is zero, because a
 * silent fallback would hide a broken user configuration.
 */
export function normalizeWeights(weights: WeightsConfig): Record<WeightKey, number> {
  const total = WEIGHT_KEYS.reduce((sum, key) => sum + weights[key], 0);
  if (total <= 0) throw new Error("Cannot normalize weights: total is zero.");
  const out = {} as Record<WeightKey, number>;
  for (const key of WEIGHT_KEYS) out[key] = weights[key] / total;
  return out;
}

/** Rescale weights to sum to 100, preserving their ratios (for the UI). */
export function toPercentages(weights: WeightsConfig): WeightsConfig {
  const normalized = normalizeWeights(weights);
  const out = {} as WeightsConfig;
  for (const key of WEIGHT_KEYS) out[key] = +(normalized[key] * 100).toFixed(2);
  return out;
}

/** fa-IR labels for the eight pillars. */
export const WEIGHT_LABEL_FA: Record<WeightKey, string> = {
  technical: "تکنیکال",
  fundamental: "بنیادی",
  smartMoney: "پول هوشمند",
  codal: "کدال",
  news: "اخبار",
  liquidity: "نقدشوندگی",
  risk: "ریسک",
  ai: "هوش مصنوعی",
};
