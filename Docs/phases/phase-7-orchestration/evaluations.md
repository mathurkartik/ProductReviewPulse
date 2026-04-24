# Phase 7 — Orchestration, Scheduling & Hardening: Evaluations

## Evaluation Criteria

### E7.1 — Full Pipeline Orchestration
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | `pulse run` chains all phases | Single command executes: ingest → cluster → summarize → render → publish |
| 2 | Status checkpoints work | Each phase updates `runs.status`; crash mid-pipeline resumes from last good status |
| 3 | Resume from failure | If run failed at `clustered`, re-running starts from `summarize` (not from scratch) |
| 4 | Full run completes in < 5 minutes | On staging Workspace with mocked MCP, end-to-end < 5 min |

### E7.2 — Scheduling (GitHub Actions)
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Cron schedule correct | `.github/workflows/weekly-pulse.yml` triggers Monday 07:00 IST |
| 2 | Matrix per product | Workflow runs once per product in `products.yaml` |
| 3 | Dry-run passes in CI | Workflow with mocked MCP servers completes without error |
| 4 | Secrets configured | `GROQ_API_KEY`, `MCP_SERVER_URL` available as GitHub secrets |

### E7.3 — Backfill CLI
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Backfill specific week | `pulse run --product groww --week 2026-W15` runs successfully |
| 2 | Backfill is idempotent | Running same `--week` twice is a no-op at every phase |
| 3 | Backfill uses correct window | Review window anchored to the specified ISO week, not current date |

### E7.4 — Observability
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Structured logs have `run_id` context | Every log line includes `run_id`, `product_key`, `iso_week` |
| 2 | Run metrics captured | `runs.metrics_json` includes: `reviews_ingested`, `clusters_formed`, `llm_tokens`, `llm_cost_usd` |
| 3 | MCP call latencies tracked | `mcp_call_latencies` field populated in metrics JSON |
| 4 | Publish status tracked | `publish_status` = `success`, `skipped`, or `failed` |

### E7.5 — Cost Controls
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Per-run cost cap enforced | Exceeding `max_llm_cost_usd_per_run` raises `PulseCostExceeded` |
| 2 | Cost tracked in metrics | `llm_cost_usd` accurately reflects actual token usage |
| 3 | Cost cap is configurable | `products.yaml` → `defaults.max_llm_cost_usd_per_run` |

### E7.6 — Alerting Thresholds
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Ingestion drop > 50% WoW | Alert/warning logged when review count drops > 50% vs prior week |
| 2 | Average rating delta > 1.0 | Alert/warning logged for significant rating shift |
| 3 | LLM schema validation failure rate > 2% | Alert/warning when too many LLM responses fail validation |
| 4 | MCP call error rate > 1% | Alert/warning for MCP reliability issues |

### E7.7 — Resilience
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | MCP server killed mid-run | Orchestrator retries; second run completes and is idempotent |
| 2 | Network blip during ingestion | Retry logic handles transient failures |
| 3 | Partial pipeline failure | Status reflects last successful phase; re-run resumes |

## Summary Metrics

| Metric | Target |
|--------|--------|
| End-to-end run time (staging) | < 5 minutes |
| Resume from failure | Correct checkpoint |
| Backfill idempotency | No-op on duplicate week |
| Cost cap enforcement | Yes |
| Alert thresholds | 4 conditions monitored |
| MCP crash recovery | Retry + idempotent re-run |
