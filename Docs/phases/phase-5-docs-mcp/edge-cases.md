# Phase 5 — Google Docs MCP — Append: Edge Cases

## EC5.1 — MCP Server Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | MCP server is down | Connection refused | Retry 3× with exponential backoff; then hard fail with clear error |
| 2 | MCP server returns malformed JSON-RPC | Parse error | Catch `JSONDecodeError`; log raw response; fail |
| 3 | MCP server tool schema has changed | Tool validation fails at handshake | Fail fast: "Expected tool 'docs.batch_update' not found" |
| 4 | MCP server times out mid-request | Hanging connection | 30-second timeout per tool call; retry once |
| 5 | MCP server returns partial success | Some requests applied, some not | Treat as failure; re-run will detect anchor and skip (idempotent) |

## EC5.2 — Document Resolution Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `docs.search_documents` returns multiple matches | Ambiguous doc resolution | Use first match; log warning with all matches |
| 2 | `docs.create_document` fails (quota, permissions) | No doc created | Fail with descriptive error; suggest checking MCP server credentials |
| 3 | Cached `gdoc_id` in DB points to a deleted document | `docs.get_document` returns 404 | Clear cached `gdoc_id`; create new document |
| 4 | Product has never had a doc created | `gdoc_id` is NULL | Trigger `docs.create_document`; persist new ID |

## EC5.3 — Idempotency Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Anchor string appears in a review quote (not a heading) | False positive: system thinks section already exists | Use unique prefix: `pulse-{product}-{iso_week}` unlikely in review text |
| 2 | Anchor check succeeds but section is partially rendered | Incomplete section in doc | Accept: anchor present = skip; manual fix needed for partial sections |
| 3 | Doc was manually edited to remove the anchor | Re-run will re-append (duplicate section) | Document: "Do not edit anchor text in Google Doc" |
| 4 | `docs.get_document` returns stale cached version | Anchor not detected; duplicate append | Google Docs API returns live content; caching unlikely |

## EC5.4 — batchUpdate Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | batchUpdate request exceeds API size limit | Request rejected | Split into multiple smaller batchUpdate calls if needed |
| 2 | batchUpdate contains invalid character for Docs | API error on specific request | Sanitize text: remove null bytes, control characters |
| 3 | Heading ID extraction fails (heading not found after insert) | `gdoc_heading_id` is NULL | Log warning; deep link will be empty; email sent without link |
| 4 | Concurrent batchUpdate from two runs | Race condition on document | `run_id` is deterministic; same run won't run twice concurrently |

## EC5.5 — Credential Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Google OAuth token expired | MCP server returns 401 | MCP server handles token refresh; agent sees error only if refresh fails |
| 2 | Google credentials revoked | All Docs API calls fail | Fail with: "MCP server authentication failed; check Render secrets" |
| 3 | Wrong Google account (no access to target doc) | Permission denied on `docs.get_document` | Fail with descriptive error |
