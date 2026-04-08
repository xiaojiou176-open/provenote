# Provenote MCP Outcome Workflows Public Skill

This folder is the OpenHands/extensions-friendly and ClawHub-style public skill
packet for Provenote.

## Purpose

Use it when you want one portable skill folder that keeps the Provenote story
honest:

- first-party MCP server remains the execution surface
- read-first outcome workflows stay primary
- no hosted SaaS or public skills catalog claim is introduced
- no live listing is implied without fresh platform read-back

## What this packet includes

- `SKILL.md`
  - the canonical host-facing skill instructions
- `manifest.yaml`
  - repo-owned listing metadata for ClawHub-style and OpenHands-style submits

## Best-fit hosts

- OpenHands/extensions contribution flow
- ClawHub-style skill publication
- repo-local skill import flows that expect a standalone folder

## What this packet must not claim

- no live OpenHands/extensions listing without fresh PR/read-back
- no live ClawHub listing without fresh host-side read-back
- no official marketplace or directory listing by itself
- no replacement of the first-party `provenote-mcp` server

## Source of truth

Keep this packet aligned with:

- `docs/distribution.md`
- `docs/project-status.md`
- `server.json`
- `examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md`
