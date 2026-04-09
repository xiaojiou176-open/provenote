# Publishable Public Artifact Prep

This file records the repo-owned work that would be needed to upgrade Provenote's live Official MCP Registry entry into a package-backed install surface later.

In plain language: the Official MCP Registry entry is already live, but the repo can still prepare package metadata, build commands, and release checklist so a future package-backed install path is only one human login plus one publish step.

## Current Goal

Keep the live registry entry truthful while preparing a later package-backed public artifact path without overclaiming that a public package is already published.

## Repo-Owned Prep That Is Already In Place

- package metadata lives in [../../../pyproject.toml](../../../pyproject.toml)
- first-party server identity lives in [../../../server.json](../../../server.json)
- registry-facing server identity lives in [server.json](server.json)
- first-party MCP docs live in [../../../docs/mcp.md](../../../docs/mcp.md)
- first-party MCP code and schemas live in:
  - [../../../packages/core/mcp/server.py](../../../packages/core/mcp/server.py)
  - [../../../packages/core/mcp/schemas.py](../../../packages/core/mcp/schemas.py)

## Build Commands

Use the repo-managed build path:

```bash
uv build
```

Expected outputs:

- `dist/provenote-<version>.tar.gz`
- `dist/provenote-<version>-py3-none-any.whl`

These are build artifacts only. They do **not** prove that a public package registry listing already exists.

## Publish-Ready Metadata Checklist

- package name remains `provenote`
- version matches the current repo release line
- project URLs point to the current public repo/docs surface
- README is the package long description source
- the repository still exposes the `provenote-mcp` script surface

## What Still Needs An External Button

1. log in to the target public package registry
2. publish the built package artifacts
3. log in with `mcp-publisher login github`
4. add the registry-facing `packages` entry only after the published artifact exists
5. run `mcp-publisher publish`

## Safe Current Wording

Safe now:

- the repo keeps package-backed public-artifact prep for a future Official MCP Registry upgrade
- the official MCP Registry entry is already live for `io.github.xiaojiou176-open/provenote-mcp`
- the package metadata and build path are prepared in-tree

Not safe now:

- a public package registry entry already exists
- the live registry entry guarantees a package-backed install path
