"""Embedding provider interface with local bge-small-en-v1.5 default."""

from __future__ import annotations

import hashlib

import numpy as np
import structlog

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------

class EmbeddingProvider:
    """Abstract base for embedding providers."""

    model_name: str = "unknown"
    dimensions: int = 0

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Local BGE provider (default, zero-cost)
# ---------------------------------------------------------------------------

class LocalBGEProvider(EmbeddingProvider):
    """bge-small-en-v1.5 via sentence-transformers.  384-dim, local, no API key."""

    model_name = "bge-small-en-v1.5"
    dimensions = 384

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        log.info("embeddings.loading_model", model=self.model_name)
        self._model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        log.info("embeddings.model_loaded", model=self.model_name)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Return (N, 384) float32 array."""
        return self._model.encode(
            texts,
            batch_size=256,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).astype(np.float32)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def text_cache_key(text: str) -> str:
    """sha1 of normalised text — used as the embedding cache key."""
    normalised = " ".join(text.split())
    return hashlib.sha1(normalised.encode()).hexdigest()


def get_provider(name: str = "bge-small-en-v1.5") -> EmbeddingProvider:
    """Factory: return the requested embedding provider."""
    if name == "bge-small-en-v1.5":
        return LocalBGEProvider()
    raise ValueError(f"Unknown embedding provider: {name!r}")
