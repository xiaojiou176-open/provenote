# Public Proof

This page exists to make Notebooklab easier to evaluate in public.

In plain language: marketing claims should point to inspectable surfaces. If a promise cannot be traced to a page, file, route, or workflow, treat it as incomplete.

## Proof Map

![Notebooklab public proof stack showing product proof, workflow proof, trust proof, and growth proof](./assets/proof/notebooklab-proof-stack.png)

## Fastest Public Proof Path

If you only want one short evaluation loop, use this sequence:

1. read the [README front door](../README.md)
2. scan [project-status.md](project-status.md) so the scope boundary is clear
3. review the repo-authored [quick-result overview](./assets/demo/notebooklab-quick-result-overview.png)
4. follow the [quickstart](quickstart.md)
5. inspect the UI and API surfaces linked below

This is the shortest **repo-documented local proof loop** today. It is not a hosted one-click demo claim.

## Product Proof In One Minute

If you only want the shortest product-level answer before reading file-level
anchors, keep these four points:

- Notebooklab already ships a path from messy long context to structured insight.
- Auditable Markdown is the shortest repo-backed inspectable output lane.
- Notes, research threads, and drafts are continuation lanes after that first
  result exists.
- MCP, host bundles, and distribution pages are real, but they stay second ring
  around the product path.

## Proof Routes By Audience

| If you want to check... | Start here | Then inspect |
| --- | --- | --- |
| whether Notebooklab fits messy long context at all | [../README.md](../README.md) and [use-cases/long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md) | the transformation and continuation anchors in the Product Proof table below |
| whether the research and draft ladders are real | [use-cases/source-grounded-ai-research.md](use-cases/source-grounded-ai-research.md) | [../apps/web/src/components/notebooks/ResearchThreadsPanel.tsx](../apps/web/src/components/notebooks/ResearchThreadsPanel.tsx), [../apps/web/src/components/notebooks/NotebookDraftPanel.tsx](../apps/web/src/components/notebooks/NotebookDraftPanel.tsx), and [../services/api/routers/drafts.py](../services/api/routers/drafts.py) |
| whether the coding-agent story is repo-backed | [mcp.md](mcp.md) | [../packages/core/mcp/server.py](../packages/core/mcp/server.py), [../packages/core/mcp/schemas.py](../packages/core/mcp/schemas.py), and the host pages under [integrations/](integrations/) |
| whether the terminal/operator story is real | [runbooks/operator-cli.md](runbooks/operator-cli.md) | [../pyproject.toml](../pyproject.toml), [../packages/core/operator/cli.py](../packages/core/operator/cli.py), and [../tests/test_operator_cli.py](../tests/test_operator_cli.py) |
| whether the public release/distribution story is already open | [project-status.md](project-status.md) and [distribution.md](distribution.md) | [../CHANGELOG.md](../CHANGELOG.md) and [GitHub Releases](https://github.com/xiaojiou176-open/notebooklab/releases), keeping draft-vs-published status separate |

## Product Proof

| Claim | Public proof surface |
| --- | --- |
| Long messy context already has a repo-backed first-entry path | [use-cases/long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md), [../README.md](../README.md), and [../apps/web/src/app/(dashboard)/transformations/components/LongContextTransformationStarter.tsx](../apps/web/src/app/(dashboard)/transformations/components/LongContextTransformationStarter.tsx) |
| Notebooklab is a full workbench, not a single chat page | [../apps/web/src/components/layout/AppSidebar.tsx](../apps/web/src/components/layout/AppSidebar.tsx) |
| Auditable markdown is a first-class output lane | [../apps/web/src/components/source/AuditableMarkdownPanel.tsx](../apps/web/src/components/source/AuditableMarkdownPanel.tsx) and [../services/api/routers/auditable_runs.py](../services/api/routers/auditable_runs.py) |
| Notebook drafts are a first-class notebook outcome lane | [../apps/web/src/components/notebooks/NotebookDraftPanel.tsx](../apps/web/src/components/notebooks/NotebookDraftPanel.tsx) and [../services/api/routers/drafts.py](../services/api/routers/drafts.py) |
| Notebook outcomes can be handed off as a richer export bundle, not only plain markdown | [../services/api/routers/drafts.py](../services/api/routers/drafts.py) and [../apps/web/src/lib/api/drafts.ts](../apps/web/src/lib/api/drafts.ts) |
| Research threads are persisted notebook artifacts, not only transient chats | [../apps/web/src/components/notebooks/ResearchThreadsPanel.tsx](../apps/web/src/components/notebooks/ResearchThreadsPanel.tsx) and [../services/api/routers/research_threads.py](../services/api/routers/research_threads.py) |
| Source QA and claim-level repair are inspectable in the source detail surface | [../apps/web/src/components/source/AuditableClaimReviewWorkspace.tsx](../apps/web/src/components/source/AuditableClaimReviewWorkspace.tsx), [../apps/web/src/components/source/SourceProcessingReportPanel.tsx](../apps/web/src/components/source/SourceProcessingReportPanel.tsx), and [../services/api/routers/auditable_runs.py](../services/api/routers/auditable_runs.py) |
| Notebooklab exposes outcome-first MCP tools for coding-agent hosts | [../packages/core/mcp/server.py](../packages/core/mcp/server.py), [mcp.md](mcp.md), and the host-specific integration pages under [integrations/](integrations/) |
| Notebooklab exposes a first-party local operator CLI for the same outcome lanes | [../pyproject.toml](../pyproject.toml), [../packages/core/operator/cli.py](../packages/core/operator/cli.py), [runbooks/operator-cli.md](runbooks/operator-cli.md), and [../tests/test_operator_cli.py](../tests/test_operator_cli.py) |
| The OpenCode compatibility claim includes a repo-documented self-verify loop, not only a host name in a list | [integrations/opencode.md](integrations/opencode.md), [../pyproject.toml](../pyproject.toml), [../packages/core/mcp/server.py](../packages/core/mcp/server.py), [../packages/core/mcp/schemas.py](../packages/core/mcp/schemas.py), and [../tests/test_mcp_server.py](../tests/test_mcp_server.py) |
| The repo has broad product APIs behind the UI | [../services/api/main.py](../services/api/main.py) |
| The product shape is documented at the repo level | [architecture.md](architecture.md) |

## Result-Shape Proof

The repo now also exposes a sanitized result shape in [../README.md](../README.md). That sample is intentionally described as a sanitized shape, not a copied user artifact, so the public proof story stays honest while still showing what the lane is for.

If you want the shortest scope-and-readiness summary before reading deeper proof, start with [project-status.md](project-status.md).

For a fixed, reproducible local proof loop, use [../examples/public-proof/auditable-markdown/README.md](../examples/public-proof/auditable-markdown/README.md).

## Workflow Proof

| What to inspect | Why it matters |
| --- | --- |
| [../CHANGELOG.md](../CHANGELOG.md) | Shows what changed and gives the project a public memory instead of forcing readers to infer momentum |
| [GitHub Releases](https://github.com/xiaojiou176-open/notebooklab/releases) | Turns version history into a user-facing subscription and discovery surface |
| [../.github/workflows/test.yml](../.github/workflows/test.yml) | Shows that verification is part of the public repo contract |
| [../.github/workflows/uiux-gemini-gate.yml](../.github/workflows/uiux-gemini-gate.yml) | Shows that the repo keeps a trusted maintainer witness lane for UI artifact review outside the default required path |

## Compatibility Proof

The current OpenCode page is meant to behave like a small inspection loop, not a marketing badge:

1. start from [mcp.md](mcp.md)
2. open [integrations/opencode.md](integrations/opencode.md)
3. confirm `notebooklab-mcp` in [../pyproject.toml](../pyproject.toml)
4. inspect the outcome-first tool families in [../packages/core/mcp/server.py](../packages/core/mcp/server.py)
5. inspect the typed schemas in [../packages/core/mcp/schemas.py](../packages/core/mcp/schemas.py)

That is why the host wording stays at compatibility through MCP. The proof story is repo-owned setup plus inspectable tool surfaces, not partnership language.

## Ecosystem Boundary Proof

| Boundary | What public proof supports |
| --- | --- |
| Host pages stay in the compatibility bucket | [mcp.md](mcp.md) plus the integration pages all point back to repo-owned entrypoints and official host docs instead of partnership language |
| The CLI is real but narrow | [runbooks/operator-cli.md](runbooks/operator-cli.md), [../packages/core/operator/cli.py](../packages/core/operator/cli.py), and [../tests/test_operator_cli.py](../tests/test_operator_cli.py) |
| OpenClaw-compatible bundles are public repo artifacts but no external listing is live | [distribution.md](distribution.md), [project-status.md](project-status.md), [faq.md](faq.md), [integrations/openclaw.md](integrations/openclaw.md), and [../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md) keep the package-vs-listing boundary explicit |
| public skills / plugin / marketplace surfaces are not shipped repo truth | [distribution.md](distribution.md), [project-status.md](project-status.md), [faq.md](faq.md), [mcp.md](mcp.md), and [integrations/opencode.md](integrations/opencode.md) all keep those ideas in the non-claim or deferred bucket |

## Trust Proof

| Trust layer | Public proof surface |
| --- | --- |
| License | [../LICENSE](../LICENSE) |
| Security reporting path | [../SECURITY.md](../SECURITY.md) |
| Support boundary | [../SUPPORT.md](../SUPPORT.md) |
| Contribution and review flow | [../CONTRIBUTING.md](../CONTRIBUTING.md) and [../CODEOWNERS](../CODEOWNERS) |
| Stewardship and fork provenance | [../MAINTAINERS.md](../MAINTAINERS.md) and [../NOTICE.md](../NOTICE.md) |

## Growth Proof

The public growth story for Notebooklab should not depend on people reading test directories or private planning notes.

The visible proof layers are meant to live in:

- the README front door
- this proof page
- GitHub Releases
- GitHub Discussions
- issue and PR templates
- changelog and public health files

## What This Page Does Not Claim

This page is intentionally honest about boundaries.

It does **not** claim that Notebooklab is:

- the upstream project's canonical homepage
- a multi-provider runtime by default
- a hosted SaaS product with off-repo support channels

Those boundaries still matter. They just belong in the evidence layer, not in the first headline a new visitor sees.

It also does **not** claim that a visible release page automatically means the latest release-event build or asset set is healthy.

It also does **not** claim that Claude Code, OpenAI Codex, Cursor, or OpenCode officially endorse Notebooklab. Current integration pages document compatibility through MCP, not partnerships or marketplace status.
