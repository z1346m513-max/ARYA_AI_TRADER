import { createFileRoute } from "@tanstack/react-router";

import { handleTradeJournal } from "@/lib/trade-journal.server";

export const Route = createFileRoute("/api/trade-journal")({
  server: { handlers: { POST: ({ request }) => handleTradeJournal(request) } },
});
