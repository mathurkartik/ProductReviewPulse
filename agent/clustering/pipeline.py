"""UMAP + HDBSCAN clustering pipeline.

Orchestrates:
  1. Fetch reviews from DB
  2. Batch-embed (with cache)
  3. UMAP dimensionality reduction
  4. HDBSCAN density clustering
  5. Medoid selection per cluster
  6. KeyBERT keyphrase extraction per cluster
  7. Persist clusters + review_embeddings to DB
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import structlog

from agent.clustering.embedder import batch_embed_reviews
from agent.clustering.keyphrases import extract_keyphrases
from agent.embeddings import get_provider

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Fixed seeds for determinism
# ---------------------------------------------------------------------------
RANDOM_SEED = 42


def _select_medoid(vectors: np.ndarray, review_ids: list[str]) -> str:
    """Return the review_id whose vector is closest to the cluster centroid."""
    centroid = vectors.mean(axis=0)
    # cosine distance: 1 - dot(a, b) / (||a|| * ||b||)
    # vectors are already L2-normalised by BGE, so dot product = cosine sim
    sims = vectors @ centroid
    best_idx = int(np.argmax(sims))
    return review_ids[best_idx]


def run_clustering(
    run_id: str,
    db_path: Path,
    *,
    min_cluster_size: int = 8,
    umap_n_components: int = 15,
    embedding_model: str = "bge-small-en-v1.5",
) -> dict:
    """Execute the full clustering pipeline for a given run.

    Args:
        run_id: the run to cluster
        db_path: SQLite database path
        min_cluster_size: HDBSCAN minimum cluster size
        umap_n_components: UMAP output dimensions
        embedding_model: which embedding provider to use

    Returns:
        dict with summary metrics: cluster_count, noise_ratio, review_count
    """
    # ------------------------------------------------------------------
    # 1. Fetch reviews for this run's product
    # ------------------------------------------------------------------
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        run_row = conn.execute(
            "SELECT product_key FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if not run_row:
            raise ValueError(f"Run {run_id!r} not found in database")

        product_key = run_row["product_key"]
        review_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT id, body, rating FROM reviews WHERE product_key = ?",
                (product_key,),
            ).fetchall()
        ]

    if not review_rows:
        log.warning("clustering.no_reviews", run_id=run_id)
        return {"cluster_count": 0, "noise_ratio": 0.0, "review_count": 0}

    log.info("clustering.reviews_loaded", count=len(review_rows))

    # ------------------------------------------------------------------
    # 2. Embed
    # ------------------------------------------------------------------
    provider = get_provider(embedding_model)
    embeddings_map = batch_embed_reviews(provider, review_rows, run_id, db_path)

    # Build aligned arrays
    review_ids = [r["id"] for r in review_rows]
    vectors = np.array([embeddings_map[rid] for rid in review_ids], dtype=np.float32)

    log.info("clustering.embeddings_ready", shape=vectors.shape)

    # ------------------------------------------------------------------
    # 3. UMAP dimensionality reduction
    # ------------------------------------------------------------------
    import umap

    n_components = min(umap_n_components, len(review_ids) - 2)
    if n_components < 2:
        n_components = 2

    log.info("clustering.umap_start", n_components=n_components)
    reducer = umap.UMAP(
        n_components=n_components,
        metric="cosine",
        random_state=RANDOM_SEED,
        n_neighbors=min(15, len(review_ids) - 1),
    )
    reduced = reducer.fit_transform(vectors)
    log.info("clustering.umap_done", output_shape=reduced.shape)

    # ------------------------------------------------------------------
    # 4. HDBSCAN clustering
    # ------------------------------------------------------------------
    import hdbscan

    effective_min = min(min_cluster_size, max(3, len(review_ids) // 10))
    log.info("clustering.hdbscan_start", min_cluster_size=effective_min)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=effective_min,
        metric="euclidean",
        core_dist_n_jobs=1,
    )
    labels = clusterer.fit_predict(reduced)

    unique_labels = set(labels)
    cluster_labels = sorted(l for l in unique_labels if l >= 0)
    noise_count = int(np.sum(labels == -1))
    noise_ratio = noise_count / len(labels) if len(labels) > 0 else 0.0

    log.info(
        "clustering.hdbscan_done",
        clusters=len(cluster_labels),
        noise_count=noise_count,
        noise_ratio=round(noise_ratio, 3),
    )

    if noise_ratio > 0.35:
        log.warning("clustering.high_noise", noise_ratio=round(noise_ratio, 3))

    # ------------------------------------------------------------------
    # 5. Build cluster objects: medoid + keyphrases
    # ------------------------------------------------------------------
    clusters = []
    for label in cluster_labels:
        mask = labels == label
        cluster_review_ids = [rid for rid, m in zip(review_ids, mask) if m]
        cluster_vectors = vectors[mask]
        cluster_texts = [
            r["body"] for r in review_rows if r["id"] in set(cluster_review_ids)
        ]

        # Medoid
        medoid_id = _select_medoid(cluster_vectors, cluster_review_ids)

        # Keyphrases
        keyphrases = extract_keyphrases(cluster_texts, top_n=8)

        cluster_id = hashlib.sha1(
            f"{run_id}-cluster-{label}".encode()
        ).hexdigest()

        clusters.append(
            {
                "id": cluster_id,
                "run_id": run_id,
                "label": label,
                "review_ids": cluster_review_ids,
                "keyphrases": keyphrases,
                "medoid_review_id": medoid_id,
            }
        )

    log.info("clustering.clusters_built", count=len(clusters))

    # ------------------------------------------------------------------
    # 6. Persist to DB
    # ------------------------------------------------------------------
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        with conn:
            # Clear old clusters for this run
            conn.execute("DELETE FROM clusters WHERE run_id = ?", (run_id,))

            for c in clusters:
                conn.execute(
                    """
                    INSERT INTO clusters
                        (id, run_id, review_ids_json, keyphrases_json, medoid_review_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        c["id"],
                        c["run_id"],
                        json.dumps(c["review_ids"]),
                        json.dumps(c["keyphrases"]),
                        c["medoid_review_id"],
                    ),
                )

    log.info("clustering.persisted", clusters=len(clusters))

    return {
        "cluster_count": len(clusters),
        "noise_ratio": round(noise_ratio, 3),
        "review_count": len(review_rows),
        "noise_count": noise_count,
    }
