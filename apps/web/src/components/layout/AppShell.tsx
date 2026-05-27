"use client";

import { Menu } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/hooks/use-translation";
import { AppSidebar } from "./AppSidebar";
import { SetupBanner } from "./SetupBanner";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { t } = useTranslation();
  const appName = t.common.appName ?? "Notebooklab";
  const mobileSectionLabel = t.navigation?.process ?? "Workbench";

  return (
    <div className="flex min-h-screen overflow-hidden bg-transparent">
      <AppSidebar mobileOpen={mobileSidebarOpen} onMobileOpenChange={setMobileSidebarOpen} />
      <main
        id="main-content"
        tabIndex={-1}
        className="app-main-content relative flex min-h-screen flex-1 flex-col overflow-hidden"
      >
        <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="md:hidden border-b border-border/70 bg-background/78 px-4 py-3 backdrop-blur-xl">
            <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-card/85 px-3 py-2 shadow-[0_12px_24px_oklch(18%_0.02_45deg_/6%)]">
              <div className="space-y-0.5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {mobileSectionLabel}
                </p>
                <p className="font-serif text-lg leading-none tracking-[-0.03em]">{appName}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setMobileSidebarOpen(true)}
                className="ui-icon-button rounded-xl"
                aria-label={t.common.accessibility.openSidebarNavigation}
                aria-controls="mobile-sidebar"
                aria-expanded={mobileSidebarOpen}
              >
                <Menu className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="relative z-10 px-4 pt-4 md:px-6 lg:px-8">
            <SetupBanner />
          </div>

          <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
