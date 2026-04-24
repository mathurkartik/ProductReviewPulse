# Phase 4 — Report & Email Rendering: Evaluations

## Evaluation Criteria

### E4.1 — Google Docs batchUpdate Rendering
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Doc requests JSON generated | `data/artifacts/{run_id}/doc_requests.json` exists |
| 2 | Heading 1 contains product + ISO week | First request creates heading matching `"{Product} — Weekly Review Pulse | {ISO week}"` |
| 3 | Anchor string embedded | Heading text contains `pulse-{product}-{iso_week}` |
| 4 | Section structure matches spec | Heading 2s: "Top Themes", "Real User Quotes", "Action Ideas", "Who This Helps" |
| 5 | Themes rendered as numbered paragraphs | Each theme: `"{n}. {theme_name} — {theme_summary}"` |
| 6 | Quotes rendered in italics | Each quote wrapped in italic formatting requests |
| 7 | Who This Helps is a 2-column table | Table with headers: Audience, Value; 3 data rows |
| 8 | Schema validation passes | `doc_requests.json` validates against `templates/doc_section.schema.json` |

### E4.2 — Email HTML Rendering
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | HTML email generated | `data/artifacts/{run_id}/email.html` exists |
| 2 | Plain-text email generated | `data/artifacts/{run_id}/email.txt` exists |
| 3 | Subject line correct | `[Weekly Pulse] {Product} — {ISO week} — {Top theme name}` |
| 4 | Body contains theme bullets | Top 3 theme names listed as bullet points |
| 5 | Deep link placeholder present | `{DOC_DEEP_LINK}` placeholder in "Read full report →" link |
| 6 | Footer present | Email includes standard footer |

### E4.3 — Determinism & Golden Tests
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Doc requests golden test | Output matches `tests/fixtures/doc_requests_golden.json` byte-for-byte on fixture input |
| 2 | Email HTML golden test | Output matches `tests/fixtures/email_golden.html` byte-for-byte on fixture input |
| 3 | Malformed summary rejected | Schema validator raises error for missing themes or invalid sentiment |

### E4.4 — Status
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Run status updated | `runs.status` = `'rendered'` after successful run |
| 2 | No MCP calls made | Phase 4 is pure local; zero network calls |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Doc section headings | 4 (Top Themes, Real User Quotes, Action Ideas, Who This Helps) |
| Email artifacts | 2 (HTML + plain-text) |
| Golden test stability | Byte-identical |
| MCP calls | 0 |
