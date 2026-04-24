# Phase 1 — Review Ingestion: Evaluations

## Evaluation Criteria

### E1.1 — Data Volume & Source Coverage
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Play Store ingestion returns reviews | `pulse ingest --product groww` yields ≥ 200 Play Store reviews |
| 2 | App Store ingestion returns reviews | ≥ 1 App Store review ingested (RSS or HTML fallback) |
| 3 | Both sources tagged correctly | `SELECT DISTINCT source FROM reviews` returns `appstore`, `playstore` |
| 4 | 12-week window respected | No `review_date` older than 12 weeks from run time |

### E1.2 — Filtering Pipeline
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Non-English reviews excluded | No reviews with `language != 'en'` in DB |
| 2 | Short reviews excluded | Every `body` in DB has ≥ 3 words |
| 3 | Emoji reviews excluded | No review body contains emoji characters |
| 4 | Filter counts logged | Structured log shows count of filtered-out reviews |

### E1.3 — PII Scrubbing
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Email addresses scrubbed | Input `"contact me at john@test.com"` → `"contact me at [EMAIL]"` |
| 2 | Phone numbers scrubbed | Input `"call 9876543210"` → `"call [PHONE]"` |
| 3 | Aadhaar patterns scrubbed | Input `"my aadhaar 1234 5678 9012"` → `"my aadhaar [AADHAAR]"` |
| 4 | Clean text unchanged | Input `"great app, love it"` → identical output |

### E1.4 — Idempotency & Dedup
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Review ID is deterministic | `sha1("appstore" + external_id)` produces same hash across runs |
| 2 | Re-run produces 0 new inserts | Running `pulse ingest` twice → second run inserts 0 new rows |
| 3 | `run_id` is deterministic | Same product + ISO week → same `run_id` |

### E1.5 — Audit Trail
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | JSONL audit file created | `data/raw/{product}/{run_id}.jsonl` exists after ingestion |
| 2 | JSONL line count matches DB count | Lines in JSONL = rows inserted/updated in reviews table |
| 3 | Run status updated | `runs.status` = `'ingested'` after successful run |

### E1.6 — Fixture Replay (CI)
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Canned HTTP responses produce deterministic snapshot | Feed pre-recorded App Store + Play Store responses → exact same review set |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Total reviews ingested (Groww) | ≥ 5,000 |
| App Store reviews | ≥ 100 |
| Play Store reviews | ≥ 4,000 |
| PII patterns caught | 3 types (email, phone, Aadhaar) |
| Idempotent re-run inserts | 0 |
