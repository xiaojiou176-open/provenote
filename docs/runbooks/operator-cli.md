# Operator CLI

This runbook explains Provenote's first-party local operator CLI.

In plain language: if MCP is the host-facing door for coding agents, `provenote` is the terminal-facing tool cart for humans and agents who want to inspect or run the same outcome lanes directly.

## What It Is For

The CLI is now a repo-backed local operator surface for:

- checking runtime reachability through `status`
- inspecting one notebook's current outcome state through `inspect notebook`
- promoting a research thread into a draft and optionally verifying/downloading it
- creating an auditable run and downloading markdown

This is intentionally a real first-party operator surface, not a plugin, marketplace package, or a renamed MCP server.

## Bootstrap

Refresh the managed environment first so the script surface is installed:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync
```

## Status Check

Use this when you want to confirm that the local runtime is reachable before touching any outcome object:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote status --json
```

If you want the command itself to fail when the local `/health` probe is down, use:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote status --json --require-healthy
```

What it reports:

- whether the current `/health` probe is healthy
- the configured API base
- the `/health` response
- the shipped MCP entrypoint
- the current operator lanes owned by the CLI

## Outcome Lane 1: Source -> Auditable Markdown

This is the direct terminal version of the auditable markdown lane:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote auditable-markdown source:123 \
  --output ./exports/ \
  --json
```

Expected result:

- one auditable run is created
- one markdown file is downloaded
- stdout prints a JSON payload with `source_id`, `run`, and `saved_markdown`

## Outcome Lane 2: Research Thread -> Draft -> Verified Artifact

This is the strongest current multi-object operator lane:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote research-thread-to-draft research_thread:123 \
  --verify \
  --download-markdown \
  --download-bundle \
  --output-dir ./exports \
  --json
```

Expected result:

- the research thread is promoted into a draft
- the draft is optionally verified
- markdown and bundle artifacts are downloaded when requested
- stdout prints the resulting `draft` plus any saved artifact paths

Think of it like taking a labeled research folder, freezing it into a handoff draft, and then saving the handoff copy to disk.

## Inspect Notebook Outcome State

Use this when you want operator visibility before you run a mutating workflow:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote inspect notebook notebook:123 --json
```

If you also want auditable-run context in the same response:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run provenote inspect notebook notebook:123 \
  --source-id source:123 \
  --json
```

## Auth And Remote Boundary

- `--api-base` accepts either the root API URL or a `/api` URL and normalizes it
- `--password` overrides `OPEN_NOTEBOOK_PASSWORD` for one command
- remote targets still require the same runtime/auth contract as the rest of the repo

## What This Does Not Claim

This runbook does **not** claim that Provenote now ships:

- a plugin marketplace surface
- an official host partnership
- a hosted one-click operator console
- a separate public product line independent from the main Provenote workbench

## Related Docs

- [../development.md](../development.md)
- [../mcp.md](../mcp.md)
- [../use-cases/source-grounded-drafts.md](../use-cases/source-grounded-drafts.md)
- [../use-cases/source-to-verified-draft.md](../use-cases/source-to-verified-draft.md)
