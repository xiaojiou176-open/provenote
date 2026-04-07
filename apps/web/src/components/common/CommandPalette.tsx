"use client";

import {
  Book,
  Bot,
  FileText,
  Loader2,
  MessageCircleQuestion,
  Mic,
  Monitor,
  Moon,
  Plus,
  Search,
  Settings,
  Shuffle,
  Sun,
  Wrench,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useId, useMemo, useState } from "react";
import { useCreateDialogs } from "@/components/providers/CreateDialogsProvider";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { TranslationKeys } from "@/lib/locales";
import { useTheme } from "@/lib/stores/theme-store";

const getNavigationItems = (t: TranslationKeys) => [
  {
    name: t.navigation.sources,
    href: "/sources",
    icon: FileText,
    keywords: ["files", "documents", "upload"],
  },
  {
    name: t.navigation.notebooks,
    href: "/notebooks",
    icon: Book,
    keywords: ["notes", "research", "projects"],
  },
  { name: t.navigation.askAndSearch, href: "/search", icon: Search, keywords: ["find", "query"] },
  {
    name: t.navigation.podcasts,
    href: "/podcasts",
    icon: Mic,
    keywords: ["audio", "episodes", "generate"],
  },
  {
    name: t.navigation.models,
    href: "/settings/api-keys",
    icon: Bot,
    keywords: ["ai", "llm", "providers", "openai", "anthropic"],
  },
  {
    name: t.navigation.transformations,
    href: "/transformations",
    icon: Shuffle,
    keywords: ["prompts", "templates", "actions"],
  },
  {
    name: t.navigation.settings,
    href: "/settings",
    icon: Settings,
    keywords: ["preferences", "config", "options"],
  },
  {
    name: t.navigation.advanced,
    href: "/advanced",
    icon: Wrench,
    keywords: ["debug", "system", "tools"],
  },
];

const getCreateItems = (t: TranslationKeys) => [
  { name: t.common.newSource, action: "source", icon: FileText },
  { name: t.common.newNotebook, action: "notebook", icon: Book },
  { name: t.common.newPodcast, action: "podcast", icon: Mic },
];

const getThemeItems = (t: TranslationKeys) => [
  { name: t.common.light, value: "light" as const, icon: Sun, keywords: ["bright", "day"] },
  { name: t.common.dark, value: "dark" as const, icon: Moon, keywords: ["night"] },
  { name: t.common.system, value: "system" as const, icon: Monitor, keywords: ["auto", "default"] },
];

export function CommandPalette() {
  const { t } = useTranslation();
  const commandInputId = useId();
  const navigationItems = useMemo(() => getNavigationItems(t), [t]);
  const createItems = useMemo(() => getCreateItems(t), [t]);
  const themeItems = useMemo(() => getThemeItems(t), [t]);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();
  const { openSourceDialog, openNotebookDialog, openPodcastDialog } = useCreateDialogs();
  const { setTheme } = useTheme();
  const { data: notebooks, isLoading: notebooksLoading } = useNotebooks(false);

  // Global keyboard listener for ⌘K / Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      // Skip if focus is inside editable elements
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
      ) {
        return;
      }

      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        e.stopPropagation();
        setOpen((open) => !open);
      }
    };

    // Use capture phase to intercept before other handlers
    document.addEventListener("keydown", down, true);
    return () => document.removeEventListener("keydown", down, true);
  }, []);

  // Reset query when dialog closes
  useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  const handleSelect = useCallback((callback: () => void) => {
    setOpen(false);
    setQuery("");
    // Use setTimeout to ensure dialog closes before action
    setTimeout(callback, 0);
  }, []);

  const handleNavigate = useCallback(
    (href: string) => {
      handleSelect(() => router.push(href));
    },
    [handleSelect, router],
  );

  const handleSearch = useCallback(() => {
    if (!query.trim()) {
      return;
    }
    handleSelect(() => router.push(`/search?q=${encodeURIComponent(query)}&mode=search`));
  }, [handleSelect, router, query]);

  const handleAsk = useCallback(() => {
    if (!query.trim()) {
      return;
    }
    handleSelect(() => router.push(`/search?q=${encodeURIComponent(query)}&mode=ask`));
  }, [handleSelect, router, query]);

  const handleCreate = useCallback(
    (action: string) => {
      handleSelect(() => {
        if (action === "source") {
          openSourceDialog();
        } else if (action === "notebook") {
          openNotebookDialog();
        } else if (action === "podcast") {
          openPodcastDialog();
        }
      });
    },
    [handleSelect, openSourceDialog, openNotebookDialog, openPodcastDialog],
  );

  const handleTheme = useCallback(
    (theme: "light" | "dark" | "system") => {
      handleSelect(() => setTheme(theme));
    },
    [handleSelect, setTheme],
  );

  // Check if query matches any command (navigation, create, theme, or notebook)
  const queryLower = query.toLowerCase().trim();
  const commandMatchesCount = useMemo(() => {
    if (!queryLower) {
      return 0;
    }

    const navigationCount = navigationItems.filter(
      (item) =>
        item.name.toLowerCase().includes(queryLower) ||
        item.keywords.some((keyword) => keyword.includes(queryLower)),
    ).length;
    const createCount = createItems.filter((item) =>
      item.name.toLowerCase().includes(queryLower),
    ).length;
    const themeCount = themeItems.filter(
      (item) =>
        item.name.toLowerCase().includes(queryLower) ||
        item.keywords.some((keyword) => keyword.includes(queryLower)),
    ).length;
    const notebookCount =
      notebooks?.filter(
        (notebook) =>
          notebook.name.toLowerCase().includes(queryLower) ||
          notebook.description?.toLowerCase().includes(queryLower),
      ).length ?? 0;

    return navigationCount + createCount + themeCount + notebookCount;
  }, [createItems, navigationItems, notebooks, queryLower, themeItems]);

  const hasCommandMatch = useMemo(() => {
    if (!queryLower) {
      return false;
    }
    return (
      navigationItems.some(
        (item) =>
          item.name.toLowerCase().includes(queryLower) ||
          item.keywords.some((k) => k.includes(queryLower)),
      ) ||
      createItems.some((item) => item.name.toLowerCase().includes(queryLower)) ||
      themeItems.some(
        (item) =>
          item.name.toLowerCase().includes(queryLower) ||
          item.keywords.some((k) => k.includes(queryLower)),
      ) ||
      (notebooks?.some(
        (nb) =>
          nb.name.toLowerCase().includes(queryLower) ||
          nb.description?.toLowerCase().includes(queryLower),
      ) ??
        false)
    );
  }, [queryLower, notebooks, navigationItems, createItems, themeItems]);

  // Determine if we should show the Search/Ask section at the top
  const showSearchFirst = query.trim() && !hasCommandMatch;

  return (
    <CommandDialog
      open={open}
      onOpenChange={setOpen}
      title={t.common.quickActions}
      description={t.common.quickActionsDesc}
      className="ui-cmd-dialog sm:max-w-lg"
    >
      <CommandInput
        id={commandInputId}
        name="command-search"
        className="ui-cmd-input"
        placeholder={t.searchPage.enterSearchPlaceholder}
        value={query}
        onValueChange={setQuery}
        aria-label={t.common.search}
        autoComplete="off"
      />
      {queryLower && (
        <p className="sr-only" aria-live="polite">
          {commandMatchesCount > 0
            ? t.searchPage.matches.replace("{count}", commandMatchesCount.toString())
            : t.searchPage.noResultsFor.replace("{query}", query)}
        </p>
      )}
      <CommandList>
        {/* Search/Ask - show FIRST when there's a query with no command match */}
        {showSearchFirst && (
          <CommandGroup heading={t.searchPage.searchAndAsk} forceMount>
            <CommandItem
              className="ui-cmd-item"
              value={`__search__ ${query}`}
              onSelect={handleSearch}
              forceMount
            >
              <Search className="ui-icon-shift h-4 w-4" />
              <span>{t.searchPage.searchResultsFor.replace("{query}", query)}</span>
            </CommandItem>
            <CommandItem
              className="ui-cmd-item"
              value={`__ask__ ${query}`}
              onSelect={handleAsk}
              forceMount
            >
              <MessageCircleQuestion className="ui-icon-shift h-4 w-4" />
              <span>{t.searchPage.askAbout.replace("{query}", query)}</span>
            </CommandItem>
          </CommandGroup>
        )}

        {/* Navigation */}
        <CommandGroup heading={t.navigation.nav}>
          {navigationItems.map((item) => (
            <CommandItem
              className="ui-cmd-item"
              key={item.href}
              value={`${item.name} ${item.keywords.join(" ")}`}
              onSelect={() => handleNavigate(item.href)}
            >
              <item.icon className="ui-icon-shift h-4 w-4" />
              <span>{item.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        {/* Notebooks */}
        <CommandGroup heading={t.notebooks.title}>
          {notebooksLoading ? (
            <CommandItem disabled>
              <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
              <span>{t.common.loading}</span>
            </CommandItem>
          ) : notebooks && notebooks.length > 0 ? (
            notebooks.map((notebook) => (
              <CommandItem
                className="ui-cmd-item"
                key={notebook.id}
                value={`notebook ${notebook.name} ${notebook.description || ""}`}
                onSelect={() => handleNavigate(`/notebooks/${notebook.id}`)}
              >
                <Book className="ui-icon-shift h-4 w-4" />
                <span>{notebook.name}</span>
              </CommandItem>
            ))
          ) : null}
        </CommandGroup>

        {/* Create */}
        <CommandGroup heading={t.navigation.create}>
          {createItems.map((item) => (
            <CommandItem
              className="ui-cmd-item"
              key={item.action}
              value={`create ${item.name}`}
              onSelect={() => handleCreate(item.action)}
            >
              <Plus className="ui-icon-shift h-4 w-4" />
              <span>{item.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        {/* Theme */}
        <CommandGroup heading={t.navigation.theme}>
          {themeItems.map((item) => (
            <CommandItem
              className="ui-cmd-item"
              key={item.value}
              value={`theme ${item.name} ${item.keywords.join(" ")}`}
              onSelect={() => handleTheme(item.value)}
            >
              <item.icon className="ui-icon-shift h-4 w-4" />
              <span>{item.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        {/* Search/Ask - show at bottom when there IS a command match */}
        {query.trim() && hasCommandMatch && (
          <>
            <CommandSeparator />
            <CommandGroup heading={t.searchPage.orSearchKb} forceMount>
              <CommandItem
                className="ui-cmd-item"
                value={`__search__ ${query}`}
                onSelect={handleSearch}
                forceMount
              >
                <Search className="ui-icon-shift h-4 w-4" />
                <span>{t.searchPage.searchResultsFor.replace("{query}", query)}</span>
              </CommandItem>
              <CommandItem
                className="ui-cmd-item"
                value={`__ask__ ${query}`}
                onSelect={handleAsk}
                forceMount
              >
                <MessageCircleQuestion className="ui-icon-shift h-4 w-4" />
                <span>{t.searchPage.askAbout.replace("{query}", query)}</span>
              </CommandItem>
            </CommandGroup>
          </>
        )}
        <CommandEmpty>{t.searchPage.noResultsFor.replace("{query}", query)}</CommandEmpty>
      </CommandList>
    </CommandDialog>
  );
}
