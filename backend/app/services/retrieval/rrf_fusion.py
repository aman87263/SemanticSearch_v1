"""Reciprocal Rank Fusion (RRF) for combining multiple search result lists.

Implements the RRF algorithm described in semanticAdditions.md §12. RRF
combines rankings from different retrievers (e.g. BM25 sparse + dense vector)
without needing to normalize incompatible score scales.

Formula:
  rrf_score(doc) = sum over each list: 1 / (rank(doc) + k)

Where k is a constant (default 60) that controls how much weight is given
to higher ranks vs. lower ranks.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[Any]],
    k: int = DEFAULT_K,
    top_k: int | None = None,
) -> list[tuple[Any, float]]:
    """Fuse multiple ranked lists using RRF.

    Args:
        ranked_lists: A list of lists, where each inner list is an ordered
            sequence of items (typically document/chunk IDs or objects with
            an identifiable attribute).
        k: RRF constant (default 60, per the original paper).
        top_k: Maximum number of fused results to return (None = all).

    Returns:
        A list of (item, rrf_score) tuples sorted by score descending.
    """
    fused: dict[Any, float] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            # Convert item to a hashable key if needed
            key = _make_hashable(item)
            score = 1.0 / (rank + k)
            fused[key] = fused.get(key, 0.0) + score

    # Sort by score descending
    sorted_results = sorted(fused.items(), key=lambda x: x[1], reverse=True)

    if top_k is not None:
        sorted_results = sorted_results[:top_k]

    return sorted_results


def _make_hashable(item: Any) -> Any:
    """Return a hashable key for *item*, preserving the original object when possible.

    Callers typically pass IDs (``UUID``/``str``) and then look the fused keys
    back up in a dict keyed by those same IDs. Stringifying a ``UUID`` here
    would silently break that lookup, so we return already-hashable items
    unchanged and only coerce the genuinely unhashable ones.
    """
    # Already hashable (str, int, float, bool, bytes, UUID, tuple, frozenset, ...):
    # keep the original object so identity/equality is preserved.
    try:
        hash(item)
        return item
    except TypeError:
        pass

    # Objects exposing an identifier (e.g. a RetrievedChunk) -> use its id.
    if hasattr(item, "id"):
        return item.id

    if isinstance(item, dict):
        return tuple(sorted(item.items()))

    return str(item)
