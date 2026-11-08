import { createFileRoute } from "@tanstack/react-router";
import { Briefcase } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";
import { TradeJournalTool } from "@/components/arya/TradeJournalTool";

const title = "پرتفوی | آریا";
const description = "مدیریت پرتفوی، اندازه‌ی موقعیت، ریسک کل سبد و همبستگی دارایی‌ها در ARYA AI Trader.";

export const Route = createFileRoute("/portfolio")({
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
  component: PortfolioPage,
});

function PortfolioPage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-4">
      <TradeJournalTool />
      <ModuleStub
        title="پرتفوی"
        icon={Briefcase}
        phase="فاز ۱۱"
        summary="ثبت موقعیت‌ها، محاسبه‌ی اندازه‌ی موقعیت بر پایه ریسک هر معامله، ریسک کل سبد، حداکثر افت سرمایه و ریسک همبستگی."
        scope={[
          "ثبت و ویرایش موقعیت",
          "اندازه‌ی موقعیت",
          "ریسک کل سبد",
          "حداکثر افت سرمایه",
          "ریسک همبستگی",
          "سود و زیان تحقق‌نیافته",
        ]}
      />
      </div>
    </AppShell>
  );
}
