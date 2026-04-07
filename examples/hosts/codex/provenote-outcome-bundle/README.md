# Provenote Codex Starter Bundle

This is a tracked public-ready starter bundle for Codex-style MCP usage.

It exists to make Provenote easier to wire into Codex from a public Git-backed package path without pretending there is already a listed Codex plugin, marketplace package, or official OpenAI integration surface.

## What it contains

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `config.toml.example`
- `skills/provenote-mcp-outcome-workflows/SKILL.md`

## What it is for

- public-ready Codex starter package distribution through this repository
- read-first Provenote MCP workflows
- notebook draft / research-thread / auditable-run starter actions

## How to use it

1. Copy this bundle into a workspace or keep it as a checked-in starter directory that Codex operators can reuse.
2. Confirm `provenote-mcp` is available in the environment that launches Codex.
3. Start from `config.toml.example` if you want a repo-owned Codex config snippet that matches the official `config.toml` flow.
4. Register the bundle-local MCP config using the current Codex MCP flow.
5. Start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
6. Only after that move to a narrow write-oriented action.

## Why this counts as public-ready

- the package is publicly reachable in this repository
- the install path is documented and reproducible
- the proof loop stays read-first and inspectable
- the package still points to the same first-party `provenote-mcp` entrypoint as the rest of the repo

## Boundary

- public-ready package available from this repository
- not a listed Codex plugin or official OpenAI surface
- not a marketplace or directory listing
- not an official OpenAI integration or endorsement claim
