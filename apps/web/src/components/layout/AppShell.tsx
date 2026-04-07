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

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar mobileOpen={mobileSidebarOpen} onMobileOpenChange={setMobileSidebarOpen} />
      <main
        id="main-content"
        tabIndex={-1}
        className="app-main-content flex-1 flex flex-col min-h-0 overflow-hidden"
      >
        <div className="md:hidden border-b border-border px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMobileSidebarOpen(true)}
            className="ui-icon-button"
            aria-label={t.common.accessibility.openSidebarNavigation}
            aria-controls="mobile-sidebar"
            aria-expanded={mobileSidebarOpen}
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        <SetupBanner />
        {children}
      </main>
    </div>
  );
}
