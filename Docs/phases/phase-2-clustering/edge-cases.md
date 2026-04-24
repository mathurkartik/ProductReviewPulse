# Phase 2 — Embeddings & Clustering: Edge Cases

## EC2.1 — Embedding Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Review body is extremely long (> 512 tokens) | Model truncates to max token length; embedding still produced | bge-small-en-v1.5 truncates at 512 tokens; no crash |
| 2 | Review body contains only punctuation or special chars | Embedding is produced but may be low-quality | Upstream filter (≥ 3 words) should prevent this; if not, HDBSCAN may assign to noise |
| 3 | `sentence-transformers` model not downloaded yet | First run downloads model (~130 MB) | Log download progress; cache in default HuggingFace dir |
| 4 | Embedding cache file corrupted | Stale/invalid cache entry | Re-compute embedding if deserialization fails; overwrite cache entry |
| 5 | Very large review set (> 50,000 reviews) | Memory pressure during batch embed | Batch embedding in chunks of 256; log progress |
| 6 | Empty review set (0 reviews for the run) | Clustering skipped; log warning | Guard: if len(reviews) == 0, set status to 'clustered' with 0 clusters |

## EC2.2 — UMAP Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Fewer reviews than `n_components` (< 15 reviews) | UMAP cannot reduce to 15 dims | Auto-reduce `n_components` to `min(n_reviews - 1, 15)` |
| 2 | All reviews are nearly identical embeddings | UMAP produces a tight cluster; HDBSCAN may form 1 giant cluster | Acceptable; report as single cluster |
| 3 | UMAP takes too long on large datasets | Timeout or memory issues | Log timing; consider `n_neighbors` tuning for large sets |
| 4 | Non-deterministic UMAP output despite fixed seed | Random state not fully controlled | Set `random_state=42` in UMAP constructor; document limitation |

## EC2.3 — HDBSCAN Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Noise ratio exceeds 35% | Warning logged; clustering still completes | Log warning with actual noise %; do not fail the run |
| 2 | Only 1 or 2 clusters formed | Too few themes for a useful report | Log warning; proceed — Phase 3 handles sparse input |
| 3 | More than 12 clusters formed | Too many for the report format | Log info; Phase 3 ranks and selects top 3 anyway |
| 4 | All reviews assigned to noise (-1) | 0 clusters; no themes possible | Set status to 'clustered'; Phase 3 will produce empty summary with explanation |
| 5 | `min_cluster_size` > number of reviews | HDBSCAN produces 0 clusters | Guard: cap `min_cluster_size` at `max(3, len(reviews) // 10)` |
| 6 | Reviews from different rating bands cluster together | Mixed sentiment in one cluster | Expected; `sentiment_weight` in Phase 3 handles this |

## EC2.4 — Medoid & Keyphrase Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Cluster has exactly `min_cluster_size` reviews (8) | Medoid selected from small pool | Works fine; medoid is the one closest to centroid |
| 2 | KeyBERT returns fewer than 8 keyphrases | Use however many are returned (could be 1–7) | `keyphrases_json` stores the actual list; no padding |
| 3 | KeyBERT returns empty keyphrases for a cluster | Cluster has no key phrases | Store empty list `[]`; Phase 3 uses medoid reviews as fallback context |
| 4 | Medoid review was deleted from DB between runs | Foreign key violation | `REFERENCES reviews(id)` constraint; clustering re-validates review existence |

## EC2.5 — Concurrency & Performance Edge Cases

| # | Scenario | Expected Behavior | Mitigation |
|---|----------|-------------------|------------|
| 1 | Clustering run while ingestion is still writing | Stale or partial review set | CLI should enforce: only cluster if `runs.status == 'ingested'` |
| 2 | Re-running `pulse cluster` on already-clustered run | Overwrite previous cluster results | Clear old clusters + embeddings for this run; re-compute |
| 3 | Out-of-memory on large embedding matrix | Process killed | Batch processing; log memory usage; document minimum RAM (4 GB) |
