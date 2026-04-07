"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";

export function useAuth() {
  const router = useRouter();
  const {
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
    checkAuthRequired,
    error,
    hasHydrated,
    authRequired,
  } = useAuthStore();

  useEffect(() => {
    // Only check auth after the store has hydrated from localStorage
    if (hasHydrated) {
      // First check if auth is required
      if (authRequired === null) {
        checkAuthRequired().then((required) => {
          // If auth is required, check if we have valid credentials
          if (required) {
            checkAuth();
          }
        });
      } else if (authRequired) {
        // Auth is required, check credentials
        checkAuth();
      }
      // If authRequired === false, we're already authenticated (set in checkAuthRequired)
    }
  }, [
    hasHydrated,
    authRequired, // Auth is required, check credentials
    checkAuth,
    checkAuthRequired,
  ]);

  const handleLogin = async (password: string) => {
    const success = await login(password);
    if (success) {
      // Check if there's a stored redirect path
      const redirectPath = sessionStorage.getItem("redirectAfterLogin");
      if (redirectPath) {
        sessionStorage.removeItem("redirectAfterLogin");
        router.push(redirectPath);
      } else {
        router.push("/notebooks");
      }
    }
    return success;
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return {
    isAuthenticated,
    authRequired,
    isLoading: isLoading || !hasHydrated, // Treat lack of hydration as loading
    error,
    login: handleLogin,
    logout: handleLogout,
  };
}
