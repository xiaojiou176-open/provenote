# Notebooklab Codex-Style Bundle

This is a tracked public-ready Codex-style bundle package.

It exists so OpenClaw-compatible bundle detection and Codex-style bundle markers can be installed from this public repository without claiming an official Codex plugin or live OpenClaw listing.

## Included surfaces

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `skills/notebooklab-mcp-outcome-workflows/SKILL.md`

## Local install loop

```bash
openclaw plugins install ./examples/hosts/openclaw/notebooklab-codex-bundle
openclaw plugins list
openclaw plugins info notebooklab-codex-bundle
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
- not a public Codex plugin claim
- not a marketplace or directory listing
