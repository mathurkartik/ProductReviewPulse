"""KeyBERT keyphrase extraction per cluster — singleton model for efficiency."""

from __future__ import annotations

import structlog

log = structlog.get_logger()

# Module-level singleton: loaded once per process, reused for all clusters
_kw_model = None


def _get_model():
    global _kw_model
    if _kw_model is None:
        from keybert import KeyBERT

        log.info("keyphrases.loading_model")
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        log.info("keyphrases.model_loaded")
    return _kw_model


def free_model():
    """Release the globally cached KeyBERT model to free memory."""
    global _kw_model
    _kw_model = None
    import gc

    gc.collect()


def extract_keyphrases(
    review_texts: list[str],
    top_n: int = 8,
) -> list[str]:
    """Extract top-N keyphrases from a cluster's reviews using KeyBERT.

    Args:
        review_texts: list of review body strings belonging to one cluster
        top_n: maximum number of keyphrases to return

    Returns:
        list of keyphrase strings, ordered by relevance score descending
    """
    if not review_texts:
        return []

    # Concatenate all reviews in the cluster into one document
    combined = " ".join(review_texts)

    kw_model = _get_model()

    keywords = kw_model.extract_keywords(
        combined,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=top_n,
        use_mmr=True,  # Maximal Marginal Relevance for diversity
        diversity=0.5,
    )

    phrases = [kw for kw, _score in keywords]
    return phrases
