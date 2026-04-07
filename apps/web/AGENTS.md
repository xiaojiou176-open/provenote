# Frontend AGENTS.md

## Purpose

- Maintain the Next.js web application in `apps/web/`.
- Keep UI behavior, client API usage, and E2E coverage aligned.

## Stack
- Next.js 16 + React 19 + TypeScript
- TanStack Query + Zustand
- Tailwind CSS + Radix UI
- Vitest + Playwright

## Local map

- `apps/web/src/app/` - routes and page entrypoints
- `apps/web/src/components/` - UI and page components
- `apps/web/src/lib/api/` - backend client wrappers
- `apps/web/src/lib/hooks/` - query and mutation hooks
- `apps/web/e2e/` - browser tests

## Core commands
```bash
cd apps/web
npm run dev
npm run lint
npm test
npm run test:coverage
```

## Test entrypoints
```bash
cd apps/web
npm test
npm run test:e2e:install
npm run test:e2e -- --project=chromium
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `apps/web/`, then fall back to root guidance if needed.

Evidence token example: `apps/web/src/app/page.tsx:1`
command + matched result

## Notes

- Update i18n strings when user-visible copy changes.
- Update client types and API wrappers when backend fields change.
- Prefer stable selectors and no hard-coded sleeps in Playwright.
