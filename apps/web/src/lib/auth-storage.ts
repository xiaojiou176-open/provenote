import { appLog } from "@/lib/log";

const AUTH_STORAGE_KEY = "auth-storage";

type AuthStoragePayload = {
  state?: {
    token?: string;
  };
};

function parseToken(raw: string | null): string | null {
  if (!raw) {
    return null;
  }
  try {
    const payload = JSON.parse(raw) as AuthStoragePayload;
    return payload.state?.token ?? null;
  } catch (error) {
    appLog.error("auth-storage", "Failed to parse auth storage payload", error);
    return null;
  }
}

function migrateLegacyLocalStorageToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const legacyRaw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  const token = parseToken(legacyRaw);
  if (!token) {
    return null;
  }

  const payload = JSON.stringify({ state: { token } });
  window.sessionStorage.setItem(AUTH_STORAGE_KEY, payload);
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  return token;
}

export function getStoredAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const sessionRaw = window.sessionStorage.getItem(AUTH_STORAGE_KEY);
  const sessionToken = parseToken(sessionRaw);
  if (sessionToken) {
    return sessionToken;
  }
  return migrateLegacyLocalStorageToken();
}

export function clearStoredAuthToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}
