# Registry Ownership Snapshot

Snapshot Date: 2026-03-27

This file is a manual review aid, not live proof.

Specific remote repo slugs, secondary reviewer accounts, and package-lookup identifiers are intentionally generalized in this public artifact. When a maintainer re-runs the remote review, use the current `origin` remote and the active reviewer accounts from that execution wave rather than treating any older identifier as a public constant.

## Truth Boundary For This Snapshot

- `repo-side truth`: workflows resolve GHCR targets from `${{ github.repository }}`, and Docker Hub publishing stays disabled unless maintainers set `DOCKERHUB_IMAGE_REPOSITORY`
- `remote/manual truth`: who actually controls a package namespace, whether packages exist today, and whether historical artifacts still point at inherited namespaces

Repo files can define where publishing would go. They cannot, by themselves, prove namespace ownership on a live registry.

## Remote Review Status Contract

Use one of these statuses for registry reviews:

- `verified`
- `pending-remote-proof`
- `blocked-by-platform`
- `blocked-by-token-scope`
- `re-review-required`

Do not describe registry ownership as `verified` unless the minimum remote proof record is present.

## Minimum Remote Proof Record

Every registry ownership review wave must record at least:

- `review_status`
- `review_surface`
- `reviewer`
- `review_date`
- `scope_reviewed`
- `candidate_namespace_or_package`
- `evidence_pointer`
- `exceptions_or_limits`
- `next_recheck_trigger`

## Current Repo-Side State

- repo-owned GHCR publish target is expected to resolve from `${{ github.repository }}`
- optional Docker Hub publishing is disabled unless `DOCKERHUB_IMAGE_REPOSITORY` is explicitly configured by maintainers

## Not Yet Proven By Repo Files Alone

- who controls any external Docker Hub namespace
- whether a published package already exists under the current repository GHCR path
- whether older release artifacts still point at inherited upstream namespaces

## Latest Recorded Remote Review Summary

- Review Status: `re-review-required`
- Review Date: 2026-04-06 03:10 PDT
- Review Surface: GitHub Packages / Releases / workflow metadata for the current `origin` repository
- Reviewer context:
  - active maintainer account could confirm repo visibility, workflow access, and current package lookup responses
- Latest recorded evidence:
  - predecessor owner-scope GitHub Packages lookup for the historical `notebooklab` container namespace currently returns `404 Not Found`
  - predecessor repo-scoped package lookup for the historical `notebooklab` container namespace also returns `404 Not Found`
  - predecessor release-tag lookup for `v1.8.1` currently returns `404 Not Found`
  - the new post-cutover repository therefore does not yet have fresh package/release evidence that can replace the predecessor repository's historical review

Interpretation:

- pre-cutover package ownership evidence from the deleted predecessor repository must not be treated as current truth for the new repository object
- current package ownership on the new repository is not yet proven by a positive live registry record
- the honest posture for the new repository is `re-review-required`, not `verified`

## Manual Verification Needed

- confirm live package ownership in GitHub Packages / Docker Hub
- confirm public release notes match the current fork's declared boundary
- review this snapshot together with the required-checks snapshot and the live repository settings when a release path is being prepared

## Claim Discipline

- Repo docs may say which namespace the workflows are configured to target.
- Repo docs must not say "this fork controls registry X" unless a fresh `review_status: verified` record exists with the minimum proof fields above.
- Empty package listings, `404` lookups, or token-scope failures must stay recorded as evidence limits, not be rewritten into definitive ownership claims.
