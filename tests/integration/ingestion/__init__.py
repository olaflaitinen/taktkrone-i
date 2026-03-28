"""Integration tests for TAKTKRONE-I data ingestion components.

This module contains integration tests for the data ingestion adapters
that interact with real transit operator APIs. These tests verify that
adapters can successfully connect to APIs, fetch data, and normalize
it according to TAKTKRONE-I schemas.

Test Coverage:
    - MTA GTFS-RT feed integration
    - MBTA V3 API integration
    - WMATA API integration
    - BART API integration
    - TfL Unified API integration
    - Generic GTFS feed processing
    - Data normalization pipelines
    - Storage operations with real data

Fixtures:
    - Cached API responses for deterministic testing
    - Sample GTFS static feeds
    - Mock network configurations
    - Test database instances

Environment Variables:
    - MTA_API_KEY: API key for MTA real-time data (optional)
    - MBTA_API_KEY: API key for MBTA V3 API (optional)
    - WMATA_API_KEY: API key for WMATA API (optional)
    - TFL_APP_KEY: Application key for TfL API (optional)
    - USE_CACHED_RESPONSES: Use cached responses instead of live APIs

Usage:
    Run ingestion integration tests:
    ```
    pytest tests/integration/ingestion/ -v --timeout=120
    ```

    Run with live APIs (requires API keys):
    ```
    USE_CACHED_RESPONSES=false pytest tests/integration/ingestion/
    ```
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Test configuration
INGESTION_TEST_TIMEOUT = 120  # seconds
API_REQUEST_TIMEOUT = 30  # seconds
CACHE_DIR = Path("tests/fixtures/integration/cached_responses")

# API key mappings
API_KEYS = {
    "mta": os.getenv("MTA_API_KEY"),
    "mbta": os.getenv("MBTA_API_KEY"),
    "wmata": os.getenv("WMATA_API_KEY"),
    "tfl": os.getenv("TFL_APP_KEY"),
    "bart": None,  # BART API doesn't require key
}

# Test data paths
TEST_DATA_PATHS = {
    "gtfs_static": "tests/fixtures/integration/sample_gtfs_static.zip",
    "gtfs_realtime": "tests/fixtures/integration/sample_gtfs_rt.pb",
    "network_config": "tests/fixtures/integration/test_network_config.json",
}


def use_cached_responses() -> bool:
    """Check if tests should use cached responses instead of live APIs."""
    return os.getenv("USE_CACHED_RESPONSES", "true").lower() in ("true", "1", "yes")


def get_api_key(operator: str) -> str | None:
    """Get API key for a specific transit operator."""
    return API_KEYS.get(operator.lower())


def has_api_key(operator: str) -> bool:
    """Check if API key is available for a transit operator."""
    key = get_api_key(operator)
    return key is not None and len(key.strip()) > 0


def get_test_config() -> dict[str, Any]:
    """Get ingestion test configuration."""
    return {
        "use_cached": use_cached_responses(),
        "timeout": API_REQUEST_TIMEOUT,
        "cache_dir": str(CACHE_DIR),
        "api_keys_available": {
            operator: has_api_key(operator) for operator in API_KEYS.keys()
        },
        "test_data_paths": TEST_DATA_PATHS,
    }


__all__ = [
    "INGESTION_TEST_TIMEOUT",
    "API_REQUEST_TIMEOUT",
    "CACHE_DIR",
    "API_KEYS",
    "TEST_DATA_PATHS",
    "use_cached_responses",
    "get_api_key",
    "has_api_key",
    "get_test_config",
]
