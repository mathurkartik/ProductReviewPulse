# Phase 1 — Review Ingestion: Edge Cases

## EC1.1 — App Store Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | iTunes RSS feed returns 200 OK but empty `entry` array | Fallback to HTML scraping of apps.apple.com page | Two-tier fetching: RSS first, then HTML parse |
| 2 | App Store ID is wrong or app is delisted | 0 reviews from App Store; ingestion continues with Play Store only | Log warning; do not fail the entire run |
| 3 | Apple rate-limits or blocks requests | HTTP 429 or connection timeout | Retry with exponential backoff (3 attempts); User-Agent header mimics browser |
| 4 | App Store HTML structure changes (Shoebox JSON schema) | HTML fallback fails to parse reviews | Catch parse errors; log structured error; continue with 0 App Store reviews |
| 5 | RSS feed returns reviews in non-English | Reviews pass through to filter stage | `is_valid_review` language filter catches these |
| 6 | RSS pagination returns duplicate entries across pages | Duplicate review IDs | `sha1(source + external_id)` dedup ensures upsert, not double-insert |

## EC1.2 — Play Store Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | `google-play-scraper` raises network error | Log error; continue with 0 Play Store reviews | Try/except around the scraper call |
| 2 | Play Store returns reviews outside the time window | Reviews older than `since` date are discarded | Date comparison filter in ingestion loop |
| 3 | Play Store returns reviews in Hindi or mixed scripts | Filtered out by language check | `is_valid_review(language='en')` rejects non-English |
| 4 | Extremely long review body (> 10,000 chars) | Stored as-is; no truncation | SQLite TEXT has no practical limit; downstream phases handle long text |
| 5 | Review body is `None` or empty string | Filtered out by 3-word minimum | `is_valid_review` catches empty/short bodies |
| 6 | `google-play-scraper` API changes or breaks | Ingestion fails for Play Store | Pin library version; catch import/call errors gracefully |

## EC1.3 — PII Scrubbing Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Phone number with country code (e.g., +91-9876543210) | Scrubbed to `[PHONE]` | Regex handles `+\d{1,3}[-\s]?\d{10}` pattern |
| 2 | Email in unusual format (e.g., `user+tag@sub.domain.co.in`) | Scrubbed to `[EMAIL]` | Broad email regex |
| 3 | False positive: "rated 4.5/5.0 by 12345678 users" | Number should NOT be scrubbed | Aadhaar regex requires specific spacing pattern (4-4-4 digits) |
| 4 | Multiple PII items in one review | All instances scrubbed | Regex uses `re.sub` with global replacement |
| 5 | PII at start/end of body or adjacent to punctuation | Correctly scrubbed regardless of position | Regex word boundary handling |

## EC1.4 — Filter Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Review with exactly 3 words | Passes filter (≥ 3) | `len(body.split()) >= 3` |
| 2 | Review with 2 words | Rejected | Same check |
| 3 | Review that is all whitespace or newlines | Rejected (0 words after split) | `body.split()` handles this |
| 4 | Review with emojis mixed into English text | Rejected (emoji count > 0) | `emoji.emoji_count(body) > 0` |
| 5 | Review with Unicode symbols that look like emojis (e.g., ™, ©) | Should pass (these are not emojis) | `emoji` library distinguishes true emoji from symbols |
| 6 | Review in English but with `language=None` from scraper | Passes (language filter only rejects explicit non-English) | `if language and not language.startswith('en')` |

## EC1.5 — Data Integrity Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Ingestion crashes mid-write | Partial data in DB; JSONL may be incomplete | Next run re-upserts; `run_id` is deterministic so same run resumes |
| 2 | Two concurrent `pulse ingest` for the same product | SQLite write lock prevents corruption | SQLite serializes writes; second process waits or errors |
| 3 | Clock skew: `since` date computed differently on re-run | Slightly different review window | Use UTC consistently; `datetime.now(timezone.utc)` |
| 4 | Product key in CLI doesn't exist in `products.yaml` | Clear error: "Product 'xyz' not found in products.yaml" | Validate before starting ingestion |
| 5 | `data/raw/` directory doesn't exist | Auto-create on first write | `os.makedirs(exist_ok=True)` |
