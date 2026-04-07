# Security Policy

This policy applies to the current fork of Provenote in this repository.

> Think of this file like the emergency entrance sign for this checkout: it tells you where to report a problem here, not where the upstream project handles its own inbox.

## Scope

This policy covers security issues in the active repository surface for this fork, including:

- application runtime and API behavior shipped in this checkout
- repository-owned scripts, containers, and CI workflows tracked here
- documentation or governance surfaces that could misroute secrets, support, or disclosure flow

Upstream history still matters for provenance, but upstream maintainers are not the current public intake path for this repository. See [NOTICE.md](NOTICE.md) and [MAINTAINERS.md](MAINTAINERS.md) for that boundary.

## How To Report

Do not post exploit details, credentials, or proof-of-concept material in a public issue.

### Report a vulnerability privately

Use the repository's private vulnerability reporting path first whenever it is available.

Preferred path:

1. Use this repository's GitHub `Security` tab and private vulnerability reporting flow when it is enabled.
2. If private reporting is unavailable, open a minimal public issue in this repository without technical details and request a private handoff.

If you are unsure whether an issue is security-sensitive, treat it as private first.

## What To Include

- affected version, branch, or commit SHA
- clear reproduction steps
- impact summary
- mitigation ideas, if you already know them

## Response Expectations

This fork does not advertise an off-platform security inbox or guaranteed SLA.

Conservative expectations:

- acknowledgement target: within 7 calendar days
- triage update target: within 14 calendar days when maintainers can reproduce or assess the report

Stewardship for these expectations is repository-local and documented in [MAINTAINERS.md](MAINTAINERS.md).

## Disclosure Guidance

- Avoid public disclosure until maintainers for this repository have had a reasonable chance to assess and mitigate the issue.
- If active exploitation, credential exposure, or user data risk is involved, say so immediately in the first report.

## Public Residual Exposure

Sometimes a repository-side fix is not the end of the story.

In plain language: if sensitive material was already published and later removed from `main` or normal branch refs, a hosting platform may still retain a read-only public snapshot such as a closed pull request ref or cached blob/search result.

If that happens, use this order:

1. If the leaked material includes real credentials, rotate or revoke them first.
2. Rewrite or remove every repo-owned ref you can control.
3. Confirm the current public heads are clean.
4. If a public residual still survives only on a read-only platform ref such as `refs/pull/*`, open a GitHub Support request and ask for platform-side purge of the read-only ref plus related caches and search indexes.
5. Keep the evidence of what was already fixed repo-side so Support can distinguish a platform-retained snapshot from an unfinished repository cleanup.

Do not assume a closed pull request snapshot is self-service deletable. If the API says the ref is read-only, treat GitHub Support as the next authority boundary.

## Out Of Scope

- issues caused only by unsupported local modifications
- vulnerabilities in third-party services you operate separately
- hardening requests that do not describe a concrete security problem
