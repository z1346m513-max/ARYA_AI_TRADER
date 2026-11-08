import { createFileRoute } from "@tanstack/react-router";

import { handleMarketSummary } from "@/lib/market-summary.server";

export const Route = createFileRoute("/api/market-summary")({
  server: { handlers: { POST: ({ request }) => handleMarketSummary(request) } },
});
