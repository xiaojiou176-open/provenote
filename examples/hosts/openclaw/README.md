# OpenClaw-Compatible Bundle Index

These are tracked public-ready OpenClaw-compatible bundle artifacts for Provenote.

In plain language: this folder is the repo-owned shelf for "install it from the public repo, verify it locally, and prepare a ClawHub submission" without pretending an official listing is already live.

## Included Bundles

| Bundle | Best fit | Included surfaces |
| --- | --- | --- |
| `provenote-claude-bundle` | Claude-style plugin layout | `.claude-plugin`, `.mcp.json`, `commands/`, and `skills/` |
| `provenote-cursor-bundle` | Cursor-style command layout | `.cursor-plugin`, `.cursor/commands`, `.mcp.json`, and `skills/` |
| `provenote-codex-bundle` | Codex-style plugin layout | `.codex-plugin`, `.mcp.json`, and `skills/` |

## Fast Local Loop

1. Confirm `provenote-mcp` is available in the environment that launches OpenClaw.
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
- `provenote-claude-bundle/README.md`
- `provenote-cursor-bundle/README.md`
- `provenote-codex-bundle/README.md`

## Boundary

- public-ready OpenClaw-compatible bundle install path is available from this repository
- official ClawHub or community-plugin listing is not live
- not a marketplace, directory, or registry listing claim for Provenote today
- not a public Skills distribution claim
