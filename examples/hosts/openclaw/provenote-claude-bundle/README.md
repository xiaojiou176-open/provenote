# Provenote OpenClaw-Compatible Claude Bundle

This is a tracked public-ready bundle package for local installation and verification work.

It is designed around the Claude-style bundle layout that OpenClaw documents as a supported compatible bundle format.

## What it contains

- `.claude-plugin/plugin.json`
- `.mcp.json`
- `commands/provenote-mcp-outcome-workflows.md`
- `skills/provenote-mcp-outcome-workflows/SKILL.md`

## What it is for

- local host proof and prep
- public-ready OpenClaw-compatible bundle distribution through this repository
- OpenClaw-compatible bundle detection
- Claude-style workspace skill loading
- read-first Provenote MCP workflows

## What it is not

- not a public marketplace package
- not a public skills catalog
- not a claim that Provenote already ships official OpenClaw listing live

## Local install loop

```bash
openclaw plugins install ./examples/hosts/openclaw/provenote-claude-bundle
openclaw plugins list
openclaw plugins info provenote-claude-bundle
openclaw gateway restart
```

## After install

Use a read-first workflow first:

- list drafts
- list research threads
- list auditable runs

Only after that should you try mutations like:

- `research_thread.to_draft`
- `draft.verify`
- `auditable_run.download`
