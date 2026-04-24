# Phase 6 — Gmail MCP — Deliver: Edge Cases

## EC6.1 — MCP Server Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Gmail MCP server is down | Connection refused | Retry 3× with exponential backoff; then hard fail |
| 2 | MCP server returns unexpected tool list | Tool validation fails | Fail fast: "Expected tool 'gmail.create_draft' not found" |
| 3 | MCP server timeout during `send_message` | Draft created but not sent | Re-run detects the draft via `search_messages` header; skips (idempotent) |
| 4 | MCP server rate-limited by Google | 429 response | Retry with backoff; log the rate limit details |

## EC6.2 — Idempotency Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `gmail.search_messages` returns multiple matches for same `run_id` | Unexpected: should be exactly 0 or 1 | Use first match; log warning about duplicates |
| 2 | Email was manually deleted from inbox | `search_messages` returns 0; re-run sends again | Acceptable behavior: manual deletion = intent to re-send |
| 3 | `X-Pulse-Run-Id` header stripped by email server | Idempotency check fails; duplicate email possible | Document: header must survive; test with target email provider |
| 4 | Draft exists but was never sent (`CONFIRM_SEND` was false) | `search_messages` finds the draft → skip | Correct: draft counts as "sent" for idempotency |

## EC6.3 — Recipient Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | No `to` recipients configured | Error: "At least one 'to' recipient required" | Validate before attempting to create draft |
| 2 | Invalid email address in recipients | Gmail API rejects the draft | Validate email format at config load time |
| 3 | `cc` or `bcc` is empty | Draft created with only `to` field | Empty lists are valid; don't add empty cc/bcc headers |
| 4 | CLI `--to` override with multiple addresses | All addresses included | Accept comma-separated or multiple `--to` flags |
| 5 | Recipient email bounces | Bounce notification goes to sender | Out of scope for agent; document in runbook |

## EC6.4 — Deep Link Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Phase 5 failed; no `gdoc_heading_id` | `{DOC_DEEP_LINK}` cannot be replaced | Use doc-level link (without heading) as fallback; log warning |
| 2 | Deep link points to deleted heading | Link works but scrolls to wrong position | Out of scope; document: "Do not delete Doc sections" |
| 3 | `{DOC_DEEP_LINK}` placeholder not in email template | No link substitution needed | Template validation should catch missing placeholder |

## EC6.5 — Send vs Draft Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `CONFIRM_SEND=true` but `PULSE_ENV` not set | Default to `development` → forced draft-only | `PULSE_ENV` defaults to `development`; guard enforced |
| 2 | `CONFIRM_SEND` is a non-boolean string (e.g., "yes") | Treated as truthy or rejected | Strict boolean parsing: only `true`/`false` accepted |
| 3 | `gmail.send_message` fails after draft created | Draft exists but email not sent | Re-run detects draft → skip; manual send from Gmail UI |
| 4 | `gmail.create_draft` succeeds but returns no draftId | Cannot send | Log error; mark run as failed |

## EC6.6 — Email Content Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Theme name contains HTML-unsafe characters | Escaped in HTML body; raw in plain-text | `html.escape()` for HTML; raw for plain-text |
| 2 | Subject line exceeds 998-char RFC limit | Truncated | Cap subject at 200 chars |
| 3 | Email body contains non-ASCII characters (e.g., ₹, é) | Rendered correctly | UTF-8 encoding for both HTML and plain-text |
