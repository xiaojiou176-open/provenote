/**
 * Runtime configuration for the frontend.
 * This allows the same Docker image to work in different environments.
 */

import { appLog } from "@/lib/log";
import type { AppConfig, BackendConfigResponse } from "@/lib/types/config";

// Build timestamp for debugging - set at build time
const BUILD_TIME = new Date().toISOString();

let config: AppConfig | null = null;
let configPromise: Promise<AppConfig> | null = null;

const resolveRuntimeApiUrl = (payload: unknown): string | null => {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const apiUrl = (payload as { apiUrl?: unknown }).apiUrl;
  if (typeof apiUrl !== "string" || apiUrl === "") {
    return null;
  }
  return apiUrl;
};

const getOrLoadConfig = async (): Promise<AppConfig> => {
  if (config) {
    return config;
  }

  if (!configPromise) {
    configPromise = fetchConfig();
  }

  try {
    return await configPromise;
  } catch (error) {
    configPromise = null;
    throw error;
  }
};

/**
 * Get the API URL to use for requests.
 *
 * Priority:
 * 1. Runtime config from API server (/api/config endpoint)
 * 2. Environment variable (NEXT_PUBLIC_API_URL)
 * 3. Default fallback (http://localhost:5055)
 */
export async function getApiUrl(): Promise<string> {
  const cfg = await getOrLoadConfig();
  return cfg.apiUrl;
}

/**
 * Get the full configuration.
 */
export async function getConfig(): Promise<AppConfig> {
  return await getOrLoadConfig();
}

/**
 * Fetch configuration from the API or use defaults.
 */
async function fetchConfig(): Promise<AppConfig> {
  const isDev = process.env.NODE_ENV === "development";

  if (isDev) {
    appLog.info("config", "Starting configuration detection", { buildTime: BUILD_TIME });
  }

  // STEP 1: Try to get runtime config from Next.js server-side endpoint
  // This allows API_URL to be set at runtime (not baked into build)
  // Note: Endpoint is at /config (not /api/config) to avoid reverse proxy conflicts
  let runtimeApiUrl: string | null = null;
  try {
    if (isDev) {
      appLog.info("config", "Attempting to fetch runtime config from /config endpoint");
    }
    const runtimeResponse = await fetch("/config", {
      cache: "no-store",
    });
    if (runtimeResponse.ok) {
      const runtimeData = await runtimeResponse.json();
      runtimeApiUrl = resolveRuntimeApiUrl(runtimeData);
      if (isDev) {
        appLog.info("config", "Runtime API URL resolved from /config", { runtimeApiUrl });
      }
    } else {
      if (isDev) {
        appLog.info("config", "Runtime config endpoint returned non-ok status", {
          status: runtimeResponse.status,
        });
      }
    }
  } catch (error) {
    if (isDev) {
      appLog.info("config", "Could not fetch runtime config", error);
    }
  }

  // STEP 2: Fallback to build-time environment variable
  const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (isDev) {
    appLog.info("config", "NEXT_PUBLIC_API_URL from build", {
      envApiUrl: envApiUrl || "(not set)",
    });
  }

  // STEP 3: Smart default - prefer relative path to use Next.js Rewrites
  // This avoids CORS issues and port mapping complexities by proxying through Next.js
  const defaultApiUrl = "";

  if (typeof window !== "undefined" && isDev) {
    appLog.info("config", "Using relative rewrites path as default API base");
  }

  // Priority: Runtime config > Build-time env var > Smart default
  // Note: runtimeApiUrl must be checked against null explicitly as empty string might be valid if intended (though we treat '' as null above)
  const baseUrl =
    runtimeApiUrl !== null && runtimeApiUrl !== undefined
      ? runtimeApiUrl
      : envApiUrl || defaultApiUrl;
  if (isDev) {
    appLog.info("config", "Resolved configuration selection priority", {
      baseUrl,
      usedRuntimeConfig: Boolean(runtimeApiUrl),
      usedBuildTimeEnv: Boolean(envApiUrl),
      usedSmartDefault: !runtimeApiUrl && !envApiUrl,
    });
  }
  if (isDev) {
    appLog.info("config", "Fetching backend config", {
      endpoint: `${baseUrl}/api/config`,
    });
  }
  // Try to fetch runtime config from backend API
  const response = await fetch(`${baseUrl}/api/config`, {
    cache: "no-store",
  });

  if (response.ok) {
    const data: BackendConfigResponse = await response.json();
    config = {
      apiUrl: baseUrl, // Use baseUrl from runtime-config (Python no longer returns this)
      version: data.version || "unknown",
      buildTime: BUILD_TIME,
      latestVersion: data.latestVersion || null,
      hasUpdate: data.hasUpdate || false,
      dbStatus: data.dbStatus, // Can be undefined for old backends
    };
    if (isDev) {
      appLog.info("config", "Successfully loaded API config", config);
    }
    return config;
  } else {
    // Don't log error here - ConnectionGuard will display it
    throw new Error(`API config endpoint returned status ${response.status}`);
  }
}

/**
 * Reset the configuration cache (useful for testing).
 */
export function resetConfig(): void {
  config = null;
  configPromise = null;
}
