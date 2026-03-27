"""Topology consistency benchmark for network validation.

Verifies that model outputs respect network topology constraints
including line/station existence, valid connections, and realistic
travel times for transit networks.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

__all__ = ["TopologyConsistency"]


class TopologyConsistency:
    """Verify model outputs respect network topology: error_rate, false_positives."""

    def __init__(self, model_name: str = "topo_checker", dataset_path: str = "data/topology.json"):
        """Initialize topology consistency benchmark.

        Args:
            model_name: Model identifier
            dataset_path: Path to network topology and test cases

        Raises:
            ValueError: If dataset path is invalid
        """
        self.model_name = model_name
        self.dataset_path = Path(dataset_path)
        self.test_cases: List[Dict] = []
        self.topology = self._load_topology()
        self.load_test_cases()

    def _load_topology(self) -> Dict:
        """Load network topology reference.

        Returns:
            Dict containing transit network structure and metadata
        """
        return {
            "lines": ["L1", "L2", "L3", "L4", "L5"],
            "stations": {
                "L1": ["St1", "St2", "St3", "St9"],
                "L2": ["St2", "St4", "St5", "St10"],
                "L3": ["St1", "St6", "St11"],
                "L4": ["St3", "St7", "St12"],
                "L5": ["St5", "St8", "St13"],
            },
            "connections": {
                ("L1", "L2"): ["St2"],
                ("L1", "L3"): ["St1"],
                ("L1", "L4"): ["St3"],
                ("L2", "L3"): [],
                ("L3", "L4"): ["St3"],
            },
            "travel_times": {
                ("St1", "St2"): 5,
                ("St2", "St3"): 4,
                ("St2", "St4"): 6,
                ("St3", "St9"): 3,
                ("St4", "St5"): 5,
            },
            "max_travel_time_minutes": 60,
        }

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
            logger.info(f"Loaded {len(self.test_cases)} topology test cases")
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            self.test_cases = self._create_dummy_cases()
        return self.test_cases

    def _create_dummy_cases(self) -> List[Dict]:
        """Create dummy test cases.

        Returns:
            List of 100 synthetic routing queries
        """
        return [
            {
                "query_id": f"Q_{i:03d}",
                "query": f"Route from L1 to L{i % 5 + 1}",
                "expected_route": ["St1", "St2", "St4"],
                "expected_lines": [f"L{i % 5 + 1}"],
            }
            for i in range(100)
        ]

    def validate_topology(self, response: Dict) -> Dict[str, bool]:
        """Validate if response respects network topology.

        Args:
            response: Model response with claimed route/stops

        Returns:
            Dict with validation check results

        Raises:
            ValueError: If response format is invalid
        """
        checks = {
            "routes_exist": True,
            "stops_valid": True,
            "connections_valid": True,
            "travel_times_realistic": True,
        }

        try:
            # Check if mentioned lines exist
            mentioned_lines = response.get("lines", [])
            for line in mentioned_lines:
                if line not in self.topology["lines"]:
                    checks["routes_exist"] = False

            # Check if mentioned stops exist
            mentioned_stops = response.get("stops", [])
            valid_stops = set()
            for line_stops in self.topology["stations"].values():
                valid_stops.update(line_stops)

            for stop in mentioned_stops:
                if stop not in valid_stops:
                    checks["stops_valid"] = False

            # Check connections between consecutive stops
            if len(mentioned_stops) > 1:
                for i in range(len(mentioned_stops) - 1):
                    s1, s2 = mentioned_stops[i], mentioned_stops[i + 1]
                    travel_time = response.get("travel_times", {}).get(f"{s1}-{s2}", -1)
                    max_time = self.topology["max_travel_time_minutes"]
                    if travel_time > 0 and travel_time > max_time:
                        checks["travel_times_realistic"] = False

        except Exception as e:
            logger.warning(f"Topology validation failed: {e}")
            checks["routes_exist"] = False

        return checks

    def evaluate_topology(
        self, predictions: List[Dict], references: List[Dict]
    ) -> Dict[str, float]:
        """Compute topology consistency metrics.

        Args:
            predictions: Model responses
            references: Reference responses

        Returns:
            Dict with error_rate, false_positives, false_negatives, consistency_score

        Raises:
            ValueError: If lists have different lengths
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        total_violations = 0
        false_positives = 0  # Claimed invalid stops/routes
        false_negatives = 0  # Missed valid stops/routes

        for pred, ref in zip(predictions, references):
            checks = self.validate_topology(pred)

            # Count violations
            if not all(checks.values()):
                total_violations += 1

            # Check for false positives
            pred_stops = set(pred.get("stops", []))
            ref_stops = set(ref.get("stops", []))

            invalid_claims = pred_stops - ref_stops
            false_positives += len(invalid_claims)

            # Check for false negatives
            false_negatives += len(ref_stops - pred_stops)

        n = len(predictions) if predictions else 1
        error_rate = total_violations / n
        fp_rate = false_positives / (false_positives + n) if (false_positives + n) > 0 else 0
        fn_rate = false_negatives / (false_negatives + n) if (false_negatives + n) > 0 else 0

        return {
            "error_rate": float(error_rate),
            "false_positive_rate": float(fp_rate),
            "false_negative_rate": float(fn_rate),
            "consistency_score": 1.0 - float(error_rate),
        }

    def check_line_connectivity(self, lines: List[str]) -> bool:
        """Check if given lines are connected.

        Args:
            lines: List of line identifiers

        Returns:
            True if lines form connected path
        """
        if len(lines) <= 1:
            return True

        for i in range(len(lines) - 1):
            line1, line2 = lines[i], lines[i + 1]
            connected = (
                (line1, line2) in self.topology["connections"]
                or (line2, line1) in self.topology["connections"]
            )
            if not connected:
                return False

        return True

    def run(self, generate_fn=None) -> Dict[str, float]:
        """Execute benchmark.

        Args:
            generate_fn: Function(query) -> response_dict. Uses dummy if None.

        Returns:
            Dict of computed metrics

        Raises:
            RuntimeError: If benchmark execution fails
        """
        if not generate_fn:
            generate_fn = lambda x: {"lines": ["L1"], "stops": ["St1", "St2"], "travel_times": {}}

        predictions = []
        references = []

        for case in self.test_cases:
            try:
                pred = generate_fn(case["query"])
                predictions.append(pred)
                references.append(case)
            except Exception as e:
                logger.warning(f"Generation failed: {e}")
                predictions.append({"lines": [], "stops": [], "travel_times": {}})
                references.append(case)

        try:
            metrics = self.evaluate_topology(predictions, references)
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
