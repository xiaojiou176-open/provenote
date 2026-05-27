---
name: notebooklab-mcp-outcome-workflows
description: Use Notebooklab through the first-party MCP server from a Cursor starter bundle without overclaiming plugin, marketplace, or public skills support.
---

# Purpose

Give local Cursor users one tracked starter bundle for Notebooklab's existing MCP outcome surfaces.

This is a tracked example artifact.
It is not a public plugin, skills, marketplace, or directory claim.

# Read-first workflow

1. confirm `notebooklab-mcp` is available
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

1. the host can execute `notebooklab-mcp`
2. a read-first tool succeeds
3. one narrow write-oriented workflow succeeds
4. the result maps back to an inspectable repo-owned surface

# Boundary

- compatibility/prep artifact only
- not an official Cursor integration or partnership claim
- not a marketplace or directory listing
- keep the product center on long-context outcome work
