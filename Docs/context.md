# Agent Context — Weekly Review Pulse

## 1. What is this project?
**Weekly Review Pulse** is an automated, AI-driven weekly "pulse" pipeline designed to monitor user sentiment for major fintech apps (INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera). 

Instead of relying on manual reading, this system:
1. **Intelligent Ingestion:** Automatically ingests hundreds of App Store and Play Store reviews, applying real-time language filtering (`langdetect`) to focus on English-only feedback.
2. **ML Clustering:** Uses machine learning (Embeddings, HDBSCAN) to group reviews into distinct clusters.
3. **Thematic Deduplication:** Employs cosine similarity post-processing to merge highly similar themes, ensuring a clean and concise report.
4. **LLM Insights:** Uses flagship LLMs (**Llama-3.3 70B** via Groq) to label themes, extract verbatim representative quotes, and generate actionable insights citing specific user evidence.
5. **Delta Tracking:** Automatically calculates rating changes (**Deltas**) compared to previous weeks to highlight sentiment trends.
6. **Multi-Channel Distribution:** Distributes these insights across **Google Docs**, **Gmail**, and a live **Web Dashboard**.

## 2. How does it work? (The Architecture)
The project is built on a split architecture to ensure fast, free AI processing while maintaining a permanent, accessible live dashboard.

| Layer | Responsibility | Hosted On |
|---|---|---|
| **Pipeline Agent** | Fetches reviews, runs ML clustering, queries the LLM, and orchestrates the updates. Produces a local SQLite database and CSV audit trails. | **GitHub Actions** (Runs weekly on a schedule) |
| **MCP Server & Data API** | Provides a secure bridge to Google Workspace (Docs/Gmail) using Model Context Protocol (MCP). It also hosts the central SQLite database and exposes the `/api/pulse/latest` endpoint. | **Render** (FastAPI Python Server) |
| **Live Dashboard** | A Next.js frontend that fetches the latest JSON payload from the Render API to display themes, quotes, and metrics in real-time. | **Vercel** (Next.js Application) |

### The "Sync" Mechanism
Because the heavy ML pipeline runs on ephemeral GitHub Action servers, the resulting `pulse.sqlite` database is temporarily lost when the run finishes. To solve this, the last step of the GitHub Action automatically **syncs (uploads)** the newly generated database directly to the Render server via a secure `POST /api/sync/db` endpoint. This ensures the live Dashboard always has the latest data.

## 3. How is it getting executed?
The entire system is completely zero-touch and automated:
1. **Cron Trigger:** Every Monday at 07:00 IST (or via manual "Run workflow" trigger), **GitHub Actions** spins up an Ubuntu server.
2. **Data Ingestion:** The `pulse run` CLI command starts. It pulls the last 10 weeks of reviews, filtering for English and exporting a CSV for audit.
3. **AI Processing:** It uses local sentence-transformers to embed reviews, HDBSCAN to cluster them, and Llama 3.3 70B to summarize. Deduplication merges similar themes.
4. **Publishing (MCP):** The agent makes an HTTP request to the **Render Server**, instructing it to:
   - Append a new section to the company's running Google Doc (including Rating Delta).
   - Create a draft email in the stakeholder's Gmail account with the summary and deep-links.
5. **Database Sync:** The agent uploads the updated `pulse.sqlite` file to Render.
6. **Dashboard Update:** The **Vercel Dashboard** reflects the new themes and quotes immediately.

## 4. Tech Stack Breakdown
| Component | Technology |
|---|---|
| Language | Python 3.12, uv |
| Web Framework (Frontend) | Next.js (React), hosted on Vercel |
| API / MCP Server | FastAPI, hosted on Render |
| Database | SQLite (`pulse.sqlite`) |
| Embeddings | `bge-small-en-v1.5` (local, sentence-transformers) |
| Clustering | UMAP + HDBSCAN + Cosine Deduplication |
| LLM | Groq **Llama-3.3-70b-versatile** via OpenAI SDK |
| CI/CD & Orchestration | GitHub Actions |

## 5. Recent Improvements (April 2026)
1. **Language Filtering:** Immediate post-ingestion filtering using `langdetect` to skip non-English reviews.
2. **Advanced Prompting:** Verbatim quote extraction (max 150 chars) and structured Action Ideas with specific feature recommendations.
3. **Theme Deduplication:** Post-processing merge logic for themes with >80% similarity based on embedding dot products.
4. **Rating Delta Tracking:** Automated calculation and visual display (⬆/⬇) of rating changes vs the previous published week.
5. **CSV Export:** Automated export of ingested data to `data/raw/{product}_{run_id}.csv` for audit trails.
6. **Branding Revamp:** Complete transition from *FinPulse* to **Weekly Review Pulse** across all surfaces.

## 6. How to Run Locally
```bash
uv sync
uv run pulse init-db
# Run the full pipeline for a specific product:
uv run pulse run --product groww --weeks 10
```

## 7. Key Environment Variables
**Render (Backend):**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (For Google API Access)
- `SYNC_API_KEY` (To authorize DB uploads from GitHub)

**GitHub Actions:**
- `GROQ_API_KEY` (For LLM processing)
- `MCP_SERVER_URL` (URL of the Render backend)
- `SYNC_API_KEY` (Matches the Render key)

**Vercel (Frontend):**
- `NEXT_PUBLIC_API_URL` (URL of the Render backend)
