# Weekly Product Review Pulse — Architecture

## §1 System Overview

The system is an MCP-native AI agent that ingests public app store reviews, clusters and summarises them with an LLM, renders a structured report, and delivers it exclusively through Google Workspace MCP servers (Google Docs + Gmail). No direct REST calls to Google APIs are made from the agent at delivery time.

```
┌──────────────────────────────────────────────────────────────────┐
│                          Agent Process                           │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐  │
│  │Ingestion │→ │Clustering│→ │Summarization│→ │  Renderer    │  │
│  │(Phase 1) │  │(Phase 2) │  │ (Phase 3)  │  │  (Phase 4)   │  │
│  └──────────┘  └──────────┘  └────────────┘  └──────┬───────┘  │
│                                                       │          │
│                          MCP Client Layer             │          │
│                    ┌──────────────────────────────────┘          │
│                    ▼                                             │
│        ┌────────────────────┐     ┌───────────────────┐         │
│        │  Google Docs MCP   │     │   Gmail MCP       │         │
│        │    (Phase 5)       │     │   (Phase 6)       │         │
│        └────────────────────┘     └───────────────────┘         │
└──────────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
  Running Google Doc             Stakeholder Inbox
  (one per product,              (email with deep link
   dated sections)                to Doc section)
```

### Supported Products (initial scope)
- INDMoney
- Groww
- PowerUp Money
- Wealth Monitor
- Kuvera

---

## §2 Module Map

| Concern | Module path | Phase |
|---|---|---|
| CLI entry point | `agent/__main__.py` | 0 |
| Config loading | `agent/config.py` | 0 |
| Storage / schema | `agent/storage.py` | 0 |
| App Store ingestion | `agent/ingestion/appstore.py` | 1 |
| Play Store ingestion | `agent/ingestion/playstore.py` | 1 |
| PII scrubber | `agent/ingestion/pii.py` | 1 |
| Embedding provider | `agent/embeddings.py` | 2 |
| Clustering (UMAP + HDBSCAN) | `agent/clustering/pipeline.py` | 2 |
| LLM summarization | `agent/summarization.py` | 3 |
| Doc tree renderer | `agent/renderer/docs_tree.py` | 4 |
| Email renderer | `agent/renderer/email_html.py` | 4 |
| MCP session manager | `agent/mcp_client/session.py` | 5–6 |
| Google Docs MCP ops | `agent/mcp_client/docs_ops.py` | 5 |
| Gmail MCP ops | `agent/mcp_client/gmail_ops.py` | 6 |
| Orchestrator | `agent/orchestrator.py` | 7 |

> **Note:** Clustering lives inside `agent/clustering/`, not in a separate top-level `phases/` directory. The `phases/` directory is reserved for per-phase documentation (evaluations, edge cases), not production code.

---

## §3 Data Flow

### §3.1 Ingestion → Storage
```
iTunes RSS (App Store)    ─┐
                            ├→ RawReview(pydantic) → PII scrub → upsert reviews table
google-play-scraper        ─┘
                                                               ↓
                                             data/raw/{product}/{run_id}.jsonl  (audit)
```

- Review ID: `sha1(source + external_id)` — stable across re-runs
- Window: configurable, default 8–12 weeks, ISO-week aligned
- Language filter + length filter applied at ingest time (keep `en`, `len ≥ 20 chars`)

### §3.2 Clustering Pipeline
```
reviews table
    → embed (bge-small-en-v1.5 via sentence-transformers, local, zero-cost)
    → on-disk embedding cache (keyed sha1(text))
    → UMAP (n_components=15, metric=cosine)
    → HDBSCAN (min_cluster_size=8)
    → medoid selection per cluster
    → KeyBERT keyphrases (top 8 per cluster)
    → persist: review_embeddings + clusters tables
```

Noise ratio target: < 35%. Cluster count target: 4–12 per run.

> **Embedding provider:** Ships with `bge-small-en-v1.5` (local, no API key, no cost). The provider interface (`agent/embeddings.py`) supports adding alternative implementations (e.g. OpenAI) later, but only one ships initially.

### §3.3 Summarization Pipeline
```
clusters table
    → label_theme(keyphrases, medoid_reviews)     → Theme
    → select_quotes(cluster_reviews)               → Quote[]  (verbatim-validated)
    → generate_action_ideas(themes)                → ActionIdea[]
    → generate_who_this_helps(themes)              → WhoThisHelps[]  (audience→value mapping)
    → summarize_pulse(...)                         → PulseSummary (top 3 themes + quotes + actions + who_this_helps)
    → data/summaries/{run_id}.json
```

**`PulseSummary` output model includes:**
- `themes: list[Theme]` — top 3, ranked by `review_count × |sentiment_weight|`
- `quotes: list[Quote]` — verbatim-validated, per-theme
- `action_ideas: list[ActionIdea]`
- `who_this_helps: list[AudienceValue]` — 3 rows: Product, Support, Leadership with value descriptions derived from the themes

**Verbatim validator:** every `Quote.text` must be a normalised-whitespace substring of some `review.body`. Failures trigger one re-prompt; if still failing, the quote is dropped.

### §3.4 Rendering Pipeline
```
PulseSummary
    → docs_tree.py  → list[batchUpdateRequest]  + anchor string pulse-{product}-{iso_week}
    → email_html.py → HTML + plain-text  (placeholder {DOC_DEEP_LINK})
    → data/artifacts/{run_id}/doc_requests.json
    → data/artifacts/{run_id}/email.html + email.txt
```

Doc section structure (per batchUpdate mapping):
```
Heading 1:  "{Product} — Weekly Review Pulse  |  {ISO week}"  [anchor embedded]
Heading 2:  "Top Themes"
  Paragraph (Normal):  "{n}. {theme_name} — {theme_summary}"
Heading 2:  "Real User Quotes"
  Paragraph (Italic):  '"{quote_text}"'
Heading 2:  "Action Ideas"
  Paragraph (Normal):  "• {action_title}: {action_description}"
Heading 2:  "Who This Helps"
  Table (2 col):  Audience | Value  (3 data rows: Product, Support, Leadership)
```

Email body structure:
```
Subject: [Weekly Pulse] {Product} — {ISO week} — {Top theme name}
Body:
  - Greeting line
  - "Top themes this week:" header
  - Bullet list of top 3 theme names
  - "Read full report →" deep link to the Doc section ({DOC_DEEP_LINK})
  - Footer
```

### §3.5 MCP Delivery
```
docs_ops.py
    resolve_document(product)  → docId   (create once, cache)
    append_pulse_section(docId, doc_requests, anchor)
        ├── docs.get_document  → check anchor → SKIP if present (idempotency)
        ├── docs.batch_update  (insert new section)
        └── docs.get_document  → locate headingId → build deep_link
    → persist runs.gdoc_heading_id, runs.gdoc_id

gmail_ops.py
    send_pulse_email(run_id, recipients, html+text with real deep_link)
        ├── gmail.search_messages  X-Pulse-Run-Id:{run_id} → SKIP if found
        ├── gmail.create_draft     (with custom header + label Pulse/{product})
        └── if CONFIRM_SEND=true: gmail.send_message(draftId)
    → persist runs.gmail_message_id
```

`recipients` are sourced from the per-product config in `products.yaml` (see §7), with optional CLI override.

---

## §4 MCP Integration

### §4.1 MCP Server
- **Repository:** `https://github.com/saksham20189575/saksham-mcp-server`
- **Hosted at:** `https://saksham-mcp-server.onrender.com/`
- **Deployment:** Render (Blueprint from GitHub)
- **Credentials:** `credentials.json` + `token.json` stored as Render environment secrets — never committed to the agent repo

### §4.2 Session Management (`agent/mcp_client/session.py`)
- Transport: stdio locally, SSE in production
- Validates tool schemas at handshake time
- One session per MCP server; both opened by orchestrator at run start, closed at end
- Tool call failures: exponential backoff, 3 retries, then hard fail (no silent degradation)

### §4.3 Tool Usage Summary

| Phase | MCP Server | Tool | Purpose |
|---|---|---|---|
| 5 | Google Docs | `docs.search_documents` | Resolve existing product Doc |
| 5 | Google Docs | `docs.create_document` | Create Doc on first run |
| 5 | Google Docs | `docs.get_document` | Idempotency check + headingId lookup |
| 5 | Google Docs | `docs.batch_update` | Append rendered section |
| 6 | Gmail | `gmail.search_messages` | Idempotency check via custom header |
| 6 | Gmail | `gmail.create_draft` | Create draft with X-Pulse-Run-Id header |
| 6 | Gmail | `gmail.send_message` | Send draft (only if CONFIRM_SEND=true) |

---

## §5 Data Schema (SQLite)

> **Note:** Plain SQLite — no extensions required. Embeddings are stored as BLOB for caching; no vector similarity search is performed at runtime.

### `products`
```sql
product_key  TEXT PRIMARY KEY,   -- e.g. "groww"
display_name TEXT NOT NULL,
app_store_id TEXT,               -- iTunes app ID
play_store_id TEXT,              -- com.foo.bar
gdoc_id      TEXT,               -- populated after first Docs MCP run
created_at   TEXT NOT NULL
```

### `reviews`
```sql
id           TEXT PRIMARY KEY,   -- sha1(source + external_id)
product_key  TEXT REFERENCES products,
source       TEXT NOT NULL,      -- "appstore" | "playstore"
external_id  TEXT NOT NULL,
body         TEXT NOT NULL,      -- PII-scrubbed
rating       INTEGER,
review_date  TEXT NOT NULL,      -- ISO-8601
language     TEXT,
created_at   TEXT NOT NULL
```

### `review_embeddings`
```sql
review_id    TEXT PRIMARY KEY REFERENCES reviews(id),
run_id       TEXT NOT NULL,
embedding    BLOB NOT NULL,      -- float32 vector
model        TEXT NOT NULL,
cached       INTEGER NOT NULL    -- 0|1
```

### `runs`
```sql
run_id            TEXT PRIMARY KEY,   -- sha1(product_key + iso_week)
product_key       TEXT REFERENCES products,
iso_week          TEXT NOT NULL,      -- e.g. "2026-W17"
window_weeks      INTEGER NOT NULL,
status            TEXT NOT NULL,      -- pending|ingested|clustered|summarized|rendered|published|failed
gdoc_id           TEXT,
gdoc_heading_id   TEXT,
gmail_message_id  TEXT,
metrics_json      TEXT,               -- token count, cost, latencies
created_at        TEXT NOT NULL,
updated_at        TEXT NOT NULL
```

### `themes` (per run)
```sql
id               INTEGER PRIMARY KEY AUTOINCREMENT,
run_id           TEXT REFERENCES runs,
cluster_id       TEXT NOT NULL,
name             TEXT NOT NULL,
summary          TEXT NOT NULL,
review_count     INTEGER NOT NULL,
sentiment_weight REAL NOT NULL,
rank             INTEGER NOT NULL,     -- 1-indexed, top-3 surfaced in report
quotes_json      TEXT NOT NULL         -- JSON array of verbatim quote strings (validated)
```

> **`quotes_json`**: Each theme persists its validated quotes so that resuming from `summarized` status doesn't lose quote data.

### `clusters`
```sql
id              TEXT PRIMARY KEY,
run_id          TEXT REFERENCES runs,
review_ids_json TEXT NOT NULL,
keyphrases_json TEXT NOT NULL,
medoid_review_id TEXT REFERENCES reviews(id)
```

---

## §6 Run Lifecycle & Idempotency

```
run_id = sha1(product_key + iso_week)      # deterministic, collision-safe

Status transitions:
pending → ingested → clustered → summarized → rendered → published
                                                               ↑
                                                         gdoc + gmail
Any phase failure → status = "failed"; re-run resumes from last good status.
```

**Doc idempotency:** anchor string `pulse-{product}-{iso_week}` is searched in the document body before any `batch_update`. If found → skip.

**Email idempotency:** `gmail.search_messages` for `X-Pulse-Run-Id:{run_id}` before creating any draft. If found → skip.

---

## §7 Configuration

`products.yaml` (loaded via pydantic-settings):
```yaml
products:
  - key: groww
    display_name: Groww
    app_store_id: "1404310251"
    play_store_id: com.nextbillion.groww
    recipients:
      to:
        - product-team@example.com
      cc:
        - leadership@example.com
  # ... other products

defaults:
  window_weeks: 10
  embedding_model: bge-small-en-v1.5
  llm_provider: groq
  llm_model: llama3-70b-8192
  max_llm_cost_usd_per_run: 0.50
  hdbscan_min_cluster_size: 8
  confirm_send: false                    # see below
```

**`confirm_send` behavior:**
- Defaults to `false` (draft-only) in all environments.
- To send email in production, set `CONFIRM_SEND=true` **and** `PULSE_ENV=production` in `.env`.
- If `PULSE_ENV` is not `production`, `confirm_send` is forced to `false` regardless of the setting, preventing accidental sends from staging/dev.

All secrets in `.env` (never committed):
```
GROQ_API_KEY=
MCP_SERVER_URL=https://saksham-mcp-server.onrender.com/
CONFIRM_SEND=false
PULSE_ENV=development     # development | staging | production
```

---

## §8 CLI Interface

```bash
pulse init-db                                        # Phase 0
pulse ingest  --product groww --weeks 10             # Phase 1
pulse cluster --run <run_id>                         # Phase 2
pulse summarize --run <run_id>                       # Phase 3
pulse render  --run <run_id>                         # Phase 4
pulse publish --run <run_id> --target docs           # Phase 5
pulse publish --run <run_id> --target gmail          # Phase 6
pulse publish --run <run_id> --target both           # Phase 5+6
pulse run     --product groww --weeks 10             # Phase 7 (full orchestration)
pulse run     --product groww --week 2026-W15        # backfill any ISO week
```

Optional CLI overrides for email recipients:
```bash
pulse publish --run <run_id> --target gmail --to user@example.com --cc boss@example.com
```

---

## §9 Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | Best library support for ML/NLP tasks |
| Package manager | uv | Fast, reproducible |
| CLI | Typer | Clean, type-safe |
| Config | pydantic-settings | Env + YAML validation |
| Database | SQLite (stdlib) | Zero-infra; no extensions needed |
| Embeddings | bge-small-en-v1.5 (local, sentence-transformers) | Zero cost, no API key, good quality for clustering |
| Dimensionality reduction | UMAP | Preserves local structure for clustering |
| Clustering | HDBSCAN | Density-based; handles noise; no fixed K |
| Keyphrases | KeyBERT | Unsupervised, embedding-based |
| LLM | Groq (llama3-70b-8192) | Free tier, high rate limits, OpenAI-compatible |
| LLM client | openai SDK (pointed at Groq) | Portable; structured JSON output |
| Templating | Jinja2 | Doc + email rendering |
| MCP transport | stdio (local) / SSE (prod) | Per MCP spec |
| Logging | structlog | Structured JSON logs with run_id context |
| Scheduling | GitHub Actions cron | No infra; easy matrix per product |
| Deployment | Render (MCP server) + GitHub Actions (agent) | Free tier available |
| Testing | pytest + vcr.py-style mocking | Deterministic; no live calls in CI |

---

## §10 Security Model

1. **Google credentials never enter the agent repo.** `credentials.json` and `token.json` live inside the MCP server's Render environment only.
2. **LLM API keys are in `.env`** — `.gitignore`d; never pasted into prompts or committed.
3. **AI coding tools (Cursor, Antigravity) never have access to `.env`** — the file is excluded from all context by default.
4. **PII scrubbing** (regex: emails, phone numbers, Aadhaar-like patterns) is applied to `review.body` before persistence **and** before any LLM call.
5. **Prompt injection defense:** Reviews are treated as data, not instructions — system prompts explicitly instruct the LLM to ignore any command-like content in review text. All review text is placed in a clearly delimited `<reviews>` block, never interpolated into the instruction portion of the prompt.
6. **CONFIRM_SEND defaults to false** — no email is sent without explicit opt-in; non-production environments force draft mode regardless of config.

---

## §11 Repo Layout

```
/
├── agent/
│   ├── __main__.py             # CLI (Typer)
│   ├── config.py               # pydantic-settings + products.yaml
│   ├── storage.py              # SQLite schema + helpers
│   ├── orchestrator.py         # Phase 7: full pipeline
│   ├── embeddings.py           # provider interface (local bge default)
│   ├── summarization.py        # Phase 3: LLM calls + PulseSummary
│   ├── ingestion/
│   │   ├── appstore.py
│   │   ├── playstore.py
│   │   └── pii.py
│   ├── clustering/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # UMAP + HDBSCAN orchestration
│   │   ├── embedder.py         # batch embed + cache
│   │   └── keyphrases.py       # KeyBERT extraction
│   ├── renderer/
│   │   ├── docs_tree.py        # PulseSummary → batchUpdate requests
│   │   └── email_html.py       # Jinja2 → HTML + plain-text
│   └── mcp_client/
│       ├── session.py          # MCP connect/close + schema validation
│       ├── docs_ops.py         # Phase 5: Docs MCP operations
│       └── gmail_ops.py        # Phase 6: Gmail MCP operations
├── docs/
│   ├── problemStatement.md
│   ├── architecture.md         # ← this file
│   ├── implementationPlan.md
│   ├── runbook.md              # Phase 7
│   └── phases/
│       ├── phase-0-foundations/
│       │   ├── evaluations.md
│       │   └── edge-cases.md
│       ├── phase-1-ingestion/
│       │   ├── evaluations.md
│       │   └── edge-cases.md
│       └── ...                 # one folder per phase
├── tests/
│   └── fixtures/
│       ├── reviews/golden.jsonl
│       ├── clusters_golden.json
│       ├── pulse_summary_golden.json
│       ├── doc_requests_golden.json
│       └── email_golden.html
├── templates/
│   ├── doc_section.schema.json
│   └── email.html.j2
├── data/
│   ├── raw/                    # jsonl audit files (gitignored)
│   ├── summaries/              # PulseSummary JSON (gitignored)
│   └── artifacts/              # rendered doc + email (gitignored)
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── weekly-pulse.yml    # Phase 7: cron matrix
├── products.yaml
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## §12 Traceability Matrix

| Problem Statement Requirement | Phase | Exit Criterion |
|---|---|---|
| Ingest App Store + Play Store reviews (8–12 week window) | 1 | `pulse ingest` fills reviews table; fixture replay deterministic |
| PII scrubbing before storage and LLM | 1 | Regex scrubber test; no PII in DB or LLM payloads |
| Cluster and rank feedback (UMAP + HDBSCAN) | 2 | 4–12 clusters; noise < 35%; deterministic seeds |
| LLM themes, verbatim-validated quotes, action ideas | 3 | All quotes pass verbatim validator; snapshot test stable |
| "Who this helps" audience-value mapping | 3 | PulseSummary includes `who_this_helps` with 3 audience rows |
| Render one-page narrative | 4 | Golden-image test on doc_requests.json + email HTML |
| Email body includes top themes as bullets + deep link | 4 | Email template verified against spec; golden test |
| Append to running Google Doc via MCP only | 5 | Mock MCP test; real Workspace smoke test |
| Send stakeholder email via Gmail MCP only | 6 | Draft-first; send only if CONFIRM_SEND=true + PULSE_ENV=production |
| Idempotent per product + ISO week | 5, 6 | Anchor check (Docs); header search (Gmail); double-run = no-op |
| Weekly cadence + backfill CLI | 7 | GH Actions cron; `--week` flag |
| Auditable delivery identifiers | 5, 6 | `runs.gdoc_heading_id` + `runs.gmail_message_id` persisted |
| Cost cap per run | 3, 7 | `PulseCostExceeded` error; tracked in `runs.metrics_json` |
| Google credentials not in agent repo | 5, 6 | Credential handling delegated to MCP server's Render secrets |
| Reviews treated as data, not instructions (prompt injection) | 3 | System prompt + delimited review block; tested with adversarial fixtures |
| Per-product recipient configuration | 7 | `products.yaml` recipients field; CLI override; validated at config load |
| Draft-only default in non-production | 6, 7 | `PULSE_ENV` guard; staging always draft; tested |

---

## §13 Logging & Auditability

**Structured logging:** `structlog` with JSON output. Every log line includes `run_id`, `product_key`, `phase`, and `iso_week` as context fields.

**Run metrics:** `runs.metrics_json` captures per-run:
- `reviews_ingested` — count
- `clusters_formed` — count
- `llm_tokens` — prompt + completion
- `llm_cost_usd` — total
- `mcp_call_latencies` — per tool call
- `publish_status` — success | skipped | failed

**Audit trail:** `runs` table records `gdoc_heading_id`, `gmail_message_id`, and status transitions with timestamps. Sufficient to answer "what was sent when, for which week?"

**Future:** If a monitoring backend (Grafana, Datadog) is provisioned, add OpenTelemetry spans and OTLP export. Until then, structured logs + metrics JSON are the observability layer.

---

*Last updated: April 2026 | Derived from docs/problemStatement.md and docs/implementationPlan.md*