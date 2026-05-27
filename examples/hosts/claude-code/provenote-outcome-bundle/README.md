# Notebooklab Claude Code Starter Bundle

This is a tracked public-ready starter bundle for Claude Code-style MCP usage.

It exists to make Notebooklab easier to wire into Claude Code from a public Git-backed package path without pretending there is already an official directory listing, public skills catalog, or Anthropic-owned plugin surface.

## What it contains

- `.claude-plugin/plugin.json`
- `.mcp.json`
- `claude-code.project.example.json`
- `commands/notebooklab-mcp-outcome-workflows.md`
- `skills/notebooklab-mcp-outcome-workflows/SKILL.md`

## What it is for

- public-ready Claude Code starter package distribution through this repository
- read-first Notebooklab MCP workflows
- notebook draft / research-thread / auditable-run starter actions

## How to use it

1. Copy this bundle into a workspace or keep it as a checked-in starter directory that Claude Code operators can reuse.
2. Confirm `notebooklab-mcp` is available in the environment that launches Claude Code.
3. Register Notebooklab with Claude Code through one of the current official local stdio paths:

   ```bash
   claude mcp add notebooklab -- notebooklab-mcp
   ```

   Or copy the checked-in project-scoped example:

   ```bash
   cp ./examples/hosts/claude-code/notebooklab-outcome-bundle/claude-code.project.example.json ./.mcp.json
   ```

4. Start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
5. Only after that move to a narrow write-oriented action.

## Why this counts as public-ready

- the package is publicly reachable in this repository
- the install path is documented and reproducible
- the bundle includes a project-scoped MCP config example that matches Claude Code's documented `mcpServers` structure
- the proof loop stays read-first and inspectable
- the package still points to the same first-party `notebooklab-mcp` entrypoint as the rest of the repo

## Boundary

- public-ready package available from this repository
- not an official Claude Code directory or marketplace listing
- not a marketplace or directory listing
- not an official Anthropic partnership or endorsement claim
