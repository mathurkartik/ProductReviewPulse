# Phase 7 — Orchestration, Scheduling & Hardening: Edge Cases

## EC7.1 — Orchestrator Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Run fails at `ingested` status (clustering crashes) | `runs.status` = `'failed'`; re-run resumes from `ingested` | Status-based checkpoint: skip completed phases |
| 2 | Run fails at `rendered` status (MCP server down) | Re-run skips ingest/cluster/summarize/render; retries publish | Same checkpoint logic |
| 3 | `runs.status` is in unknown state | Error: "Unknown run status: {status}" | Validate status against known enum before proceeding |
| 4 | Two `pulse run` commands for same product+week simultaneously | SQLite lock prevents corruption; one waits or errors | Acceptable: SQLite serializes; second run detects existing `run_id` |
| 5 | Orchestrator called with product not in `products.yaml` | Error before any phase executes | Validate product key at start |
| 6 | All phases succeed but metrics write fails | Run marked as published; metrics lost | Metrics write in `finally` block; log error but don't fail the run |

## EC7.2 — Scheduling Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | GitHub Actions cron fires twice in same week | Second run is a no-op (idempotent `run_id`) | `run_id = sha1(product_key + iso_week)` ensures dedup |
| 2 | GitHub Actions cron misses a week (outage) | That week's report is never generated | Manual backfill: `pulse run --product groww --week 2026-W15` |
| 3 | Workflow matrix product list out of sync with `products.yaml` | Some products skipped or unknown products attempted | Generate matrix from `products.yaml` dynamically, or document sync requirement |
| 4 | GitHub Actions runner has no internet | All network-dependent phases fail | Fail fast with clear error; retry on next cron trigger |
| 5 | Secrets not configured in GitHub | `GROQ_API_KEY` empty → Phase 3 fails | Fail at first LLM call with: "GROQ_API_KEY not set" |
| 6 | IST vs UTC cron confusion | Cron fires at wrong local time | Document: cron is UTC; `07:00 IST = 01:30 UTC` |

## EC7.3 — Backfill Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Backfilling a future week | Reviews may not exist yet; ingestion returns 0 | Log warning: "No reviews found for future week {week}" |
| 2 | Backfilling a very old week (> 1 year ago) | Store APIs may not have historical reviews | Ingest whatever is available; may be 0 reviews |
| 3 | Backfilling multiple weeks in sequence | Each week gets its own `run_id` and independent pipeline | Works correctly; each run is independent |
| 4 | `--week` format is invalid (e.g., "2026-15") | Parse error | Validate ISO week format: `YYYY-Www`; reject with example |
| 5 | `--week` and `--weeks` both provided | Conflict | `--week` takes precedence; `--weeks` ignored with warning |

## EC7.4 — Cost Control Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Cost cap set to $0.00 | No LLM calls allowed; Phase 3 immediately fails | Validate: cost cap must be > 0; or skip summarization with warning |
| 2 | LLM provider changes pricing | Cost calculation is inaccurate | Use response `usage` field for actual tokens; update pricing table periodically |
| 3 | Multiple retries inflate cost | Each retry adds to cumulative cost | Cost check before each call, including retries |
| 4 | Cost cap exceeded on final LLM call | Partial summary produced | Fail the entire summarization; don't persist partial results |

## EC7.5 — Alerting Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | First run ever (no prior week to compare) | No WoW comparison possible | Skip WoW alerts on first run; log "No prior week for comparison" |
| 2 | Prior week had 0 reviews (e.g., new product) | Division by zero in WoW calculation | Guard: if prior_count == 0, skip percentage calculation |
| 3 | Alert threshold met but no alerting backend configured | Warning logged to structured logs only | Acceptable: logs are the minimum alerting layer |
| 4 | Multiple alerts fire simultaneously | All logged independently | Each alert is a separate log entry with its own context |

## EC7.6 — Resilience Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | MCP server crashes during `docs.batch_update` | Partial document update | Re-run: anchor check detects partial (or complete) section; handles accordingly |
| 2 | Agent process killed (SIGKILL) mid-pipeline | `runs.status` may be stale | Re-run detects status and resumes; worst case: re-does the current phase |
| 3 | SQLite file corruption | All queries fail | Documented recovery: delete `pulse.db`, re-init, re-run from scratch |
| 4 | Disk full during any write | Write fails | Catch `OSError`; log disk usage; fail with actionable message |
| 5 | Python dependency conflict after update | Import errors | Pin all dependencies in `pyproject.toml`; use `uv.lock` |

## EC7.7 — Runbook Scenarios

| # | Scenario | Documented Resolution |
|---|----------|-----------------------|
| 1 | "Email not sent" | Check `CONFIRM_SEND` + `PULSE_ENV`; check `runs.gmail_message_id`; check MCP server logs |
| 2 | "Duplicate section in Doc" | Anchor was manually deleted; remove duplicate manually; re-run is safe |
| 3 | "Ingestion empty" | Check store IDs in `products.yaml`; check network; check if store API changed |
| 4 | "LLM cost spike" | Check `runs.metrics_json`; review prompt sizes; adjust `max_llm_cost_usd_per_run` |
| 5 | "MCP server crash" | Check Render dashboard; redeploy MCP server; re-run agent |
| 6 | "Token revoked" | Re-authenticate on MCP server's Render instance; update secrets |
