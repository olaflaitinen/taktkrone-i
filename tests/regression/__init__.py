"""Regression tests for TAKTKRONE-I system.

This module contains regression tests that ensure previously working functionality
continues to work correctly after code changes. These tests focus on preserving
system behavior and preventing the introduction of bugs through regression.

Test Categories:
    - Model output consistency tests
    - API response format stability
    - Data processing pipeline regression
    - Performance regression detection
    - Configuration compatibility tests
    - Backwards compatibility validation

Test Strategy:
    - Golden output comparison for critical paths
    - Snapshot testing for complex outputs
    - Performance baseline maintenance
    - Error message consistency validation
    - API contract preservation

Regression Test Types:
    - Output Regression: Compare model outputs with known good results
    - Performance Regression: Ensure latency/throughput within bounds
    - API Regression: Validate API response schemas and formats
    - Data Regression: Check data processing consistency
    - Config Regression: Verify configuration changes don't break existing setups

Usage:
    Run all regression tests:
    ```
    pytest tests/regression/ -v
    ```

    Update regression baselines:
    ```
    pytest tests/regression/ --update-snapshots
    ```

    Run performance regression tests:
    ```
    pytest tests/regression/ -k performance
    ```

Environment Variables:
    - UPDATE_REGRESSION_BASELINES: Update stored baselines (use with caution)
    - REGRESSION_TOLERANCE: Numeric tolerance for comparisons (default: 1e-6)
    - SKIP_SLOW_REGRESSION: Skip slow regression tests
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Regression test configuration
BASELINES_DIR = Path("tests/regression/baselines")
SNAPSHOTS_DIR = Path("tests/regression/snapshots")
DEFAULT_TOLERANCE = 1e-6
MAX_OUTPUT_LENGTH = 10000  # characters

# Baseline categories
BASELINE_CATEGORIES = {
    "model_outputs": "Model inference outputs for standard queries",
    "api_responses": "API response formats and schemas",
    "data_processing": "Data normalization and processing results",
    "performance_metrics": "Performance benchmarks and timings",
    "error_messages": "Error message formats and content",
}


@dataclass
class RegressionConfig:
    """Configuration for regression tests."""

    tolerance: float = DEFAULT_TOLERANCE
    update_baselines: bool = False
    skip_slow: bool = False
    max_output_length: int = MAX_OUTPUT_LENGTH

    @classmethod
    def from_env(cls) -> "RegressionConfig":
        """Create configuration from environment variables."""
        return cls(
            tolerance=float(os.getenv("REGRESSION_TOLERANCE", DEFAULT_TOLERANCE)),
            update_baselines=os.getenv("UPDATE_REGRESSION_BASELINES", "false").lower()
            in ("true", "1", "yes"),
            skip_slow=os.getenv("SKIP_SLOW_REGRESSION", "false").lower()
            in ("true", "1", "yes"),
            max_output_length=int(
                os.getenv("MAX_OUTPUT_LENGTH", MAX_OUTPUT_LENGTH)
            ),
        )


class BaselineManager:
    """Manages regression test baselines."""

    def __init__(self, config: Optional[RegressionConfig] = None):
        self.config = config or RegressionConfig.from_env()
        self.baselines_dir = BASELINES_DIR
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def load_baseline(self, category: str, test_name: str) -> Optional[Dict[str, Any]]:
        """Load a baseline for comparison."""
        baseline_file = self.baselines_dir / f"{category}_{test_name}.json"
        if baseline_file.exists():
            with open(baseline_file) as f:
                return json.load(f)
        return None

    def save_baseline(self, category: str, test_name: str, data: Dict[str, Any]) -> None:
        """Save a new baseline."""
        if not self.config.update_baselines:
            return

        baseline_file = self.baselines_dir / f"{category}_{test_name}.json"
        with open(baseline_file, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def compare_outputs(
        self, current: Any, baseline: Any, tolerance: Optional[float] = None
    ) -> bool:
        """Compare current output with baseline."""
        tolerance = tolerance or self.config.tolerance

        if isinstance(current, (int, float)) and isinstance(baseline, (int, float)):
            return abs(current - baseline) <= tolerance
        elif isinstance(current, str) and isinstance(baseline, str):
            return current == baseline
        elif isinstance(current, list) and isinstance(baseline, list):
            if len(current) != len(baseline):
                return False
            return all(
                self.compare_outputs(c, b, tolerance)
                for c, b in zip(current, baseline)
            )
        elif isinstance(current, dict) and isinstance(baseline, dict):
            if set(current.keys()) != set(baseline.keys()):
                return False
            return all(
                self.compare_outputs(current[k], baseline[k], tolerance)
                for k in current.keys()
            )
        else:
            return current == baseline


def get_regression_test_cases() -> List[Dict[str, Any]]:
    """Get standard regression test cases."""
    return [
        {
            "name": "signal_failure_basic",
            "input": {
                "query": "Signal failure at Union Square on the N/Q/R/W lines",
                "operator": "mta_nyct",
            },
            "category": "model_outputs",
        },
        {
            "name": "medical_emergency",
            "input": {
                "query": "Medical emergency on platform at Times Square",
                "operator": "mta_nyct",
            },
            "category": "model_outputs",
        },
        {
            "name": "api_health_check",
            "endpoint": "/health",
            "method": "GET",
            "category": "api_responses",
        },
        {
            "name": "api_model_info",
            "endpoint": "/v1/model/info",
            "method": "GET",
            "category": "api_responses",
        },
    ]


def should_update_baselines() -> bool:
    """Check if baselines should be updated."""
    return os.getenv("UPDATE_REGRESSION_BASELINES", "false").lower() in (
        "true",
        "1",
        "yes",
    )


__all__ = [
    "BASELINES_DIR",
    "SNAPSHOTS_DIR",
    "BASELINE_CATEGORIES",
    "RegressionConfig",
    "BaselineManager",
    "get_regression_test_cases",
    "should_update_baselines",
]
