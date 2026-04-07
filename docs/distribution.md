# Distribution Status

This page explains Provenote's current public distribution status without blurring package readiness, public discoverability, and official listing status.

In plain language: a public GitHub repo can already ship real starter bundles and real proof loops before any official marketplace or registry listing goes live.

## Claim Ladder

| Level | What it means | What it does not mean |
| --- | --- | --- |
| `repo-owned prep exists` | the repo contains setup pages, starter files, sample config, or proof notes | public-ready package, public listing, or official marketplace status |
| `public-ready package available` | a public visitor can follow public docs, copy a public starter bundle, and run the documented verify loop | official marketplace listing, official directory inclusion, or platform endorsement |
| `publicly discoverable listing live` | the package or server is already visible in a public registry, directory, or marketplace surface | official partnership, endorsement, or automatic support guarantees |
| `official marketplace listing live` | the official platform listing is publicly visible and live | anything stronger than the platform actually says |

## Distribution Surface Matrix

| Surface | Official public surface exists? | Public submission path verified? | Current repo-owned artifact | Current claim level | Official listing live? | Remaining blocker |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code | yes, official Claude Code MCP docs exist and Anthropic documents a discovery surface plus official marketplace submission flows | yes, official marketplace/discovery docs and submission forms are documented | [../examples/hosts/claude-code/provenote-outcome-bundle/README.md](../examples/hosts/claude-code/provenote-outcome-bundle/README.md), [../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md), and [integrations/claude-code.md](integrations/claude-code.md) | `public-ready package available` | no | authenticated Anthropic marketplace submission plus directory review and any extra publisher-side materials Anthropic requires |
| OpenAI Codex | yes, official Codex MCP docs exist | no verified official listing flow was confirmed in this turn | [../examples/hosts/codex/provenote-outcome-bundle/README.md](../examples/hosts/codex/provenote-outcome-bundle/README.md), [../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md), and [integrations/codex.md](integrations/codex.md) | `public-ready package available` | no | wait for OpenAI to expose or document an official listing path before claiming more |
| OpenClaw / ClawHub | yes | yes | [../examples/hosts/openclaw/README.md](../examples/hosts/openclaw/README.md), [../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md), [../examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md](../examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md), and [integrations/openclaw.md](integrations/openclaw.md) | `public-ready package available` | no | authenticated ClawHub publish under a valid account and namespace |
| Official MCP Registry | yes | yes | [../examples/public-distribution/mcp-registry/README.md](../examples/public-distribution/mcp-registry/README.md), [../examples/public-distribution/mcp-registry/PUBLISHABLE_ARTIFACT.md](../examples/public-distribution/mcp-registry/PUBLISHABLE_ARTIFACT.md), [../examples/public-distribution/mcp-registry/server.json](../examples/public-distribution/mcp-registry/server.json), [mcp.md](mcp.md), and [../pyproject.toml](../pyproject.toml) | `repo-owned prep exists` | no | authenticated registry publish plus a supported public artifact path |

## What Is Already Public-Ready

### Claude Code

- public setup page: [integrations/claude-code.md](integrations/claude-code.md)
- public starter bundle: [../examples/hosts/claude-code/provenote-outcome-bundle/README.md](../examples/hosts/claude-code/provenote-outcome-bundle/README.md)
- public submission pack: [../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md)
- public verify loop:
  - confirm `provenote-mcp`
  - register the bundle or `.mcp.json`
  - list drafts / research threads / auditable runs
  - then do one narrow write-oriented workflow

### OpenAI Codex

- public setup page: [integrations/codex.md](integrations/codex.md)
- public starter bundle: [../examples/hosts/codex/provenote-outcome-bundle/README.md](../examples/hosts/codex/provenote-outcome-bundle/README.md)
- public submission pack: [../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md)
- public verify loop:
  - confirm `provenote-mcp`
  - register the bundle or `.mcp.json`
  - list drafts / research threads / auditable runs
  - then verify or download one concrete outcome

### OpenClaw

- public setup page: [integrations/openclaw.md](integrations/openclaw.md)
- public bundle family: [../examples/hosts/openclaw/README.md](../examples/hosts/openclaw/README.md)
- public submission pack: [../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md)
- canonical publish root: [../examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md](../examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md)
- public verify loop:
  - install one checked-in OpenClaw-compatible bundle from the public repo
  - inspect it through OpenClaw's plugin commands
  - keep the first action read-first
  - only then run one narrow outcome mutation

## Why MCP Registry Is Still One Rung Lower

The official MCP Registry already exists and its docs include a publish quickstart plus a [`server.json`](../server.json) reference that supports custom installation paths via `websiteUrl`.

The current repo now keeps the canonical submission metadata in [../examples/public-distribution/mcp-registry/server.json](../examples/public-distribution/mcp-registry/server.json) and mirrors the same registry-facing identity in [`server.json`](../server.json), both pointing at the first-party install docs in [mcp.md](mcp.md).

The current repo still does **not** prove a supported public artifact has already been published through the registry's accepted install paths. The official quickstart still assumes a real published package before `mcp-publisher publish`, and the official registry requirements still enforce package-ownership verification for registry-backed artifacts. That means the honest current level is:

- `provenote-mcp` exists
- the repo has public docs, proof loops, registry submission-pack metadata, and a build-verified public-artifact checklist
- registry-specific publication is still blocked by external publish/auth work plus the absence of a supported public package or public remote-server artifact from this repo

## Promotion Asset Pack

The repo now has a reusable promotion foundation, but not a complete promotion kit yet.

Current tracked assets include:

- [../docs/assets/hero/provenote-hero.png](../docs/assets/hero/provenote-hero.png)
- [../docs/assets/demo/provenote-quick-result-overview.png](../docs/assets/demo/provenote-quick-result-overview.png)
- [../docs/assets/proof/provenote-proof-stack.png](../docs/assets/proof/provenote-proof-stack.png)
- [../docs/assets/architecture/provenote-architecture.png](../docs/assets/architecture/provenote-architecture.png)
- [../docs/assets/social/provenote-social-preview.png](../docs/assets/social/provenote-social-preview.png)

Those assets already support README framing, proof storytelling, and social-preview upload.

They still do **not** add up to a full promotion pack by themselves. A stronger promotion-ready state also needs:

- one reusable short pitch set
- platform-specific submission copy
- a short demo or promo script
- one inventory page for where each public-facing asset belongs

Use [promotion-kit.md](promotion-kit.md) for the tracked copy starters, asset inventory, and short demo storyboard.

## Official References

- [Claude Code MCP docs](https://code.claude.com/docs/en/mcp)
- [Claude Code discover plugins](https://code.claude.com/docs/en/discover-plugins)
- [Claude Code create plugins and marketplace submission](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-official-marketplace)
- [Anthropic Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)
- [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
- [OpenAI Codex MCP guide](https://developers.openai.com/codex/mcp/)
- [OpenAI Codex plugins overview](https://developers.openai.com/codex/plugins)
- [OpenAI Codex build plugins](https://developers.openai.com/codex/plugins/build)
- [OpenClaw Plugins](https://docs.openclaw.ai/plugins)
- [OpenClaw ClawHub](https://docs.openclaw.ai/clawhub)
- [MCP Registry homepage](https://registry.modelcontextprotocol.io/)
- [MCP Registry quickstart](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx)
- [MCP Registry server.json reference](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md)
- [MCP Registry official requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md)

## Current Non-Claims

This page does **not** claim:

- an official Claude Code listing is live
- an official Codex plugin listing is live
- a live official OpenClaw / ClawHub listing for Provenote
- a live MCP Registry entry for Provenote
- any vendor partnership or endorsement
