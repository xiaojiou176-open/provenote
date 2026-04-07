"use client";

import {
  Book,
  Bot,
  ChevronLeft,
  Command,
  FileText,
  LogOut,
  Menu,
  Mic,
  Plus,
  Search,
  Settings,
  Shuffle,
  Wrench,
  X,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { LanguageToggle } from "@/components/common/LanguageToggle";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { useCreateDialogs } from "@/components/providers/CreateDialogsProvider";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuth } from "@/lib/hooks/use-auth";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { TranslationKeys } from "@/lib/locales";
import { useSidebarStore } from "@/lib/stores/sidebar-store";
import { cn } from "@/lib/utils";

const FOCUSABLE_SELECTOR =
  'a[href], area[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), summary, iframe, object, embed, audio[controls], video[controls], [contenteditable="true"], [tabindex]:not([tabindex="-1"])';

const isKeyEventInsideSidebar = (event: KeyboardEvent, sidebarElement: HTMLElement): boolean => {
  if (event.target instanceof Node && sidebarElement.contains(event.target)) {
    return true;
  }

  if (typeof event.composedPath !== "function") {
    return false;
  }

  return event
    .composedPath()
    .some((pathNode) => pathNode instanceof Node && sidebarElement.contains(pathNode));
};

const getNavigation = (t: TranslationKeys) =>
  [
    {
      title: t.navigation.collect,
      items: [{ name: t.navigation.sources, href: "/sources", icon: FileText }],
    },
    {
      title: t.navigation.process,
      items: [
        { name: t.navigation.notebooks, href: "/notebooks", icon: Book },
        { name: t.navigation.askAndSearch, href: "/search", icon: Search },
      ],
    },
    {
      title: t.navigation.create,
      items: [{ name: t.navigation.podcasts, href: "/podcasts", icon: Mic }],
    },
    {
      title: t.navigation.manage,
      items: [
        { name: t.navigation.models, href: "/settings/api-keys", icon: Bot },
        { name: t.navigation.transformations, href: "/transformations", icon: Shuffle },
        { name: t.navigation.settings, href: "/settings", icon: Settings },
        { name: t.navigation.advanced, href: "/advanced", icon: Wrench },
      ],
    },
  ] as const;

type CreateTarget = "source" | "notebook" | "podcast";

interface AppSidebarProps {
  mobileOpen?: boolean;
  onMobileOpenChange?: (open: boolean) => void;
}

export function AppSidebar({ mobileOpen = false, onMobileOpenChange }: AppSidebarProps = {}) {
  const { t } = useTranslation();
  const navigation = getNavigation(t);
  const pathname = usePathname();
  const { logout } = useAuth();
  const { isCollapsed, toggleCollapse } = useSidebarStore();
  const { openSourceDialog, openNotebookDialog, openPodcastDialog } = useCreateDialogs();
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const lastFocusedElementRef = useRef<HTMLElement | null>(null);

  const [createMenuOpen, setCreateMenuOpen] = useState(false);
  const [pendingNavHref, setPendingNavHref] = useState<string | null>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const [isMac, setIsMac] = useState(true); // Default to Mac for SSR
  const effectiveCollapsed = isDesktop ? isCollapsed : false;
  const expandSidebarLabel = t.common.accessibility.expandSidebarNavigation;
  const collapseSidebarLabel = t.common.accessibility.collapseSidebarNavigation;
  const isMobileSidebarOpen = mobileOpen && !isDesktop;
  const isMobileSidebarHidden = !isDesktop && !mobileOpen;
  const currentPath = pathname ?? "";
  const activeHref =
    navigation
      .flatMap((section) => section.items.map((item) => item.href))
      .filter((href) => currentPath === href || currentPath.startsWith(`${href}/`))
      .sort((leftHref, rightHref) => rightHref.length - leftHref.length)[0] ?? null;

  useEffect(() => {
    setPendingNavHref(null);
  }, [pathname]);

  // Detect platform for keyboard shortcut display
  useEffect(() => {
    setIsMac(navigator.platform.toLowerCase().includes("mac"));
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(min-width: 768px)");
    const updateDesktop = () => {
      setIsDesktop(media.matches);
      if (media.matches) {
        onMobileOpenChange?.(false);
      }
    };

    updateDesktop();
    media.addEventListener("change", updateDesktop);
    return () => media.removeEventListener("change", updateDesktop);
  }, [onMobileOpenChange]);

  useEffect(() => {
    if (!isDesktop && !mobileOpen) {
      setCreateMenuOpen(false);
    }
  }, [isDesktop, mobileOpen]);

  useEffect(() => {
    if (!isMobileSidebarOpen) {
      return;
    }

    const sidebarElement = sidebarRef.current;
    if (!sidebarElement) {
      return;
    }

    if (document.activeElement instanceof HTMLElement) {
      lastFocusedElementRef.current = document.activeElement;
    } else {
      lastFocusedElementRef.current = null;
    }

    const getFocusableElements = () =>
      Array.from(sidebarElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (element) => element.tabIndex >= 0 && element.getClientRects().length > 0,
      );

    const focusableElements = getFocusableElements();
    const firstFocusableElement = focusableElements[0];
    (firstFocusableElement ?? sidebarElement).focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isKeyEventInsideSidebar(event, sidebarElement)) {
        return;
      }

      if (event.key === "Escape") {
        event.preventDefault();
        onMobileOpenChange?.(false);
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const availableFocusableElements = getFocusableElements();
      if (availableFocusableElements.length === 0) {
        event.preventDefault();
        sidebarElement.focus();
        return;
      }

      const firstElement = availableFocusableElements[0];
      const lastElement = availableFocusableElements[availableFocusableElements.length - 1];
      const activeElement =
        document.activeElement instanceof HTMLElement ? document.activeElement : null;

      if (!activeElement || !sidebarElement.contains(activeElement)) {
        event.preventDefault();
        (event.shiftKey ? lastElement : firstElement).focus();
        return;
      }

      if (event.shiftKey && activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      const lastFocusedElement = lastFocusedElementRef.current;
      if (
        lastFocusedElement &&
        document.contains(lastFocusedElement) &&
        !sidebarElement.contains(lastFocusedElement)
      ) {
        lastFocusedElement.focus();
      }
      lastFocusedElementRef.current = null;
    };
  }, [isMobileSidebarOpen, onMobileOpenChange]);

  const handleCreateSelection = (target: CreateTarget) => {
    setCreateMenuOpen(false);
    if (!isDesktop) {
      onMobileOpenChange?.(false);
    }

    if (target === "source") {
      openSourceDialog();
    } else if (target === "notebook") {
      openNotebookDialog();
    } else if (target === "podcast") {
      openPodcastDialog();
    }
  };

  return (
    <TooltipProvider delayDuration={0}>
      {mobileOpen && !isDesktop && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/40 opacity-100 transition-opacity duration-200 ease-out motion-reduce:transition-none md:hidden"
          aria-label={t.common.close}
          onClick={() => onMobileOpenChange?.(false)}
        />
      )}
      <div
        ref={sidebarRef}
        id="mobile-sidebar"
        tabIndex={isMobileSidebarOpen ? -1 : undefined}
        role={isMobileSidebarOpen ? "dialog" : "navigation"}
        aria-modal={isMobileSidebarOpen ? true : undefined}
        aria-hidden={isMobileSidebarHidden ? true : undefined}
        aria-label={t.navigation.nav}
        className={cn(
          "app-sidebar fixed inset-y-0 left-0 z-50 flex h-full flex-col bg-sidebar border-sidebar-border border-r transition-transform duration-300 ease-out motion-reduce:transition-none md:static md:z-auto md:translate-x-0",
          effectiveCollapsed ? "w-16" : "w-64",
          mobileOpen || isDesktop ? "translate-x-0" : "-translate-x-full",
          isMobileSidebarHidden && "pointer-events-none invisible",
        )}
      >
        <div
          className={cn(
            "flex h-16 items-center group",
            effectiveCollapsed ? "justify-center px-2" : "justify-between px-4",
          )}
        >
          {effectiveCollapsed ? (
            <div className="relative flex items-center justify-center w-full">
              <Image
                src="/logo.svg"
                alt="Provenote"
                width={32}
                height={32}
                className="transition-opacity group-hover:opacity-0"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleCollapse}
                className="absolute text-sidebar-foreground hover:bg-sidebar-accent opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                aria-label={expandSidebarLabel}
              >
                <Menu className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <Image src="/logo.svg" alt={t.common.appName} width={32} height={32} />
                <span className="text-base font-medium text-sidebar-foreground">
                  {t.common.appName}
                </span>
              </div>
              {isDesktop && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleCollapse}
                  className="text-sidebar-foreground hover:bg-sidebar-accent"
                  data-testid="sidebar-toggle"
                  aria-label={collapseSidebarLabel}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              )}
              {!isDesktop && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onMobileOpenChange?.(false)}
                  aria-label={t.common.close}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </>
          )}
        </div>

        <nav className={cn("flex-1 space-y-1 py-4", effectiveCollapsed ? "px-2" : "px-3")}>
          <div className={cn("mb-4", effectiveCollapsed ? "px-0" : "px-3")}>
            <DropdownMenu open={createMenuOpen} onOpenChange={setCreateMenuOpen}>
              {effectiveCollapsed ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <DropdownMenuTrigger asChild>
                      <Button
                        onClick={() => setCreateMenuOpen(true)}
                        variant="default"
                        size="sm"
                        className="w-full justify-center px-2 bg-primary hover:bg-primary/90 text-primary-foreground border-0 hover:-translate-y-px active:translate-y-0 motion-reduce:transform-none"
                        aria-label={t.common.create}
                        aria-haspopup="menu"
                        aria-expanded={createMenuOpen}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                  </TooltipTrigger>
                  <TooltipContent side="right">{t.common.create}</TooltipContent>
                </Tooltip>
              ) : (
                <DropdownMenuTrigger asChild>
                  <Button
                    onClick={() => setCreateMenuOpen(true)}
                    variant="default"
                    size="sm"
                    className="w-full justify-start bg-primary hover:bg-primary/90 text-primary-foreground border-0 hover:-translate-y-px active:translate-y-0 motion-reduce:transform-none"
                    aria-haspopup="menu"
                    aria-expanded={createMenuOpen}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    {t.common.create}
                  </Button>
                </DropdownMenuTrigger>
              )}

              <DropdownMenuContent
                align={effectiveCollapsed ? "end" : "start"}
                side={effectiveCollapsed ? "right" : "bottom"}
                className="w-48"
              >
                <DropdownMenuItem
                  onSelect={(event) => {
                    event.preventDefault();
                    handleCreateSelection("source");
                  }}
                  className="gap-2"
                >
                  <FileText className="h-4 w-4" />
                  {t.common.source}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={(event) => {
                    event.preventDefault();
                    handleCreateSelection("notebook");
                  }}
                  className="gap-2"
                >
                  <Book className="h-4 w-4" />
                  {t.common.notebook}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={(event) => {
                    event.preventDefault();
                    handleCreateSelection("podcast");
                  }}
                  className="gap-2"
                >
                  <Mic className="h-4 w-4" />
                  {t.common.podcast}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {navigation.map((section, index) => (
            <div key={section.title}>
              {index > 0 && <Separator className="my-3" />}
              <div className="space-y-1">
                {!effectiveCollapsed && (
                  <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground">
                    {section.title}
                  </h3>
                )}

                {section.items.map((item) => {
                  const isActive = item.href === activeHref;
                  const isPending = pendingNavHref === item.href;
                  const linkClasses = cn(
                    "ui-nav-link group w-full gap-3 text-sidebar-foreground sidebar-menu-item",
                    isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
                    isPending && "opacity-90",
                    effectiveCollapsed ? "justify-center px-2" : "justify-start",
                  );

                  if (effectiveCollapsed) {
                    return (
                      <Tooltip key={item.name}>
                        <TooltipTrigger asChild>
                          <Link
                            href={item.href}
                            className={cn(
                              linkClasses,
                              "inline-flex h-9 items-center rounded-md text-sm font-medium transition-[background-color,transform] duration-150 hover:bg-sidebar-accent active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar",
                            )}
                            aria-label={item.name}
                            aria-current={isActive ? "page" : undefined}
                            aria-busy={isPending}
                            onClick={() => {
                              setPendingNavHref(item.href);
                              if (!isDesktop) {
                                onMobileOpenChange?.(false);
                              }
                            }}
                          >
                            <item.icon
                              className={cn("ui-nav-icon h-4 w-4", isPending && "ui-shimmer")}
                            />
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="right">{item.name}</TooltipContent>
                      </Tooltip>
                    );
                  }

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        linkClasses,
                        "inline-flex h-9 items-center rounded-md px-3 text-sm font-medium transition-[background-color,transform] duration-150 hover:bg-sidebar-accent active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar",
                      )}
                      aria-current={isActive ? "page" : undefined}
                      aria-busy={isPending}
                      onClick={() => {
                        setPendingNavHref(item.href);
                        if (!isDesktop) {
                          onMobileOpenChange?.(false);
                        }
                      }}
                    >
                      <item.icon className={cn("ui-nav-icon h-4 w-4", isPending && "ui-shimmer")} />
                      <span>{item.name}</span>
                      {isPending && (
                        <span
                          className="ml-auto inline-flex h-2 w-2 rounded-full bg-current opacity-80 ui-shimmer"
                          aria-hidden="true"
                        />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div
          className={cn(
            "border-t border-sidebar-border p-3 space-y-2",
            effectiveCollapsed && "px-2",
          )}
        >
          {/* Command Palette hint */}
          {!effectiveCollapsed && (
            <div className="ui-quick-hint px-3 py-1.5 text-xs text-sidebar-foreground">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Command className="h-3 w-3" />
                  {t.common.quickActions}
                </span>
                <kbd className="ui-quick-kbd pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                  {isMac ? <span className="text-xs">⌘</span> : <span>Ctrl+</span>}K
                </kbd>
              </div>
              <p className="mt-1 text-[10px] text-sidebar-foreground">
                {t.common.quickActionsDesc}
              </p>
            </div>
          )}

          <div
            className={cn(
              "flex flex-col gap-2",
              effectiveCollapsed ? "items-center" : "items-stretch",
            )}
          >
            {effectiveCollapsed ? (
              <>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <ThemeToggle iconOnly />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right">{t.common.theme}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <LanguageToggle iconOnly />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right">{t.common.language}</TooltipContent>
                </Tooltip>
              </>
            ) : (
              <>
                <ThemeToggle />
                <LanguageToggle />
              </>
            )}
          </div>

          {effectiveCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  className="ui-signout-btn w-full justify-center text-sidebar-foreground hover:text-sidebar-accent-foreground"
                  onClick={() => {
                    if (!isDesktop) {
                      onMobileOpenChange?.(false);
                    }
                    logout();
                  }}
                  aria-label={t.common.signOut}
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">{t.common.signOut}</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              variant="ghost"
              className="ui-signout-btn w-full justify-start gap-3 text-sidebar-foreground hover:text-sidebar-accent-foreground"
              onClick={() => {
                if (!isDesktop) {
                  onMobileOpenChange?.(false);
                }
                logout();
              }}
              aria-label={t.common.signOut}
            >
              <LogOut className="ui-icon-shift h-4 w-4" />
              {t.common.signOut}
            </Button>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
