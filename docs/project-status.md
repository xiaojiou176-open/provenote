# Project Status

This page explains the current public status boundary for Provenote.

In plain language: Provenote already has a strong repo-documented local proof loop, public-ready starter packages for several hosts, and a clearer distribution matrix. That is still not the same thing as claiming a hosted product, official vendor endorsement, or an official listing that is already live.

## What Is Already Repo-Documented

The current repository already documents and proves these product layers:

- a first-entry path for long messy context:
  - source import
  - built-in `Chat Knowledgeization`
  - structured insight review
  - note / notebook research-thread / draft-adjacent continuation
- source import across text, files, audio, and web content
- auditable markdown as a first-class output lane
- notebook drafts and verified draft snapshots
- research threads as persisted notebook artifacts
- richer draft bundle export for handoff-oriented outcomes
- source-level claim and section repair surfaces
- first-party MCP compatibility for coding-agent hosts
- a first-party operator CLI for terminal-driven status checks, notebook outcome inspection, auditable markdown, and `research_thread -> draft -> verify/download` handoffs
- repo-backed public-ready starter bundles for Claude Code, Codex, Cursor, and OpenCode
- repo-backed public-ready OpenClaw-compatible bundle packages plus a ClawHub submission pack

If you want the file-and-route proof, start with [proof.md](proof.md).

## What Status To Assume Today

The safest current interpretation is:

- **repo-documented local proof loop**: yes
- **product shape visible in public docs and code**: yes
- **public-ready starter bundles for Claude Code / Codex / Cursor / OpenCode**: yes
- **public-ready OpenClaw-compatible bundle install path and submission pack**: yes
- **official vendor partnership or marketplace listing**: not claimed
- **official listing live for Claude Code / Codex / OpenClaw / MCP Registry**: not claimed
- **hosted one-click trial**: not claimed
- **public skills catalog or skills-ready product surface**: not claimed
- **automatic repo/package/CLI rename around a future domain**: not claimed

Think of it like a well-labeled workshop you can inspect and run locally today, not a hotel lobby promising every external storefront is already open.

If you want the package-readiness and listing matrix, use [distribution.md](distribution.md).
If you want the terminal-first operator surface instead of starting from MCP host setup, use [runbooks/operator-cli.md](runbooks/operator-cli.md).

## Claim Ladder

Use this ladder when you describe distribution status in public docs:

| Level | What it means | What it does not mean |
| --- | --- | --- |
| `repo-owned prep exists` | the repo contains setup pages, starter files, sample config, or proof notes | public-ready package, public listing, or official marketplace status |
| `public-ready package available` | a public visitor can follow public docs, copy a public starter bundle, and run the documented verify loop | official marketplace listing, official directory inclusion, or platform endorsement |
| `publicly discoverable listing live` | the package or server is already visible in a public registry, directory, or marketplace surface | official partnership, endorsement, or automatic support guarantees |
| `official marketplace listing live` | the official platform listing is publicly visible and live | anything stronger than the platform actually says |

The plain-language rule is simple: a public GitHub bundle can already be `public-ready package available`, but it does **not** become a live marketplace or directory listing until the external listing is actually published.

## Distribution Surface Matrix

| Surface | Official public surface exists? | Current repo-owned artifact | Current claim level | Listing live? | What still needs owner or platform action |
| --- | --- | --- | --- | --- | --- |
| Claude Code | yes, official Claude Code MCP docs exist and Anthropic now documents a public discovery surface plus marketplace submission forms | [integrations/claude-code.md](integrations/claude-code.md), [../examples/hosts/claude-code/provenote-outcome-bundle/README.md](../examples/hosts/claude-code/provenote-outcome-bundle/README.md), and [../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md) | `public-ready package available` | no | authenticated Anthropic submission, marketplace review, and any additional publisher-side materials Anthropic requires at submission time |
| OpenAI Codex | yes, official Codex MCP docs exist | [integrations/codex.md](integrations/codex.md), [../examples/hosts/codex/provenote-outcome-bundle/README.md](../examples/hosts/codex/provenote-outcome-bundle/README.md), and [../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md) | `public-ready package available` | no | wait for OpenAI to expose or document an official listing path before claiming more |
| OpenClaw / ClawHub | yes, OpenClaw plugin, bundle, and ClawHub docs exist | [integrations/openclaw.md](integrations/openclaw.md), [../examples/hosts/openclaw/README.md](../examples/hosts/openclaw/README.md), and [../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md) | `public-ready package available` | no | authenticated ClawHub submission under a valid account and namespace |
| Official MCP Registry | yes, the registry and publish path exist | [distribution.md](distribution.md), [../server.json](../server.json), [../examples/public-distribution/mcp-registry/README.md](../examples/public-distribution/mcp-registry/README.md), [mcp.md](mcp.md), and [../pyproject.toml](../pyproject.toml) | `repo-owned prep exists` | no | authenticated registry publish and registry-side approval |

## Ecosystem Truth Today

| Surface | Safe current reading | Not claimed | Strongest proof or boundary page |
| --- | --- | --- | --- |
| Claude Code / Codex / Cursor / OpenCode | compatibility through the first-party MCP server, with repo-backed public-ready starter bundles | official partnership, bundled integration, plugin-store or marketplace status | [mcp.md](mcp.md) plus the host pages under [integrations/](integrations/) |
| `provenote` CLI | a first-party terminal/operator surface for current outcome objects | a separate distributed product line | [runbooks/operator-cli.md](runbooks/operator-cli.md) |
| public skills surface | no tracked public product surface exists today | skills marketplace, public skills catalog, or host-specific skills program | this page, [faq.md](faq.md), and the absence of any tracked public skills page |
| OpenClaw | public-ready bundle artifacts plus a ClawHub submission pack exist in the repo | official ClawHub or community listing live | this page, [faq.md](faq.md), [integrations/openclaw.md](integrations/openclaw.md), and [../examples/hosts/openclaw/README.md](../examples/hosts/openclaw/README.md) |
| Official MCP Registry | the official registry and publish docs exist | a live Provenote registry entry | this page, [distribution.md](distribution.md), [../examples/public-distribution/mcp-registry/README.md](../examples/public-distribution/mcp-registry/README.md), and [mcp.md](mcp.md) |
| plugin / marketplace / directory presence | official host surfaces exist, but no Provenote official listing is live today | shipped listing-live truth | this page and the host pages' non-claim language |
| release / domain / trademark / partnership | owner or platform decision layer | finished repo-side proof | this page and [brand-domain.md](brand-domain.md) |

## Current External Window Snapshot

The current repo can already prepare the storefront materials without claiming the storefront is open.

| Surface | Fresh current state | What still needs owner or platform action |
| --- | --- | --- |
| GitHub repository description | already synced to the current public positioning | only change it if the public brand story changes again |
| GitHub homepage field | currently points to the GitHub Pages front door at `https://xiaojiou176-open.github.io/provenote/` | decide later whether the long-term homepage should stay on GitHub Pages, move to a custom docs site, or move to a custom domain |
| Release surface | no current GitHub release object is published or drafted; tag truth and release-object truth are intentionally separate | owner decides later whether to create and publish a release once the external-distribution window is acceptable |
| Claude Code / Codex starter bundles | public-ready package artifacts already exist in the repo | Claude Code now has an official marketplace/discovery surface, but live submission and review remain external; Codex official listing status remains separate and unclaimed |
| OpenClaw bundle family | public-ready bundle artifacts and a ClawHub submission pack already exist in the repo | live ClawHub/community submission still needs platform action |
| Official MCP Registry | official submission path exists | a supported public artifact plus publisher auth are still required before a listing can go live |
| custom domain / redirect | not claimed here | domain registration, DNS, and redirect setup remain external |
| trademark / naming clearance | not claimed here | owner or counsel must decide whether a stronger public naming move is safe |
| directory / marketplace / partnership surfaces | not claimed here | separate platform submission or agreement is required before any public claim changes |

## Strongest Current Evaluation Path

If you only want the shortest honest evaluation loop:

1. read [../README.md](../README.md)
2. follow [quickstart.md](quickstart.md)
3. inspect the public proof map in [proof.md](proof.md)
4. use [distribution.md](distribution.md) if you want the public package-vs-listing ladder
5. use [mcp.md](mcp.md) if you want to connect coding-agent hosts after that product path is clear
6. use [runbooks/operator-cli.md](runbooks/operator-cli.md) if you want a first-party terminal/operator surface for the same outcome objects

## Current Non-Claims

This page intentionally does **not** claim that Provenote is:

- a hosted SaaS by default
- officially endorsed by Anthropic, OpenAI, Cursor, OpenCode, or OpenClaw
- already listed in an official Claude Code, Codex, OpenClaw, or MCP Registry surface
- a public Skills catalog or separately distributed Skills product
- already promoted through a final brand/domain decision
- a multi-user collaboration platform with hosted review workflows

Some next steps are real, but they remain outside pure repo-side completion:

- intentionally establishing a release object after tag truth is set
- authenticated directory / registry / marketplace submissions
- domain registration or redirect setup for any future `.ai` landing
- trademark and naming clearance for a stronger external brand move

The repo also now keeps a reusable visual asset pool under `docs/assets/{hero,demo,proof,architecture,social}`. Promotion polish can still improve over time, but the asset pool no longer depends on a missing social-preview upload before it can be referenced honestly.
