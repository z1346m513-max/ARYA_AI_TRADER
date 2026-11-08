import { createFileRoute } from "@tanstack/react-router";
import { Newspaper } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "اخبار و کدال | آریا";
const description = "اطلاعیه‌های کدال، صورت‌های مالی، گزارش‌های ماهانه و تحلیل احساسات اخبار بازار.";

export const Route = createFileRoute("/news")({
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
  component: NewsPage,
});

function NewsPage() {
  return (
    <AppShell>
      <ModuleStub
        title="اخبار و کدال"
        icon={Newspaper}
        phase="فاز ۸ و ۱۰"
        summary="موتور کدال و موتور اخبار هنوز Provider واقعی ندارند. هیچ اطلاعیه یا خبری ساختگی در این صفحه نمایش داده نمی‌شود؛ هر رکورد در آینده با منبع و زمان انتشار خود ثبت می‌شود."
        scope={[
          "گزارش ماهانه",
          "گزارش فصلی",
          "صورت‌های مالی",
          "افزایش سرمایه",
          "افشای بااهمیت",
          "تحلیل احساسات اخبار",
        ]}
      />
    </AppShell>
  );
}
