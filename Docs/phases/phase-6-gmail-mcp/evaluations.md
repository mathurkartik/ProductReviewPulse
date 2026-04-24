# Phase 6 — Gmail MCP — Deliver: Evaluations

## Evaluation Criteria

### E6.1 — Email Idempotency
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | First run creates draft | `gmail.create_draft` called with correct headers and body |
| 2 | Second run is a no-op | `gmail.search_messages` finds `X-Pulse-Run-Id:{run_id}` → skip |
| 3 | Custom header present | Draft includes `X-Pulse-Run-Id` header with correct `run_id` |
| 4 | Label applied | Draft has label `Pulse/{product}` |

### E6.2 — Draft vs Send Behavior
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Default mode: draft only | `CONFIRM_SEND=false` → `gmail.create_draft` called; `gmail.send_message` NOT called |
| 2 | Production send mode | `CONFIRM_SEND=true` + `PULSE_ENV=production` → `gmail.send_message(draftId)` called |
| 3 | Non-production guard | `CONFIRM_SEND=true` + `PULSE_ENV=staging` → forced to draft-only; warning logged |
| 4 | Non-production guard (dev) | `CONFIRM_SEND=true` + `PULSE_ENV=development` → forced to draft-only |

### E6.3 — Email Content
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Subject line correct | `[Weekly Pulse] {Product} — {ISO week} — {Top theme name}` |
| 2 | Body contains theme bullets | All 3 top themes listed as bullet points |
| 3 | Deep link substituted | `{DOC_DEEP_LINK}` replaced with actual Google Docs heading link from Phase 5 |
| 4 | HTML and plain-text versions | Both provided in the draft |

### E6.4 — Recipients
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Default recipients from `products.yaml` | `to` and `cc` fields match product config |
| 2 | CLI override works | `--to user@test.com --cc boss@test.com` overrides YAML config |
| 3 | Empty recipient list | Error raised: "No recipients configured for product" |

### E6.5 — Persistence
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | `runs.gmail_message_id` populated | DB field contains the Gmail message/draft ID |
| 2 | Run status updated | `runs.status` = `'published'` after both Docs + Gmail succeed |

### E6.6 — Mock MCP Integration Test
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | First run: draft → send | Mock records `create_draft` + `send_message` calls |
| 2 | Second run: skip | Mock records only `search_messages`; no draft/send |
| 3 | `gmail_message_id` populated exactly once | DB check confirms single ID |

### E6.7 — Real Workspace Smoke Test
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Email arrives in test inbox | Subject, body, and deep link all correct |
| 2 | Deep link jumps to Doc heading | Clicking "Read full report →" navigates to correct section |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Idempotent double-run | No-op on second run |
| Draft-only in non-production | Enforced |
| Deep link accuracy | Points to correct heading |
| `gmail_message_id` persisted | Yes |
| Recipient override working | Yes |
