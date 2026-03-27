"""Ranking benchmark for recovery action effectiveness.

Evaluates ranking models on recovery action prioritization including nDCG@5,
nDCG@10, MRR, and MAP metrics for transit incident recovery scenarios.
"""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

__all__ = ["RecoveryRanking"]


class RecoveryRanking:
    """Rank recovery actions by effectiveness: nDCG@5, nDCG@10, MRR."""

    def __init__(self, model_name: str = "recovery_ranker", dataset_path: str = "data/recovery_actions.json"):
        """Initialize recovery ranking benchmark.

        Args:
            model_name: Model identifier
            dataset_path: Path to test cases

        Raises:
            ValueError: If dataset path is invalid
        """
        self.model_name = model_name
        self.dataset_path = Path(dataset_path)
        self.test_cases: list[dict] = []
        self.load_test_cases()

    def load_test_cases(self) -> list[dict]:
        """Load test cases.

        Returns:
            List of test case dictionaries

        Raises:
            IOError: If dataset file cannot be read
        """
        try:
            if self.dataset_path.exists():
                with open(self.dataset_path) as f:
                    self.test_cases = json.load(f)
            else:
                self.test_cases = self._create_dummy_cases()
            logger.info(f"Loaded {len(self.test_cases)} test cases")
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            self.test_cases = self._create_dummy_cases()
        return self.test_cases

    def _create_dummy_cases(self) -> list[dict]:
        """Create dummy test cases.

        Returns:
            List of 50 synthetic recovery scenarios
        """
        actions = [
            "restart_service",
            "increase_frequency",
            "divert_traffic",
            "deploy_staff",
            "repair_track",
            "check_signals",
            "clear_obstruction",
            "restore_power",
        ]
        cases = []
        for i in range(50):
            # Create realistic ranking based on scenario
            ranked_actions = sorted(actions, key=lambda x: hash(x + str(i)))
            cases.append(
                {
                    "scenario_id": f"SCENARIO_{i:03d}",
                    "incident": f"Disruption scenario {i}: {['signal_failure', 'overcrowding', 'vehicle_delay'][i % 3]}",
                    "optimal_action_ranking": ranked_actions,
                    "severity": ["low", "medium", "high"][i % 3],
                }
            )
        return cases

    def compute_ndcg(self, predicted: list[str], ideal: list[str], k: int = 5) -> float:
        """Compute normalized discounted cumulative gain.

        Args:
            predicted: Predicted ranking
            ideal: Ideal/reference ranking
            k: Cutoff position

        Returns:
            nDCG@k score

        Raises:
            ValueError: If k is negative
        """
        if k < 0:
            raise ValueError("k must be non-negative")

        def dcg(ranking: list[str], relevant: list[str], k: int) -> float:
            score = 0.0
            for i, item in enumerate(ranking[:k]):
                if item in relevant:
                    rel = len(relevant) - relevant.index(item)
                    score += rel / np.log2(i + 2)
            return score

        if not ideal:
            return 1.0 if not predicted else 0.0

        dcg_score = dcg(predicted, ideal, k)
        ideal_dcg = dcg(ideal, ideal, k)

        return float(dcg_score / ideal_dcg) if ideal_dcg > 0 else 0.0

    def compute_mrr(self, predicted: list[str], ideal: list[str]) -> float:
        """Compute mean reciprocal rank.

        Args:
            predicted: Predicted ranking
            ideal: Ideal ranking

        Returns:
            MRR score
        """
        if not ideal:
            return 0.0

        best_ideal = ideal[0]
        for i, item in enumerate(predicted):
            if item == best_ideal:
                return float(1.0 / (i + 1))
        return 0.0

    def compute_map(self, predicted: list[str], ideal: list[str], k: int = 10) -> float:
        """Compute mean average precision@k.

        Args:
            predicted: Predicted ranking
            ideal: Ideal ranking (set of relevant items)
            k: Cutoff position

        Returns:
            MAP@k score
        """
        if not ideal:
            return 0.0

        ideal_set = set(ideal)
        relevance = [1 if item in ideal_set else 0 for item in predicted[:k]]

        if not any(relevance):
            return 0.0

        precision_sum = 0.0
        num_relevant = 0

        for i, rel in enumerate(relevance):
            if rel:
                num_relevant += 1
                precision_sum += num_relevant / (i + 1)

        return float(precision_sum / len(ideal))

    def evaluate_ranking(
        self, predictions: list[list[str]], references: list[list[str]]
    ) -> dict[str, float]:
        """Compute ranking metrics: nDCG@5, nDCG@10, MRR, MAP.

        Args:
            predictions: List of predicted action rankings
            references: List of reference rankings

        Returns:
            Dict with ndcg5, ndcg10, mrr, map metrics

        Raises:
            ValueError: If predictions and references have different lengths
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        ndcg5_scores = []
        ndcg10_scores = []
        mrr_scores = []
        map_scores = []

        for pred, ref in zip(predictions, references, strict=False):
            ndcg5_scores.append(self.compute_ndcg(pred, ref, k=5))
            ndcg10_scores.append(self.compute_ndcg(pred, ref, k=10))
            mrr_scores.append(self.compute_mrr(pred, ref))
            map_scores.append(self.compute_map(pred, ref, k=10))

        return {
            "ndcg_at_5": float(np.mean(ndcg5_scores)),
            "ndcg_at_10": float(np.mean(ndcg10_scores)),
            "mrr": float(np.mean(mrr_scores)),
            "map_at_10": float(np.mean(map_scores)),
        }

    def evaluate_ranking_diversity(
        self, predictions: list[list[str]], references: list[list[str]]
    ) -> dict[str, float]:
        """Evaluate diversity of predicted rankings.

        Args:
            predictions: List of predicted rankings
            references: List of reference rankings

        Returns:
            Dict with diversity metrics
        """
        diversity_scores = []

        for pred in predictions:
            # Simple diversity: fraction of unique items
            unique_ratio = len(set(pred)) / len(pred) if pred else 0.0
            diversity_scores.append(unique_ratio)

        return {
            "ranking_diversity": float(np.mean(diversity_scores)) if diversity_scores else 0.0,
        }

    def run(self, rank_fn=None) -> dict[str, float]:
        """Execute benchmark.

        Args:
            rank_fn: Function(incident) -> ranked_actions. Uses dummy if None.

        Returns:
            Dict of computed metrics

        Raises:
            RuntimeError: If benchmark execution fails
        """
        if not rank_fn:
            def rank_fn(x):
                return ["restart_service", "increase_frequency", "divert_traffic"]

        predictions = []
        references = []

        for case in self.test_cases:
            try:
                pred = rank_fn(case["incident"])
                predictions.append(pred if isinstance(pred, list) else [pred])
                references.append(case["optimal_action_ranking"])
            except Exception as e:
                logger.warning(f"Ranking failed: {e}")
                predictions.append([])
                references.append(case["optimal_action_ranking"])

        try:
            metrics = self.evaluate_ranking(predictions, references)
            metrics.update(self.evaluate_ranking_diversity(predictions, references))
            return metrics
        except Exception as e:
            logger.error(f"Metric computation failed: {e}")
            raise RuntimeError(f"Benchmark execution failed: {e}")

    def get_test_cases(self) -> list[dict]:
        """Return test cases.

        Returns:
            List of benchmark test cases
        """
        return self.test_cases
