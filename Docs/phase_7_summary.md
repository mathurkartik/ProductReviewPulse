# Phase 7: Deployment & Dashboard Integration (Summary)

## Objective
To provide a live, real-time dashboard of the Weekly Pulse data while maintaining the serverless ML architecture, and to stabilize the Google Workspace integrations on a persistent Render environment.

## What was built:

### 1. Render MCP Server Enhancements
- Rebuilt the `auth.py` flow to securely accept individual `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` environment variables directly from Render, bypassing the need for physical `credentials.json` files on the cloud filesystem.
- Added a new `GET /api/pulse/{run_id}` REST API directly to the MCP Server. Since the MCP server is already a FastAPI instance, it now also serves as the Data API for the frontend dashboard.
- Added a secure `POST /api/sync/db` endpoint (protected by `SYNC_API_KEY`) to receive the SQLite database from the GitHub Actions runner.

### 2. Next.js Dashboard (Vercel)
- The static demo dashboard (`frontend-next/src/app/page.tsx`) was refactored into a fully dynamic React Client Component.
- It now fetches data from the Render API endpoint via `NEXT_PUBLIC_API_URL` and dynamically renders the `Top Themes`, `Quotes`, and `Operational Insights` using the real ML clustering data.

### 3. CI/CD Pipeline Automation
- Updated `.github/workflows/weekly-pulse.yml` with a new "Sync Database to Render" step.
- After a successful ML run, the GitHub Action automatically sends the fresh `pulse.sqlite` to the Render server.
- This creates a completely automated workflow: 
  `Ingest → Cluster → Summarize → Render to Google Docs/Gmail → Sync DB to Render → Vercel Dashboard Updates`.

## How it gets executed:
1. Every Monday at 07:00 IST (or via manual trigger), the **GitHub Action** spins up an Ubuntu runner.
2. The agent fetches the latest App Store and Play Store reviews.
3. The LLM (via Groq API) summarizes and clusters the data, storing everything in `pulse.sqlite`.
4. The agent calls the **Render MCP Server** (`/docs.batch_update` and `/gmail.create_draft`) to publish the report to Google Workspace.
5. Upon successful publishing, the agent uploads the `pulse.sqlite` file to Render via the `/api/sync/db` endpoint.
6. A user visits the **Vercel Dashboard URL**, which calls Render, reads the SQLite file, and displays the latest insights in real-time.
