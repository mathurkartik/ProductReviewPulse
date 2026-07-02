# ProductReviewPulse — Improvement Instructions
> Paste this entire file into Antigravity and run it. Fix all issues in order.

---

## Context
The pipeline is working end to end. These are targeted fixes only.
Do not restructure any phase. Do not touch files not mentioned here.
After each fix, confirm what changed and what file was modified.

---

## Fix 1 — Language Filter (10 mins)
**File:** `agent/ingestion/playstore.py` and `agent/ingestion/appstore.py`

The language filter is running too late. Non-English reviews (Hindi, Tamil, etc.)
are making it into the final output and appearing in quotes.

Move the language filter to happen immediately after ingestion,
before any review is saved to the database.

```python
# Add this check before upsert in both ingestion files
if review.language and review.language != 'en':
    continue
```

Also add a fallback: if `language` is None or empty, 
attempt to detect it using `langdetect` library.
If detected language is not 'en', skip the review.

Exit check: re-run `pulse ingest --product groww --weeks 10`
and confirm no non-English text appears in the reviews table.

---

## Fix 2 — Quote Selection Prompt (15 mins)
**File:** `agent/summarization.py`

Find the `select_quotes` function and update the LLM prompt to:

```
Select 3 quotes that meet ALL of these criteria:
1. Written in English only — no mixed language or transliterated text
2. Mentions a specific feature, screen, or pain point by name
3. Prefer reviews rated 2–4 stars — they are more actionable than 
   1-star rage or 5-star generic praise
4. Must be a word-for-word substring of the source review text
5. Must be under 150 characters

Bad quote: "user friendly interface i have a great experience with groww"
Good quote: "The option chain fails to load even on a stable connection, 
missed two trades because of this"

If no quotes meet all criteria, relax rule 3 only (allow 1-star or 5-star)
but never relax rules 1, 2, 4, or 5.
```

Exit check: run `pulse summarize --run <run_id>` and verify
all 3 quotes are in English, specific, and under 150 chars.

---

## Fix 3 — Action Ideas Prompt (15 mins)
**File:** `agent/summarization.py`

Find the `generate_action_ideas` function and update the LLM prompt to:

```
Generate 3 action ideas. Each must:
1. Name a specific feature, screen, flow, or metric — not a generic process
2. Reference evidence from the reviews (e.g., "users mention X")
3. Be actionable by a PM in the next sprint — not a vague engineering task

Format: "{Action title}: {One sentence with specific feature + user evidence}"

Bad: "Optimize backend processes for faster account growth"
Good: "Add a progress indicator to the account activation flow — 
users report waiting without feedback during KYC verification"

Bad: "Enhance Trading Execution"  
Good: "Fix option chain loading on the trading screen — 
multiple users report it fails on stable connections during market hours"
```

Exit check: run `pulse summarize --run <run_id>` and verify
each action idea names a specific feature and cites user evidence.

---

## Fix 4 — Theme Deduplication (30 mins)
**File:** `agent/summarization.py`

After the LLM generates themes, add a post-processing step that merges
semantically similar themes before returning PulseSummary.

Logic:
1. For each pair of themes, compute cosine similarity between their
   description embeddings (reuse the existing embedding model)
2. If similarity > 0.80, merge them:
   - Keep the theme with the higher review_count as the primary
   - Add the secondary theme's review_count to the primary
   - Keep the primary theme's label and description
   - Drop the secondary theme
3. After merging, re-rank by review_count descending
4. Return top 3 themes only

Also add this instruction to the LLM theme-labeling prompt:
```
If two clusters appear to cover the same user concern, 
label them differently enough to be distinct, or note 
that they should be merged. Never return two themes 
that say essentially the same thing.
```

Exit check: run `pulse summarize --run <run_id>` and verify
the 3 themes are meaningfully distinct from each other.

---

## Fix 5 — Rating Delta (45 mins)
**File:** `agent/summarization.py` and `agent/storage.py`

The `PulseSummary.stats` block currently shows `avg_rating` 
but not `rating_delta_vs_prev`.

Add this logic to `summarize_pulse()`:

```python
# After computing avg_rating for current run:
prev_run = storage.get_previous_run(product_key, current_iso_week)
if prev_run and prev_run.metrics_json:
    prev_metrics = json.loads(prev_run.metrics_json)
    prev_avg = prev_metrics.get("avg_rating")
    if prev_avg:
        rating_delta = round(current_avg_rating - prev_avg, 2)
    else:
        rating_delta = None
else:
    rating_delta = None

stats = PulseStats(
    total_reviews=total,
    avg_rating=current_avg_rating,
    rating_delta_vs_prev=rating_delta  # e.g. -0.3 or +0.2 or None
)
```

Add `get_previous_run(product_key, iso_week)` to `agent/storage.py`:
- Query runs table for same product_key
- Filter where iso_week < current iso_week and status = 'published'
- Order by iso_week DESC, return the first result

Update the email template and Doc renderer to display:
- If delta is negative: "⬇ 0.3 vs last week" in red/orange
- If delta is positive: "⬆ 0.2 vs last week" in green
- If delta is None (first run): show nothing

Exit check: run the pipeline twice for two different weeks and
verify the second run shows a delta in the email output.

---

## Fix 6 — Branding Cleanup (5 mins)
**Files:** all Jinja2 templates, email renderer, any hardcoded strings

Replace all instances of "FinPulse Analytics" with "Weekly Review Pulse".
Replace "INTERNAL REVIEW TOOL" with "Automated by Pulse Agent".

Search for "FinPulse" across the entire codebase and replace every instance.

Exit check: run `pulse render --run <run_id>` and open
`data/artifacts/{run_id}/email.html` — confirm no "FinPulse" text appears.

---

## Fix 7 — CSV Export Verification
**File:** `agent/ingestion/` (whichever file handles post-ingestion export)

Verify that a CSV is being exported after each ingest run at:
`data/raw/{product}_{run_id}.csv`

Required columns: `source, rating, title, body, date, language, country`
Rules: no IDs, no usernames, no raw_json, body must be PII-scrubbed.

If the CSV export does not exist, add it now.
If it exists, verify the columns match the spec above.

Exit check: run `pulse ingest --product groww --weeks 10`
and confirm the CSV file exists with correct columns and no PII.

---

## Run Order

Apply fixes in this order:
1. Fix 1 (language filter) — run ingest to verify
2. Fix 2 + Fix 3 (prompts) — run summarize to verify  
3. Fix 4 (deduplication) — run summarize to verify
4. Fix 6 (branding) — run render to verify
5. Fix 5 (rating delta) — run two weeks to verify
6. Fix 7 (CSV) — run ingest to verify

After all fixes are applied, run the full pipeline:
```
uv run pulse run --product groww --weeks 10
```

Confirm:
- All 3 themes are distinct
- All 3 quotes are in English and specific
- All 3 action ideas name a feature and cite user evidence
- Email shows avg_rating (delta optional on first full run)
- No "FinPulse" branding anywhere
- CSV exists at data/raw/groww_{run_id}.csv