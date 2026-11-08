import type { ReactNode } from "react";

import { TopBar } from "@/components/arya/TopBar";
import { Sidebar } from "@/components/arya/Sidebar";

/** Shared chrome for every ARYA page: ticker bar + navigation + content. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div dir="rtl" className="min-h-screen bg-background p-3">
      <div className="mx-auto flex max-w-[1560px] flex-col gap-3">
        <div className="panel overflow-hidden">
          <TopBar />
          <div className="flex">
            <Sidebar />
            <main className="min-w-0 flex-1 p-3">{children}</main>
          </div>
        </div>
      </div>
    </div>
  );
}
