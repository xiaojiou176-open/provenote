---
name: provenote-mcp-outcome-workflows
description: Use Provenote through the first-party MCP server from a ClawHub publish root without overclaiming a live listing or official compatibility status.
---

# Purpose

Use Provenote's existing first-party MCP surfaces from an OpenClaw-installed skill.

This is a public-ready ClawHub skill package and canonical publish root.
It is not proof that the skill is already listed publicly.

# Requirements

Before using this skill, configure an MCP server named `provenote` that can execute `provenote-mcp`.

# Read-first workflow

1. list drafts
2. list research threads
3. list auditable runs
4. only then move to one narrow write-oriented action

# Safe first mutations

- `research_thread.to_draft`
- `draft.verify`
- `draft.download`
- `auditable_run.create`
- `auditable_run.download`

# Validation

Before calling this skill working, prove all four:

1. the host can execute `provenote-mcp`
2. a read-first tool succeeds
3. one narrow write-oriented workflow succeeds
4. the result maps back to an inspectable repo-owned surface

# Boundary

- public-ready ClawHub skill package from this repository
- not a live ClawHub listing yet
- not a claim that Provenote already ships official OpenClaw listing live
- not a marketplace or directory listing
