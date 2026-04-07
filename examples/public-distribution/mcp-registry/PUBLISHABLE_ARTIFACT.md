# Publishable Public Artifact Prep

This file records the repo-owned work that must be true before a maintainer performs the final public package publish for the official MCP Registry lane.

In plain language: the registry still needs a real published install artifact, but the repo can already prepare the package metadata, build commands, and release checklist so the final publish is only one human login plus one publish step.

## Current Goal

Move Provenote from:

- `repo-owned prep exists`

to:

- build-verified public-artifact prep

without overclaiming that a public package is already published.

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

- the repo keeps publishable public-artifact prep for the official MCP Registry lane
- the package metadata and build path are prepared in-tree
- official registry publish still requires a real public package plus authenticated publish

Not safe now:

- a public package registry entry already exists
- Provenote is already listed in the official MCP Registry
