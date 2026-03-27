"""Classification benchmark for disruption type identification.

Provides comprehensive classification evaluation for transit disruption
incident types including accuracy, precision, recall, F1, and per-class
performance metrics for 10 disruption categories.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

__all__ = ["DisruptionDiagnosis"]


class DisruptionDiagnosis:
    """Classify disruption types (10 classes): accuracy, precision, recall, F1."""

    DISRUPTION_CLASSES = [
        "signal_failure",
        "power_outage",
        "track_obstruction",
        "staff_shortage",
        "vehicle_fault",
        "weather_impact",
        "security_incident",
        "overcrowding",
        "timetable_issue",
        "unknown",
    ]

    def __init__(self, model_name: str = "disruption_classifier", dataset_path: str = "data/disruptions.json"):
        """Initialize disruption classification benchmark.

        Args:
            model_name: Model identifier
            dataset_path: Path to test cases

        Raises:
            ValueError: If dataset path is invalid
        """
        self.model_name = model_name
        self.dataset_path = Path(dataset_path)
        self.test_cases: List[Dict] = []
        self.class_weights = self._compute_class_weights()
        self.load_test_cases()

    def _compute_class_weights(self) -> Dict[str, float]:
        """Compute weights for imbalanced classification.

        Returns:
            Dict mapping class labels to weights
        """
        base_weight = 1.0 / len(self.DISRUPTION_CLASSES)
        return {cls: base_weight for cls in self.DISRUPTION_CLASSES}

    def load_test_cases(self) -> List[Dict]:
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

    def _create_dummy_cases(self) -> List[Dict]:
        """Create dummy test cases.

        Returns:
            List of 100 synthetic disruption incidents
        """
        cases = []
        for i in range(100):
            class_idx = i % len(self.DISRUPTION_CLASSES)
            cases.append(
                {
                    "incident_id": f"INC_{i:03d}",
                    "report": f"Incident report {i}: {self.DISRUPTION_CLASSES[class_idx]} detected. "
                             f"Location: Station {i % 20}. Time: {i % 24:02d}:00. "
                             f"Status: {'Active' if i % 2 else 'Resolved'}.",
                    "true_label": self.DISRUPTION_CLASSES[class_idx],
                    "confidence": 0.8 + (i % 20) / 100,
                }
            )
        return cases

    def evaluate_classification(
        self, predictions: List[str], references: List[str]
    ) -> Dict[str, float]:
        """Compute classification metrics: accuracy, precision, recall, F1.

        Args:
            predictions: Predicted class labels
            references: Ground truth labels

        Returns:
            Dict with accuracy, macro_precision, macro_recall, macro_f1, weighted_f1

        Raises:
            ValueError: If predictions and references have different lengths
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        accuracy = np.mean([p == r for p, r in zip(predictions, references)])

        # Per-class metrics
        precisions = []
        recalls = []
        f1_scores = []
        weighted_f1_components = []

        for class_label in self.DISRUPTION_CLASSES:
            tp = sum(1 for p, r in zip(predictions, references) if p == r == class_label)
            fp = sum(1 for p, r in zip(predictions, references) if p == class_label and r != class_label)
            fn = sum(1 for p, r in zip(predictions, references) if p != class_label and r == class_label)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            precisions.append(precision)
            recalls.append(recall)
            f1_scores.append(f1)

            # Weight by class frequency for weighted F1
            class_count = sum(1 for r in references if r == class_label)
            weight = class_count / len(references) if references else 0
            weighted_f1_components.append(f1 * weight)

        macro_precision = float(np.mean(precisions))
        macro_recall = float(np.mean(recalls))
        macro_f1 = float(np.mean(f1_scores))
        weighted_f1 = float(np.sum(weighted_f1_components))

        return {
            "accuracy": float(accuracy),
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "micro_f1": macro_f1,
        }

    def evaluate_per_class_metrics(
        self, predictions: List[str], references: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Compute per-class detailed metrics.

        Args:
            predictions: Predicted class labels
            references: Ground truth labels

        Returns:
            Dict mapping class labels to their metrics

        Raises:
            ValueError: If lists have different lengths
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        per_class = {}

        for class_label in self.DISRUPTION_CLASSES:
            tp = sum(1 for p, r in zip(predictions, references) if p == r == class_label)
            fp = sum(1 for p, r in zip(predictions, references) if p == class_label and r != class_label)
            fn = sum(1 for p, r in zip(predictions, references) if p != class_label and r == class_label)
            tn = sum(1 for p, r in zip(predictions, references) if p != class_label and r != class_label)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

            per_class[class_label] = {
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "specificity": float(specificity),
                "support": tp + fn,
            }

        return per_class

    def evaluate_confusion_matrix(
        self, predictions: List[str], references: List[str]
    ) -> np.ndarray:
        """Compute confusion matrix.

        Args:
            predictions: Predicted class labels
            references: Ground truth labels

        Returns:
            Confusion matrix as numpy array

        Raises:
            ValueError: If lists have different lengths
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        n_classes = len(self.DISRUPTION_CLASSES)
        cm = np.zeros((n_classes, n_classes), dtype=int)

        for pred, ref in zip(predictions, references):
            if pred in self.DISRUPTION_CLASSES and ref in self.DISRUPTION_CLASSES:
                pred_idx = self.DISRUPTION_CLASSES.index(pred)
                ref_idx = self.DISRUPTION_CLASSES.index(ref)
                cm[ref_idx, pred_idx] += 1

        return cm

    def run(self, classify_fn=None) -> Dict[str, float]:
        """Execute benchmark.

        Args:
            classify_fn: Function(report) -> class_label. Uses dummy if None.

        Returns:
            Dict of computed metrics

        Raises:
            RuntimeError: If benchmark execution fails
        """
        if not classify_fn:
            classify_fn = lambda x: "unknown"  # Dummy classifier

        predictions = []
        references = []

        for case in self.test_cases:
            try:
                pred = classify_fn(case["report"])
                # Validate prediction
                if pred not in self.DISRUPTION_CLASSES:
                    pred = "unknown"
                predictions.append(pred)
                references.append(case["true_label"])
            except Exception as e:
                logger.warning(f"Classification failed: {e}")
                predictions.append("unknown")
                references.append(case["true_label"])

        try:
            metrics = self.evaluate_classification(predictions, references)
            return metrics
        except Exception as e:
            logger.error(f"Metric computation failed: {e}")
            raise RuntimeError(f"Benchmark execution failed: {e}")

    def get_test_cases(self) -> List[Dict]:
        """Return test cases.

        Returns:
            List of benchmark test cases
        """
        return self.test_cases
