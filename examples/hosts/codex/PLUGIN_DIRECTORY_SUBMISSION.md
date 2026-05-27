# Codex Plugin Directory Submission Pack

This file keeps the Codex public-distribution truth in one place.

In plain language: the Codex plugin package is public-ready in this repository, but no official Codex plugin listing is claimed as live yet.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | yes |
| `publicly discoverable listing live` | no |
| `official marketplace listing live` | no |

## Official Surface Evidence

- OpenAI's Codex docs document MCP server setup and configuration.
- This turn did **not** verify a live official Codex plugin or directory submission flow in the current public docs.
- The strongest current public truth therefore stays at the repo-owned package layer.

## Official Raw URLs

- Codex overview:
  - `https://developers.openai.com/codex/`
- Codex MCP guide:
  - `https://developers.openai.com/codex/mcp/`
- Codex plugins overview:
  - `https://developers.openai.com/codex/plugins`
- Public submission URL:
  - no self-serve public submission URL was verified from the current official docs in this turn

Use those official pages together with:

- [notebooklab-outcome-bundle/README.md](./notebooklab-outcome-bundle/README.md)
- [../../../docs/integrations/codex.md](../../../docs/integrations/codex.md)
- [../../../docs/mcp.md](../../../docs/mcp.md)
- [../../../tests/ci/test_host_examples_contract.py](../../../tests/ci/test_host_examples_contract.py)
- [../../../tests/test_mcp_server.py](../../../tests/test_mcp_server.py)

## Repo-Owned Submission Materials

| Artifact | Purpose |
| --- | --- |
| `notebooklab-outcome-bundle/.codex-plugin/plugin.json` | plugin-grade bundle manifest |
| `notebooklab-outcome-bundle/.mcp.json` | bundle-local MCP wiring to `notebooklab-mcp` |
| `notebooklab-outcome-bundle/skills/notebooklab-mcp-outcome-workflows/SKILL.md` | bundle-local workflow skill |
| `notebooklab-outcome-bundle/README.md` | public-ready package install loop |
| `../../../docs/integrations/codex.md` | official-surface-facing compatibility and proof page |

## What Still Blocks An Official Directory Entry

An official Codex directory entry remains outside repo control because:

- this turn did not verify a self-serve public listing path in the official Codex docs
- any future official listing still depends on OpenAI exposing or granting that path

Those are not repository-code blockers.

## Exact Unblock Pack

| Item | Current repo-side state | Minimum external action |
| --- | --- | --- |
| starter bundle and proof loop | ready in `examples/hosts/codex/notebooklab-outcome-bundle/` | none |
| plugin-directory submission materials | ready in this file plus `docs/integrations/codex.md` | none |
| official Codex directory entry | no self-serve public listing flow was verified in the official docs above | owner waits for OpenAI to expose or grant an official submission path, then submits the package through that path |

## Safe Current Wording

Safe now:

- public-ready Codex plugin package available from this repository
- Notebooklab works with OpenAI Codex via MCP
- repo-owned plugin-directory submission material is ready

Not safe now:

- official Codex plugin listing live
- official OpenAI integration or endorsement
- marketplace-ready Codex app live in the official directory
