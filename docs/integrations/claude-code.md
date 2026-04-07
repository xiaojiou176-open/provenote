# Use Provenote With Claude Code

This page documents the current compatibility story for Provenote and Claude Code.

In plain language: if you already use Claude Code, you can connect it to Provenote through MCP so the agent can work with drafts, research threads, auditable runs, and notebook context without leaving your local stack.

## Current Claim Ladder

Provenote works with Claude Code **via MCP**, and this repository now ships a **public-ready Claude Code starter bundle**.

That is the right level of public truth today:

- `repo-owned prep exists`: yes
- `public-ready package available`: yes
- `publicly discoverable listing live`: no separate official listing is claimed here
- `official marketplace listing live`: no

This page does **not** claim an official partnership, endorsement, directory listing, or native Anthropic-owned plugin surface.

## What Works Today

Current fit through MCP:

- list and create drafts
- verify drafts and download markdown
- list, create, append, and promote research threads
- list and create auditable runs
- repair auditable claims and sections

## Why This Claim Is Safe

- Claude Code's official docs include MCP as a first-party extension path.
- Claude Code's official docs document MCP, and Anthropic publishes separate Software Directory terms, so a public-ready starter package is a valid repo-owned distribution layer even when no official listing is live.
- Provenote ships a first-party stdio MCP entrypoint through `provenote-mcp`.
- The current repo keeps concrete MCP contract coverage in `tests/test_mcp_server.py`.
- This page stays in the compatibility bucket and does not rely on directory, marketplace, or partnership language.

## Public-Ready Starter Bundle

If you want a checked-in install package instead of a prose-only setup page, use [../../examples/hosts/claude-code/provenote-outcome-bundle/README.md](../../examples/hosts/claude-code/provenote-outcome-bundle/README.md).

If you want the repo-owned directory submission materials that stop one step before listing-live truth, use [../../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md).

That bundle is public-ready because:

- the package lives in a public Git-tracked path
- the install path is documented
- the proof loop is explicit
- the package points to the same first-party `provenote-mcp` entrypoint this page documents

## Minimal Setup

1. Start Provenote locally and confirm the API is reachable.
2. Make sure the environment used by Claude Code can run `provenote-mcp`.
3. Follow the current Claude Code MCP instructions in the official docs and register Provenote as a stdio MCP server.
4. If you are targeting a non-local Provenote API, set `OPEN_NOTEBOOK_URL` and `OPEN_NOTEBOOK_PASSWORD` before launching the MCP process.

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
6. In Claude Code, register `provenote-mcp` as a stdio MCP server and start with one read-first step:
   - list drafts
   - list research threads
   - list auditable runs
7. Only after the list/read step is visible, move to a write-oriented action such as verifying a draft or promoting a research thread into a draft.

If you want a checked-in local host artifact instead of only this page, start with [../../examples/hosts/claude-code/provenote-outcome-bundle/README.md](../../examples/hosts/claude-code/provenote-outcome-bundle/README.md), continue with [../../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md](../../examples/hosts/claude-code/DIRECTORY_SUBMISSION.md), and then use [../../examples/hosts/README.md](../../examples/hosts/README.md) as the broader host-artifact index.

## What To Inspect

| Surface | Why it matters |
| --- | --- |
| [../../pyproject.toml](../../pyproject.toml) | Proves the repo actually ships `provenote-mcp` |
| [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py) | Shows the concrete outcome-tool families Claude Code can call |
| [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py) | Shows the typed request shapes behind those tools |
| [../../tests/test_mcp_server.py](../../tests/test_mcp_server.py) | Shows the repo keeps a real MCP contract test |
| [../mcp.md](../mcp.md) | Keeps this host page anchored to the broader MCP truth |
| [../proof.md](../proof.md) | Maps the compatibility wording back to inspectable repo surfaces |

## Good First Workflows

- review a draft and freeze it through `draft.verify`
- turn a search session into a reusable draft through `research_thread.to_draft`
- repair weak evidence sections in an auditable run before handing the result off

## Claim Boundary

| Bucket | What this page can say |
| --- | --- |
| Safe now | Provenote works with Claude Code via MCP; Claude Code can register repo-owned MCP servers; Provenote ships a first-party stdio MCP entrypoint; a public-ready Claude Code starter bundle and directory submission pack are available in this repository |
| Not claimed | official Anthropic partnership, endorsement, directory inclusion, marketplace listing, or native Anthropic-owned plugin surface |
| Deferred / proof gap | public Skills distribution, OpenClaw support, generic `works with every MCP host`, hosted/team/autopilot surfaces |

For the latest Claude Code MCP setup syntax, use the official docs:

- [Claude Code overview](https://code.claude.com/docs/en/overview)
- [Claude Code MCP docs](https://code.claude.com/docs/en/mcp)

For Anthropic naming and directory constraints, review:

- [Anthropic trademark guidelines](https://www.anthropic.com/legal/trademark-guidelines)
- [Anthropic software directory terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)
