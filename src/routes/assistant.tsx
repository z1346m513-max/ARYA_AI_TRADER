import { createFileRoute } from "@tanstack/react-router";
import { Bot } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";
import { MarketSummaryTool } from "@/components/arya/MarketSummaryTool";

const title = "دستیار هوش مصنوعی | آریا";
const description = "دستیار تحلیلی که بر پایه داده‌های موتور تحلیل، سناریو، اعتبار و شرایط ابطال تصمیم را توضیح می‌دهد.";

export const Route = createFileRoute("/assistant")({
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
  component: AssistantPage,
});

function AssistantPage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-4">
        <MarketSummaryTool />
        <ModuleStub
          title="دستیار هوش مصنوعی"
          icon={Bot}
          phase="فاز ۱۳"
          summary="موتور تصمیم هوش مصنوعی روی خروجی موتورهای تحلیل کار می‌کند: تشخیص تضاد سیگنال‌ها، ساخت سناریو، بیان اعتبار و تعیین شرایط ابطال."
          scope={["مقایسه‌ی چند نماد", "تشخیص تضاد سیگنال", "سناریوسازی", "بیان درصد اعتبار", "شرایط ابطال تحلیل"]}
        />
      </div>
    </AppShell>
  );
}
