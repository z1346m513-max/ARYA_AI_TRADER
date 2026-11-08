/**
 * Provider registry with timeout, retry and graceful degradation
 * (specification rules 13 and 29). A provider failure degrades a single
 * envelope to UNAVAILABLE; it never throws into the UI.
 */
import { unavailable, type DataEnvelope } from "@/arya/core/data-envelope";

import type { MarketDataProvider } from "./base";
import { MockProvider } from "./mock-provider";

const marketProviders = new Map<string, MarketDataProvider>();

export function registerMarketProvider(provider: MarketDataProvider): void {
  marketProviders.set(provider.info.id, provider);
}

export function getMarketProvider(id: string): MarketDataProvider | undefined {
  return marketProviders.get(id);
}

export function listMarketProviders(): MarketDataProvider[] {
  return [...marketProviders.values()];
}

registerMarketProvider(new MockProvider());

export interface SafeCallOptions {
  timeoutMs: number;
  retries: number;
  backoffMs: number;
  /** Awaitable delay; injectable for tests. */
  sleep?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

function timeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Provider timeout after ${ms}ms`)), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error: unknown) => {
        clearTimeout(timer);
        reject(error instanceof Error ? error : new Error(String(error)));
      },
    );
  });
}

/**
 * Run a provider call with timeout + retry. On total failure returns an
 * UNAVAILABLE envelope wrapping `fallback` instead of throwing.
 */
export async function safeProviderCall<T>(
  label: string,
  providerId: string,
  fallback: T,
  call: () => Promise<DataEnvelope<T>>,
  options: SafeCallOptions,
): Promise<DataEnvelope<T>> {
  const sleep = options.sleep ?? defaultSleep;
  let lastError = "Unknown provider error";

  for (let attempt = 0; attempt <= options.retries; attempt++) {
    try {
      return await timeout(call(), options.timeoutMs);
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
      if (attempt < options.retries) await sleep(options.backoffMs * (attempt + 1));
    }
  }

  return unavailable(fallback, label, providerId, lastError);
}
