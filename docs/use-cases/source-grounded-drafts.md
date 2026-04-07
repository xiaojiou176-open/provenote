# Source-Grounded Drafts

This page explains the notebook draft lane in product terms.

In plain language: Provenote can take multiple notebook-linked sources and turn them into one draft outcome, so you are not forced to treat every result as a one-source, one-shot export.

## What A Draft Means Here

A draft in Provenote is not just a text blob.

It is a notebook-level outcome object that can carry:

- source references
- draft versions
- compare/verify semantics
- export bundle metadata

That is why the product can support a path like:

```text
Search / Ask -> Research Thread -> Draft
```

or:

```text
Source -> Auditable Markdown -> Draft
```

## Why It Matters

This use case is for work that needs to move from raw material to a reusable result.

Examples:

- collecting several sources into one notebook and producing one draft
- turning a research thread into a more durable writing object
- verifying a draft before handing it off as markdown or bundle output

## Current Public Boundary

Current repo truth supports:

- creating drafts from notebook-linked sources
- promoting research threads into drafts
- verifying drafts into a frozen snapshot
- downloading markdown and richer export bundles

Current repo truth does **not** claim:

- collaborative multi-user review workflows
- hosted draft sharing by default
- a full publishing CMS built on top of drafts

## Where To Go Next

- [proof.md](../proof.md)
- [quickstart.md](../quickstart.md)
- [from source to verified draft](source-to-verified-draft.md)
- [MCP compatibility](../mcp.md)
