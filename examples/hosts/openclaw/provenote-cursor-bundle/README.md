# Notebooklab Cursor-Style Bundle

This is a tracked public-ready Cursor-style bundle package.

It exists so OpenClaw-compatible bundle detection and Cursor-style command layout can be installed from this public repository without claiming an official Cursor plugin or live OpenClaw listing.

## Included surfaces

- `.cursor-plugin/plugin.json`
- `.mcp.json`
- `.cursor/commands/notebooklab-mcp-outcome-workflows.md`
- `skills/notebooklab-mcp-outcome-workflows/SKILL.md`

## Local install loop

```bash
openclaw plugins install ./examples/hosts/openclaw/notebooklab-cursor-bundle
openclaw plugins list
openclaw plugins info notebooklab-cursor-bundle
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

## Boundary

- public-ready package available from this repository
- not a public Cursor plugin claim
- not a marketplace listing
