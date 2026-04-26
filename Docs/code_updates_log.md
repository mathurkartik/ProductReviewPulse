# Code Updates Log (Architecture Alignment)

This document tracks all code changes made to align the `ProductReviewPulse` agent with the updated `Docs/Architecture.md`, `Docs/ProblemStatement.md`, and `Docs/implementationPlan.md`. 

## Phase 0: Foundations & Data Schema

### `agent/storage.py`
- Updated `products` table schema: renamed `product_key` to `key`, `display_name` to `display`, `app_store_id` to `appstore_id`, `play_store_id` to `play_package`, and added `gmail_to TEXT`.
- Updated `reviews` table schema: renamed `review_date` to `posted_at DATETIME`, `created_at` to `ingested_at DATETIME`, added `title TEXT`, `version TEXT`, `country TEXT`, and `raw_json TEXT`.
- Updated `review_embeddings` table schema: stripped down to only `review_id` and `embedding` (removed `run_id`, `model`, `cached`).
- Updated `runs` table schema: renamed `run_id` to `id`, replaced `window_weeks` with `window_start DATE` and `window_end DATE`.
- Updated `themes` table schema: renamed `name` to `label`, `summary` to `description`, changed `sentiment_weight REAL` to `sentiment TEXT`, replaced `quotes_json` with `representative_review_ids_json TEXT`.
- Updated corresponding helper functions (e.g., `upsert_product`, `get_product_gdoc_id`, `upsert_run`) to use the new column names (like `key`, `id`).

### `agent/config.py`
- Updated `ProductConfig` to use `appstore_id` and `play_package` instead of `app_store_id` and `play_store_id`.

## Phase 1: Review Ingestion

### `agent/ingestion/models.py`
- Updated `RawReview` Pydantic model to include `title`, `version`, `country`, and changed `review_date` to `posted_at`.

### `agent/ingestion/appstore.py`
- Modified the RSS and HTML fallback scrapers to correctly extract and map `title`, `version`, and `country` instead of concatenating them into the review body.
- Ensured `posted_at` is populated correctly.

### `agent/ingestion/playstore.py`
- Modified the Play Store scraper to extract and map `title`, `version`, and `country`.
- Ensured `posted_at` is populated correctly.

## Phase 2: Embeddings & Clustering

### `agent/clustering/pipeline.py`
- Confirmed UMAP/HDBSCAN parameters strictly matched the architecture (`n_components=15`, `metric=cosine`, `min_cluster_size=8`).
- Updated the SQL query fetching the `product_key` from the `runs` table to query by `id` instead of `run_id` due to the Phase 0 schema change.

### `agent/clustering/embedder.py`
- Updated the `INSERT OR REPLACE INTO review_embeddings` SQL query to only include `review_id` and `embedding`, removing obsolete columns (`run_id`, `model`, `cached`) as dictated by the Phase 0 schema change.
- Removed fetching of unused column during cache check.

## Phase 3: LLM Summarization

### `agent/summarization_models.py`
- Refactored `Theme` to use `label`, `description`, `sentiment` (Literal string instead of float), and `representative_review_ids`.
- Refactored `PulseSummary` to reflect the new architecture constraints: added `window`, `stats`, decoupled `quotes` into a top-level list, and renamed `who_this_helps` to `what_this_solves`.

### `agent/summarization.py`
- Updated LLM Prompts: Enforced word counts ("under 250 words total"), exactly 1 quote per theme ("exactly 1 quote"), and exactly 3 action ideas.
- Updated pipeline logic (`Summarizer.run_summarization`) to aggregate exactly 3 verbatim quotes total across all themes.
- Added queries to compute `total_reviews` and `avg_rating` to populate the new `PulseStats` model.
- Updated database insertions for the `themes` table to match the new Phase 0 schema (`label`, `description`, `sentiment`, `representative_review_ids_json`).

## Phase 4: Document & Email Rendering

### `agent/mcp_client/docs_ops.py`
- Updated the document resolution logic to dynamically find the `endIndex` of the target Google Doc.
- Ensured idempotency logic strictly uses `[pulse-{product}-{iso_week}]` format for skipping.

### `agent/renderer/docs_tree.py`
- **Math-based Table Insertion:** Implemented precise index tracking for Google Docs API to properly generate and insert the 2-column "What This Solves" table, accounting for row, cell, and newline marker offsets natively.
- Updated all fields to reference the new `PulseSummary` schema (`top_themes`, `quotes`, `action_ideas`, `what_this_solves`).
- Changed the batch updates to append content sequentially from the bottom of the document (`endIndex - 1`) instead of forcibly overwriting index 1.

### Email Templates
- Updated `agent/renderer/email_html.py`, `email.html.j2`, and `email.txt.j2` to consume the new `Theme` fields (`label`, `description`) and calculate the `iso_week` strictly from the `window.end` boundary.

## Phase 5: Orchestration & CLI

### `agent/__main__.py`
- Updated the `ingest` command to supply `window_start` and `window_end` strings to `upsert_run` (to match Phase 0 schema changes) instead of `iso_week`.
- Updated the `reviews` SQLite insertion query to insert all new fields from the `RawReview` model (`title`, `posted_at`, `version`, `language`, `country`, `raw_json`), and explicitly added the `ingested_at` column.
- Updated the `summarize`, `render`, and `publish` commands to reference the updated `PulseSummary` schema fields (`product` instead of `product_key`, `top_themes` instead of `themes`, `theme.label` instead of `theme.name`, and calculated `iso_week`).
- Fixed Typer `OptionInfo` leaking into internal function calls by explicitly passing `to=None` when calling `publish()` inside the orchestrator.

## Phase 6: Gmail MCP Integration

### `mcp_server/server.py` & `mcp_server/gmail_tool.py`
- Added the `label` parameter to `EmailInput` and propagated it to `create_draft`.
- Implemented `get_or_create_label` in `gmail_tool.py` to idempotently resolve Gmail label IDs by name and assign them to drafts via the `labelIds` attribute on the message payload.

### `agent/mcp_client/gmail_ops.py`
- Fully aligned with the architecture spec: search for existing email via header (`X-Pulse-Run-Id`), create draft with custom header and dynamic label (`Pulse/{product}`), and conditionally send if `CONFIRM_SEND=true`.

### `agent/mcp_client/session.py`
- Increased HTTPX client timeout from 90.0s to 300.0s to accommodate Render cold-starts.

---
*Log will be updated as subsequent phases are implemented.*
