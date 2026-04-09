# MCP Registry Submission Pack

This folder keeps the repo-owned submission materials for the official MCP Registry lane.

In plain language: Provenote already ships the first-party `provenote-mcp` server, proof loops, and a registry submission-pack stub, but no official MCP Registry listing is claimed as live yet.

Treat this as a companion registry lane around the outcome-first workbench. It
exists after the main product path is already clear; it is not the first door
for understanding Provenote.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | no |
| `publicly discoverable listing live` | no |
| `official marketplace listing live` | no |

## Repo-Owned Submission Materials

- [server.json](server.json)
- [PUBLISHABLE_ARTIFACT.md](PUBLISHABLE_ARTIFACT.md)
- [../../../docs/mcp.md](../../../docs/mcp.md)
- [../../../pyproject.toml](../../../pyproject.toml)
- [../../../packages/core/mcp/server.py](../../../packages/core/mcp/server.py)
- [../../../packages/core/mcp/schemas.py](../../../packages/core/mcp/schemas.py)
- [../../../tests/test_mcp_server.py](../../../tests/test_mcp_server.py)

## Official Raw URLs

- MCP Registry homepage:
  - `https://registry.modelcontextprotocol.io/`
- MCP Registry quickstart:
  - `https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx`
- MCP Registry generic `server.json` reference:
  - `https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md`

## What Still Blocks A Live Registry Entry

- the official quickstart still assumes a real published package before registry publish
- the official registry requirements still enforce package-ownership verification for registry-backed artifacts
- authenticated registry publish access
- a registry-compatible public package or public remote-server artifact path and release flow
- the external publish step itself

Those are not repository-code blockers.

In the official quickstart, the blocking public-artifact step is explicit:

- publish the install artifact to a public package registry first
- add `mcpName` to the package metadata
- add a `packages` entry to `server.json`
- authenticate with `mcp-publisher login`
- publish with `mcp-publisher publish`

This repo currently stops before those steps because the public artifact itself is not yet published.

## Exact Unblock Pack

| Item | Current repo-side state | Minimum external action |
| --- | --- | --- |
| first-party MCP docs and server identity | ready in `docs/mcp.md`, `server.json`, and `examples/public-distribution/mcp-registry/server.json` | none |
| registry-facing metadata shell | ready | none |
| public artifact publish | not done | owner publishes the supported install artifact to a public registry first |
| registry auth | not done | owner runs `mcp-publisher login github` with a valid account |
| registry publish | not done | owner runs `mcp-publisher publish` after the public artifact exists |

This pack is intentionally one rung below a real listing:

- it records the candidate registry name and website URL
- it does **not** claim that a supported public package or public remote-server artifact is already published
