# AI Notes With Receipts

This page explains the most direct use-case fit for Notebooklab.

In plain language: Notebooklab is for moments when a normal AI note is not enough because you need to see where the result came from, what was covered, and what still needs review.

## What Problem It Solves

Generic AI note tools are good at producing words quickly.

They are often weaker at showing:

- which source material supported the result
- which claims are still weak or uncited
- whether the result is ready to hand off

Notebooklab is built to keep those questions visible instead of hiding them behind a finished-looking paragraph.

## The Current Outcome Path

The shortest repo-documented path today is:

```text
Source -> Auditable Markdown -> Draft -> Verify
```

What that means in practice:

- import one source
- run the auditable markdown lane to get a result with integrity counters
- move the source into a notebook draft when you need a reusable outcome object
- verify the draft when you want a frozen snapshot of the current result

## Why This Is More Than A Chat Transcript

Current repo truth already supports:

- source-level auditable runs
- notebook-level drafts
- research threads that preserve ask/search work
- richer draft export bundles

That makes the product fit people who need to keep working with the output after the first AI response is gone.

## Best-Fit Users

This use case is a strong fit if you:

- write long-form notes from source material
- need traceability beyond a plain chat reply
- want a repo-documented local workbench instead of a hosted black box

It is a weaker fit if you only want:

- a one-line summary tool
- a hosted no-setup app
- a generic chat UI with no interest in evidence quality

## Where To Go Next

- [quickstart.md](../quickstart.md)
- [proof.md](../proof.md)
- [source-grounded drafts](source-grounded-drafts.md)
- [from source to verified draft](source-to-verified-draft.md)
