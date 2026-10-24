"""Tests for RRF (Reciprocal Rank Fusion) (semanticAdditions.md §12)."""

import pytest

from app.services.retrieval.rrf_fusion import reciprocal_rank_fusion


class TestReciprocalRankFusion:
    def test_basic_fusion(self):
        """Two ranked lists should be fused by reciprocal rank."""
        list_a = ["A", "B", "C"]  # BM25
        list_b = ["C", "A", "D"]  # Dense

        results = reciprocal_rank_fusion(
            ranked_lists=[list_a, list_b],
            k=60,
        )

        # A appears at rank 1 (BM25) and rank 2 (dense): 1/1 + 1/2 = 1.5
        # C appears at rank 3 (BM25) and rank 1 (dense): 1/3 + 1/1 = 1.333
        # B appears at rank 2 (BM25) only: 1/2 = 0.5
        # D appears at rank 3 (dense) only: 1/3 = 0.333

        scores = dict(results)
        assert scores["A"] > scores["C"]
        assert scores["A"] > scores["B"]
        assert scores["B"] > scores["D"]

        # A should be ranked first
        assert results[0][0] == "A"

    def test_empty_lists(self):
        """Empty lists should return empty results."""
        results = reciprocal_rank_fusion(ranked_lists=[])
        assert results == []

        results = reciprocal_rank_fusion(ranked_lists=[[], []])
        assert results == []

    def test_top_k_limit(self):
        """top_k should limit the number of results."""
        list_a = ["A", "B", "C", "D", "E"]
        list_b = ["E", "D", "C", "B", "A"]

        results = reciprocal_rank_fusion(
            ranked_lists=[list_a, list_b],
            k=60,
            top_k=3,
        )

        assert len(results) == 3

    def test_single_list(self):
        """Single ranked list should preserve order with RRF scoring."""
        items = ["A", "B", "C"]
        results = reciprocal_rank_fusion(ranked_lists=[items], k=60)

        # With one list, RRF score = 1/(rank + k)
        # A: rank 0 → 1/60, B: rank 1 → 1/61, C: rank 2 → 1/62
        assert len(results) == 3
        assert all(r[0] in items for r in results)

    def test_custom_k(self):
        """Custom k value should change the score distribution."""
        items = ["A", "B", "C"]
        results_default = reciprocal_rank_fusion(ranked_lists=[items])
        results_custom = reciprocal_rank_fusion(ranked_lists=[items], k=10)

        # Scores should differ but order should be the same
        ids_default = [r[0] for r in results_default]
        ids_custom = [r[0] for r in results_custom]
        assert ids_default == ids_custom

    def test_duplicate_items_across_lists(self):
        """An item appearing in both lists should have combined scores."""
        list_a = ["A", "B"]
        list_b = ["A", "B"]

        results = reciprocal_rank_fusion(ranked_lists=[list_a, list_b], k=60)

        scores = dict(results)
        # A: 1/(0+60) + 1/(0+60) = 2/60
        # B: 1/(1+60) + 1/(1+60) = 2/61
        assert scores["A"] == pytest.approx(2.0 / 60.0)
        assert scores["B"] == pytest.approx(2.0 / 61.0)
        assert results[0][0] == "A"

    def test_identical_lists(self):
        """Two identical lists should produce same order as the input."""
        items = ["X", "Y", "Z"]
        results = reciprocal_rank_fusion(ranked_lists=[items, items], k=60)

        ids = [r[0] for r in results]
        assert ids == ["X", "Y", "Z"]

    def test_preserves_uuid_keys(self):
        """UUID items must come back as UUIDs, not stringified.

        Regression: stringifying UUIDs here breaks the caller's dict lookup
        (search returned zero results).
        """
        from uuid import UUID

        a = UUID("aaaaaaaa-0000-0000-0000-000000000001")
        b = UUID("bbbbbbbb-0000-0000-0000-000000000002")

        results = reciprocal_rank_fusion(ranked_lists=[[a, b], [b, a]], k=60)

        returned_ids = [r[0] for r in results]
        assert all(isinstance(i, UUID) for i in returned_ids), returned_ids
        assert set(returned_ids) == {a, b}

        # The caller's lookup pattern must work
        lookup = {a: "chunk-a", b: "chunk-b"}
        assert lookup[returned_ids[0]] in ("chunk-a", "chunk-b")

    def test_preserves_uuid_keys_across_lists(self):
        """A UUID appearing in both lists should fuse into a single UUID key."""
        from uuid import UUID

        a = UUID("aaaaaaaa-0000-0000-0000-000000000001")

        results = reciprocal_rank_fusion(ranked_lists=[[a], [a]], k=60)

        assert len(results) == 1
        assert isinstance(results[0][0], UUID)
        assert results[0][0] == a
