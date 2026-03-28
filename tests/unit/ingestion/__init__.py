"""Unit tests for TAKTKRONE-I data ingestion components.

This module contains unit tests for the data ingestion system components,
including adapters, parsers, normalizers, and storage modules. These tests
focus on isolated component behavior with mocked external dependencies.

Test Coverage:
    - Individual adapter functionality (MTA, MBTA, WMATA, BART, TfL)
    - Data parsing and transformation logic
    - Normalization pipeline components
    - Error handling and edge cases
    - Configuration validation
    - Storage interface behavior

Mocking Strategy:
    - HTTP requests mocked with pytest-responses
    - File system operations mocked with pytest-mock
    - Database operations mocked with in-memory stores
    - Time-dependent operations mocked with freezegun

Test Data:
    Unit tests use synthetic and anonymized data samples that exercise
    various code paths without requiring external API access.

Usage:
    Run ingestion unit tests:
    ```
    pytest tests/unit/ingestion/ -v
    ```

    Run with coverage:
    ```
    pytest tests/unit/ingestion/ --cov=occlm.ingestion
    ```

    Run specific adapter tests:
    ```
    pytest tests/unit/ingestion/test_mta.py -v
    ```

Test Organization:
    - test_adapters.py: Base adapter functionality
    - test_mta.py: MTA-specific adapter tests
    - test_mbta.py: MBTA-specific adapter tests
    - test_wmata.py: WMATA-specific adapter tests
    - test_bart.py: BART-specific adapter tests
    - test_tfl.py: TfL-specific adapter tests
    - test_normalizer.py: Data normalization tests
    - test_validator.py: Data validation tests
    - test_storage.py: Storage interface tests
"""

from __future__ import annotations

from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Test configuration
UNIT_TEST_TIMEOUT = 30  # seconds
MOCK_DATA_DIR = Path("tests/fixtures/unit/ingestion")

# Mock data samples for different transit operators
MOCK_RESPONSES = {
    "mta_gtfs_rt": {
        "trip_updates": "mta_trip_updates.pb",
        "vehicle_positions": "mta_vehicle_positions.pb",
        "service_alerts": "mta_service_alerts.pb",
    },
    "mbta_v3": {
        "vehicles": "mbta_vehicles.json",
        "predictions": "mbta_predictions.json",
        "alerts": "mbta_alerts.json",
        "routes": "mbta_routes.json",
        "stops": "mbta_stops.json",
    },
    "wmata": {
        "incidents": "wmata_incidents.json",
        "positions": "wmata_positions.json",
        "predictions": "wmata_predictions.json",
    },
    "bart": {
        "advisories": "bart_advisories.json",
        "estimates": "bart_estimates.json",
        "stations": "bart_stations.json",
    },
    "tfl": {
        "line_status": "tfl_line_status.json",
        "arrivals": "tfl_arrivals.json",
        "disruptions": "tfl_disruptions.json",
    },
}

# Expected data schemas for validation tests
EXPECTED_SCHEMAS = {
    "normalized_incident": {
        "required_fields": [
            "incident_id",
            "operator",
            "timestamp",
            "incident_type",
            "severity",
            "location",
        ],
        "optional_fields": [
            "description",
            "affected_lines",
            "estimated_duration",
            "resolution_actions",
        ],
    },
    "normalized_vehicle": {
        "required_fields": [
            "vehicle_id",
            "operator",
            "route_id",
            "timestamp",
            "position",
        ],
        "optional_fields": [
            "speed",
            "occupancy",
            "delay_seconds",
            "next_stop",
        ],
    },
}


@dataclass
class TestDataConfig:
    """Configuration for unit test data."""

    mock_data_dir: Path = MOCK_DATA_DIR
    timeout: int = UNIT_TEST_TIMEOUT
    use_real_timestamps: bool = False
    validate_schemas: bool = True


class MockResponseHelper:
    """Helper for creating mock HTTP responses."""

    def __init__(self, config: TestDataConfig):
        self.config = config

    def get_mock_data_path(self, operator: str, data_type: str) -> Path:
        """Get path to mock data file."""
        filename = MOCK_RESPONSES.get(operator, {}).get(data_type)
        if not filename:
            raise ValueError(f"No mock data for {operator}.{data_type}")
        return self.config.mock_data_dir / operator / filename

    def load_mock_json(self, operator: str, data_type: str) -> Dict[str, Any]:
        """Load mock JSON data."""
        import json
        path = self.get_mock_data_path(operator, data_type)
        with open(path) as f:
            return json.load(f)

    def load_mock_protobuf(self, operator: str, data_type: str) -> bytes:
        """Load mock protobuf data."""
        path = self.get_mock_data_path(operator, data_type)
        with open(path, 'rb') as f:
            return f.read()


def create_mock_incident(operator: str = "test", **overrides) -> Dict[str, Any]:
    """Create a mock incident for testing."""
    incident = {
        "incident_id": "test_incident_001",
        "operator": operator,
        "timestamp": "2024-03-27T10:30:00Z",
        "incident_type": "signal_failure",
        "severity": "medium",
        "location": {
            "station": "Test Station",
            "line": "Test Line",
            "coordinates": [40.7128, -74.0060],
        },
        "description": "Signal failure causing delays",
        "affected_lines": ["Test Line"],
        "estimated_duration": 900,
    }
    incident.update(overrides)
    return incident


def create_mock_vehicle(operator: str = "test", **overrides) -> Dict[str, Any]:
    """Create a mock vehicle position for testing."""
    vehicle = {
        "vehicle_id": "test_vehicle_001",
        "operator": operator,
        "route_id": "Test Route",
        "timestamp": "2024-03-27T10:30:00Z",
        "position": {
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        "speed": 25.5,
        "occupancy": "MANY_SEATS_AVAILABLE",
        "delay_seconds": 120,
    }
    vehicle.update(overrides)
    return vehicle


__all__ = [
    "UNIT_TEST_TIMEOUT",
    "MOCK_DATA_DIR",
    "MOCK_RESPONSES",
    "EXPECTED_SCHEMAS",
    "TestDataConfig",
    "MockResponseHelper",
    "create_mock_incident",
    "create_mock_vehicle",
]
