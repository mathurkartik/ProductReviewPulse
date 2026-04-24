# Phase 0 — Foundations & Scaffolding: Evaluations

## Evaluation Criteria

### E0.1 — CLI Skeleton
| # | Test | Command | Pass Condition |
|---|------|---------|----------------|
| 1 | Help output lists all subcommands | `uv run pulse --help` | Output contains: `init-db`, `ingest`, `cluster`, `summarize`, `render`, `publish`, `run` |
| 2 | Each subcommand prints its own help | `uv run pulse ingest --help` | No crash; shows `--product`, `--weeks` flags |
| 3 | Unknown subcommand fails cleanly | `uv run pulse foobar` | Exit code ≠ 0; error message printed (no traceback) |

### E0.2 — Database Initialization
| # | Test | Command | Pass Condition |
|---|------|---------|----------------|
| 1 | Fresh init creates all tables | `uv run pulse init-db` | SQLite file created; tables exist: `products`, `reviews`, `review_embeddings`, `runs`, `themes`, `clusters` |
| 2 | Schema matches architecture §5 | Inspect table schemas | Column names, types, and constraints match spec exactly |
| 3 | Re-init on existing DB is safe | Run `pulse init-db` twice | No crash; tables preserved (CREATE TABLE IF NOT EXISTS) |

### E0.3 — Configuration Loading
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | `products.yaml` parses correctly | All product keys, display names, store IDs, and recipients load into pydantic models |
| 2 | Missing `.env` key raises clear error | If `GROQ_API_KEY` is missing and needed, error message names the missing variable |
| 3 | `run_id` is deterministic | `sha1("groww" + "2026-W17")` produces the same hash every time |

### E0.4 — CI Pipeline
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Lint passes | `ruff check` returns exit code 0 |
| 2 | Type check passes | `mypy agent/` returns exit code 0 (or configured equivalent) |
| 3 | Smoke tests pass | `pytest` runs ≥ 2 tests, all green |

### E0.5 — Structured Logging
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Log output is valid JSON | Every line from `pulse init-db` parses as JSON |
| 2 | Context fields present | Log entries include `event`, `level`, `timestamp` |

## Summary Metrics

| Metric | Target |
|--------|--------|
| All subcommands registered | 7 subcommands |
| All tables created | 6 tables |
| CI green on empty repo | Yes |
| Smoke tests passing | ≥ 2 |
