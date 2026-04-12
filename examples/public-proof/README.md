# Public Workspace Proof Pack

This folder is the canonical public workspace proof pack for Provenote's
`/sources -> source detail -> Auditable Markdown` journey.

In plain language: if you want to inspect the main product route without
pretending there is already a hosted trial or host-accepted live receipt, start
here.

## What This Pack Covers

- the `/sources` workbench as the sources-first starting point
- the `/sources/{id}` detail page as the next-step handoff surface
- Auditable Markdown as the first strict output lane inside source detail
- the narrow runnable local proof loop under [./auditable-markdown/README.md](./auditable-markdown/README.md)

## Route Contract

| Step | What to verify | Repo-owned proof surface |
| --- | --- | --- |
| `1. /sources` | The first doorway is a sources-first workbench, not a generic chat landing page. | [../../apps/web/src/app/(dashboard)/sources/page.tsx](../../apps/web/src/app/(dashboard)/sources/page.tsx) |
| `2. /sources/{id}` | Opening one source moves you into a detail page that explicitly says "verify the source first, then move into auditable output or chat." | [../../apps/web/src/app/(dashboard)/sources/[id]/page.tsx](../../apps/web/src/app/(dashboard)/sources/[id]/page.tsx) |
| `3. Auditable Markdown` | The source detail route keeps Auditable Markdown as a first-class next-step lane inside the page. | [../../apps/web/src/app/(dashboard)/sources/[id]/page.tsx](../../apps/web/src/app/(dashboard)/sources/[id]/page.tsx) and [../../docs/quickstart.md](../../docs/quickstart.md) |
| `4. Reproducible follow-through` | A repo-owned local script can create one source, run auditable markdown, download the markdown, and clean up the temporary source. | [./auditable-markdown/README.md](./auditable-markdown/README.md) |

## Fastest Honest Evaluation Order

1. Start at [../../README.md](../../README.md) for the product front door.
2. Use [../../docs/quickstart.md](../../docs/quickstart.md) for the shortest local first-run path.
3. Read this workspace proof pack to keep the `/sources -> source detail -> Auditable Markdown` route explicit.
4. Use the runnable [Auditable Markdown proof pack](./auditable-markdown/README.md) when you want the narrow local proof loop.
5. Finish with [../../docs/proof.md](../../docs/proof.md) if you want the wider public evidence map.

## Truth Boundary

- This pack is repo-authored workspace proof, not a hosted demo.
- It does **not** claim host marketplace acceptance, directory listing acceptance, or external operator verification.
- It explains the public route and points to the runnable local lane without pretending that the repo has off-repo receipts it does not own.
