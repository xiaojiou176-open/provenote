# Quality

This page explains the current honest evaluation boundary for Notebooklab.

## Current Eval Positioning

- `promptfoo-eval` is a **manual-only deterministic lexical evidence gate**
- `ragas-eval` is a **manual-only threshold gate**
- the current repo **must not claim** that these two surfaces form a live end-to-end model-quality loop

## What This Means

- Promptfoo currently replays deterministic fixtures and lexical assertions.
- Ragas currently evaluates supplied metrics against configured thresholds.
- These are useful manual proof surfaces, but they are not a substitute for a live-model, end-to-end quality lane and they do not belong on the blocking PR path.
