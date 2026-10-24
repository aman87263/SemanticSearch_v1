"""Tests for the evaluation framework (semanticAdditions.md §21, §1205)."""

import pytest

from app.services.evaluation.retrieval_evaluator import (
    EvaluationQuery,
    RetrievalEvaluator,
)


class TestRetrievalEvaluator:
    def test_load_dataset(self):
        """Should load evaluation queries from JSON."""
        evaluator = RetrievalEvaluator()
        evaluator.load_dataset(
            "app/services/evaluation/sample_dataset.json"
        )
        assert len(evaluator.queries) == 5
        assert evaluator.queries[0].query == "How do I reset my password?"

    def test_evaluate_perfect_recall(self):
        """Retrieving all relevant documents should give recall=1.0."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B", "C"],
        )

        result = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["A", "B", "C", "D"],
            query=query,
            k=10,
        )

        assert result.recall == 1.0  # All relevant retrieved
        assert result.mrr == 1.0  # Relevant item at rank 1

    def test_evaluate_partial_recall(self):
        """Only retrieving some relevant docs should give partial recall."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B", "C", "D"],
        )

        result = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["A", "C", "E"],
            query=query,
            k=10,
        )

        # 2 of 4 relevant retrieved
        assert result.recall == 0.5

    def test_evaluate_mrr_first_relevant_at_rank_3(self):
        """MRR should be 1/3 if first relevant item is at rank 3."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B"],
        )

        result = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["X", "Y", "A", "Z"],
            query=query,
            k=10,
        )

        assert result.mrr == pytest.approx(1.0 / 3.0)

    def test_evaluate_mrr_no_relevant(self):
        """MRR should be 0 if no relevant items are retrieved."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B"],
        )

        result = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["X", "Y", "Z"],
            query=query,
            k=10,
        )

        assert result.mrr == 0.0
        assert result.recall == 0.0

    def test_evaluate_ndcg(self):
        """NDCG should be between 0 and 1."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B", "C"],
        )

        # Perfect ordering
        result = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["A", "B", "C", "D", "E"],
            query=query,
            k=10,
        )
        assert result.ndcg == pytest.approx(1.0, abs=0.01)

        # Worst ordering (relevant at the end)
        result2 = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["D", "E", "A", "B", "F"],
            query=query,
            k=10,
        )
        assert result2.ndcg < result.ndcg

    def test_evaluate_all_strategies(self):
        """Should compute aggregate metrics for multiple strategies."""
        evaluator = RetrievalEvaluator()
        evaluator.add_query(EvaluationQuery(
            query="q1", relevant_chunk_ids=["A", "B"],
        ))
        evaluator.add_query(EvaluationQuery(
            query="q2", relevant_chunk_ids=["C"],
        ))

        strategies_results = {
            "bm25": [
                ["A", "B", "X"],  # q1: recall=1.0, mrr=1.0
                ["Y", "Z"],       # q2: recall=0.0, mrr=0.0
            ],
            "dense": [
                ["X", "A", "B"],  # q1: recall=1.0, mrr=0.5
                ["C", "Y"],       # q2: recall=1.0, mrr=1.0
            ],
        }

        aggregate = evaluator.evaluate_all_strategies(strategies_results, k=10)

        assert "bm25" in aggregate
        assert "dense" in aggregate
        assert aggregate["dense"]["recall"] > aggregate["bm25"]["recall"]
        assert aggregate["dense"]["mrr"] > aggregate["bm25"]["mrr"]

    def test_generate_report(self):
        """Should generate a readable evaluation report."""
        evaluator = RetrievalEvaluator()
        evaluator.add_query(EvaluationQuery(
            query="q1", relevant_chunk_ids=["A"],
        ))

        strategies_results = {
            "bm25": [["A", "B"]],
            "hybrid": [["A", "B"]],
        }

        report = evaluator.generate_report(strategies_results, k=10)

        assert "Retrieval Evaluation Report" in report
        assert "bm25" in report
        assert "hybrid" in report
        assert "Best strategy" in report

    def test_k_truncation_affects_recall(self):
        """Lower k should potentially reduce recall."""
        evaluator = RetrievalEvaluator()
        query = EvaluationQuery(
            query="test",
            relevant_chunk_ids=["A", "B", "C", "D", "E"],
        )

        result_k5 = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["A", "B", "C", "D", "E"],
            query=query,
            k=5,
        )

        result_k3 = evaluator.evaluate_retrieval(
            strategy="test",
            retrieved_ids=["A", "B", "C", "D", "E"],
            query=query,
            k=3,
        )

        # With k=5, all 5 relevant are in top 5 → recall 1.0
        assert result_k5.recall == 1.0

        # With k=3, only 3 of 5 relevant → recall 0.6
        assert result_k3.recall == pytest.approx(0.6)
