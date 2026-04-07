"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ConnectionErrorOverlay } from "@/components/errors/ConnectionErrorOverlay";
import { getConfig, resetConfig } from "@/lib/config";
import type { ConnectionError } from "@/lib/types/config";

interface ConnectionGuardProps {
  children: React.ReactNode;
}

export function ConnectionGuard({ children }: ConnectionGuardProps) {
  const [error, setError] = useState<ConnectionError | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  // Use a ref to track checking status to avoid dependency cycles
  const isCheckingRef = useRef(false);
  const errorRef = useRef<ConnectionError | null>(null);

  const checkConnection = useCallback(async () => {
    // Prevent re-entry if already checking
    if (isCheckingRef.current) {
      return;
    }

    isCheckingRef.current = true;
    setIsChecking(true);

    setError(null);

    // Reset config cache to force a fresh fetch
    resetConfig();

    try {
      const config = await getConfig();

      // Check if database is offline
      if (config.dbStatus === "offline") {
        const dbError: ConnectionError = {
          type: "database-offline",
          details: {
            message: "Database is offline", // Fallback message, UI will translate
            attemptedUrl: config.apiUrl,
          },
        };
        setError(dbError);
        isCheckingRef.current = false;
        setIsChecking(false);
        return;
      }

      // If we got here, connection is good
      setError(null);
      isCheckingRef.current = false;
      setIsChecking(false);
    } catch (err) {
      // API is unreachable
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      const attemptedUrl =
        typeof window !== "undefined" ? `${window.location.origin}/api/config` : undefined;

      const apiError: ConnectionError = {
        type: "api-unreachable",
        details: {
          message: "Unable to connect to API", // Fallback message
          technicalMessage: errorMessage,
          stack: err instanceof Error ? err.stack : undefined,
          attemptedUrl,
        },
      };

      setError(apiError);
      isCheckingRef.current = false;
      setIsChecking(false);
    }
  }, []); // Empty dependency array - stable callback

  // Check connection on mount
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  useEffect(() => {
    errorRef.current = error;
  }, [error]);

  // Add keyboard shortcut for retry (R key)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (errorRef.current && (e.key === "r" || e.key === "R")) {
        e.preventDefault();
        checkConnection();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [checkConnection]);

  // Show overlay if there's an error
  if (error) {
    return <ConnectionErrorOverlay error={error} onRetry={checkConnection} />;
  }

  // Show nothing while checking (prevents flash of content)
  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <LoadingSpinner size="md" label="Checking connection" />
          <span>Checking connection...</span>
        </div>
      </div>
    );
  }

  // Render children if connection is good
  return <>{children}</>;
}
