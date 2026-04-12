# OpenClaw Public-Ready Bundle Path

This page documents the current repo-owned public-ready path for using Provenote with OpenClaw-compatible bundles.

In plain language: Provenote now ships checked-in OpenClaw-compatible bundle layouts so developers can wire `provenote-mcp`, local skills, and plugin markers into an OpenClaw install from this public repository, and the matching ClawHub skill listing is already live at `https://clawhub.ai/xiaojiou176/provenote-mcp-outcome-workflows`.

## Current Claim Ladder

Provenote ships tracked OpenClaw-compatible bundles as a **public-ready package path** and a **submission-ready ClawHub pack**.

That is the right truth layer today:

- `repo-owned prep exists`: yes
- `public-ready package available`: yes
- `publicly discoverable listing live`: yes, on ClawHub
- `official marketplace listing live`: yes, on ClawHub

This page does **not** claim:

- current public OpenClaw compatibility support
- an official partnership or endorsement
- every other OpenClaw marketplace, directory, or registry surface
- a public Skills catalog or separate public plugin package from this repo

## Why This Page Exists

OpenClaw's official docs already treat plugins, skills, and MCP as real building blocks.

That makes it reasonable for Provenote to provide a repo-owned local install path, as long as the wording stays honest:

- OpenClaw owns the runtime and plugin loading rules
- Provenote owns the `provenote-mcp` entrypoint plus the checked-in local bundle examples
- a live ClawHub skill page is not the same as every OpenClaw marketplace surface being live

## Bundle Map

If you want the repo-owned bundle inventory first, start with [../../examples/hosts/openclaw/README.md](../../examples/hosts/openclaw/README.md).

| Bundle | When to use it | What it includes |
| --- | --- | --- |
| [../../examples/hosts/openclaw/provenote-claude-bundle/README.md](../../examples/hosts/openclaw/provenote-claude-bundle/README.md) | You want a Claude-style bundle layout that OpenClaw can detect as a compatible local plugin bundle | `.claude-plugin`, `.mcp.json`, command markdown, and the local `provenote-mcp-outcome-workflows` skill |
| [../../examples/hosts/openclaw/provenote-cursor-bundle/README.md](../../examples/hosts/openclaw/provenote-cursor-bundle/README.md) | You want a Cursor-style command layout with `.cursor/commands` plus the same local Provenote MCP workflow skill | `.cursor-plugin`, `.cursor/commands`, `.mcp.json`, and the local skill |
| [../../examples/hosts/openclaw/provenote-codex-bundle/README.md](../../examples/hosts/openclaw/provenote-codex-bundle/README.md) | You want a Codex-style bundle marker with MCP wiring and a local skill | `.codex-plugin`, `.mcp.json`, and the local skill |

## Fastest Bundle Install Loop

1. Start Provenote locally and make sure the environment that launches OpenClaw can execute `provenote-mcp`.
2. Choose one checked-in bundle under `examples/hosts/openclaw/`.
3. Install that bundle into OpenClaw:

   ```bash
   openclaw plugins install ./examples/hosts/openclaw/provenote-claude-bundle
   openclaw plugins list
   openclaw plugins info provenote-claude-bundle
   openclaw gateway restart
   ```

4. Keep the first agent action read-first:
   - list drafts
   - list research threads
   - list auditable runs
5. Only after the read-first step is visible should you try a narrow mutation such as:
   - `research_thread.to_draft`
   - `draft.verify`
   - `auditable_run.download`

The exact bundle path changes depending on which bundle family you choose. The verify loop does not.

## Repo-Backed Proof Loop

If you want to verify this page instead of trusting it, inspect the same repo-owned layers:

1. [../../pyproject.toml](../../pyproject.toml) exposes `provenote-mcp`.
2. [../../packages/core/mcp/server.py](../../packages/core/mcp/server.py) and [../../packages/core/mcp/schemas.py](../../packages/core/mcp/schemas.py) show the outcome-first MCP tool surface.
3. [../../examples/hosts/openclaw/README.md](../../examples/hosts/openclaw/README.md) maps the three checked-in OpenClaw-compatible bundle families.
4. [../../tests/test_mcp_server.py](../../tests/test_mcp_server.py) keeps the local skill boundary honest.
5. [../../tests/ci/test_host_examples_contract.py](../../tests/ci/test_host_examples_contract.py) and [../../tests/ci/test_host_surface_contract.py](../../tests/ci/test_host_surface_contract.py) keep the bundle/index/docs contract from drifting.

## Submission Pack

If you want the repo-owned submission materials, use [../../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md](../../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md).

That pack keeps three things separate:

- the public-ready bundle install path that already exists in this repository
- the official OpenClaw/ClawHub surface that exists in the platform docs
- the broader OpenClaw account/tooling work that would still be required if the maintainer wants more than the current live ClawHub page

## Boundary

| Safe now | Not claimed |
| --- | --- |
| checked-in public-ready OpenClaw-compatible bundles exist and the ClawHub skill page is live | every other OpenClaw marketplace surface being live |
| the bundles target the first-party `provenote-mcp` entrypoint | official OpenClaw endorsement or partnership |
| local skills and plugin markers are present in repo-owned artifacts | plugin marketplace, directory, or registry listing |
| the install path is suitable for public-ready bundle distribution from this repository | public Skills program or universal host guarantee |

Use [../project-status.md](../project-status.md) if you want the full status map before translating this local prep path into any public wording.

## Official References

- [OpenClaw Plugins](https://docs.openclaw.ai/plugins)
- [OpenClaw Writing Plugins Guide](https://docs.openclaw.ai/guide/extensions/writing-plugins/)
- [OpenClaw Custom Skills Guide](https://docs.openclaw.ai/guide/skills/custom-skills/)
- [OpenClaw MCP CLI](https://docs.openclaw.ai/cli/mcp)
