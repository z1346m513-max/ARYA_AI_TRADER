import { createFileRoute } from "@tanstack/react-router";
import { Radar } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "اسکنر بازار | آریا";
const description = "اسکن و رتبه‌بندی نمادهای بازار بر پایه امتیاز تکنیکال، بنیادی، پول هوشمند، حجم و ریسک.";

export const Route = createFileRoute("/scanner")({
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
  component: ScannerPage,
});

function ScannerPage() {
  return (
    <AppShell>
      <ModuleStub
        title="اسکنر بازار"
        icon={Radar}
        phase="فاز ۱۴"
        summary="پالایش کل بازار و رتبه‌بندی نمادها در شش سطح تصمیم از خرید قوی تا فروش قوی، بر اساس امتیازهای وزن‌دار."
        scope={[
          "فیلتر چندمعیاره",
          "رتبه‌بندی امتیاز نهایی",
          "شش سطح تصمیم",
          "فیلتر حجم و نقدشوندگی",
          "فیلتر ساختار بازار",
          "خروجی به واچ‌لیست",
        ]}
      />
    </AppShell>
  );
}
