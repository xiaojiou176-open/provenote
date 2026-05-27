# MCP Research Context For Coding Agents

This page explains the most agent-native use case in Notebooklab's current public surface.

In plain language: instead of pasting the same long research context into every coding-agent session, you can keep that context inside Notebooklab and let an MCP-capable host query the same notebooks, drafts, research threads, and auditable runs through one local server.

## Why This Is Valuable

Coding agents are good at acting on context, but long copied prompts are like carrying loose papers from room to room.

Notebooklab's MCP surface is closer to putting those papers into labeled folders and giving the agent a librarian desk instead of a single oversized clipboard.

That matters when you want an agent to:

- inspect notebook drafts before changing code
- search grounded research without re-pasting every note
- continue a research thread instead of starting from zero
- download a markdown or bundle artifact after the outcome is ready

## The Practical Flow

```text
Collect sources in Notebooklab
-> Organize them into notebooks and research threads
-> Start the first-party MCP server
-> Connect Claude Code, OpenAI Codex, Cursor, or another MCP-capable host
-> Let the host call outcome-first tools against the same local workbench
```

## What Makes Notebooklab's Current MCP Story Different

The current repo-documented MCP story is not just "there is a server."

It is that the server is attached to outcome objects people already care about:

- `draft.*`
- `research_thread.*`
- `auditable_run.*`

That keeps the integration centered on grounded work products instead of turning MCP into a detached control plane.

## Current Boundary

The honest public claim here is:

- compatibility through a first-party MCP server over stdio

The current repo does **not** claim:

- official vendor endorsement
- marketplace or plugin-directory listing by default
- a hosted remote MCP service as the default product shape
- identical support for every MCP transport variant and host workflow

## Where To Start

- [mcp.md](../mcp.md)
- [integrations/claude-code.md](../integrations/claude-code.md)
- [integrations/codex.md](../integrations/codex.md)
- [integrations/cursor.md](../integrations/cursor.md)
- [source-grounded AI research](source-grounded-ai-research.md)
