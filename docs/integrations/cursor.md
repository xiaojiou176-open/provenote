# Use Notebooklab With Cursor

This page documents the current compatibility story for Notebooklab and Cursor.

In plain language: if Cursor is your day-to-day coding environment, Notebooklab can join that workflow through MCP so the editor can work with auditable runs, research threads, and notebook drafts instead of treating them as off-screen context.

## Current Safe Claim

Notebooklab works with Cursor **via MCP**.

That is the strongest public claim the current repository can support. This page does **not** claim an official plugin listing, marketplace publication, or any partnership with Anysphere.

## What Works Today

Current fit through MCP:

- outcome-first draft tools
- research-thread create / append / promote flows
- auditable-run create / download / repair actions

## Why This Claim Is Safe

- Cursor documents MCP as a supported integration path.
- Notebooklab ships a first-party stdio MCP entrypoint through `notebooklab-mcp`.
- The current repo keeps concrete MCP contract coverage in `tests/test_mcp_server.py`.
- This page stays in the compatibility bucket and does not claim marketplace, plugin, or partnership status.

## Minimal Setup

1. Start Notebooklab locally and confirm the API is reachable.
2. Make sure the environment used by Cursor can run `notebooklab-mcp`.
3. Add Notebooklab as an MCP server using Cursor's current MCP setup flow.
4. If you are targeting a non-local Notebooklab API, set `OPEN_NOTEBOOK_URL` and `OPEN_NOTEBOOK_PASSWORD` before the MCP process starts.

## Repo-Backed Proof Loop

If you want to verify this page instead of trusting the wording, use this local proof loop:

1. Confirm the MCP script surface exists in [../../pyproject.toml](../../pyproject.toml) as `notebooklab-mcp`.
2. Confirm the server exposes outcome-first tool groups in [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py):
   - `draft.*`
   - `research_thread.*`
   - `auditable_run.*`
3. Confirm the typed schemas in [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py).
4. Run the repo-owned MCP contract test:

   ```bash
   bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q
   ```

5. Start Notebooklab locally with the repo-documented path in [../quickstart.md](../quickstart.md).
6. In Cursor, register `notebooklab-mcp` as an MCP server and start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
7. Only after the list/read step is visible, move to a write-oriented action such as verifying a draft or downloading auditable markdown.

If you want a checked-in local host artifact instead of only this page, start with [../../examples/hosts/cursor/notebooklab-outcome-bundle/README.md](../../examples/hosts/cursor/notebooklab-outcome-bundle/README.md) and keep [../../examples/hosts/README.md](../../examples/hosts/README.md) as the broader host-artifact index.

## What To Inspect

| Surface | Why it matters |
| --- | --- |
| [../../pyproject.toml](../../pyproject.toml) | Proves the repo actually ships `notebooklab-mcp` |
| [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py) | Shows the concrete outcome-tool families Cursor can call |
| [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py) | Shows the typed request shapes behind those tools |
| [../../tests/test_mcp_server.py](../../tests/test_mcp_server.py) | Shows the repo keeps a real MCP contract test |
| [../mcp.md](../mcp.md) | Keeps this host page anchored to the broader MCP truth |
| [../proof.md](../proof.md) | Maps the compatibility wording back to inspectable repo surfaces |

## Good First Workflows

- use auditable runs while reviewing source material inside Cursor
- verify a draft before handing the markdown back to another workflow
- move a research thread into a draft without leaving the editor

## Current Boundary

- compatibility through MCP, not a Cursor Marketplace plugin claim
- no claim of partnership with Anysphere
- no claim that Notebooklab is already listed as a Cursor plugin or marketplace package

## Claim Boundary

| Bucket | What this page can say |
| --- | --- |
| Safe now | Notebooklab works with Cursor via MCP; Cursor can register MCP servers; Notebooklab ships a first-party stdio MCP entrypoint |
| Not claimed | official Cursor plugin, marketplace publication, partnership, or bundled distribution |
| Deferred / proof gap | public Skills distribution, OpenClaw support, generic `works with every MCP host`, hosted/team/autopilot surfaces |

Use the latest official docs for exact setup and naming guidance:

- [Cursor MCP docs](https://cursor.com/docs/mcp)
- [Cursor brand page](https://cursor.com/brand)
