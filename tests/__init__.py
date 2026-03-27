"""TAKTKRONE-I test suite."""

__version__ = "0.1.0"

# Test configuration
TEST_DATA_DIR = "tests/fixtures"
INTEGRATION_TEST_TIMEOUT = 60  # seconds
LOAD_TEST_DURATION = 30  # seconds

# Test utilities
__all__ = [
    "TEST_DATA_DIR",
    "INTEGRATION_TEST_TIMEOUT",
    "LOAD_TEST_DURATION"
]
