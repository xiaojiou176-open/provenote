# ClawHub Submission Pack

This file keeps the OpenClaw public-distribution truth in one place.

In plain language: the bundle install path is ready in this repository, but an official ClawHub or community-plugin listing is **not** live yet.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | yes |
| `publicly discoverable listing live` | no |
| `official marketplace listing live` | no |

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
- [clawhub/provenote-mcp-outcome-workflows/SKILL.md](./clawhub/provenote-mcp-outcome-workflows/SKILL.md)
- `provenote-claude-bundle/README.md`
- `provenote-cursor-bundle/README.md`
- `provenote-codex-bundle/README.md`

## Repo-Owned Submission Materials

| Artifact | Purpose |
| --- | --- |
| `clawhub/provenote-mcp-outcome-workflows/SKILL.md` | canonical ClawHub publish target for the OpenClaw skill submission lane |
| `provenote-claude-bundle/` | primary OpenClaw-compatible bundle with commands, plugin marker, `.mcp.json`, and skill |
| `provenote-cursor-bundle/` | alternate Cursor-style bundle family |
| `provenote-codex-bundle/` | alternate Codex-style bundle family |
| `clawhub/provenote-mcp-outcome-workflows/` | canonical ClawHub skill publish root |
| `../../../docs/integrations/openclaw.md` | public-facing install and proof page |
| `../../../docs/mcp.md` | first-party MCP truth anchor |
| `../../../tests/ci/test_host_examples_contract.py` | bundle/index contract guard |
| `../../../tests/ci/test_host_surface_contract.py` | docs surface guard |
| `../../../tests/test_mcp_server.py` | skill and MCP boundary guard |

## What Still Blocks A Live Listing

An official ClawHub or community-plugin listing still needs an external platform step:

- authenticated OpenClaw / ClawHub access
- the operator tooling or web session used for submission
- a final owner decision on package name, listing target, and submit account

Those are not repository-code blockers.

## Official Command Card

The current ClawHub docs expose these publish-oriented commands:

```bash
clawhub skill publish <path>
clawhub package publish <source> --dry-run
```

The same docs also note that:

- ClawHub is a public discovery surface for skills and plugins
- a GitHub account must be at least one week old to publish
- `clawhub` is the separate CLI used for authenticated publish and sync flows

## Exact Unblock Pack

| Item | Current state | What is already done in repo | What still needs an external button |
| --- | --- | --- | --- |
| OpenClaw-compatible install package | ready | three compatible bundle families plus docs and proof loop | none |
| Listing metadata and proof | ready | this pack plus the bundle READMEs and host docs | none |
| Live ClawHub/community listing | not live | repo-owned package and docs are ready | authenticated submission in OpenClaw / ClawHub using the official docs above and the canonical publish root below |

## Canonical Publish Target

Use the canonical ClawHub publish root when the submit account is ready:

- `examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/`

This repository does **not** claim that Provenote has already been published. The safe truth is only that the canonical publish root is ready once the official OpenClaw / ClawHub tooling and account path are available.

## Safe Current Wording

Safe now:

- public-ready OpenClaw-compatible bundles are available from this repository
- the repo includes a submission-ready ClawHub pack
- the repo includes a canonical ClawHub skill publish target

Not safe now:

- official OpenClaw listing live
- official partnership or endorsement
- public skills catalog
