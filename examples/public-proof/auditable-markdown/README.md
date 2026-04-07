# Public Proof Pack: Auditable Markdown

This folder is the canonical public proof pack for Provenote's auditable markdown lane.

In plain language: if you want one fixed, reusable demonstration instead of reading repo prose, start here.

## What This Pack Proves

- the repo can accept one text source through the public API
- the auditable markdown lane can run on that source
- the lane can return one downloadable markdown artifact

This pack does **not** claim to be a hosted demo or a zero-setup path.

## Files In This Pack

- `sample-source.txt` - fixed public input text for the proof loop
- `run-public-proof.sh` - reproducible local script that creates one source, runs auditable markdown, downloads the markdown, and deletes the temporary source

## Prerequisites

1. Start the local stack first.
2. Make sure the API is reachable.
3. Export `OPEN_NOTEBOOK_PASSWORD`.

The default API base is `http://localhost:5055/api`.

## Fast Path

```bash
export OPEN_NOTEBOOK_PASSWORD=your-local-password
bash examples/public-proof/auditable-markdown/run-public-proof.sh
```

## Expected Output

The script prints:

- `source_id=...`
- `run_id=...`
- `saved_markdown=...`

The markdown artifact is written under:

```text
.runtime-cache/public-proof/
```

## What Good Looks Like

- one temporary text source is created through `/api/sources/json`
- one auditable run is created through `/api/sources/{source_id}/auditable-runs`
- one markdown file is downloaded
- the temporary source is deleted during cleanup

## Truth Boundary

- This pack is a reproducible local proof loop, not a remote hosted demo
- it uses a fixed public sample text, not user data
- it does not write secrets or local absolute paths into tracked files
