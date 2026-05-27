/* eslint-disable @typescript-eslint/no-explicit-any */
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useCreateDialogs } from "@/components/providers/CreateDialogsProvider";
import { useAuth } from "@/lib/hooks/use-auth";
import { useSidebarStore } from "@/lib/stores/sidebar-store";

const SLOW_TEST_TIMEOUT_MS = 15_000;

const navigationHoisted = vi.hoisted(() => ({
  usePathname: vi.fn(() => ""),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    onClick,
    children,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    children: React.ReactNode;
  }) => (
    <a
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
      }}
      {...props}
    >
      {children}
    </a>
  ),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: navigationHoisted.usePathname,
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/components/providers/CreateDialogsProvider", () => ({
  useCreateDialogs: vi.fn(),
}));

import { AppSidebar } from "./AppSidebar";

// Mock Tooltip components to avoid Radix UI async issues in tests
vi.mock("@/components/ui/tooltip", () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({
    asChild,
    children,
  }: {
    asChild?: boolean;
    children: React.ReactElement;
  }) => (asChild ? children : <button type="button">{children}</button>),
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => (
    <div role="menu">{children}</div>
  ),
  DropdownMenuItem: ({
    children,
    onSelect,
    className,
  }: {
    children: React.ReactNode;
    onSelect?: (event: React.MouseEvent<HTMLButtonElement>) => void;
    className?: string;
  }) => (
    <button className={className} onClick={onSelect} role="menuitem" type="button">
      {children}
    </button>
  ),
}));
// But setup.ts has some basic mocks, let's see.

describe("AppSidebar", () => {
  const makeElementVisibleForFocusTrap = (element: HTMLElement) => {
    Object.defineProperty(element, "getClientRects", {
      configurable: true,
      value: () =>
        [
          {
            width: 16,
            height: 16,
            top: 0,
            right: 16,
            bottom: 16,
            left: 0,
          },
        ] as DOMRect[],
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
    navigationHoisted.usePathname.mockReturnValue("");
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: query === "(min-width: 768px)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: false,
      toggleCollapse: vi.fn(),
    } as any);
    vi.mocked(useCreateDialogs).mockReturnValue({
      openSourceDialog: vi.fn(),
      openNotebookDialog: vi.fn(),
      openPodcastDialog: vi.fn(),
    });
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "test@example.com" },
      logout: vi.fn(),
      isLoading: false,
    });
  });

  it("renders correctly when expanded", { timeout: SLOW_TEST_TIMEOUT_MS }, () => {
    render(<AppSidebar />);

    expect(screen.getByText(/Notebooklab/i)).toBeInTheDocument();
    expect(screen.getByText(/Sources/i)).toBeInTheDocument();
    expect(screen.getByText(/Notebooks/i)).toBeInTheDocument();
  });

  it("toggles collapse state when clicking handle", () => {
    const toggleCollapse = vi.fn();
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: false,
      toggleCollapse,
    } as any);

    render(<AppSidebar />);

    fireEvent.click(screen.getByTestId("sidebar-toggle"));

    expect(toggleCollapse).toHaveBeenCalled();
  });

  it("shows collapsed view when isCollapsed is true", () => {
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: true,
      toggleCollapse: vi.fn(),
    } as any);

    render(<AppSidebar />);

    expect(screen.queryByText(/Notebooklab/i)).toBeNull();
  });

  it(
    "closes mobile sidebar when Escape is pressed from inside sidebar",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    () => {
      const onMobileOpenChange = vi.fn();
      vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
      fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });

      expect(onMobileOpenChange).toHaveBeenCalledWith(false);
    },
  );

  it("does not close mobile sidebar when Escape comes from portal content outside sidebar", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    const portalButton = document.createElement("button");
    portalButton.type = "button";
    portalButton.textContent = "Portal action";
    document.body.appendChild(portalButton);
    portalButton.focus();

    fireEvent.keyDown(portalButton, { key: "Escape" });

    expect(onMobileOpenChange).not.toHaveBeenCalled();
    portalButton.remove();
  });

  it("does not trap Tab when key event comes from portal content outside sidebar", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    const sidebarDialog = screen.getByRole("dialog");
    const portalButton = document.createElement("button");
    portalButton.type = "button";
    portalButton.textContent = "Portal focus";
    document.body.appendChild(portalButton);
    portalButton.focus();

    const eventWasNotPrevented = fireEvent.keyDown(portalButton, { key: "Tab" });

    expect(eventWasNotPrevented).toBe(true);
    expect(document.activeElement).toBe(portalButton);
    expect(document.activeElement).not.toBe(sidebarDialog);
    expect(onMobileOpenChange).not.toHaveBeenCalled();
    portalButton.remove();
  });

  it("closes mobile sidebar when backdrop is clicked", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    const closeButtons = screen.getAllByRole("button", { name: /close/i });
    fireEvent.click(closeButtons[0]);

    expect(onMobileOpenChange).toHaveBeenCalledWith(false);
  });

  it(
    "closes mobile sidebar when the explicit close button is clicked",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    () => {
      const onMobileOpenChange = vi.fn();
      vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
      const closeButtons = screen.getAllByRole("button", { name: /close/i });
      fireEvent.click(closeButtons[1]);

      expect(onMobileOpenChange).toHaveBeenCalledWith(false);
    },
  );

  it(
    "closes mobile sidebar and logs out when sign out is clicked on mobile",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    () => {
      const onMobileOpenChange = vi.fn();
      const logout = vi.fn();
      vi.mocked(useAuth).mockReturnValue({
        user: { id: "1", email: "test@example.com" },
        logout,
        isLoading: false,
      });
      vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
      fireEvent.click(screen.getByRole("button", { name: /sign out/i }));

      expect(onMobileOpenChange).toHaveBeenCalledWith(false);
      expect(logout).toHaveBeenCalled();
    },
  );

  it(
    "opens source create dialog from create menu and closes mobile sidebar",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    async () => {
      const onMobileOpenChange = vi.fn();
      const openSourceDialog = vi.fn();
      vi.mocked(useCreateDialogs).mockReturnValue({
        openSourceDialog,
        openNotebookDialog: vi.fn(),
        openPodcastDialog: vi.fn(),
      });
      vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
      fireEvent.click(screen.getByRole("button", { name: /new/i }));
      fireEvent.click(await screen.findByRole("menuitem", { name: /source/i }));

      expect(openSourceDialog).toHaveBeenCalled();
      expect(onMobileOpenChange).toHaveBeenCalledWith(false);
    },
  );

  it("restores focus to the previously focused element when mobile sidebar closes", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.textContent = "open sidebar";
    document.body.appendChild(trigger);
    trigger.focus();

    const { rerender } = render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    rerender(<AppSidebar mobileOpen={false} onMobileOpenChange={onMobileOpenChange} />);

    expect(document.activeElement).toBe(trigger);
    trigger.remove();
  });

  it("exposes create menu expanded state for assistive technologies", async () => {
    render(<AppSidebar />);

    const createButton = screen.getByRole("button", { name: /create|new/i });
    expect(createButton).toHaveAttribute("aria-haspopup", "menu");
    expect(createButton).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(createButton);

    expect(await screen.findByRole("menuitem", { name: /source/i })).toBeInTheDocument();
    expect(createButton).toHaveAttribute("aria-expanded", "true");
  });

  it("marks clicked mobile navigation as pending and closes sidebar", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    const sourcesLink = screen.getByRole("link", { name: /sources/i });
    fireEvent.click(sourcesLink);

    expect(sourcesLink).toHaveAttribute("aria-busy", "true");
    expect(onMobileOpenChange).toHaveBeenCalledWith(false);
  });

  it(
    "supports collapsed desktop create actions and collapsed sign-out",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    async () => {
      const openNotebookDialog = vi.fn();
      const openPodcastDialog = vi.fn();
      const logout = vi.fn();
      vi.mocked(useSidebarStore).mockReturnValue({
        isCollapsed: true,
        toggleCollapse: vi.fn(),
      } as any);
      vi.mocked(useCreateDialogs).mockReturnValue({
        openSourceDialog: vi.fn(),
        openNotebookDialog,
        openPodcastDialog,
      });
      vi.mocked(useAuth).mockReturnValue({
        user: { id: "1", email: "test@example.com" },
        logout,
        isLoading: false,
      });

      render(<AppSidebar />);

      const createButton = screen.getByRole("button", { name: /create|new/i });
      fireEvent.click(createButton);
      fireEvent.click(await screen.findByRole("menuitem", { name: /notebook/i }));
      fireEvent.click(createButton);
      fireEvent.click(await screen.findByRole("menuitem", { name: /podcast/i }));

      expect(openNotebookDialog).toHaveBeenCalledTimes(1);
      expect(openPodcastDialog).toHaveBeenCalledTimes(1);

      const sourcesLink = screen.getByRole("link", { name: /sources/i });
      fireEvent.click(sourcesLink);
      expect(sourcesLink).toHaveAttribute("aria-busy", "true");

      fireEvent.click(screen.getByRole("button", { name: /sign out/i }));
      expect(logout).toHaveBeenCalledTimes(1);
    },
  );

  it("closes collapsed mobile navigation link clicks", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: true,
      toggleCollapse: vi.fn(),
    } as any);
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    fireEvent.click(screen.getByRole("link", { name: /sources/i }));

    expect(onMobileOpenChange).toHaveBeenCalledWith(false);
  });

  it("closes collapsed mobile sign out before logging out", () => {
    const onMobileOpenChange = vi.fn();
    const logout = vi.fn();
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: true,
      toggleCollapse: vi.fn(),
    } as any);
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "test@example.com" },
      logout,
      isLoading: false,
    });
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));

    expect(onMobileOpenChange).toHaveBeenCalledWith(false);
    expect(logout).toHaveBeenCalledTimes(1);
  });

  it("handles null pathname without marking any route active", () => {
    navigationHoisted.usePathname.mockReturnValue(null as unknown as string);

    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /sources/i })).not.toHaveAttribute("aria-current");
  });

  it("marks the active expanded route and keeps desktop nav clicks open", () => {
    const onMobileOpenChange = vi.fn();
    navigationHoisted.usePathname.mockReturnValue("/sources/details");

    render(<AppSidebar onMobileOpenChange={onMobileOpenChange} />);
    const sourcesLink = screen.getByRole("link", { name: /sources/i });
    onMobileOpenChange.mockClear();

    expect(sourcesLink).toHaveAttribute("aria-current", "page");

    fireEvent.click(sourcesLink);

    expect(onMobileOpenChange).not.toHaveBeenCalled();
  });

  it("marks the active collapsed route by aria-current", () => {
    navigationHoisted.usePathname.mockReturnValue("/sources");
    vi.mocked(useSidebarStore).mockReturnValue({
      isCollapsed: true,
      toggleCollapse: vi.fn(),
    } as any);

    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /sources/i })).toHaveAttribute("aria-current", "page");
  });

  it("does not request mobile close when desktop sign-out is clicked", () => {
    const logout = vi.fn();
    const onMobileOpenChange = vi.fn();
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "test@example.com" },
      logout,
      isLoading: false,
    });

    render(<AppSidebar onMobileOpenChange={onMobileOpenChange} />);
    onMobileOpenChange.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));

    expect(onMobileOpenChange).not.toHaveBeenCalled();
    expect(logout).toHaveBeenCalledTimes(1);
  });

  it("ignores portal keydown when composedPath is unavailable", () => {
    const onMobileOpenChange = vi.fn();
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={onMobileOpenChange} />);
    const portalButton = document.createElement("button");
    portalButton.type = "button";
    document.body.appendChild(portalButton);

    const event = new KeyboardEvent("keydown", { key: "Escape", bubbles: true });
    Object.defineProperty(event, "composedPath", {
      configurable: true,
      value: undefined,
    });
    portalButton.dispatchEvent(event);

    expect(onMobileOpenChange).not.toHaveBeenCalled();
    portalButton.remove();
  });

  it("traps focus within mobile sidebar when navigating with Tab keys", () => {
    vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<AppSidebar mobileOpen onMobileOpenChange={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    const firstLink = screen.getByRole("link", { name: /sources/i });
    const lastButton = screen.getByRole("button", { name: /sign out/i });
    makeElementVisibleForFocusTrap(firstLink);
    makeElementVisibleForFocusTrap(lastButton);

    const outsideButton = document.createElement("button");
    outsideButton.type = "button";
    document.body.appendChild(outsideButton);
    outsideButton.focus();

    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(firstLink);

    outsideButton.focus();
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(lastButton);

    firstLink.focus();
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(lastButton);

    lastButton.focus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(firstLink);

    const enterWasNotPrevented = fireEvent.keyDown(dialog, { key: "Enter" });
    expect(enterWasNotPrevented).toBe(true);

    outsideButton.remove();
  });

  it("shows Ctrl shortcut hint on non-mac platforms", () => {
    const originalPlatform = navigator.platform;
    Object.defineProperty(window.navigator, "platform", {
      value: "Win32",
      configurable: true,
    });

    render(<AppSidebar />);
    expect(screen.getByText("Ctrl+")).toBeInTheDocument();

    Object.defineProperty(window.navigator, "platform", {
      value: originalPlatform,
      configurable: true,
    });
  });
});
