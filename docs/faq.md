# FAQ

## What is Notebooklab?

Notebooklab is a long-context-first, source-grounded workbench for structured insight, auditable markdown, notebook drafts, and outcome workflows across notes, documents, audio, and web content.

The short version: it is built to help you move from "I have too much messy material" to "I can structure it, inspect it, and keep working with the result."

## What is the strongest reason to care?

Notebooklab is not trying to be just another chat box over files.

Its strongest hook is the combination of:

- long-context structuring that turns messy source material into reusable insight
- source collection
- notebook drafts, research threads, and search workflows
- transformations and podcast-ready creation paths
- an auditable markdown lane for stronger traceability

## Why would someone star it now?

Because a star is not only applause on GitHub. It is also a bookmark for projects that look likely to matter later.

Good reasons to star Notebooklab today:

- you care about auditable AI writing and source-grounded outputs
- you want a repo-documented research workbench to watch as it matures
- you want to follow the public release and proof surfaces, not just code churn

## Is this just Open Notebook under a new name?

No, but provenance still matters.

Notebooklab is a deep, productized fork of the upstream Open Notebook project. Upstream lineage remains part of the evidence story, while the current public support, release, and review boundary is repository-local to this checkout.

## Do I need Gemini?

The current runtime contract in this repository is Gemini-first.

If you are evaluating the repo today, the practical answer is yes: plan around the Gemini-first setup described in [configuration.md](configuration.md).

## Can I use Notebooklab with Claude Code, Codex, Cursor, or OpenCode?

Yes, through the first-party MCP server documented in [mcp.md](mcp.md).

The short version is:

- Notebooklab can expose notebooks, drafts, research threads, auditable runs, and a few controlled utility actions to MCP-capable hosts
- current public docs support Claude Code, OpenAI Codex, Cursor, and OpenCode as compatibility targets
- current public starter bundles are also available for Claude Code, OpenAI Codex, Cursor, and OpenCode
- this is still not an official partnership or marketplace claim

If your starting problem is long messy context rather than agent integration, start with [use-cases/long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md) first and treat MCP as the carry-forward surface.

If you want host-specific setup and boundary notes, start with:

- [integrations/claude-code.md](integrations/claude-code.md)
- [integrations/codex.md](integrations/codex.md)
- [integrations/cursor.md](integrations/cursor.md)
- [integrations/opencode.md](integrations/opencode.md)

If you want the narrowest self-verify loop instead of the full host list, start with [integrations/opencode.md](integrations/opencode.md). That page points back to the shipped `notebooklab-mcp` entrypoint and the concrete outcome-tool families.

## Does Notebooklab currently support OpenClaw?

Yes, at the repo-owned package layer, but not as a live official listing.

The safe current host list is:

- Claude Code
- OpenAI Codex
- Cursor
- OpenCode

All four are documented as compatibility-through-MCP surfaces.

Tracked public-ready example bundles now exist under [../examples/hosts/README.md](../examples/hosts/README.md), including OpenClaw-compatible layouts under `examples/hosts/openclaw/`.

If you want the narrowest repo-owned OpenClaw install path, use [integrations/openclaw.md](integrations/openclaw.md) together with [../examples/hosts/openclaw/README.md](../examples/hosts/openclaw/README.md).

Those artifacts now reach a stronger rung:

- repo-owned public-ready OpenClaw-compatible bundles exist in this repository
- the repo includes a ClawHub submission pack
- the ClawHub skill listing is now live at `https://clawhub.ai/xiaojiou176/notebooklab-mcp-outcome-workflows`

The same caution applies to plugin, marketplace, and public Skills language:

- no official OpenClaw listing is currently claimed as live
- no directory listing is currently claimed as live
- no separate public Skills catalog or product line is currently claimed

If you want the exact boundary map, use [project-status.md](project-status.md).
If you want the claim ladder and distribution matrix in one place, use [distribution.md](distribution.md).

## Can I operate Notebooklab outcome lanes without staying inside the web app?

Yes.

The repository now ships a first-party local operator CLI through the `notebooklab` command.

That surface is useful when you want to:

- inspect draft, research-thread, or auditable-run state
- promote a research thread into a draft
- verify a draft and download markdown or bundle artifacts
- create an auditable run from one source and save the markdown locally

The honest boundary is still important:

- this is a repo-backed local operator surface
- it is **not** a plugin-store, marketplace, or official host-partnership claim
- MCP remains the host-integration surface, while the CLI is the first-party terminal surface

Start with [runbooks/operator-cli.md](runbooks/operator-cli.md) for the concrete commands.
Use [project-status.md](project-status.md) if you want the bigger map around CLI, MCP, OpenClaw, and packaging claims.

## Does this repo ship public Skills, a plugin, or a marketplace package?

Not as an official listing.

The current public surfaces are:

- the web workbench
- the first-party MCP server
- the first-party `notebooklab` operator CLI
- public-ready starter bundles under [../examples/hosts/README.md](../examples/hosts/README.md)
- public-ready starter bundles in `examples/hosts/`
- tracked public-ready skill packets under [../public-skills/README.md](../public-skills/README.md)

What is not claimed today:

- a public skills catalog
- a host-specific skills program
- an official plugin-store package
- a marketplace listing that is already live

In plain language: the repo already has real doors you can use, but it is not pretending there is a gift shop outside each one.

## Should Notebooklab be renamed to `notebooklab.ai`?

Not by default.

The current repo truth supports `Notebooklab` as the product brand and treats any future `.ai` domain as a possible landing or redirect domain, not a reason to rename the repository, package, CLI, or MCP script surface.

In plain language: a `.ai` domain can help people find the product, but it does not automatically improve the product's identity. The real differentiator is still the source-grounded, auditable outcome path.

If a domain decision happens later, keep these boundaries:

- use vendor and domain language conservatively
- do not imply partnerships or endorsement
- do not rename technical surfaces until the brand decision is actually settled

## What still needs owner or platform action?

The shortest honest answer is: external publication and naming/distribution moves.

Current repo-side preparation can go far, but these steps are still outside pure repository truth:

- deciding whether to create and publish a future release
- deciding whether the long-term homepage should stay on GitHub docs or move elsewhere
- registering a custom domain or redirect
- trademark and naming clearance for a stronger public brand move
- marketplace, directory, or partner-program submissions
- package-backed Official MCP Registry upgrade once a supported public package or public remote-server artifact exists

In plain language: the workshop can be swept and labeled before someone unlocks the storefront.

## What should I try first?

If your raw material already looks like one long messy source, start with [long-context-to-structured-notes.md](use-cases/long-context-to-structured-notes.md) first, then use the [quick result path](quickstart.md).

If you want the shortest general proof loop, use the [quick result path](quickstart.md):

1. create the local `.env`
2. start the Docker stack
3. open the workbench
4. import a source
5. run **Auditable Markdown**
6. create a **Draft** inside a notebook if you want a reusable notebook-level outcome

That path gives you the fastest feel for what Notebooklab is trying to make easier.

## Where should I go if I want proof, not promises?

Start with [proof.md](proof.md).

It maps product claims to inspectable repo surfaces so you do not have to reverse-engineer trust from scattered files.
