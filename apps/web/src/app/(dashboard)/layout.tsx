"use client";

import { usePathname, useRouter } from "next/navigation";
import { type AnimationEvent, useEffect, useState } from "react";
import { CommandPalette } from "@/components/common/CommandPalette";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { CreateDialogsProvider } from "@/components/providers/CreateDialogsProvider";
import { ModalProvider } from "@/components/providers/ModalProvider";
import { useAuth } from "@/lib/hooks/use-auth";
import { useVersionCheck } from "@/lib/hooks/use-version-check";
import { cn } from "@/lib/utils";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, authRequired } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);
  const [isRouteTransitioning, setIsRouteTransitioning] = useState(false);
  const [routeProgressKey, setRouteProgressKey] = useState(0);

  // Check for version updates once per session
  useVersionCheck();

  useEffect(() => {
    // Mark that we've completed the initial auth check only after auth policy resolves.
    if (!isLoading && authRequired !== null) {
      setHasCheckedAuth(true);

      // Redirect only when auth is explicitly required and user is unauthenticated.
      // This avoids race conditions before /api/auth/status resolves.
      if (authRequired && !isAuthenticated) {
        // Store the current path to redirect back after login
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem("redirectAfterLogin", currentPath);
        router.push("/login");
      }
    }
  }, [authRequired, isAuthenticated, isLoading, router]);

  useEffect(() => {
    setIsRouteTransitioning(true);
    setRouteProgressKey((prev) => prev + 1);
  }, [pathname]);

  useEffect(() => {
    if (!isRouteTransitioning || typeof window.matchMedia !== "function") {
      return;
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIsRouteTransitioning(false);
    }
  }, [isRouteTransitioning]);

  const handleRouteProgressAnimationEnd = (event: AnimationEvent<HTMLDivElement>) => {
    if (event.target !== event.currentTarget) {
      return;
    }
    setIsRouteTransitioning(false);
  };

  // Show loading spinner during initial auth check or while loading
  if (isLoading || !hasCheckedAuth || authRequired === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // Don't render anything only when authentication is explicitly required and missing.
  if (authRequired !== false && !isAuthenticated) {
    return null;
  }

  return (
    <ErrorBoundary>
      <CreateDialogsProvider>
        <div
          key={routeProgressKey}
          aria-hidden="true"
          className={cn("ui-route-progress", isRouteTransitioning && "ui-route-progress-active")}
          onAnimationEnd={handleRouteProgressAnimationEnd}
        />
        <div key={pathname} className="ui-route-shell">
          {children}
        </div>
        <ModalProvider />
        <CommandPalette />
      </CreateDialogsProvider>
    </ErrorBoundary>
  );
}
