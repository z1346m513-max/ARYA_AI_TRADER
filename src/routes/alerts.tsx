import { createFileRoute } from "@tanstack/react-router";
import { Bell } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "هشدارها | آریا";
const description = "هشدار قیمت، اندیکاتور، حجم، شکست ساختار، کدال و سیگنال هوش مصنوعی.";

export const Route = createFileRoute("/alerts")({
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
  component: AlertsPage,
});

function AlertsPage() {
  return (
    <AppShell>
      <ModuleStub
        title="هشدارها"
        icon={Bell}
        phase="فاز ۱۶"
        summary="تعریف شرط‌های هشدار روی قیمت، اندیکاتور، حجم، شکست، BOS، CHOCH، خبر، کدال، ریسک و سیگنال هوش مصنوعی."
        scope={[
          "هشدار قیمت",
          "هشدار اندیکاتور",
          "هشدار حجم",
          "هشدار شکست و BOS/CHOCH",
          "هشدار خبر و کدال",
          "هشدار ریسک",
        ]}
      />
    </AppShell>
  );
}
