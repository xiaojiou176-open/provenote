import "@testing-library/jest-dom";
import { vi } from "vitest";
import { enUS } from "../lib/locales/en-US";

const INTERPOLATION_RE = /\{(\w+)\}/g;

function resolveMessage(key: string, values?: Record<string, unknown>) {
  const resolved = key
    .split(".")
    .reduce<unknown>(
      (current, segment) =>
        typeof current === "object" && current !== null
          ? (current as Record<string, unknown>)[segment]
          : undefined,
      enUS,
    );

  if (typeof resolved !== "string") {
    return key;
  }

  if (!values) {
    return resolved;
  }

  return resolved.replace(INTERPOLATION_RE, (_, name: string) =>
    String(values[name] ?? `{${name}}`),
  );
}

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock @/lib/hooks/use-translation with full locale structure
vi.mock("../lib/hooks/use-translation", () => {
  const t = (key: string, values?: Record<string, unknown>) => resolveMessage(key, values);
  Object.assign(t, enUS);

  return {
    useTranslation: () => ({
      t,
      language: "en-US",
      setLanguage: vi.fn(),
    }),
  };
});

// Mock @/lib/hooks/use-auth
vi.mock("@/lib/hooks/use-auth", () => ({
  useAuth: vi.fn(() => ({
    user: { id: "1", email: "test@example.com" },
    logout: vi.fn(),
    isLoading: false,
  })),
}));

// Mock @/lib/stores/sidebar-store
vi.mock("@/lib/stores/sidebar-store", () => ({
  useSidebarStore: vi.fn(() => ({
    isCollapsed: false,
    toggleCollapse: vi.fn(),
  })),
}));

// Mock @/lib/hooks/use-create-dialogs
vi.mock("@/lib/hooks/use-create-dialogs", () => ({
  useCreateDialogs: vi.fn(() => ({
    openSourceDialog: vi.fn(),
    openNotebookDialog: vi.fn(),
    openPodcastDialog: vi.fn(),
  })),
}));
