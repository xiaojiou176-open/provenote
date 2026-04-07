# Frontend CLAUDE.md

## Purpose

Use this file when the change is mainly inside `apps/web/`.

## Stack

- Next.js 16 (App Router)
- React 19 + TypeScript
- TanStack Query / Zustand
- Vitest / Playwright

## Local map

- `apps/web/src/app/` - routes and page entrypoints
- `apps/web/src/components/` - UI and page components
- `apps/web/src/lib/` - client API, hooks, stores, and i18n
- `apps/web/e2e/` - browser tests

## Core commands
```bash
cd apps/web
npm run dev
npm run lint
npm run build
```

## Test entrypoints
```bash
cd apps/web
npm test
npm run test:coverage
npm run test:e2e -- --project=chromium
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `apps/web/`, then fall back to root guidance if needed.

Evidence token example: `apps/web/src/lib/repo-links.ts:1`
command + matched result

## Notes

- Reuse existing shared UI and hooks before creating new patterns.
- Keep user-visible text aligned with i18n resources.
- Prefer deterministic selectors and stable ready checks in Playwright.
- Keep notebook draft-seed guidance inside the notebook lane. If you touch research-thread recommendation UI, preserve the boundary that draft creation still happens from the thread panel rather than source-level dialogs.
