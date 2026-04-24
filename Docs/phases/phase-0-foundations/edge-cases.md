# Phase 0 — Foundations & Scaffolding: Edge Cases

## EC0.1 — Database Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `data/` directory does not exist when `init-db` is called | Auto-create `data/` directory before creating SQLite file | `os.makedirs(exist_ok=True)` |
| 2 | SQLite file is locked by another process | Raise clear error with "database is locked" context | Catch `sqlite3.OperationalError`, log file path and PID hint |
| 3 | Disk full during table creation | Transaction rolls back; error logged | Wrap in transaction; catch `sqlite3.OperationalError` |
| 4 | Corrupt SQLite file from prior crash | `init-db` fails with integrity error | Document: user should delete and re-init; do NOT auto-delete |

## EC0.2 — Configuration Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `products.yaml` is missing | Clear error: "products.yaml not found at {path}" | Validate at startup; exit code 1 |
| 2 | `products.yaml` has duplicate product keys | Pydantic validation error listing the duplicate | Custom validator on product list |
| 3 | `products.yaml` has empty `app_store_id` or `play_store_id` | Treat as "skip that source" — not a fatal error | Nullable fields; ingestion skips if None |
| 4 | `.env` file does not exist | Non-fatal for phases 0–4 (no API keys needed); fatal for phase 3+ if LLM key missing | Lazy validation: only error when the key is actually needed |
| 5 | `PULSE_ENV` set to unknown value (e.g., "prod") | Reject with clear error listing valid values | Enum validation: `development`, `staging`, `production` |

## EC0.3 — CLI Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | User runs `pulse ingest` without `--product` flag | Typer prints usage error with required flags | Typer handles this natively |
| 2 | User runs `pulse run` with both `--weeks` and `--week` | One takes precedence or error raised | Document precedence; `--week` overrides `--weeks` |
| 3 | `run_id` collision (different product+week produces same hash) | Astronomically unlikely with SHA-1 | No mitigation needed; document the approach |

## EC0.4 — Environment Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Python version < 3.12 | Clear error at import time | `python_requires >= 3.12` in pyproject.toml |
| 2 | Running on Windows with path separators | All file paths work cross-platform | Use `pathlib.Path` throughout |
| 3 | Unicode in product names or file paths | No crashes | UTF-8 encoding throughout |
