import { createFileRoute } from "@tanstack/react-router";
import { LineChart } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ChartPanel } from "@/components/arya/ChartPanel";

const title = "تحلیل نمودار | آریا";
const description = "نمودار کندلی چندتایم‌فریمی با اندیکاتورهای قابل تنظیم برای بورس، ارز دیجیتال و فارکس.";

export const Route = createFileRoute("/chart")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ChartPage,
});

function ChartPage() {
  return (
    <AppShell>
      <ChartPanel />
    </AppShell>
  );
}
