# Agent Context — Weekly Product Review Pulse

## Goal
Automate a weekly "pulse" report for 5 fintech apps (INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera). Ingest App Store + Play Store reviews → cluster → LLM summarize → append to a Google Doc + send stakeholder email. All Google Workspace writes go through MCP servers only — no direct REST calls.

## Tech Stack
| Layer | Choice |
|---|---|
| Language | Python 3.12, uv |
| CLI | Typer (`pulse` command) |
| Config | pydantic-settings + `products.yaml` |
| Database | SQLite (stdlib, no extensions) |
| Embeddings | bge-small-en-v1.5 (local, sentence-transformers) |
| Clustering | UMAP + HDBSCAN + KeyBERT |
| LLM | Groq llama3-70b-8192 via openai SDK |
| Templating | Jinja2 |
| MCP | stdio (local) / SSE (prod) → Render-hosted MCP server |
| Logging | structlog (JSON, run_id context) |
| Scheduling | GitHub Actions cron (weekly, matrix per product) |

## Folder Structure
```
agent/
  __main__.py        # CLI entry (Typer)
  config.py          # loads products.yaml + .env
  storage.py         # SQLite schema (products, reviews, embeddings, runs, themes, clusters)
  orchestrator.py    # Phase 7: chains all phases
  embeddings.py      # bge embedding provider
  summarization.py   # LLM: themes, quotes, actions, who_this_helps
  ingestion/         # appstore.py, playstore.py, pii.py
  clustering/        # pipeline.py, embedder.py, keyphrases.py
  renderer/          # docs_tree.py, email_html.py
  mcp_client/        # session.py, docs_ops.py, gmail_ops.py
docs/                # architecture.md, implementationPlan.md, runbook.md, phases/*
tests/fixtures/      # golden.jsonl, clusters_golden.json, pulse_summary_golden.json, …
templates/           # doc_section.schema.json, email.html.j2
data/                # raw/, summaries/, artifacts/ (all gitignored)
.github/workflows/   # ci.yml, weekly-pulse.yml
products.yaml
```

## Phase Build Status
| Phase | Name | Status |
|---|---|---|
| 0 | Foundations & Scaffolding | COMPLETED |
| 1 | Review Ingestion | COMPLETED |
| 2 | Embeddings & Clustering | COMPLETED |
| 3 | LLM Summarization | COMPLETED |
| 4 | Report & Email Rendering | COMPLETED |
| 5 | Google Docs MCP — Append | NOT STARTED |
| 6 | Gmail MCP — Deliver | NOT STARTED |
| 7 | Orchestration & Scheduling | NOT STARTED |

## Top 3 Constraints
1. **MCP boundary is sacred.** Google Docs and Gmail are written to only via MCP tool calls. No direct Google API calls from agent code.
2. **Idempotency.** `run_id = sha1(product_key + iso_week)`. Re-running the same product + week must be a no-op — anchor check for Docs, `X-Pulse-Run-Id` header search for Gmail.
3. **Verbatim quote grounding.** Every `Quote.text` must be a normalised-whitespace substring of a real `review.body`. Failures re-prompt once; still failing → drop the quote.

## How to Run Locally
```bash
uv sync
uv run pulse init-db
uv run pulse ingest --product groww --weeks 10
uv run pulse cluster --run <run_id>
uv run pulse summarize --run <run_id>
uv run pulse render --run <run_id>
uv run pulse publish --run <run_id> --target both
# Or full pipeline:
uv run pulse run --product groww --weeks 10
```

## .env Variables
```
GROQ_API_KEY=
MCP_SERVER_URL=https://saksham-mcp-server.onrender.com/
CONFIRM_SEND=false
PULSE_ENV=development   # development | staging | production
```
Google credentials (`credentials.json`, `token.json`) live in the MCP server's Render secrets — never in this repo.

## Where to Resume
**Start at Phase 5.** Phases 0, 1, 2, 3, and 4 are completed. We have ingested, clustered, summarized, and rendered the reviews for Groww. The next step is to implement the MCP client in `agent/mcp_client/` to actually append the rendered content to Google Docs.

Full phase details: `docs/implementationPlan.md`. Full schema + data flow: `docs/architecture.md`.
