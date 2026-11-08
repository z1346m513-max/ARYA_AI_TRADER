import { createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/arya/AppShell";
import { ChartPanel } from "@/components/arya/ChartPanel";
import { ScorePanel } from "@/components/arya/ScorePanel";
import { AiPanel } from "@/components/arya/AiPanel";
import { RightRail } from "@/components/arya/RightRail";
import { Architecture } from "@/components/arya/Architecture";


const title = "آریا | داشبورد تحلیل هوشمند بازار";
const description =
  "داشبورد ARYA AI Trader: تحلیل تکنیکال، امتیازدهی وزن‌دار، موتور تصمیم هوش مصنوعی و مدیریت ریسک برای بورس، ارز دیجیتال و فارکس.";

export const Route = createFileRoute("/")({
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
  component: Index,
});

function Index() {
  return (
    <AppShell>
      <div className="flex flex-col gap-3">
        <div className="flex min-w-0 gap-3">
          <ChartPanel />
          <div className="hidden w-[228px] shrink-0 xl:block">
            <ScorePanel />
          </div>
          <div className="hidden w-[330px] shrink-0 2xl:block">
            <AiPanel />
          </div>
          <div className="hidden 2xl:block">
            <RightRail />
          </div>
        </div>

        <div className="flex flex-wrap gap-3 2xl:hidden">
          <div className="min-w-[240px] flex-1 xl:hidden">
            <ScorePanel />
          </div>
          <div className="min-w-[320px] flex-1">
            <AiPanel />
          </div>
          <RightRail />
        </div>

        <Architecture />
      </div>
    </AppShell>
  );
}

