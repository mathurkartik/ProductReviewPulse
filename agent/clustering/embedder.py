"""Batch embedding with on-disk SQLite cache."""

from __future__ import annotations

import contextlib
import struct
from pathlib import Path

import numpy as np
import structlog

from agent.embeddings import EmbeddingProvider, text_cache_key

log = structlog.get_logger()


def _blob_to_vector(blob: bytes, dim: int = 384) -> np.ndarray:
    """Deserialise BLOB → float32 vector."""
    return np.array(struct.unpack(f"{dim}f", blob), dtype=np.float32)


def _vector_to_blob(vec: np.ndarray) -> bytes:
    """Serialise float32 vector → BLOB."""
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def batch_embed_reviews(
    provider: EmbeddingProvider,
    review_rows: list[dict],
    run_id: str,
    db_path: Path,
) -> dict[str, np.ndarray]:
    """Embed all reviews, using the DB cache where possible.

    Args:
        provider: embedding provider instance
        review_rows: list of dicts with keys 'id' and 'body'
        run_id: current run identifier
        db_path: path to SQLite DB

    Returns:
        dict mapping review_id → float32 embedding vector
    """
    import sqlite3

    embeddings: dict[str, np.ndarray] = {}
    to_embed: list[dict] = []

    # 1. Check cache
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        for row in review_rows:
            cached = conn.execute(
                "SELECT embedding FROM review_embeddings WHERE review_id = ?",
                (row["id"],),
            ).fetchone()
            if cached:
                embeddings[row["id"]] = _blob_to_vector(
                    cached["embedding"], provider.dimensions
                )
            else:
                to_embed.append(row)

    cache_hits = len(embeddings)
    cache_misses = len(to_embed)
    log.info(
        "embedder.cache_check",
        hits=cache_hits,
        misses=cache_misses,
        total=len(review_rows),
    )

    # 2. Embed uncached reviews in batches
    if to_embed:
        texts = [r["body"] for r in to_embed]
        log.info("embedder.encoding", count=len(texts), model=provider.model_name)
        vectors = provider.embed_batch(texts)

        # 3. Persist to cache
        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            with conn:
                for row, vec in zip(to_embed, vectors):
                    blob = _vector_to_blob(vec)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO review_embeddings
                            (review_id, run_id, embedding, model, cached)
                        VALUES (?, ?, ?, ?, 0)
                        """,
                        (row["id"], run_id, blob, provider.model_name),
                    )
                    embeddings[row["id"]] = vec

        log.info("embedder.persisted", count=len(to_embed))

    return embeddings
