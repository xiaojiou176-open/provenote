---
name: provenote-mcp-outcome-workflows
description: Use when a host or local coding agent should work with Provenote through the first-party MCP server without overclaiming plugin, marketplace, or public skills support.
metadata: {"openclaw":{"emoji":"🧠","requires":{"bins":["provenote-mcp"],"anyBins":["uv","python3"]}}}
---

# Purpose

Use Provenote's existing first-party MCP surfaces from a Claude-style bundle that OpenClaw can detect locally.

This is a tracked example artifact.
It is not a public plugin, skills, marketplace, or directory claim.

# Read-first workflow

1. confirm `provenote-mcp` is available
2. list drafts
3. list research threads
4. list auditable runs
5. only then move to a write-oriented action

# Safe first mutations

- `research_thread.to_draft`
- `draft.verify`
- `draft.download`
- `auditable_run.create`
- `auditable_run.download`

# Validation

Before calling this bundle "working", prove all four:

1. the host can execute `provenote-mcp`
2. a read-first tool succeeds
3. one narrow write-oriented workflow succeeds
4. the result maps back to an inspectable repo-owned surface

# Boundary

- compatibility/prep artifact only
- not a claim that Provenote already ships official OpenClaw support
- not a marketplace or directory listing
- keep the product center on long-context outcome work
