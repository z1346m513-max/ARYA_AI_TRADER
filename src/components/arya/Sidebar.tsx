import { Link } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Star,
  Radar,
  LineChart,
  Bot,
  Briefcase,
  Newspaper,
  History,
  Bell,
  FileText,
  Settings,
} from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", label: "داشبورد", icon: LayoutDashboard },
  { to: "/watchlist", label: "واچ لیست", icon: Star },
  { to: "/scanner", label: "اسکنر بازار", icon: Radar },
  { to: "/chart", label: "تحلیل نمودار", icon: LineChart },
  { to: "/assistant", label: "دستیار هوش مصنوعی", icon: Bot },
  { to: "/portfolio", label: "پرتفوی", icon: Briefcase },
  { to: "/news", label: "اخبار و کدال", icon: Newspaper },
  { to: "/backtest", label: "بک‌تست", icon: History },
  { to: "/alerts", label: "هشدارها", icon: Bell },
  { to: "/reports", label: "گزارش‌ها", icon: FileText },
  { to: "/settings", label: "تنظیمات", icon: Settings },
] as const;

export function Sidebar() {
  return (
    <aside className="flex w-[212px] shrink-0 flex-col gap-1 border-l border-sidebar-border bg-sidebar p-3">
      <nav className="flex flex-col gap-0.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              className="flex items-center gap-2.5 rounded-md px-3 py-2 text-right text-[13px] text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
              activeProps={{
                className:
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-right text-[13px] transition-colors bg-sidebar-primary text-sidebar-primary-foreground",
              }}
            >
              <Icon className="size-4 shrink-0" strokeWidth={1.75} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex items-center gap-2.5 rounded-md border border-sidebar-border bg-surface-2 p-2.5">
        <div className="grid size-8 place-items-center rounded-full bg-primary/15 text-xs font-bold text-primary">
          A
        </div>
        <div className="leading-tight">
          <p className="text-[12px] font-medium">کاربر آریا</p>
          <p className="text-[10px] text-muted-foreground">نسخه توسعه ۰.۲</p>
        </div>
      </div>
    </aside>
  );
}
