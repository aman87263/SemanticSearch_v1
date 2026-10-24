"""Evaluation framework for measuring retrieval quality.

Implements semanticAdditions.md §1205 (Evaluation roadmap):

  Phase 6 — Evaluation:
    BM25, Dense, Hybrid, Hybrid + Reranker
    measured against a fixed evaluation dataset.

And the metrics from §21 (RAG quality):
    - retrieval_recall
    - MRR (Mean Reciprocal Rank)
    - NDCG (Normalized Discounted Cumulative Gain)
    - answer_groundedness
    - citation_accuracy
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvaluationQuery:
    """A single evaluation test case."""
    query: str
    relevant_doc_ids: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of running a retrieval strategy against a query."""
    strategy: str
    retrieved_chunk_ids: list[str]
    relevant_chunk_ids: set[str]
    recall: float
    mrr: float
    ndcg: float


class RetrievalEvaluator:
    """Evaluates retrieval strategies against a fixed dataset.

    Usage:
        evaluator = RetrievalEvaluator()
        evaluator.load_dataset("/path/to/eval.json")

        result = evaluator.evaluate_retrieval(
            strategy="hybrid_reranker",
            retrieved_ids=["chunk_1", "chunk_2", ...],
            query=evaluation_query
        )
    """

    def __init__(self):
        self._queries: list[EvaluationQuery] = []

    def load_dataset(self, path: str | Path) -> None:
        """Load evaluation queries from a JSON file.

        Expected format:
        [
          {
            "query": "How do I reset my password?",
            "relevant_doc_ids": ["doc_1", "doc_2"],
            "relevant_chunk_ids": ["chunk_1", "chunk_5"]
          },
          ...
        ]
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Evaluation dataset not found at {path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._queries = [
            EvaluationQuery(
                query=item["query"],
                relevant_doc_ids=item["relevant_doc_ids"],
                relevant_chunk_ids=item.get("relevant_chunk_ids"),
                metadata=item.get("metadata", {}),
            )
            for item in data
        ]

        logger.info(f"Loaded {len(self._queries)} evaluation queries from {path}")

    def add_query(self, query: EvaluationQuery) -> None:
        """Add a single evaluation query programmatically."""
        self._queries.append(query)

    @property
    def queries(self) -> list[EvaluationQuery]:
        return list(self._queries)

    def ground_truth_issues(
        self,
        available_chunk_ids: set[str],
    ) -> list[dict[str, Any]]:
        """Return queries with absent labels or labels not present in the index."""
        issues: list[dict[str, Any]] = []
        for query in self._queries:
            relevant_ids = set(query.relevant_chunk_ids or [])
            if not relevant_ids:
                issues.append({"query": query.query, "reason": "missing_chunk_labels"})
                continue

            missing_ids = sorted(relevant_ids - available_chunk_ids)
            if missing_ids:
                issues.append(
                    {
                        "query": query.query,
                        "reason": "chunk_labels_not_indexed",
                        "missing_count": len(missing_ids),
                    }
                )
        return issues

    def evaluate_retrieval(
        self,
        strategy: str,
        retrieved_ids: list[str],
        query: EvaluationQuery,
        k: int = 10,
    ) -> EvaluationResult:
        """Evaluate a single retrieval result set.

        Args:
            strategy: Name of the retrieval strategy (e.g. "bm25", "dense",
                "hybrid", "hybrid_reranker").
            retrieved_ids: Ordered list of chunk IDs retrieved (best-first).
            query: The evaluation query with ground-truth relevant IDs.
            k: Truncation rank for metrics.

        Returns:
            EvaluationResult with recall, MRR, and NDCG.
        """
        relevant_ids = set(query.relevant_chunk_ids or query.relevant_doc_ids)
        retrieved_k = retrieved_ids[:k]

        # --- Recall@k ---
        if relevant_ids:
            hit_count = len(relevant_ids & set(retrieved_k))
            recall = hit_count / len(relevant_ids)
        else:
            recall = 0.0

        # --- MRR (Mean Reciprocal Rank) ---
        mrr = 0.0
        for rank, chunk_id in enumerate(retrieved_k, start=1):
            if chunk_id in relevant_ids:
                mrr = 1.0 / rank
                break

        # --- NDCG@k ---
        ndcg = self._compute_ndcg(retrieved_k, relevant_ids, k)

        return EvaluationResult(
            strategy=strategy,
            retrieved_chunk_ids=retrieved_k,
            relevant_chunk_ids=relevant_ids,
            recall=recall,
            mrr=mrr,
            ndcg=ndcg,
        )

    @staticmethod
    def _compute_ndcg(
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int,
    ) -> float:
        """Compute NDCG@k.

        Relevance is binary (1 if relevant, 0 otherwise).
        """
        if not relevant_ids or not retrieved_ids:
            return 0.0

        # Discounted Cumulative Gain
        dcg = 0.0
        for i, chunk_id in enumerate(retrieved_ids[:k], start=1):
            if chunk_id in relevant_ids:
                dcg += 1.0 / (2.0 ** i)

        # Ideal DCG: all relevant items at the top
        ideal_count = min(len(relevant_ids), k)
        idcg = sum(1.0 / (2.0 ** i) for i in range(1, ideal_count + 1))

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def evaluate_all_strategies(
        self,
        strategies_results: dict[str, list[list[str]]],
        k: int = 10,
    ) -> dict[str, dict[str, float]]:
        """Evaluate multiple strategies across all queries.

        Args:
            strategies_results: Dict mapping strategy name to a list of
                retrieved-ID lists, one per query (in the same order as
                self._queries).
            k: Truncation rank for metrics.

        Returns:
            Dict mapping strategy name to aggregate metrics:
                {"recall": avg_recall, "mrr": avg_mrr, "ndcg": avg_ndcg}
        """
        aggregate: dict[str, dict[str, float]] = {}

        for strategy_name, per_query_results in strategies_results.items():
            if len(per_query_results) != len(self._queries):
                logger.warning(
                    f"Strategy '{strategy_name}': "
                    f"results count ({len(per_query_results)}) != "
                    f"query count ({len(self._queries)})"
                )

            recalls: list[float] = []
            mrrs: list[float] = []
            ndcgs: list[float] = []

            for i, query in enumerate(self._queries):
                if i >= len(per_query_results):
                    break

                result = self.evaluate_retrieval(
                    strategy=strategy_name,
                    retrieved_ids=per_query_results[i],
                    query=query,
                    k=k,
                )
                recalls.append(result.recall)
                mrrs.append(result.mrr)
                ndcgs.append(result.ndcg)

            if recalls:
                aggregate[strategy_name] = {
                    "recall": sum(recalls) / len(recalls),
                    "mrr": sum(mrrs) / len(mrrs),
                    "ndcg": sum(ndcgs) / len(ndcgs),
                }

        return aggregate

    def generate_report(
        self,
        strategies_results: dict[str, list[list[str]]],
        k: int = 10,
    ) -> str:
        """Generate a human-readable evaluation report."""
        aggregate = self.evaluate_all_strategies(strategies_results, k=k)

        lines = [
            "=" * 60,
            "Retrieval Evaluation Report",
            f"Queries: {len(self._queries)}  |  Cutoff: @{k}",
            "=" * 60,
            "",
            f"{'Strategy':<25} {'Recall':>10} {'MRR':>10} {'NDCG':>10}",
            "-" * 60,
        ]

        # Sort by NDCG descending
        sorted_results = sorted(
            aggregate.items(),
            key=lambda x: x[1]["ndcg"],
            reverse=True,
        )

        for strategy, metrics in sorted_results:
            lines.append(
                f"{strategy:<25} {metrics['recall']:>10.4f} "
                f"{metrics['mrr']:>10.4f} {metrics['ndcg']:>10.4f}"
            )

        lines.append("")
        lines.append("=" * 60)

        # Highlight the best strategy
        if sorted_results:
            best = sorted_results[0]
            lines.append(
                f"Best strategy: {best[0]} "
                f"(NDCG={best[1]['ndcg']:.4f})"
            )

        return "\n".join(lines)
