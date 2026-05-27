# Use Notebooklab With OpenCode

This page documents the current compatibility story for Notebooklab and OpenCode.

In plain language: OpenCode officially supports configuring MCP servers, so you can register Notebooklab's first-party MCP server and let OpenCode work with notebook outcomes instead of only ephemeral session context.

## Current Safe Claim

Notebooklab works with OpenCode **via MCP**.

That is the strongest public claim this repository can support today. This page does **not** claim an official partnership, project affiliation, bundled distribution inside OpenCode, plugin status, marketplace listing, or universal support across every MCP host/runtime mode.

## Why This Claim Is Safe

- OpenCode's official config docs expose an `mcp` configuration section.
- OpenCode's official MCP server docs describe local and remote MCP server registration.
- OpenCode's official config docs treat `mcp` and `plugin` as separate configuration surfaces, so MCP compatibility should not be paraphrased as plugin or marketplace status.
- Notebooklab ships a first-party stdio MCP entrypoint through `notebooklab-mcp`.

## What Works Today

Current fit through MCP:

- outcome-first draft tools
- research-thread create / append / promote flows
- auditable-run create / download / repair actions
- notebook/source/note lookup plus knowledge search

## Minimal Setup

1. Start Notebooklab locally and confirm the API is reachable.
2. Make sure the environment used by OpenCode can run `notebooklab-mcp`.
3. Add Notebooklab as a local MCP server in OpenCode config. Example:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "notebooklab": {
      "type": "local",
      "command": ["notebooklab-mcp"]
    }
  }
}
```

4. If you are targeting a non-local Notebooklab API, set `OPEN_NOTEBOOK_URL` and `OPEN_NOTEBOOK_PASSWORD` before OpenCode starts the MCP process.

## Repo-Backed Proof Loop

If you want to verify this page yourself instead of trusting the wording, use this local proof loop:

1. Confirm the MCP script surface exists in [../../pyproject.toml](../../pyproject.toml) as `notebooklab-mcp`.
2. Confirm the server exposes outcome-first tool groups in [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py):
   - `draft.*`
   - `research_thread.*`
   - `auditable_run.*`
3. Confirm the request schemas for those outcome lanes in [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py).
4. Run the repo-owned MCP contract test:

   ```bash
   bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q
   ```

5. Start Notebooklab locally with the repo-documented path in [../quickstart.md](../quickstart.md).
6. Add the local `notebooklab-mcp` server to OpenCode config, then ask OpenCode to do one narrow inspection first:
   - list notebook drafts
   - list research threads
   - list auditable runs
7. Only after the list/read step is visible, move to a write-oriented action such as promoting a research thread into a draft or downloading auditable markdown.

This keeps the claim honest: the page is pointing to a repo-owned entrypoint and inspectable outcome tools, not asking you to trust a marketplace badge or partnership announcement.

If you want a checked-in local host artifact instead of only this page, start with [../../examples/hosts/opencode/notebooklab-outcome-bundle/README.md](../../examples/hosts/opencode/notebooklab-outcome-bundle/README.md) and then use [../../examples/hosts/README.md](../../examples/hosts/README.md) as the broader host-artifact index.

## What To Inspect

| Surface | Why it matters |
| --- | --- |
| [../../pyproject.toml](../../pyproject.toml) | Proves the repo actually ships the `notebooklab-mcp` entrypoint instead of only naming one in docs |
| [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py) | Shows the concrete tool families OpenCode can call through MCP |
| [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py) | Shows the typed request shapes behind draft, research-thread, and auditable-run actions |
| [../../tests/test_mcp_server.py](../../tests/test_mcp_server.py) | Shows the repo keeps a concrete MCP contract test for tool registration and stdio entrypoint truth |
| [../mcp.md](../mcp.md) | Keeps the host-specific setup page anchored to the broader MCP truth and non-claim boundary |
| [../proof.md](../proof.md) | Maps the compatibility wording back to inspectable repo surfaces |

## Claim Boundary

| Bucket | What this page can say |
| --- | --- |
| Safe now | Notebooklab works with OpenCode via MCP; OpenCode can register local and remote MCP servers; Notebooklab ships a first-party stdio MCP entrypoint |
| Not claimed | official partnership, project affiliation, bundled OpenCode integration, plugin-store presence, marketplace listing, universal host guarantee |
| Deferred / proof gap | OpenClaw support, generic `works with every MCP host`, hosted/team/autopilot surfaces |

## Good First Workflows

- search notebook and source context before planning a coding change
- promote a research thread into a draft
- verify a draft and return markdown to another workflow
- repair weak claims in an auditable run before handing the result off

These are intentionally outcome-first workflows. They are a better fit for Notebooklab's real product center than treating OpenCode like the product itself.

## Official References

- [OpenCode intro](https://opencode.ai/docs/)
- [OpenCode config](https://opencode.ai/docs/config/)
- [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers/)
- [OpenCode brand page](https://opencode.ai/brand)
