# From Source To Verified Draft

This page describes the shortest higher-confidence workflow in Provenote.

In plain language: if you want one concrete reason to try the product, it is the ability to move from one source to a verified draft with visible checkpoints along the way.

## The Path

```text
Import a source
-> Run Auditable Markdown
-> Open or create a notebook draft
-> Review the current draft state
-> Verify the draft
```

## Why Verify Exists

Verify is not just another button.

It is the step that freezes the current draft state into a verified snapshot so the result is easier to hand off and reason about later.

That matters when you need a result that feels more like a checked artifact and less like an in-progress chat answer.

## What You Can Inspect Along The Way

Current repo truth gives you at least these checkpoints:

- source processing status
- auditable metrics and repair surfaces
- notebook draft state
- verified draft snapshot

## Current Boundary

This path is currently strongest as a local, repo-documented proof loop.

It should not be described as:

- a hosted one-click workflow
- a multi-user publishing pipeline
- a final proof of external production use

## Related Guides

- [quickstart.md](../quickstart.md)
- [proof.md](../proof.md)
- [AI notes with receipts](ai-notes-with-receipts.md)
- [source-grounded drafts](source-grounded-drafts.md)
