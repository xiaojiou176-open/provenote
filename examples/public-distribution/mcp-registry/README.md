# MCP Registry Submission Pack

This folder keeps the repo-owned submission materials for the official MCP Registry lane.

In plain language: Notebooklab already ships the first-party `notebooklab-mcp` server, proof loops, and a registry submission pack, and the Official MCP Registry now returns a live active entry for `io.github.xiaojiou176-open/notebooklab-mcp`.

Treat this as a companion registry lane around the outcome-first workbench. It
exists after the main product path is already clear; it is not the first door
for understanding Notebooklab.

## Current Claim Ladder

| Ladder step | Current status |
| --- | --- |
| `repo-owned prep exists` | yes |
| `public-ready package available` | no |
| `publicly discoverable listing live` | yes |
| `official marketplace listing live` | yes |

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

## Current Live Read-Back

- registry query returns `io.github.xiaojiou176-open/notebooklab-mcp`
- status is `active`
- published version is `1.8.5`

## What Still Remains A Later Upgrade

- a package-backed public install artifact is still a separate packaging improvement
- the `mcp-publisher` flow is still relevant if the maintainer wants to move from websiteUrl-based install guidance to a package-backed install surface
- host-specific directory and marketplace lanes still require their own external submission/read-back

For that later package-backed upgrade, the official quickstart still assumes a real published package before registry publish, and the official registry requirements still enforce package-ownership verification for registry-backed artifacts.

In exact terms, the official quickstart still assumes a real published package before registry publish.

The later upgrade path still looks like:

- publish the install artifact to a public package registry first
- add `mcpName` to the package metadata
- add a `packages` entry to `server.json`
- authenticate with `mcp-publisher login github`
- publish with `mcp-publisher publish`

## Exact Later-Upgrade Pack

| Item | Current repo-side state | Minimum external action |
| --- | --- | --- |
| first-party MCP docs and server identity | ready in `docs/mcp.md`, `server.json`, and `examples/public-distribution/mcp-registry/server.json` | none |
| live registry entry | already live | keep read-back attached when future docs change |
| package-backed public artifact | not done | owner publishes the supported install artifact to a public registry if a package-backed install surface is desired later |
| package-backed registry upgrade | not done | owner runs the future `mcp-publisher` flow only if the maintainer wants that richer install path later |

This pack now sits next to a real listing:

- it records the live registry identity and the repo-owned install docs that back it
- it does **not** claim that a supported public package or public remote-server artifact is already published
