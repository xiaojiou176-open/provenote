# Long Context To Structured Notes

This page explains the most direct fit for messy, oversized source material in Provenote.

In plain language: when the raw material is too long to keep re-reading or re-pasting, Provenote can help you turn it into a structured knowledge asset before you continue the work.

## Best-Fit Inputs

This path is a strong fit when the source material looks like:

- long AI chat logs or coding-agent transcripts
- copied forum threads or multi-page web discussions
- meeting notes, research dumps, or other pasted text that is rich in detail but poor in structure

Think of it like taking a stack of loose papers and asking for labeled folders before you start writing from them.

## Current Repo-Documented Path

The current built-in path is:

```text
Import long context as a source
-> Run the built-in Chat Knowledgeization transformation
-> Inspect the structured insight output
-> Choose the next durable lane: save as note first, seed the Ask lane, or capture it directly into a notebook research thread
-> Keep moving through notebook draft-adjacent work, or switch into Auditable Markdown when the job is stricter single-source verification
```

The built-in transformation is currently named:

```text
Chat Knowledgeization
```

It is repo-backed by the built-in transformation record and prompt pack, not by a marketing-only doc claim.

## Current Outcome Ladder

The strongest current continuation order is:

1. inspect the structured insight
2. save the reusable part as a notebook note when you want the lightest durable object
3. save it into a notebook research thread when you want an active research lane that can later feed the draft lane
4. keep final draft creation inside the notebook lane instead of pretending every insight should jump straight into a draft

In plain language: first sort the box, then file the useful pieces, then move the strongest lane into writing.

## What The Structured Output Is For

The current transformation is designed to turn long context into four reusable sections:

- process outline
- insights
- executive summary
- per-turn refined summaries

That makes it useful when you want to preserve reasoning, decisions, and outcomes instead of reducing everything to one disposable summary paragraph.

## Why This Matters

Generic chat workflows are good at producing a fast answer.

They are weaker when you later need to answer:

- what actually happened across the whole conversation?
- which decisions mattered?
- what should be carried forward as reusable knowledge?
- how do I turn this into the next research or writing step without starting over?

Provenote's current answer is not "chat harder." It is "structure the long context first, then continue from a stronger artifact."

## Current Honest Boundary

This page does **not** claim that Provenote already turns every long-context transformation directly into a final draft or a hosted team workflow with one click.

The honest current repo story is:

- long context can be imported into the workbench
- the built-in transformation can convert it into a structured insight artifact
- when the source is already linked to a notebook, that structured artifact can be saved forward as a reusable note in the notebook path
- from the insight detail, it can also open the existing Search / Ask lane with an editable research seed and carry the linked source/notebook context forward when available
- when notebook context is already known, the same insight detail can also capture the current insight directly into a notebook research thread using the existing thread-create contract
- that note-first handoff plus the seeded research lane and direct thread capture are the current continuity bridges into broader notebook, research-thread, draft-adjacent, and auditable work
- the current app starter and source-insight surfaces now point more directly at that ladder instead of leaving it buried in separate panels
- the current source-insight list and dialog now surface that ladder more explicitly, with `Save as note` kept as the lightest next step ahead of broader research actions

This page still does **not** claim that Provenote automatically turns every structured insight directly into a draft. The current bridge can persist into notes, seed the Ask lane, or capture into a notebook research thread, but it is still not a one-click all-outcomes shortcut.

## Where To Go Next

- [../quickstart.md](../quickstart.md)
- [../proof.md](../proof.md)
- [source-grounded-ai-research.md](source-grounded-ai-research.md)
- [source-grounded-drafts.md](source-grounded-drafts.md)
