# ProductReviewPulse — Runbook

## Overview
This runbook covers the operational procedures and troubleshooting steps for the ProductReviewPulse pipeline, which runs weekly via GitHub Actions and uses an MCP Server hosted on Render to interact with Google Docs and Gmail.

## Architecture Refresher
- **Agent**: Runs in GitHub Actions. Responsible for ingestion, clustering, summarization, and rendering.
- **MCP Server**: Runs on Render. Exposes tools to interact with Google Docs and Gmail. The agent connects via HTTP REST.
- **Database**: SQLite `pulse.sqlite`, preserved using caching or artifact storage depending on the CI/CD setup.

## 1. Pipeline Execution & Re-runs
### Backfilling or Re-running a Specific Week
If a weekly run failed or produced a bad summary, you can re-run it for any specific ISO week:
```bash
uv run pulse run --product groww --week 2026-W15 --publish-target both
```
**Safety**: The pipeline is strictly idempotent. 
- It will NOT insert duplicate reviews (uses stable IDs).
- It will NOT append a duplicate section to the Google Doc (checks for the `[pulse-...]` anchor).
- It will NOT send a duplicate email (checks the `X-Pulse-Run-Id` header).

### Triggering Manually
You can trigger the pipeline manually via the GitHub Actions "Run workflow" UI.

## 2. Troubleshooting Scenarios

### Scenario A: "Pipeline crashes with `PulseCostExceeded`"
- **Cause**: The LLM token usage exceeded the `max_llm_cost_usd_per_run` setting (default: $0.50).
- **Resolution**: 
  1. Check the number of reviews ingested. If a massive spike occurred, the clustering phase might have generated too many clusters.
  2. To unblock immediately, temporarily increase `MAX_LLM_COST_USD_PER_RUN` in the GitHub Actions Secrets or `.env` file and re-run.

### Scenario B: "MCP Server returns 500 / Connection Timeout"
- **Cause**: The Render web service might be asleep (if using a free tier) or the Google OAuth tokens expired.
- **Resolution**:
  1. Check the Render logs for the `mcp_server`. 
  2. If it's a token expiration, you must re-authenticate locally and upload the new `GOOGLE_TOKEN_JSON` to Render's environment variables.
  3. Re-run the pipeline. The agent will resume from the `rendered` status and re-attempt publishing.

### Scenario C: "Google Doc is missing or deleted"
- **Cause**: Someone deleted the target Google Doc, but the agent still has the old ID cached in SQLite.
- **Resolution**: The agent now automatically handles this by verifying the Doc ID. If it receives a 404, it will automatically create a new Doc and update the cache. Just re-run.

### Scenario D: "Ingestion returns 0 reviews"
- **Cause**: App Store/Play Store APIs might be rate-limiting, or the product hasn't received reviews.
- **Resolution**: 
  - If expected (low volume app), ignore.
  - If unexpected, run `uv run pulse ingest --product <key> --weeks 12` locally to see the stack trace or HTTP errors.

### Scenario E: "Emails are not being sent (stuck in Drafts)"
- **Cause**: The environment variable `CONFIRM_SEND` is not set to `true`, or `PULSE_ENV` is not `production`.
- **Resolution**: Ensure the GitHub Action has `AUTO_APPROVE=true` (or `CONFIRM_SEND=true`) and `PULSE_ENV=production`.
