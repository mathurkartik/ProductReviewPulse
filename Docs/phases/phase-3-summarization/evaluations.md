# Phase 3 — LLM Summarization: Evaluations

## Evaluation Criteria

### E3.1 — Theme Generation
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Top 3 themes produced | `PulseSummary.themes` has exactly 3 entries |
| 2 | Themes ranked correctly | Ranked by `review_count × |sentiment_weight|` descending |
| 3 | Theme names are human-readable | Manual spot-check: concise, descriptive, not generic |
| 4 | Theme summaries are coherent | Each summary describes the cluster's feedback accurately |

### E3.2 — Verbatim Quote Validation
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | All quotes pass verbatim check | Every `Quote.text` is a normalized-whitespace substring of a real `review.body` |
| 2 | Failed quotes trigger re-prompt | If first LLM attempt returns invalid quote, one retry occurs |
| 3 | Persistent failures are dropped | After re-prompt, still-invalid quotes are excluded (not silently kept) |
| 4 | Quotes attributed to correct theme | Each quote belongs to a review in the corresponding cluster |

### E3.3 — Action Ideas
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Action ideas generated | `PulseSummary.action_ideas` has ≥ 1 entry |
| 2 | Actions are actionable | Manual spot-check: each has a clear title and description |
| 3 | Actions derived from themes | Actions reference or relate to the identified themes |

### E3.4 — Who This Helps
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Three audience rows | `who_this_helps` contains exactly 3 entries: Product, Support, Leadership |
| 2 | Value descriptions are specific | Each row has a non-empty, theme-derived value description |

### E3.5 — PII Re-Scrub
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | No PII in LLM prompts | Review text sent to LLM has PII scrubbed (already done at ingest; re-verified here) |
| 2 | No PII in LLM responses | Output summaries and quotes do not contain email/phone/Aadhaar patterns |

### E3.6 — Cost & Token Tracking
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Token counts tracked | `runs.metrics_json` includes `llm_tokens` (prompt + completion) |
| 2 | Cost tracked | `runs.metrics_json` includes `llm_cost_usd` |
| 3 | Cost cap enforced | Exceeding `max_llm_cost_usd_per_run` raises `PulseCostExceeded` |

### E3.7 — Persistence & Status
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | PulseSummary written to disk | `data/summaries/{run_id}.json` exists |
| 2 | Themes table populated | `themes` table has ≥ 3 rows for this run |
| 3 | Run status updated | `runs.status` = `'summarized'` |
| 4 | Snapshot test stable | Mocked LLM → PulseSummary JSON is byte-stable across runs |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Themes produced | 3 (top-ranked) |
| Verbatim quote pass rate | 100% (after retry + drop) |
| Audience-value rows | 3 |
| Cost cap enforcement | Yes |
| Snapshot stability (mocked LLM) | Byte-identical |
