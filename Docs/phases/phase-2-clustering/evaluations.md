# Phase 2 — Embeddings & Clustering: Evaluations

## Evaluation Criteria

### E2.1 — Embedding Generation
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | All reviews embedded | `review_embeddings` row count = `reviews` row count for the run |
| 2 | Embedding dimensionality correct | Each BLOB decodes to 384-dim float32 vector (bge-small-en-v1.5) |
| 3 | Model field populated | `review_embeddings.model` = `'bge-small-en-v1.5'` for all rows |
| 4 | Cache works on re-run | Second run: `cached=1` for 100% of embeddings; no model inference |

### E2.2 — UMAP Dimensionality Reduction
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Output dimensionality | UMAP reduces to 15 components as configured |
| 2 | Metric is cosine | UMAP configured with `metric='cosine'` |
| 3 | Deterministic with fixed seed | Two runs with same seed produce identical UMAP output |

### E2.3 — HDBSCAN Clustering
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Cluster count in range | Between 4 and 12 clusters on golden fixture (~400 reviews) |
| 2 | Noise ratio acceptable | < 35% of reviews labeled as noise (cluster label = -1) |
| 3 | `min_cluster_size` respected | No cluster has fewer than 8 members |
| 4 | Deterministic with fixed seed | Same cluster assignments across identical runs |

### E2.4 — Medoid Selection
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | One medoid per cluster | Each cluster has exactly one `medoid_review_id` |
| 2 | Medoid is a real review | `medoid_review_id` exists in `reviews` table |
| 3 | Medoid is closest to centroid | Medoid has smallest cosine distance to cluster centroid |

### E2.5 — KeyBERT Keyphrases
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Keyphrases extracted per cluster | Each cluster has 1–8 keyphrases in `keyphrases_json` |
| 2 | Keyphrases are meaningful | Manual spot-check: keyphrases relate to review content |
| 3 | Valid JSON | `keyphrases_json` parses without error for every cluster |

### E2.6 — Persistence
| # | Test | Pass Condition |
|---|------|----------------|
| 1 | Clusters table populated | `clusters` table has rows equal to cluster count |
| 2 | `review_ids_json` is valid | Each cluster's `review_ids_json` parses to a list of valid review IDs |
| 3 | Run status updated | `runs.status` = `'clustered'` after successful run |

## Summary Metrics

| Metric | Target |
|--------|--------|
| Cluster count | 4–12 |
| Noise ratio | < 35% |
| Embedding cache hit on re-run | 100% |
| Deterministic across runs | Yes (fixed seeds) |
| Keyphrases per cluster | 1–8 |
