/**
 * Smart Money engine: aggregates structure, order blocks, FVGs and liquidity
 * into a single -100..100 reading, preserving data provenance end-to-end.
 */
import { envelope, type DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Direction } from "@/arya/core/types";
import { clamp01, rma, trueRange } from "@/arya/indicators/math";

import { findStructureEvents, findSwings } from "./structure";
import {
  DEFAULT_SMART_MONEY_PARAMS,
  type SmartMoneyParams,
  type SmartMoneyReport,
} from "./types";
import { findFairValueGaps, findLiquidityPools, findOrderBlocks } from "./zones";

const sign = (d: Direction): number => (d === "bullish" ? 1 : d === "bearish" ? -1 : 0);

function toBias(score: number): Direction {
  if (score > 10) return "bullish";
  if (score < -10) return "bearish";
  return "neutral";
}

const EMPTY_REPORT: SmartMoneyReport = {
  swings: [],
  structure: [],
  orderBlocks: [],
  fairValueGaps: [],
  liquidity: [],
  bias: "neutral",
  score: 0,
  coverage: 0,
  note: "داده کافی برای تحلیل ساختار بازار وجود ندارد",
};

/** Run the full smart-money model over a raw candle array. */
export function runSmartMoney(
  candles: Candle[],
  overrides: Partial<SmartMoneyParams> = {},
): SmartMoneyReport {
  const params: SmartMoneyParams = { ...DEFAULT_SMART_MONEY_PARAMS, ...overrides };
  const minBars = Math.max(params.atrPeriod + 2, params.swingLookback * 2 + 3);
  if (candles.length < minBars) return { ...EMPTY_REPORT };

  const atr = rma(trueRange(candles), params.atrPeriod);
  const swings = findSwings(candles, params.swingLookback);
  const structure = findStructureEvents(candles, swings, atr);
  const orderBlocks = findOrderBlocks(candles, atr, params.minImpulseAtr);
  const fairValueGaps = findFairValueGaps(candles, params.minGapPct);
  const liquidity = findLiquidityPools(candles, swings, params.equalTolerancePct);

  const recentStructure = structure.slice(-3);
  const structureScore = recentStructure.length
    ? recentStructure.reduce(
        (acc, e, i) => acc + sign(e.direction) * (0.4 + 0.6 * e.strength) * (i + 1),
        0,
      ) / recentStructure.reduce((acc, _e, i) => acc + (i + 1), 0)
    : 0;

  const activeBlocks = orderBlocks.filter((b) => !b.mitigated).slice(-params.maxZones);
  const blockScore = activeBlocks.length
    ? activeBlocks.reduce((a, b) => a + sign(b.direction) * (0.5 + 0.5 * b.strength), 0) /
      activeBlocks.length
    : 0;

  const openGaps = fairValueGaps.filter((g) => !g.filled).slice(-params.maxZones);
  const gapScore = openGaps.length
    ? openGaps.reduce((a, g) => a + sign(g.direction), 0) / openGaps.length
    : 0;

  // An unswept pool is a magnet: price is drawn toward resting liquidity.
  const unswept = liquidity.filter((p) => !p.swept);
  const liquidityScore = unswept.length
    ? unswept.reduce((a, p) => a + (p.side === "buy-side" ? 1 : -1), 0) / unswept.length
    : 0;

  const components: Array<{ value: number; weight: number; present: boolean }> = [
    { value: structureScore, weight: 0.45, present: recentStructure.length > 0 },
    { value: blockScore, weight: 0.25, present: activeBlocks.length > 0 },
    { value: gapScore, weight: 0.2, present: openGaps.length > 0 },
    { value: liquidityScore, weight: 0.1, present: unswept.length > 0 },
  ];
  const den = components.filter((c) => c.present).reduce((a, c) => a + c.weight, 0);
  const num = components.filter((c) => c.present).reduce((a, c) => a + c.value * c.weight, 0);
  const score = den ? +((num / den) * 100).toFixed(2) : 0;
  const coverage = clamp01(den / components.reduce((a, c) => a + c.weight, 0));

  const lastEvent = structure[structure.length - 1];
  const bias = toBias(score);
  const note = lastEvent
    ? `آخرین رویداد ساختاری: ${lastEvent.kind} ${lastEvent.direction === "bullish" ? "صعودی" : "نزولی"} در سطح ${lastEvent.level.toLocaleString("en-US")} · ${activeBlocks.length} اردربلاک فعال · ${openGaps.length} گپ باز`
    : "هیچ شکست ساختاری تاییدشده‌ای یافت نشد";

  return {
    swings,
    structure,
    orderBlocks,
    fairValueGaps,
    liquidity,
    bias,
    score,
    coverage,
    note,
  };
}

/** Envelope-preserving variant: demo candles can never produce live output. */
export function analyzeSmartMoney(
  input: DataEnvelope<Candle[]>,
  overrides: Partial<SmartMoneyParams> = {},
): DataEnvelope<SmartMoneyReport> {
  const report = runSmartMoney(input.data, overrides);
  return envelope(report, {
    source: input.meta.source,
    providerId: input.meta.providerId,
    status: input.data.length === 0 ? "UNAVAILABLE" : input.meta.status,
    timestamp: input.meta.timestamp,
    quality: input.meta.quality * (0.4 + 0.6 * report.coverage),
    ...(report.coverage < 1
      ? { reason: `پوشش مدل اسمارت‌مانی ${Math.round(report.coverage * 100)}٪` }
      : input.meta.reason
        ? { reason: input.meta.reason }
        : {}),
  });
}
