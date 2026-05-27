# Notebooklab OpenCode Starter Bundle

This is a tracked public-ready starter bundle for OpenCode MCP usage.

It exists to make Notebooklab easier to wire into OpenCode without pretending there is already a public plugin, marketplace package, bundled OpenCode distribution, or official affiliation surface.

## What it contains

- `opencode.json`
- `.mcp.json`
- `skills/notebooklab-mcp-outcome-workflows/SKILL.md`

## What it is for

- public-ready OpenCode starter package distribution through this repository
- read-first Notebooklab MCP workflows
- notebook draft / research-thread / auditable-run starter actions

## How to use it

1. Confirm `notebooklab-mcp` is available in the environment that launches OpenCode.
2. Start from `opencode.json` when adding the local MCP server to your OpenCode config.
3. Use `.mcp.json` as the repo-owned proof that the bundle still targets the same `notebooklab-mcp` entrypoint as the other starter bundles.
4. Start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
5. Only after that move to a narrow write-oriented action.

## Boundary

- public-ready package available from this repository
- not a public OpenCode plugin claim
- not a marketplace or directory listing
- not a bundled OpenCode integration or affiliation claim
