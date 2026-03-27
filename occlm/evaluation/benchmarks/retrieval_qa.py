"""Retrieval quality benchmark: MRR, Recall@5, nDCG@10."""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class RetrievalQA:
    """Evaluate retrieval quality: MRR, Recall@5, nDCG@10."""

    def __init__(self, model_name: str = "retrieval_model", dataset_path: str = "data/retrieval_qa.json"):
        """Initialize retrieval QA benchmark.

        Args:
            model_name: Model identifier
            dataset_path: Path to test cases
        """
        self.model_name = model_name
        self.dataset_path = Path(dataset_path)
        self.test_cases = []
        self.load_test_cases()

    def load_test_cases(self) -> list[dict]:
        """Load test cases (query, relevant_documents)."""
        if self.dataset_path.exists():
            with open(self.dataset_path) as f:
                self.test_cases = json.load(f)
        else:
            self.test_cases = self._create_dummy_cases()
        logger.info(f"Loaded {len(self.test_cases)} retrieval test cases")
        return self.test_cases

    def _create_dummy_cases(self) -> list[dict]:
        """Create dummy test cases."""
        corpus = {
            "doc_001": "Line 1 service disruption due to signal failure at Station A",
            "doc_002": "Line 2 schedule changes effective Monday",
            "doc_003": "Line 1 signal maintenance completed",
            "doc_004": "Passenger incident on Line 3",
            "doc_005": "Line 1 service resumed at 14:30",
        }

        cases = []
        queries = [
            ("Line 1 disruption", ["doc_001", "doc_003", "doc_005"]),
            ("service schedule", ["doc_002"]),
            ("signal issues", ["doc_001", "doc_003"]),
        ]

        for _i in range(100 // len(queries)):
            for query, relevant_docs in queries:
                cases.append(
                    {
                        "query_id": f"Q_{len(cases):03d}",
                        "query": query,
                        "corpus": corpus,
                        "relevant_documents": relevant_docs,
                    }
                )

        return cases[:100]

    def compute_mrr(self, ranked_docs: list[str], relevant: list[str]) -> float:
        """Compute Mean Reciprocal Rank.

        Args:
            ranked_docs: Ranked list of document IDs
            relevant: List of relevant document IDs

        Returns:
            MRR score
        """
        for i, doc in enumerate(ranked_docs):
            if doc in relevant:
                return 1.0 / (i + 1)
        return 0.0

    def compute_recall_at_k(self, ranked_docs: list[str], relevant: list[str], k: int = 5) -> float:
        """Compute Recall@K.

        Args:
            ranked_docs: Ranked list of document IDs
            relevant: List of relevant document IDs
            k: Cutoff position

        Returns:
            Recall@k score
        """
        top_k = ranked_docs[:k]
        if not relevant:
            return 1.0 if not top_k else 0.0

        retrieved_relevant = len(set(top_k) & set(relevant))
        return retrieved_relevant / len(relevant)

    def compute_ndcg_at_k(self, ranked_docs: list[str], relevant: list[str], k: int = 10) -> float:
        """Compute normalized DCG@K.

        Args:
            ranked_docs: Ranked list of document IDs
            relevant: List of relevant document IDs
            k: Cutoff position

        Returns:
            nDCG@k score
        """
        def dcg(ranking: list[str], rel_set: set, k: int) -> float:
            score = 0.0
            for i, doc in enumerate(ranking[:k]):
                if doc in rel_set:
                    score += 1.0 / np.log2(i + 2)
            return score

        rel_set = set(relevant)
        if not rel_set:
            return 1.0 if not ranked_docs else 0.0

        dcg_score = dcg(ranked_docs, rel_set, k)
        ideal_dcg = dcg(relevant[:k], rel_set, k)

        return dcg_score / ideal_dcg if ideal_dcg > 0 else 0.0

    def evaluate_retrieval(
        self, predictions: list[list[str]], references: list[list[str]]
    ) -> dict[str, float]:
        """Compute retrieval metrics.

        Args:
            predictions: List of ranked document lists
            references: List of relevant document lists

        Returns:
            Dict with mrr, recall_at_5, ndcg_at_10
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        mrr_scores = []
        recall5_scores = []
        ndcg10_scores = []

        for pred, ref in zip(predictions, references, strict=False):
            mrr_scores.append(self.compute_mrr(pred, ref))
            recall5_scores.append(self.compute_recall_at_k(pred, ref, k=5))
            ndcg10_scores.append(self.compute_ndcg_at_k(pred, ref, k=10))

        return {
            "mrr": float(np.mean(mrr_scores)),
            "recall_at_5": float(np.mean(recall5_scores)),
            "ndcg_at_10": float(np.mean(ndcg10_scores)),
        }

    def run(self, retrieve_fn=None) -> dict[str, float]:
        """Execute benchmark.

        Args:
            retrieve_fn: Function(query, corpus) -> [doc_ids]. Uses dummy if None.

        Returns:
            Dict of computed metrics
        """
        if not retrieve_fn:
            def retrieve_fn(q, c):
                return list(c.keys())[:3]  # Dummy: first 3 docs

        predictions = []
        references = []

        for case in self.test_cases:
            try:
                query = case["query"]
                corpus = case["corpus"]
                pred = retrieve_fn(query, corpus)
                predictions.append(pred)
                references.append(case["relevant_documents"])
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")
                predictions.append([])
                references.append(case["relevant_documents"])

        metrics = self.evaluate_retrieval(predictions, references)
        return metrics

    def get_test_cases(self) -> list[dict]:
        """Return test cases."""
        return self.test_cases
