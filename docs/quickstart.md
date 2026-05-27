# Quick Result Path

This page is for one job: get you from zero to a visible Notebooklab result as quickly as possible.

If you want the shortest human path, think of this as the "open the box, plug it in, see the screen light up" guide.

This is still a local proof loop, not a one-minute hosted trial.

## What You Will Get

By the end of this path, you should have:

- the local stack running
- the web workbench open in your browser
- at least one source imported
- one auditable markdown run started or downloaded
- a clear next step into notes, research threads, or notebook drafts if you want to keep going

## Time Budget

- **Fast path**: about 5 to 10 minutes if Docker is already working on your machine
- **Deeper setup**: use [installation.md](installation.md) and [configuration.md](configuration.md) after the first run works

## Step 1: Create The Local Environment File

```bash
cp .env.example .env
```

Set the two fast-path values:

```bash
OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string
GEMINI_API_KEY=your-google-ai-studio-key
```

For the Docker fast path, these are the only values you need to care about before first launch. The Compose stack injects the SurrealDB connection defaults and a known-good fast-path Gemini model for you.

## Step 2: Start The Default Local Stack

```bash
docker compose -f ops/compose/docker-compose.yml up -d --build
```

When the services are ready, open:

```text
http://localhost:8502
```

If this step is slow, wait for the initial image build to finish before assuming the stack is stuck.

## Step 3: Import Or Create A Source

Inside the workbench:

1. open the **Sources** area
2. create or import a source from text, file, audio, or web content
3. wait for the source detail view to load

## Step 4: Generate The First Evidence-Backed Output

In the source detail view, open **Auditable Markdown** and run it.

This lane is the fastest way to feel what Notebooklab is really trying to do:

- produce markdown you can inspect
- attach integrity counters
- keep stronger traceability than ordinary chat alone

## What Good Looks Like

You are in a strong first-run state if you can answer "yes" to all four:

- I can open the Notebooklab UI
- I can add or inspect a source
- I can see the Auditable Markdown panel
- I can start a run or download a generated markdown report

If you want one step after that first success, the best carry-forward move is to turn the structured result into a note, a research thread, or a notebook draft.

If you cannot say yes yet, that usually means you are still in the local setup phase, not in a hosted try-now flow.

## Common First-Run Snags

| If you hit... | Most likely reason | Fastest fix |
| --- | --- | --- |
| The UI does not open on `:8502` | the initial container build is still running | wait for the first build to finish, then refresh |
| The app starts but generation fails immediately | `GEMINI_API_KEY` is missing, invalid, or blocked for Gemini API use | update `.env`, then restart the stack |
| You are unsure why configuration docs list more keys | those are the full runtime contract keys, not the minimum Docker fast-path inputs | continue with this page first, then read [configuration.md](configuration.md) only when you need exact contract details |

## Where To Go Next

| Next goal | Recommended page |
| --- | --- |
| Full install and contributor setup | [installation.md](installation.md) |
| Environment contract and required variables | [configuration.md](configuration.md) |
| Product proof and inspectable evidence | [proof.md](proof.md) |
| Positioning and scope questions | [faq.md](faq.md) |
