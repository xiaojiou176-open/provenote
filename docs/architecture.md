# Architecture

Notebooklab is a layered application with four practical surfaces:

If you are looking for the fastest product overview instead of the system map, start with [../README.md](../README.md) and [quickstart.md](quickstart.md).

1. `apps/web` - the user interface
2. `services/api` - the HTTP boundary
3. `packages/core` - the runtime, graph, and domain logic
4. `tests` - verification and quality gates

## Request flow

1. The browser calls the API.
2. The API validates input and delegates work to core services.
3. Core services interact with Gemini, SurrealDB, and internal workflows.
4. Results return through the API to the UI.

## Runtime contract

- Gemini-only runtime
- SurrealDB-backed persistence
- `tooling/scripts/runtime/run_uv_managed.sh` as the canonical Python bootstrap path

## Traceability boundary

- Ordinary chat is a fast assistant surface.
- Source-level auditable markdown and auditable-runs are the stricter single-source evidence-backed lane.
- Notebook-level drafts are the reusable notebook outcome lane built on top of source-level evidence assets.
- Draft export bundles package markdown, metrics, PID summary, claim/section review data, and source manifest into one handoff artifact.
- Research threads preserve search/ask work as notebook artifacts instead of leaving that work only in transient chat state.
- A first-party MCP server exposes outcome-first tools on top of the local API so coding agents can work with the same draft, research-thread, and auditable-run objects without bypassing service contracts.

## Documentation boundary

This repo intentionally keeps architecture documentation short. When details drift, trust current code and tests over prose.
