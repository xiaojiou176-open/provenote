# Documentation

Provenote now uses a layered public docs entrypoint.

The idea is simple: do not make first-time visitors walk through a governance maze just to decide whether the product is worth their time.

In plain language: the front door should answer "what is this, why should I care, and where do I start" before it asks you to think about bundles, listings, or maintenance pages.

The shortest honest order is:

1. `README`
2. `quickstart`
3. `proof`

Everything else is a second-ring surface after that first pass.

## Start With The Primary Door

| If you are trying to... | Start here | Why |
| --- | --- | --- |
| Start from messy long context as the first entry | [use-cases/long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md) | Best-fit first path for long chats, forum threads, messy notes, and copied web context before you choose note, research-thread, or draft-lane continuation |
| Understand the value in under 3 minutes | [../README.md](../README.md) | Product story, result path, star reasons, public proof links |
| Reach a first visible result fast | [quickstart.md](quickstart.md) | Short path from local setup to auditable markdown |
| Verify the product is real | [proof.md](proof.md) | Public evidence map for product surface, workflow proof, and trust proof |
| Understand the current scope and readiness boundary | [project-status.md](project-status.md) | Honest status page for repo-documented proof, non-claims, and external decision boundaries |
| Connect it to coding agents after the product path is clear | [mcp.md](mcp.md) | MCP is the carry-forward integration surface, not the brand center |

## Treat These As Second-Layer Surfaces

These surfaces matter, but they should support the first impression instead of becoming the first impression.

| Surface | Open this when... | Why it is second-layer |
| --- | --- | --- |
| [distribution.md](distribution.md) | you need package-vs-listing truth | it is a claim ladder page, not the core product story |
| [promotion-kit.md](promotion-kit.md) | you need screenshots, pitch lines, or submission assets | it packages the outer ring instead of defining the product center |
| [mcp.md](mcp.md) | you already know you want coding-agent carry-forward | MCP is the integration surface, not the brand center |
| [../examples/hosts/README.md](../examples/hosts/README.md) | you want checked-in install artifacts | starter bundles are install surfaces, not the first doorway |
| [runbooks/operator-cli.md](runbooks/operator-cli.md) | you want the terminal/operator path | operator workflows are narrower than the default workbench story |

## Go Deeper By Goal

### Evaluate the product

- [../README.md](../README.md)
- [project-status.md](project-status.md)
- [proof.md](proof.md)
- [faq.md](faq.md)
- [quickstart.md](quickstart.md)

### Install and run it

- [quickstart.md](quickstart.md)
- [installation.md](installation.md)
- [configuration.md](configuration.md)

### Use it with coding agents

- [mcp.md](mcp.md)
- [../examples/hosts/README.md](../examples/hosts/README.md)
- [integrations/claude-code.md](integrations/claude-code.md)
- [integrations/codex.md](integrations/codex.md)
- [integrations/cursor.md](integrations/cursor.md)
- [integrations/openclaw.md](integrations/openclaw.md) for the OpenClaw public-ready bundle path and submission pack
- [integrations/opencode.md](integrations/opencode.md) for the tightest repo-backed setup-and-verify path

### Understand real use cases

- [use-cases/ai-notes-with-receipts.md](use-cases/ai-notes-with-receipts.md)
- [use-cases/long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md)
- [use-cases/source-grounded-ai-research.md](use-cases/source-grounded-ai-research.md)
- [use-cases/source-grounded-drafts.md](use-cases/source-grounded-drafts.md)
- [use-cases/mcp-research-context-for-coding-agents.md](use-cases/mcp-research-context-for-coding-agents.md)
- [use-cases/source-to-verified-draft.md](use-cases/source-to-verified-draft.md)

### Understand naming and domain boundaries

- [brand-domain.md](brand-domain.md)
- [faq.md](faq.md)

### Understand the system

- [architecture.md](architecture.md)
- [../services/api/main.py](../services/api/main.py)
- [../apps/web/src/components/layout/AppSidebar.tsx](../apps/web/src/components/layout/AppSidebar.tsx)

### Contribute and maintain

- [../CONTRIBUTING.md](../CONTRIBUTING.md)
- [development.md](development.md)
- [runbooks/space-governance.md](runbooks/space-governance.md)
- [../SUPPORT.md](../SUPPORT.md)
- [../SECURITY.md](../SECURITY.md)

## Keep In Mind

- Product-first docs live up front.
- If the starting problem is messy long context, treat that path as the front door, not a side use case.
- Governance and maintenance docs still matter, but they should support the decision, not block the first impression.
- If a doc disagrees with current code or tracked workflows, trust current code and tracked CI behavior first.
