# Companion Host Examples

These examples are tracked, repo-owned host artifacts.

They are companion carry-forward surfaces around the first-party Notebooklab MCP
server. They help reviewers and operators bring notebook, draft, research
thread, and auditable-run workflows into host-specific setups after the main
outcome-workbench story is already clear.

They exist to make Notebooklab easier to verify and install from real host-facing surfaces without overclaiming:

- official partnership
- marketplace publication
- public skills distribution
- universal support across every host/runtime mode

Treat them like public-ready starter packages you can copy from this public repository, not as formal product roots or proof that a host-specific plugin lane is already live.

Machine-readable packet metadata now lives in [packet-index.json](./packet-index.json). Use that index and the per-bundle `manifest.yaml` files when you need one authoritative map of every host bundle without re-reading every README by hand.

That still does **not** mean:

- an official marketplace or directory listing is live
- a host vendor endorses Notebooklab
- a public skills catalog ships from this repo

## Included now

| Example | Purpose |
| --- | --- |
| `claude-code/notebooklab-outcome-bundle` | A public-ready Claude Code starter bundle with `.claude-plugin`, `.mcp.json`, command markdown, and a local skill for read-first Notebooklab MCP workflows |
| `codex/notebooklab-outcome-bundle` | A public-ready Codex starter bundle with `.codex-plugin`, `.mcp.json`, and a local skill for read-first Notebooklab MCP workflows |
| `cursor/notebooklab-outcome-bundle` | A public-ready Cursor starter bundle with `.mcp.json`, `.cursor/commands`, and a local skill for read-first Notebooklab MCP workflows |
| `opencode/notebooklab-outcome-bundle` | A public-ready OpenCode starter bundle with `opencode.json`, `.mcp.json`, and a local skill for read-first Notebooklab MCP workflows |
| `openclaw/notebooklab-claude-bundle` | A public-ready Claude-style OpenClaw-compatible bundle install pack with plugin markers, `.mcp.json`, commands, and a local skill |
| `openclaw/notebooklab-cursor-bundle` | A public-ready Cursor-style OpenClaw-compatible bundle install pack with `.cursor-plugin`, `.cursor/commands`, and `.mcp.json` |
| `openclaw/notebooklab-codex-bundle` | A public-ready Codex-style OpenClaw-compatible bundle install pack with `.codex-plugin`, `skills/`, and `.mcp.json` |

Every bundle above now also carries a `manifest.yaml` packet descriptor so host packet identity, placement, smoke flow, and claim level stay machine-readable instead of living only in prose.

If you want the narrowest OpenClaw-specific inventory before touching a host, use [openclaw/README.md](openclaw/README.md) and [openclaw/CLAWHUB_SUBMISSION.md](openclaw/CLAWHUB_SUBMISSION.md).

If you want repo-owned submission packs that still stop below listing-live truth, use:

- [claude-code/DIRECTORY_SUBMISSION.md](claude-code/DIRECTORY_SUBMISSION.md)
- [codex/PLUGIN_DIRECTORY_SUBMISSION.md](codex/PLUGIN_DIRECTORY_SUBMISSION.md)
- [openclaw/CLAWHUB_SUBMISSION.md](openclaw/CLAWHUB_SUBMISSION.md)
- [../../docs/promotion-kit.md](../../docs/promotion-kit.md) for repo-owned copy starters, screenshots, and a short demo storyboard

## Submission Packs

| Surface | Current pack |
| --- | --- |
| Claude Code | [claude-code/DIRECTORY_SUBMISSION.md](claude-code/DIRECTORY_SUBMISSION.md) |
| Codex | [codex/PLUGIN_DIRECTORY_SUBMISSION.md](codex/PLUGIN_DIRECTORY_SUBMISSION.md) |
| OpenClaw / ClawHub | [openclaw/CLAWHUB_SUBMISSION.md](openclaw/CLAWHUB_SUBMISSION.md) |
| Official MCP Registry | [../public-distribution/mcp-registry/README.md](../public-distribution/mcp-registry/README.md) |

## Fastest Install + Verify Loop

Use these examples as public-ready starter packages from the public Git checkout, not as proof that an official listing is already live.

| If you want to verify... | Start here | What you get |
| --- | --- | --- |
| Claude Code-style local MCP wiring | `claude-code/notebooklab-outcome-bundle` | `.claude-plugin`, `.mcp.json`, command markdown, and a workspace-local skill |
| Codex-style local MCP wiring | `codex/notebooklab-outcome-bundle` | `.codex-plugin`, `.mcp.json`, and a workspace-local skill |
| Cursor-style local MCP wiring | `cursor/notebooklab-outcome-bundle` | `.mcp.json`, `.cursor/commands`, and a workspace-local skill |
| OpenCode local MCP wiring | `opencode/notebooklab-outcome-bundle` | `opencode.json`, `.mcp.json`, and a workspace-local skill |
| Claude-style local bundle loading | `openclaw/notebooklab-claude-bundle` | `.claude-plugin`, `.mcp.json`, command markdown, and a workspace-local skill |
| Cursor-style command + MCP layout | `openclaw/notebooklab-cursor-bundle` | `.cursor-plugin`, `.cursor/commands`, `.mcp.json`, and a workspace-local skill |
| Codex-style MCP + skill bundle | `openclaw/notebooklab-codex-bundle` | `.codex-plugin`, `.mcp.json`, and a workspace-local skill |

For every bundle, keep the same proof loop:

1. confirm the host can execute `notebooklab-mcp`
2. install or point the host at the local example bundle
3. do one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
4. only then try a narrow mutation such as `research_thread.to_draft` or `draft.verify`

## Boundary

- These examples are public-ready starter packages backed by tracked repo artifacts.
- They can be copied, inspected, and installed from this public repository.
- They do **not** mean Notebooklab is already listed in a marketplace or directory.
- They do **not** mean an official Claude Code, Codex, Cursor, OpenCode, or OpenClaw listing is live.
- They do **not** mean public skills distribution ships from this repo.
