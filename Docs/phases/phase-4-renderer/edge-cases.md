# Phase 4 — Report & Email Rendering: Edge Cases

## EC4.1 — Doc Rendering Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | PulseSummary has fewer than 3 themes | Render only the themes available (1 or 2) | Template iterates over `themes` list; no hardcoded count |
| 2 | Theme name contains special characters (e.g., `&`, `<`, `"`) | Characters escaped properly in batchUpdate JSON | JSON serialization handles escaping |
| 3 | Quote text contains newlines | Rendered as multi-line paragraph | batchUpdate text allows `\n`; render as-is |
| 4 | Quote text is extremely long (> 500 chars) | Rendered in full; no truncation | Google Docs handles long paragraphs |
| 5 | Action ideas list is empty | "Action Ideas" section rendered with "No action ideas for this period" | Template has fallback text |
| 6 | Who This Helps has missing audience | Table rendered with available rows | Template iterates; missing rows simply not rendered |
| 7 | Product name contains Unicode | Heading renders correctly | UTF-8 throughout |
| 8 | ISO week string format varies | Anchor still works | Normalize to `YYYY-Www` format |

## EC4.2 — Email Rendering Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Top theme name is very long (> 100 chars) | Subject line may be truncated by email clients | Truncate theme name to 60 chars in subject with `...` |
| 2 | HTML contains characters that break email clients | Rendering issues in Outlook/Gmail | Test with common email clients; use inline CSS only |
| 3 | Plain-text version missing theme bullets | Incomplete plain-text fallback | Generate plain-text from same data source; not by stripping HTML |
| 4 | `{DOC_DEEP_LINK}` placeholder not replaced before send | Broken link in email | Phase 6 replaces placeholder; Phase 4 validates it exists |
| 5 | Jinja2 template file missing | Render fails | Check template existence at startup; fail with clear path error |
| 6 | Jinja2 template has syntax error | Render fails | Catch `jinja2.TemplateSyntaxError`; log template path and line |

## EC4.3 — Schema Validation Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `doc_section.schema.json` is missing | Validation skipped with warning | Log warning; proceed without schema check |
| 2 | doc_requests.json fails schema validation | Error raised; rendering marked as failed | Clear error message listing which fields failed |
| 3 | Schema and actual output drift apart | False positives/negatives in validation | Keep schema in sync; test schema against golden fixtures |

## EC4.4 — File System Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `data/artifacts/` directory doesn't exist | Auto-created | `os.makedirs(exist_ok=True)` |
| 2 | Previous render artifacts exist for same run_id | Overwritten with new render | Explicit overwrite; log that previous artifacts replaced |
| 3 | Disk full during write | Partial file on disk | Write to temp file first; rename on success (atomic write) |
