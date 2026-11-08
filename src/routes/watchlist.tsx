import { createFileRoute } from "@tanstack/react-router";
import { Star } from "lucide-react";

import { AppShell } from "@/components/arya/AppShell";
import { ModuleStub } from "@/components/arya/ModuleStub";

const title = "واچ‌لیست | آریا";
const description = "مدیریت واچ‌لیست‌های چندبازاره، گروه‌بندی نمادها و مقایسه‌ی دارایی‌ها در ARYA AI Trader.";

export const Route = createFileRoute("/watchlist")({
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
  component: WatchlistPage,
});

function WatchlistPage() {
  return (
    <AppShell>
      <ModuleStub
        title="واچ‌لیست"
        icon={Star}
        phase="فاز ۱۴"
        summary="افزودن و حذف نماد، ساخت گروه (بانکی، خودرویی، پتروشیمی، کریپتو، فارکس)، مقایسه‌ی چند نماد و ساخت هشدار روی هر ردیف."
        scope={[
          "افزودن و حذف نماد",
          "گروه‌بندی سفارشی",
          "مقایسه‌ی چند دارایی",
          "امتیاز لحظه‌ای هر نماد",
          "ایجاد هشدار سریع",
          "ذخیره‌سازی پایدار",
        ]}
      />
    </AppShell>
  );
}
