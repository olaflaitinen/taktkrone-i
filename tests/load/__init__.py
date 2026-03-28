"""Load and performance tests for TAKTKRONE-I system.

This module contains load tests and performance benchmarks for the TAKTKRONE-I
serving infrastructure. These tests validate system behavior under various
load conditions and help identify performance bottlenecks.

Test Categories:
    - API endpoint load testing
    - Model inference throughput testing
    - Concurrent request handling
    - Memory usage under load
    - Database performance testing
    - Cache efficiency testing

Tools Used:
    - Locust for distributed load testing
    - pytest-benchmark for micro-benchmarks
    - Memory profiler for memory usage analysis
    - Custom metrics collection for latency analysis

Performance Targets:
    - API response time P95 < 2000ms
    - API response time P50 < 500ms
    - Throughput > 50 requests/second
    - Memory usage stable under load
    - Error rate < 1% under normal load

Usage:
    Run load tests with Locust:
    ```
    locust -f tests/load/test_api_load.py --host https://taktkrone.ai
    ```

    Run benchmark tests with pytest:
    ```
    pytest tests/load/ --benchmark-only
    ```

Environment Variables:
    - LOAD_TEST_DURATION: Duration for load tests in seconds (default: 60)
    - LOAD_TEST_USERS: Number of concurrent users (default: 10)
    - LOAD_TEST_SPAWN_RATE: User spawn rate per second (default: 2)
    - API_BASE_URL: Base URL for API load tests
"""

from __future__ import annotations

import os
from typing import Dict, Any
from dataclasses import dataclass

# Load test configuration
DEFAULT_DURATION = 60  # seconds
DEFAULT_USERS = 10
DEFAULT_SPAWN_RATE = 2  # users per second
DEFAULT_API_TIMEOUT = 30  # seconds

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "p50_latency_ms": 500,
    "p95_latency_ms": 2000,
    "p99_latency_ms": 5000,
    "min_throughput_rps": 50,
    "max_error_rate": 0.01,  # 1%
    "max_memory_mb": 2048,
}


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    duration: int = DEFAULT_DURATION
    users: int = DEFAULT_USERS
    spawn_rate: float = DEFAULT_SPAWN_RATE
    api_timeout: int = DEFAULT_API_TIMEOUT
    api_base_url: str = "https://taktkrone.ai"

    @classmethod
    def from_env(cls) -> "LoadTestConfig":
        """Create configuration from environment variables."""
        return cls(
            duration=int(os.getenv("LOAD_TEST_DURATION", DEFAULT_DURATION)),
            users=int(os.getenv("LOAD_TEST_USERS", DEFAULT_USERS)),
            spawn_rate=float(os.getenv("LOAD_TEST_SPAWN_RATE", DEFAULT_SPAWN_RATE)),
            api_timeout=int(os.getenv("API_TIMEOUT", DEFAULT_API_TIMEOUT)),
            api_base_url=os.getenv("API_BASE_URL", "https://taktkrone.ai"),
        )


def get_test_queries() -> list[dict]:
    """Get sample queries for load testing."""
    return [
        {
            "query": "Signal failure at 42nd Street on the 4/5/6 lines. What should OCC do?",
            "operator": "mta_nyct",
            "max_tokens": 256,
        },
        {
            "query": "Train bunching reported on Red Line between Harvard and Porter.",
            "operator": "mbta",
            "max_tokens": 200,
        },
        {
            "query": "Medical emergency at Union Station. Platform 3 blocked.",
            "operator": "wmata",
            "max_tokens": 300,
        },
        {
            "query": "Power outage affecting eastbound trains at Montgomery Street.",
            "operator": "bart",
            "max_tokens": 250,
        },
        {
            "query": "Weekend engineering works on Central Line. Service updates needed.",
            "operator": "tfl",
            "max_tokens": 200,
        },
    ]


def validate_performance_thresholds(metrics: Dict[str, float]) -> Dict[str, bool]:
    """Validate performance metrics against thresholds."""
    results = {}
    for metric, threshold in PERFORMANCE_THRESHOLDS.items():
        if metric in metrics:
            if "latency" in metric:
                results[metric] = metrics[metric] <= threshold
            elif "throughput" in metric:
                results[metric] = metrics[metric] >= threshold
            elif "error_rate" in metric:
                results[metric] = metrics[metric] <= threshold
            elif "memory" in metric:
                results[metric] = metrics[metric] <= threshold
    return results


__all__ = [
    "DEFAULT_DURATION",
    "DEFAULT_USERS",
    "DEFAULT_SPAWN_RATE",
    "PERFORMANCE_THRESHOLDS",
    "LoadTestConfig",
    "get_test_queries",
    "validate_performance_thresholds",
]
