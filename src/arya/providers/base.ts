/**
 * Provider abstraction (specification rule 13).
 *
 * Every data source — Iran equities, crypto, forex, news, Codal, macro —
 * implements one of these interfaces. Providers never return bare values;
 * they return `DataEnvelope`s so provenance survives to the UI.
 */
import type { DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Market, Symbol, Timeframe } from "@/arya/core/types";

export interface ProviderInfo {
  id: string;
  name: string;
  /** DEMO providers must never be presented as real data sources. */
  kind: "demo" | "real";
  markets: Market[];
  description: string;
}

export interface OhlcvRequest {
  symbolId: string;
  timeframe: Timeframe;
  limit: number;
}

export interface QuoteSnapshot {
  symbolId: string;
  price: number;
  changePct: number;
  volume: number;
  updatedAt: number;
}

/** Base contract for OHLCV/quote sources. */
export interface MarketDataProvider {
  readonly info: ProviderInfo;
  /** Cheap availability probe; must not throw. */
  health(): Promise<DataEnvelope<{ ok: boolean }>>;
  listSymbols(market?: Market): Promise<DataEnvelope<Symbol[]>>;
  getQuote(symbolId: string): Promise<DataEnvelope<QuoteSnapshot | null>>;
  getOhlcv(request: OhlcvRequest): Promise<DataEnvelope<Candle[]>>;
}

export interface NewsItem {
  id: string;
  symbolId?: string;
  title: string;
  publishedAt: number;
  url?: string;
  sentiment?: number;
}

export interface NewsProvider {
  readonly info: ProviderInfo;
  getNews(symbolId?: string, limit?: number): Promise<DataEnvelope<NewsItem[]>>;
}

export interface CodalFiling {
  id: string;
  symbolId: string;
  title: string;
  type: "monthly" | "quarterly" | "financial-statement" | "capital-increase" | "disclosure" | "other";
  publishedAt: number;
  url?: string;
}

export interface CodalProvider {
  readonly info: ProviderInfo;
  getFilings(symbolId: string, limit?: number): Promise<DataEnvelope<CodalFiling[]>>;
}

export interface FundamentalSnapshot {
  symbolId: string;
  eps?: number;
  pe?: number;
  ps?: number;
  pb?: number;
  roe?: number;
  roa?: number;
  debtRatio?: number;
  grossMargin?: number;
  operatingMargin?: number;
  netMargin?: number;
  freeCashFlow?: number;
  revenueGrowth?: number;
  profitGrowth?: number;
}

export interface FundamentalProvider {
  readonly info: ProviderInfo;
  getFundamentals(symbolId: string): Promise<DataEnvelope<FundamentalSnapshot | null>>;
}
