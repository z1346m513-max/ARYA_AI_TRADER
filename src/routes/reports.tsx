import { createFileRoute } from "@tanstack/react-router";
import { FileText } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "گزارش‌ها | آریا";
const description = "تولید گزارش تحلیلی در قالب PDF، Excel، CSV و JSON با ثبت منبع و زمان هر داده.";

export const Route = createFileRoute("/reports")({
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
  component: ReportsPage,
});

function ReportsPage() {
  return (
    <AppShell>
      <ModuleStub
        title="گزارش‌ها"
        icon={FileText}
        phase="فاز ۱۶"
        summary="گزارش تحلیلی کامل شامل داده‌ی بازار، تکنیکال، بنیادی، پول هوشمند، اخبار، کدال، ریسک و تصمیم نهایی — همراه با وضعیت داده‌ی هر بخش."
        scope={["خروجی PDF", "خروجی Excel", "خروجی CSV", "خروجی JSON", "درج منبع داده", "درج زمان تولید"]}
      />
    </AppShell>
  );
}
