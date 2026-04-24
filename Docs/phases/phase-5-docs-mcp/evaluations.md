# Phase 5 — Google Docs MCP — Append: Evaluations

## Evaluation Criteria

### E5.1 — MCP Session Management
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Session connects successfully | `session.py` connects to MCP server; handshake completes |
| 2 | Tool schemas validated | Available tools match expected: `docs.search_documents`, `docs.create_document`, `docs.get_document`, `docs.batch_update` |
| 3 | Session closes cleanly | No orphan connections after `publish` completes |
| 4 | Connection failure retries | 3 retries with exponential backoff before hard fail |

### E5.2 — Document Resolution
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Existing doc found | `resolve_document("groww")` returns cached `docId` if product has `gdoc_id` |
| 2 | New doc created on first run | If no `gdoc_id`, `docs.create_document` called; ID persisted to `products.gdoc_id` |
| 3 | Doc search by title | `docs.search_documents` finds doc by product display name |

### E5.3 — Idempotent Section Append
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | First run appends section | `docs.batch_update` called with rendered requests; new heading visible |
| 2 | Second run is a no-op | Anchor `pulse-{product}-{iso_week}` detected in doc body → skip |
| 3 | Anchor string present in heading | `docs.get_document` confirms anchor in Heading 1 text |

### E5.4 — Deep Link Generation
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | `headingId` extracted | After `batch_update`, `docs.get_document` returns the new heading's ID |
| 2 | Deep link built correctly | Format: `https://docs.google.com/document/d/{docId}/edit#heading=h.{headingId}` |
| 3 | `runs.gdoc_heading_id` persisted | DB field populated after successful append |
| 4 | `runs.gdoc_id` persisted | DB field populated |

### E5.5 — Mock MCP Integration Test
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Mock server records correct requests | JSON-RPC calls match expected tool names and parameters |
| 2 | First run → append; second run → skip | Two sequential runs produce exactly 1 `batch_update` call |

### E5.6 — Real Workspace Smoke Test
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Report renders in Google Doc | Headings, bullets, italic quotes, table visible |
| 2 | Deep link navigates to correct section | Clicking link scrolls to the new heading |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Idempotent double-run | No-op on second run |
| Deep link accuracy | Navigates to correct heading |
| MCP retry resilience | 3 retries on failure |
| `gdoc_heading_id` persisted | Yes |
