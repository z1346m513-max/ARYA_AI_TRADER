import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

import { TIMEFRAMES } from "@/arya/core/types";
import { fetchRealCandles } from "@/arya/providers/real-providers";

export const getCandles = createServerFn({ method: "GET" })
  .inputValidator((d) =>
    z.object({ symbolId: z.string().max(64), timeframe: z.enum(TIMEFRAMES), limit: z.number().int().min(10).max(1000) }).parse(d),
  )
  .handler(({ data }) => fetchRealCandles(data.symbolId, data.timeframe, data.limit));
