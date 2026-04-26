# Agent Context — Product Review Pulse

## 1. What is this project?
Product Review Pulse is an automated, AI-driven weekly "pulse" pipeline designed to monitor user sentiment for 5 major fintech apps (INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera). 

Instead of relying on manual reading, this system:
1. Automatically ingests hundreds of App Store and Play Store reviews.
2. Uses machine learning (Embeddings, HDBSCAN) to group reviews into distinct clusters.
3. Uses an LLM (Llama-3 via Groq) to label the themes, extract representative quotes, and generate actionable insights for product teams.
4. Distributes these insights across three platforms: **Google Docs**, **Gmail**, and a live **Web Dashboard**.

## 2. How does it work? (The Architecture)
The project is built on a split architecture to ensure fast, free AI processing while maintaining a permanent, accessible live dashboard.

| Layer | Responsibility | Hosted On |
|---|---|---|
| **Pipeline Agent** | Fetches reviews, runs ML clustering, queries the LLM, and orchestrates the updates. Produces a local SQLite database. | **GitHub Actions** (Runs weekly on a schedule) |
| **MCP Server & Data API** | Provides a secure bridge to Google Workspace (Docs/Gmail) using Model Context Protocol (MCP). It also hosts the central SQLite database and exposes the `/api/pulse/latest` endpoint. | **Render** (FastAPI Python Server) |
| **Live Dashboard** | A Next.js frontend that fetches the latest JSON payload from the Render API to display themes, quotes, and metrics in real-time. | **Vercel** (Next.js Application) |

### The "Sync" Mechanism
Because the heavy ML pipeline runs on ephemeral GitHub Action servers, the resulting `pulse.sqlite` database is temporarily lost when the run finishes. To solve this, the last step of the GitHub Action automatically **syncs (uploads)** the newly generated database directly to the Render server via a secure `POST /api/sync/db` endpoint. This ensures the live Dashboard always has the latest data.

## 3. How is it getting executed?
The entire system is completely zero-touch and automated:
1. **Cron Trigger:** Every Monday at 07:00 IST (or via manual "Run workflow" trigger), **GitHub Actions** spins up an Ubuntu server.
2. **Data Ingestion:** The `pulse run` CLI command starts. It pulls the last 8-12 weeks of reviews for the specified app.
3. **AI Processing:** It uses local sentence-transformers to embed reviews, HDBSCAN to cluster them, and the Groq LLM to summarize the clusters.
4. **Publishing (MCP):** The agent makes an HTTP request to the **Render Server**, instructing it to:
   - Append a new section to the company's running Google Doc.
   - Create a draft email in the stakeholder's Gmail account containing a deep-link to the Doc.
5. **Database Sync:** The agent uploads the updated `pulse.sqlite` file to Render using the `SYNC_API_KEY`.
6. **Dashboard Update:** The **Vercel Dashboard** immediately reflects the new data for any user who visits the site.

## 4. Tech Stack Breakdown
| Component | Technology |
|---|---|
| Language | Python 3.12, uv |
| Web Framework (Frontend) | Next.js (React), hosted on Vercel |
| API / MCP Server | FastAPI, hosted on Render |
| Database | SQLite (`pulse.sqlite`) |
| Embeddings | `bge-small-en-v1.5` (local, sentence-transformers) |
| Clustering | UMAP + HDBSCAN + KeyBERT |
| LLM | Groq `llama3-70b-8192` via OpenAI SDK |
| CI/CD & Orchestration | GitHub Actions |

## 5. Phase Build Status
| Phase | Name | Status |
|---|---|---|
| 0 | Foundations & Scaffolding | COMPLETED |
| 1 | Review Ingestion | COMPLETED |
| 2 | Embeddings & Clustering | COMPLETED |
| 3 | LLM Summarization | COMPLETED |
| 4 | Report & Email Rendering | COMPLETED |
| 5 | Google Docs MCP — Append | COMPLETED |
| 6 | Gmail MCP — Deliver | COMPLETED |
| 7 | Dashboard & DB Sync | COMPLETED |

## 6. How to Run Locally
```bash
uv sync
uv run pulse init-db
# Run the full pipeline for a specific product:
uv run pulse run --product groww --weeks 12
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
