# Use Provenote With OpenAI Codex

This page documents the current compatibility story for Provenote and OpenAI Codex.

In plain language: if you use Codex as a coding agent, Provenote can plug into that workflow through MCP so Codex can work with notebook outcomes instead of only ephemeral chat context.

## Current Claim Ladder

Provenote works with OpenAI Codex **via MCP**, and this repository now ships a **public-ready Codex starter bundle**.

That is the right public claim today:

- `repo-owned prep exists`: yes
- `public-ready package available`: yes
- `publicly discoverable listing live`: no official/public Codex directory listing is claimed here
- `official marketplace listing live`: no

This page does **not** claim that Provenote is an official OpenAI integration, a listed Codex plugin, or a marketplace-ready Codex app.

The public repository and docs are discoverable on the web today. That still does **not** count as a Codex directory or marketplace listing.

## What Works Today

Current fit through MCP:

- draft creation, verification, and markdown download
- research-thread create / append / promote flows
- auditable-run create / download / repair actions

## Why This Claim Is Safe

- OpenAI's Codex docs include MCP as the supported tool/context connection path.
- OpenAI's official Codex plugins docs expose a Plugin Directory, and the build docs explain plugin packaging and local marketplace setup while still marking official public plugin publishing as "coming soon."
- Provenote ships a first-party stdio MCP entrypoint through `provenote-mcp`.
- The current repo keeps concrete MCP contract coverage in `tests/test_mcp_server.py`.
- This page stays in the compatibility bucket and does not claim plugin, marketplace, or official integration status.

## Public-Ready Starter Bundle

If you want a checked-in install package instead of a prose-only setup page, use [../../examples/hosts/codex/provenote-outcome-bundle/README.md](../../examples/hosts/codex/provenote-outcome-bundle/README.md).

If you want the repo-owned plugin-directory submission materials that stop one step before listing-live truth, use [../../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md).

That bundle is public-ready because:

- the package lives in a public Git-tracked path
- the install path is documented
- the proof loop is explicit
- the bundle now includes a repo-owned `config.toml.example` that matches Codex's documented config surface
- the package points to the same first-party `provenote-mcp` entrypoint this page documents

## Minimal Setup

1. Start Provenote locally and confirm the API is reachable.
2. Make sure the environment used by Codex can run `provenote-mcp`.
3. Register Provenote as an MCP server using the current official Codex MCP instructions.
4. If you are targeting a non-local Provenote API, set `OPEN_NOTEBOOK_URL` and `OPEN_NOTEBOOK_PASSWORD` before the MCP process starts.

## Repo-Backed Proof Loop

If you want to verify this page instead of trusting the wording, use this local proof loop:

1. Confirm the MCP script surface exists in [../../pyproject.toml](../../pyproject.toml) as `provenote-mcp`.
2. Confirm the server exposes outcome-first tool groups in [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py):
   - `draft.*`
   - `research_thread.*`
   - `auditable_run.*`
3. Confirm the typed schemas in [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py).
4. Run the repo-owned MCP contract test:

   ```bash
   bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q
   ```

5. Start Provenote locally with the repo-documented path in [../quickstart.md](../quickstart.md).
6. In Codex, register `provenote-mcp` as an MCP server and start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
7. Only after the list/read step is visible, move to a write-oriented action such as creating a draft from a research thread or downloading auditable markdown.

If you want a checked-in local host artifact instead of only this page, start with [../../examples/hosts/codex/provenote-outcome-bundle/README.md](../../examples/hosts/codex/provenote-outcome-bundle/README.md), continue with [../../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md](../../examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md), and then use [../../examples/hosts/README.md](../../examples/hosts/README.md) as the broader host-artifact index.

## What To Inspect

| Surface | Why it matters |
| --- | --- |
| [../../pyproject.toml](../../pyproject.toml) | Proves the repo actually ships `provenote-mcp` |
| [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py) | Shows the concrete outcome-tool families Codex can call |
| [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py) | Shows the typed request shapes behind those tools |
| [../../tests/test_mcp_server.py](../../tests/test_mcp_server.py) | Shows the repo keeps a real MCP contract test |
| [../mcp.md](../mcp.md) | Keeps this host page anchored to the broader MCP truth |
| [../proof.md](../proof.md) | Maps the compatibility wording back to inspectable repo surfaces |

## Good First Workflows

- create a draft from an existing research thread and verify it
- audit one source, repair weak claims, then hand the result back as markdown
- search notebook context before planning a coding or writing change

## Claim Boundary

| Bucket | What this page can say |
| --- | --- |
| Safe now | Provenote works with OpenAI Codex via MCP; Codex can register MCP servers; Provenote ships a first-party stdio MCP entrypoint; a public-ready Codex starter bundle and plugin-directory submission pack are available in this repository |
| Not claimed | official OpenAI integration, listed Codex plugin, marketplace-ready Codex app, or OpenAI endorsement |
| Deferred / proof gap | public Skills distribution, OpenClaw support, generic `works with every MCP host`, hosted/team/autopilot surfaces |

Use the latest official docs for the exact Codex MCP configuration syntax:

- [OpenAI Codex overview](https://developers.openai.com/codex/)
- [OpenAI Codex MCP guide](https://developers.openai.com/codex/mcp)
- [OpenAI brand guidelines](https://openai.com/brand/)
