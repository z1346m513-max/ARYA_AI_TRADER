import { createFileRoute } from "@tanstack/react-router";
import { History } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "بک‌تست | آریا";
const description = "آزمون استراتژی روی داده‌های تاریخی با کارمزد، لغزش، اندازه‌ی موقعیت و تحلیل Walk Forward.";

export const Route = createFileRoute("/backtest")({
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
  component: BacktestPage,
});

function BacktestPage() {
  return (
    <AppShell>
      <ModuleStub
        title="بک‌تست"
        icon={History}
        phase="فاز ۱۲"
        summary="موتور بک‌تست با کارمزد و لغزش واقعی. خروجی شامل سود خالص، نرخ برد، ضریب سود، شارپ، حداکثر افت و امید ریاضی است. نرخ برد بالا به‌تنهایی معیار کیفیت استراتژی نیست و ارزیابی خارج از نمونه الزامی است."
        scope={[
          "داده‌ی تاریخی",
          "قوانین ورود و خروج",
          "کارمزد و لغزش",
          "سود خالص و ضریب سود",
          "شارپ و حداکثر افت",
          "ارزیابی خارج از نمونه",
        ]}
      />
    </AppShell>
  );
}
