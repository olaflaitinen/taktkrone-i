"""Integration tests for TAKTKRONE-I system components.

This module contains integration tests that verify the interaction between
different components of the TAKTKRONE-I system. These tests require external
dependencies and may take longer to execute than unit tests.

Test Categories:
    - Data ingestion with real API endpoints
    - End-to-end training pipelines
    - Model inference with various inputs
    - API server functionality
    - Database operations with test data

Configuration:
    Integration tests use the TEST_DATA_DIR and INTEGRATION_TEST_TIMEOUT
    constants imported from the parent tests package.

Usage:
    Run integration tests with:
    ```
    pytest tests/integration/ -v --timeout=180
    ```

Environment Variables:
    - SKIP_INTEGRATION_TESTS: Set to skip integration tests
    - TEST_API_BASE_URL: Base URL for API integration tests
    - TEST_DATABASE_URL: Database URL for integration tests
    - MTA_API_KEY: API key for MTA integration tests (optional)
    - MBTA_API_KEY: API key for MBTA integration tests (optional)
"""

import os
from typing import Dict, Any

# Integration test configuration
INTEGRATION_TIMEOUT = 180  # seconds
DEFAULT_API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Test data configuration
INTEGRATION_TEST_DATA = {
    "sample_incidents": "fixtures/integration/sample_incidents.json",
    "test_network": "fixtures/integration/test_network.gtfs.zip",
    "mock_responses": "fixtures/integration/mock_api_responses/",
}

# Environment variable mappings
ENV_VARS = {
    "SKIP_INTEGRATION": "SKIP_INTEGRATION_TESTS",
    "API_BASE_URL": "TEST_API_BASE_URL",
    "DATABASE_URL": "TEST_DATABASE_URL",
    "MTA_API_KEY": "MTA_API_KEY",
    "MBTA_API_KEY": "MBTA_API_KEY",
    "WMATA_API_KEY": "WMATA_API_KEY",
}


def should_skip_integration() -> bool:
    """Check if integration tests should be skipped."""
    return os.getenv("SKIP_INTEGRATION_TESTS", "false").lower() in ("true", "1", "yes")


def get_test_config() -> Dict[str, Any]:
    """Get integration test configuration from environment."""
    return {
        key.lower(): os.getenv(env_var)
        for key, env_var in ENV_VARS.items()
        if os.getenv(env_var) is not None
    }


__all__ = [
    "INTEGRATION_TIMEOUT",
    "DEFAULT_API_TIMEOUT",
    "MAX_RETRIES",
    "INTEGRATION_TEST_DATA",
    "should_skip_integration",
    "get_test_config",
]