# Anthropic Directory Submission Pack

This file keeps the Claude Code public-distribution truth in one place.

In plain language: the Claude Code install path is public-ready in this repository, but no Anthropic directory listing is claimed as live yet.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | yes |
| `publicly discoverable listing live` | no |
| `official marketplace listing live` | no |

## Official Surface Evidence

- Anthropic's Claude Code docs document MCP as the extension path for Claude Code.
- Anthropic's Software Directory terms explicitly cover submitted MCP servers, Skill folders, plugins, and apps.
- Anthropic's Software Directory policy states that Anthropic reviews submissions for safety, security, and compatibility.
- Anthropic's Claude Code docs now also document plugin discovery plus official marketplace submission forms.

## Official Raw URLs

- Claude Code MCP docs:
  - `https://code.claude.com/docs/en/mcp`
- Anthropic Software Directory terms:
  - `https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms`
- Anthropic Software Directory policy:
  - `https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy`
- Plugin discovery surface:
  - `https://code.claude.com/docs/en/discover-plugins`
- Marketplace submission docs:
  - `https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-official-marketplace`

Use those official pages together with:

- [provenote-outcome-bundle/README.md](./provenote-outcome-bundle/README.md)
- [../../../docs/integrations/claude-code.md](../../../docs/integrations/claude-code.md)
- [../../../docs/mcp.md](../../../docs/mcp.md)
- [../../../tests/ci/test_host_examples_contract.py](../../../tests/ci/test_host_examples_contract.py)
- [../../../tests/test_mcp_server.py](../../../tests/test_mcp_server.py)

## Repo-Owned Submission Materials

| Artifact | Purpose |
| --- | --- |
| `provenote-outcome-bundle/.claude-plugin/plugin.json` | starter package identity plus marketplace-facing bundle metadata for Claude Code installs |
| `provenote-outcome-bundle/.mcp.json` | bundle-local MCP wiring to `provenote-mcp` |
| `provenote-outcome-bundle/commands/provenote-mcp-outcome-workflows.md` | read-first command surface |
| `provenote-outcome-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md` | bundle-local workflow skill |
| `provenote-outcome-bundle/README.md` | public-ready package install loop |
| `../../../docs/integrations/claude-code.md` | official-surface-facing compatibility and proof page |

## What Still Blocks A Live Directory Listing

Anthropic's marketplace/directory step still keeps the final listing outside repo-only control:

- authenticated Anthropic marketplace or directory submission access
- marketplace or directory review and acceptance
- any additional publisher-side package, policy, or review materials Anthropic requires at submission time

Those are not repository-code blockers.

## Exact Unblock Pack

| Item | Current repo-side state | Minimum external action |
| --- | --- | --- |
| starter bundle and proof loop | ready in `examples/hosts/claude-code/provenote-outcome-bundle/` | none |
| directory submission materials | ready in this file plus `docs/integrations/claude-code.md` | none |
| Anthropic marketplace/directory submission entry | official docs now expose discovery and submission docs, but authenticated final submit remains external | owner opens the official submission surface above and completes the authenticated submission |
| additional publisher-side requirements | not repo-side | owner supplies any extra package, policy, or review materials Anthropic requires at submission time |

## Safe Current Wording

Safe now:

- public-ready Claude Code starter bundle available from this repository
- Provenote works with Claude Code via MCP
- repo-owned marketplace/directory submission material is ready

Not safe now:

- Anthropic directory listing live
- Anthropic marketplace listing live
- official Anthropic partnership or endorsement
- native Anthropic-owned plugin surface live
