# ClawHub Submission Pack

This file keeps the OpenClaw public-distribution truth in one place.

In plain language: the bundle install path is ready in this repository, and the ClawHub skill listing is now live at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | yes |
| `publicly discoverable listing live` | yes |
| `official marketplace listing live` | yes, on ClawHub |

## Official Surface Evidence

- OpenClaw's official plugin docs expose plugin install flows.
- OpenClaw's official community-plugin docs provide a public listing surface.
- OpenClaw's official bundle docs describe compatible Claude, Cursor, and Codex bundle layouts.

## Official Raw URLs

- OpenClaw plugins:
  - `https://docs.openclaw.ai/plugins`
- OpenClaw ClawHub:
  - `https://docs.openclaw.ai/tools/clawhub`
- OpenClaw writing plugins guide:
  - `https://docs.openclaw.ai/guide/extensions/writing-plugins/`
- OpenClaw custom skills guide:
  - `https://docs.openclaw.ai/guide/skills/custom-skills/`
- OpenClaw MCP CLI:
  - `https://docs.openclaw.ai/cli/mcp`

Use those official pages together with:

- [../../../docs/integrations/openclaw.md](../../../docs/integrations/openclaw.md)
- [README.md](README.md)
- [clawhub/notebooklab-mcp-outcome-workflows/SKILL.md](./clawhub/notebooklab-mcp-outcome-workflows/SKILL.md)
- `notebooklab-claude-bundle/README.md`
- `notebooklab-cursor-bundle/README.md`
- `notebooklab-codex-bundle/README.md`

## Repo-Owned Submission Materials

| Artifact | Purpose |
| --- | --- |
| `clawhub/notebooklab-mcp-outcome-workflows/SKILL.md` | canonical ClawHub publish target for the OpenClaw skill submission lane |
| `notebooklab-claude-bundle/` | primary OpenClaw-compatible bundle with commands, plugin marker, `.mcp.json`, and skill |
| `notebooklab-cursor-bundle/` | alternate Cursor-style bundle family |
| `notebooklab-codex-bundle/` | alternate Codex-style bundle family |
| `clawhub/notebooklab-mcp-outcome-workflows/` | canonical ClawHub skill publish root |
| `../../../docs/integrations/openclaw.md` | public-facing install and proof page |
| `../../../docs/mcp.md` | first-party MCP truth anchor |
| `../../../tests/ci/test_host_examples_contract.py` | bundle/index contract guard |
| `../../../tests/ci/test_host_surface_contract.py` | docs surface guard |
| `../../../tests/test_mcp_server.py` | skill and MCP boundary guard |

## Current Live Listing Boundary

The ClawHub skill page is already live:

- `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`

That means the earlier publish/auth step is no longer a blocker for this exact
skill lane. What still remains outside the repo is any later choice to expand
beyond this live ClawHub page into other OpenClaw bundle, plugin, or
marketplace surfaces.

## Official Command Card

The current ClawHub docs expose these publish-oriented commands:

```bash
clawhub skill publish <path>
clawhub package publish <source> --dry-run
```

The same docs also note that:

- ClawHub is a public discovery surface for skills and plugins
- a GitHub account must be at least one week old to publish
- authenticated OpenClaw / ClawHub access is still required for publish and sync flows
- `clawhub` is the separate CLI used for authenticated publish and sync flows

## Exact Unblock Pack

| Item | Current state | What is already done in repo | What still needs an external button |
| --- | --- | --- | --- |
| OpenClaw-compatible install package | ready | three compatible bundle families plus docs and proof loop | none |
| Listing metadata and proof | ready | this pack plus the bundle READMEs and host docs | none |
| Live ClawHub/community listing | live at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows` | repo-owned package and docs are already backed by a public page | broader OpenClaw bundle/plugin storefront work only if the maintainer wants more than the current live ClawHub page |

## Canonical Publish Target

Use the canonical ClawHub publish root when you need to trace or republish the
same live skill lane:

- `examples/hosts/openclaw/clawhub/notebooklab-mcp-outcome-workflows/`

This repository can now truthfully claim that the canonical ClawHub skill page
is already published. The safe remaining boundary is smaller: broader OpenClaw
bundle/plugin storefront work is still optional later work, not part of the
current live ClawHub receipt.

## Safe Current Wording

Safe now:

- public-ready OpenClaw-compatible bundles are available from this repository
- the repo includes a live ClawHub skill listing at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`
- the repo includes a canonical ClawHub skill publish target that matches the live page

Not safe now:

- official partnership or endorsement
- public skills catalog
