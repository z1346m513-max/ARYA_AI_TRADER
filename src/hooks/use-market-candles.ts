import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";

import type { DataEnvelope } from "@/arya/core/data-envelope";
import type { Candle, Timeframe } from "@/arya/core/types";
import { getCandles } from "@/lib/market-data.functions";

/** Loads real candles; `null` while loading. Never falls back to demo data. */
export function useMarketCandles(symbolId: string, timeframe: Timeframe, limit = 240) {
  const fetchCandles = useServerFn(getCandles);
  const [env, setEnv] = useState<DataEnvelope<Candle[]> | null>(null);

  useEffect(() => {
    let alive = true;
    setEnv(null);
    fetchCandles({ data: { symbolId, timeframe, limit } })
      .then((r) => alive && setEnv(r as DataEnvelope<Candle[]>))
      .catch((e: unknown) =>
        alive &&
        setEnv({
          data: [],
          meta: { source: "—", providerId: "none", timestamp: Date.now(), status: "UNAVAILABLE", quality: 0, reason: e instanceof Error ? e.message : String(e) },
        }),
      );
    return () => {
      alive = false;
    };
  }, [fetchCandles, symbolId, timeframe, limit]);

  return env;
}
