# Public Surface Snapshot

Snapshot Date: 2026-04-05

This file is a manual review aid, not live proof.

It captures the latest repo-facing view of the current public surface so maintainers can refresh GitHub page settings without relying on chat history or memory.

## Truth Boundary For This Snapshot

- `repo-side truth`: README, docs, issue templates, discussions routing, social-preview assets, and release workflow expectations tracked in this repository
- `remote/manual truth`: the actual GitHub page settings for the live repository (About panel, homepage, topics, discussions tab, social preview image, releases page)

Repo files can define the intended public surface. They cannot, by themselves, prove that GitHub Settings already match.

## Latest Recorded Remote Review Summary

- Review Status: `pending-social-preview-proof`
- Review Date: 2026-04-05 21:50 PDT
- Review Surface: `gh api repos/...`, `gh repo view`, GitHub live repository page routing, GitHub Docs social-preview guidance, and repo-side asset checks
- Evidence pointer:
  - `gh api repos/xiaojiou176/provenote --jq '{description:.description,homepage:.homepage,topics:.topics,open_graph_image_url:.open_graph_image_url}'`
  - `gh repo view xiaojiou176/provenote --json name,description,homepageUrl,isPrivate,isFork,defaultBranchRef,repositoryTopics,hasDiscussionsEnabled,url`
  - `gh release list --repo xiaojiou176/provenote`
  - `gh run list --workflow 'Build and Release' --limit 5`
  - `curl -L -s https://github.com/xiaojiou176/provenote | rg 'og:image'`
  - `curl -L 'https://docs.github.com/api/article/body?pathname=/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview'`
  - repo-side social preview assets under `docs/assets/social/`

## Latest Observed Live State

| Surface | Latest observed state |
| --- | --- |
| Repo visibility | public |
| Repo identity | `provenote` |
| Default branch | `main` |
| Description | `Source-grounded knowledge-work control tower for auditable research, notebook drafts, and MCP-assisted workflows.` |
| Homepage | `https://github.com/xiaojiou176/provenote/blob/main/docs/index.md` |
| Topics | `auditable-markdown`, `citations`, `fastapi`, `gemini`, `knowledge-management`, `nextjs`, `notebooks`, `podcast-generation`, `research-assistant`, `research-workbench`, `search`, `source-grounded-writing`, `traceable-writing` |
| Discussions | enabled |
| Releases | no visible published release and no active draft release were returned by the latest GitHub CLI readback |
| Social preview asset in repo | `docs/assets/social/provenote-social-preview.png` exists |
| Social preview asset dimensions | `1280x640`, `502837 bytes` |
| Social preview uploaded in GitHub Settings | not live as of this review; GitHub repository API currently reports `open_graph_image_url = null` |
| GitHub page Open Graph tag | repository page exposes an `og:image` URL, but that alone does not prove the custom social preview upload is live |

## Operator Checklist

Use this checklist when refreshing the GitHub live page:

- [ ] About panel description matches the value above
- [ ] Homepage matches the value above
- [ ] Topics match the value above
- [ ] Discussions remain enabled
- [ ] Social preview image uploaded from `docs/assets/social/provenote-social-preview.png`
- [ ] Repository Settings review confirms the uploaded image is the repo-owned custom social preview
- [ ] Release plan has been intentionally re-established before any new draft release is claimed
- [ ] Latest release-event `Build and Release` wave is green and matches the current public release proof story
- [ ] `open_graph_image_url` becomes non-null after the GitHub Settings upload is completed

## Exact Button Pack

Use this when you want to finish the GitHub custom social preview manually without guessing.

Local asset:

- `docs/assets/social/provenote-social-preview.png`

Settings URL:

- `https://github.com/xiaojiou176/provenote/settings`

Click path:

- `General -> Social preview -> Edit / Upload image`

Minimum manual steps:

1. Open the repository settings URL above.
2. Scroll to `Social preview`.
3. Upload `docs/assets/social/provenote-social-preview.png`.
4. Save and wait for GitHub to refresh the repository page metadata.
5. Recheck the public surface and only change the review status away from `partial-remote-proof` after the upload is visibly confirmed.

## Claim Discipline

- Repo docs may describe the intended public surface tracked in-tree.
- Repo docs must not say "social preview is live" or "release page is ready" unless a fresh remote review records that state explicitly.
- Release visibility must not be confused with release health: a visible tag/page is not proof that the latest release-event build, proof artifact, or asset set is clean.
- A repo-side PNG/SVG asset is not the same thing as a live GitHub custom social preview. In this review wave, `open_graph_image_url = null` is fresh evidence that the upload has not happened yet.
