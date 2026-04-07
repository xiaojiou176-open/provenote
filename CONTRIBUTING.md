# Contributing to This Fork

This repository is a forked collaboration surface, not the upstream project's canonical contribution inbox.

Before you open work here, read:

- [NOTICE.md](NOTICE.md)
- [MAINTAINERS.md](MAINTAINERS.md)
- [SUPPORT.md](SUPPORT.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Contribution Flow

1. Start with the current repository docs and existing issues.
2. Open or reference an issue in this repository before large changes.
3. Keep patches scoped and repo-local.
4. Use this repository's PR flow for review.

If a change requires upstream coordination, call that out explicitly in the issue or PR instead of assuming this fork speaks for upstream.

## Local Setup

Use the tracked setup commands from [README.md](README.md) and [docs/development.md](docs/development.md).

## Local Manual Browser Lane

When you need the repo-owned real Chrome lane for manual investigation, use:

```bash
npm --prefix apps/web run browser:manual
```

That helper launches or reuses the canonical Provenote browser lane with:

- `~/.cache/provenote/browser/chrome-user-data`
- the resolved `provenote` / `Profile 1` profile
- a fixed CDP listener on `http://127.0.0.1:9342`
- a generated local identity tab under `.runtime-cache/browser-identity/index.html`

Treat the identity tab as the human-facing anchor for this repo's browser lane:

- keep it open on the left when possible
- pin it manually once if you want a stable visual marker
- use `PROVENOTE_BROWSER_IDENTITY_LABEL` to override the displayed repo label
- use `PROVENOTE_BROWSER_IDENTITY_ACCENT` with a hex color such as `#2563eb` to override the accent

Do not script Chrome's private avatar/theme internals as part of the normal repo bootstrap. Manual one-time profile color or avatar customization is fine, but the tracked repo automation should stay on the stable side of Chrome's public surface.

## Security Reports

Do not file vulnerabilities as public contribution issues. Use [SECURITY.md](SECURITY.md).

## Code Ownership And Stewardship

This checkout intentionally keeps its public ownership story conservative. Review routing and stewardship are documented in [MAINTAINERS.md](MAINTAINERS.md), not inferred from upstream history.

Project participation is also governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Treat it as part of the current fork's repo-local collaboration boundary.
