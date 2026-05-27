# MCP Compatibility

This page explains the current MCP truth for Notebooklab.

In plain language: Notebooklab already exposes a first-party MCP server, so coding-agent hosts can work with the same notebooks, drafts, research threads, and auditable runs that exist in the local workbench.

If your starting problem is still "I have a long messy conversation, note dump, or copied web thread," start with [Long Context To Structured Notes](use-cases/long-context-to-structured-notes.md) first. MCP is the carry-forward surface for those outcome objects, not the product's first doorway.

If you want a direct terminal/operator path instead of a host integration, use [runbooks/operator-cli.md](runbooks/operator-cli.md). That runbook covers the first-party CLI surface without pretending MCP and CLI are the same thing.

## What It Is For

Use the MCP server when you want a coding agent to:

- list and create notebook drafts
- verify drafts and download markdown outputs
- create, append, and promote research threads
- create auditable runs and repair claim/section issues
- search the knowledge base without bypassing the local API contract

The current product center is still Notebooklab's source-grounded outcome path. MCP is the integration surface, not the brand center.

## What It Is Not

This page does **not** claim that Notebooklab is:

- an official vendor partnership or bundled host integration
- a marketplace-listed plugin by default
- an official OpenClaw listing that is already live
- a public skills catalog or skills marketplace surface
- a universal guarantee for every MCP host or transport variant
- the only operator surface in the repository

Vendor names on the linked integration pages are descriptive compatibility targets only.

## MCP / CLI / Skills / Plugin Boundary

| Surface | What it is today | What it is not |
| --- | --- | --- |
| MCP | the host-facing integration layer for Notebooklab outcome objects | not the product center and not a partnership claim |
| Operator CLI | the terminal-facing first-party operator surface | not a renamed MCP server or plugin package |
| Public Skills language | a boundary question, not a shipped public product line | not a catalog or marketplace surface today |
| OpenClaw | a live ClawHub skill listing now exists at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`, and public-ready OpenClaw-compatible bundles still live under `examples/hosts/openclaw` | not an official partnership claim or proof that every OpenClaw marketplace surface is live |
| Official MCP Registry | the official registry already returns a live websiteUrl-backed entry for `notebooklab-mcp`, while no supported public package or public remote-server artifact from this repo is published yet | not a package-backed public artifact or a broader marketplace-live claim beyond that entry |
| Plugin / marketplace / directory | a separate publication question even when repo-owned starter bundles exist | not implied by the current MCP server |

If you need the full boundary map before opening a host-specific page, start with [project-status.md](project-status.md) and [distribution.md](distribution.md).

## Current Server Truth

The repository ships a first-party MCP entrypoint:

```text
notebooklab-mcp
```

It is exposed through [pyproject.toml](../pyproject.toml) and implemented in [../packages/core/mcp/server.py](../packages/core/mcp/server.py).

The current outcome-first tool groups include:

- `draft.*`
- `research_thread.*`
- `auditable_run.*`

Those outcome groups are wired through dedicated API-client helpers and repo CI coverage so the MCP surface stays aligned with the same draft, research-thread, and auditable-run routes used by the local workbench.

The server also keeps a few controlled utility surfaces such as `knowledge.search`, `chat.run`, `model.inspect`, `settings.mutate`, `ui_test.control`, and `computer_use.control`.

If you want the narrowest host-specific verification loop instead of a generic overview, start with [Use Notebooklab with OpenCode](integrations/opencode.md). That page now links the host setup step back to the repo-owned MCP entrypoint and the concrete outcome-tool families.

OpenClaw now has crossed into listing-live truth on the ClawHub skill lane. The repo ships public-ready OpenClaw-compatible bundles plus a live ClawHub skill page at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`, but that still does not mean every other OpenClaw marketplace or bundle surface is also live.

The same honesty rule applies to the official MCP Registry:

- the registry and publish quickstart exist
- the official MCP Registry already returns a live websiteUrl-backed entry for `notebooklab-mcp`
- this repository does not yet publish a supported public package or public remote-server artifact for `notebooklab-mcp`
- therefore the honest boundary is `live registry entry: yes`, `package-backed public artifact: no`, and `other host marketplace listing: no`

## Before You Connect A Host

1. Get Notebooklab running locally.
2. Make sure the environment that launches your host can execute `notebooklab-mcp`.
3. If the MCP host targets a non-local Notebooklab API, set `OPEN_NOTEBOOK_URL` and `OPEN_NOTEBOOK_PASSWORD` according to the current runtime contract.

The fastest repo-documented local path still starts at [quickstart.md](quickstart.md).

## Host Guides

- [Use Notebooklab with Claude Code](integrations/claude-code.md)
- [Use Notebooklab with OpenAI Codex](integrations/codex.md)
- [Use Notebooklab with Cursor](integrations/cursor.md)
- [Use Notebooklab with OpenCode](integrations/opencode.md)

If you want checked-in host artifacts instead of only setup pages, inspect [../examples/hosts/README.md](../examples/hosts/README.md). That index now includes public-ready starter bundles for Claude Code, Codex, Cursor, and OpenCode local MCP usage alongside the OpenClaw-compatible bundles and the ClawHub submission pack.

If you specifically want the repo-owned OpenClaw install path, use [Use Notebooklab with OpenClaw-compatible bundles](integrations/openclaw.md). That page is intentionally scoped to public-ready bundle distribution and submission-ready materials, while keeping listing-live wording deferred.

If you want the current submission packs for official discovery surfaces, start with:

- [../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md)
- [../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md)
- [../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md)
- [../examples/public-distribution/mcp-registry/README.md](../examples/public-distribution/mcp-registry/README.md)

## Host / CLI / Skills Boundary

| Surface | Current truth | Not claimed |
| --- | --- | --- |
| host pages under `docs/integrations/` | compatibility through the first-party MCP server, with repo-backed starter bundles where available | official partnership, bundled integration, plugin, marketplace, or directory status |
| `notebooklab-mcp` | the repo-owned stdio MCP entrypoint | a universal guarantee across every host/runtime mode |
| `notebooklab` | the first-party terminal/operator surface for outcome inspection and narrow outcome workflows | a host plugin, marketplace package, or MCP replacement |
| public skills surface | tracked public-ready skill packets now exist under `../public-skills/` for host-specific submission flows | a public skills catalog, live marketplace listing, or host-specific skills program endorsement |
| OpenClaw | a live ClawHub skill page now exists and the repo-owned bundles remain available | official partnership or every other OpenClaw marketplace surface being live |
| plugin / marketplace / directory presence | external-only or intentionally not-live today | shipped listing-live truth |

## Repo-Owned Host Proof Loop

Before you treat any host page as a real compatibility claim, verify the same three layers:

1. [../pyproject.toml](../pyproject.toml) exposes `notebooklab-mcp` as the tracked entrypoint.
2. [../packages/core/mcp/server.py](../packages/core/mcp/server.py) and [../packages/core/mcp/schemas.py](../packages/core/mcp/schemas.py) show the current outcome-first tool surface.
3. Run the repo-owned MCP contract check:

   ```bash
   bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q
   ```

4. The host-specific page points back to the host's official MCP docs for the exact configuration syntax.

That keeps host guides in the `compatibility through MCP` bucket instead of drifting into bundled integration, plugin, or marketplace wording.

## Agent-Centric Use Case

If you want to see why this MCP surface matters beyond setup syntax, read [MCP research context for coding agents](use-cases/mcp-research-context-for-coding-agents.md).

## Transport Boundary

Notebooklab's first-party MCP entrypoint runs over stdio.

That keeps the repository-side truth simple:

- Notebooklab owns the server
- your host owns how it starts and routes the process

Host-specific MCP setup formats change over time, so follow the official host docs linked on each integration page for the exact configuration syntax.
