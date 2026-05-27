# OpenClaw-Compatible Bundle Index

These are tracked public-ready OpenClaw-compatible bundle artifacts for Notebooklab.

In plain language: this folder is the repo-owned shelf for "install it from the public repo, verify it locally, and reuse the same bundle family that now backs the live ClawHub skill listing" without pretending every OpenClaw storefront is already live.

## Included Bundles

| Bundle | Best fit | Included surfaces |
| --- | --- | --- |
| `notebooklab-claude-bundle` | Claude-style plugin layout | `.claude-plugin`, `.mcp.json`, `commands/`, and `skills/` |
| `notebooklab-cursor-bundle` | Cursor-style command layout | `.cursor-plugin`, `.cursor/commands`, `.mcp.json`, and `skills/` |
| `notebooklab-codex-bundle` | Codex-style plugin layout | `.codex-plugin`, `.mcp.json`, and `skills/` |

## Fast Local Loop

1. Confirm `notebooklab-mcp` is available in the environment that launches OpenClaw.
2. Install one bundle with `openclaw plugins install ./examples/hosts/openclaw/<bundle-name>`.
3. Check that OpenClaw sees it:

   ```bash
   openclaw plugins list
   openclaw plugins info <bundle-name>
   openclaw gateway restart
   ```

4. Start with a read-first action:
   - list drafts
   - list research threads
   - list auditable runs
5. Only after that move to one narrow mutation such as `research_thread.to_draft` or `draft.verify`.

## Where To Read Next

- [../../../docs/integrations/openclaw.md](../../../docs/integrations/openclaw.md) for the repo-owned public-ready bundle path
- [CLAWHUB_SUBMISSION.md](CLAWHUB_SUBMISSION.md) for the current submission pack and external unblock notes
- [../README.md](../README.md) for the broader host artifact index
- `notebooklab-claude-bundle/README.md`
- `notebooklab-cursor-bundle/README.md`
- `notebooklab-codex-bundle/README.md`

## Boundary

- public-ready OpenClaw-compatible bundle install path is available from this repository
- the ClawHub skill listing is now live at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`
- not every OpenClaw marketplace, directory, or registry surface is live for Notebooklab today
- not a public Skills distribution claim
