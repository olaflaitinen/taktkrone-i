"""Test fixtures for ingestion adapters."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from occlm.schemas import IncidentRecord, Operator, Provenance, RealtimeEvent


@pytest.fixture
def sample_realtime_event() -> Dict[str, Any]:
    """Sample realtime event fixture."""
    return {
        "id": "evt_mta_20260327_001",
        "schema_version": "1.0.0",
        "timestamp": datetime(2026, 3, 27, 17, 30, 0, tzinfo=timezone.utc),
        "operator": Operator.MTA_NYCT,
        "source": "gtfs_rt_trip_updates",
        "event_type": "trip_update",
        "provenance": {
            "ingestion_time": datetime(
                2026, 3, 27, 17, 30, 15, tzinfo=timezone.utc
            ),
            "ingestion_method": "mta_gtfs_rt_adapter",
            "raw_source_url": None,
            "source_version": "1.0",
        },
        "route_id": "1",
        "trip_id": "1234567",
        "stop_id": "101",
        "delay_seconds": 240,
        "confidence": 0.95,
    }


@pytest.fixture
def sample_incident_record() -> Dict[str, Any]:
    """Sample incident record fixture."""
    return {
        "id": "inc_mta_20260327_001",
        "schema_version": "1.0.0",
        "timestamp": datetime(2026, 3, 27, 17, 30, 0, tzinfo=timezone.utc),
        "operator": Operator.MTA_NYCT,
        "source": "service_alerts",
        "incident_type": "signal_failure",
        "severity": "high",
        "provenance": {
            "ingestion_time": datetime(
                2026, 3, 27, 17, 30, 15, tzinfo=timezone.utc
            ),
            "ingestion_method": "mta_gtfs_rt_adapter",
            "raw_source_url": None,
            "source_version": "1.0",
        },
        "affected_routes": ["1", "2", "3"],
        "affected_stops": ["101", "102"],
        "description": "Signal failure at Station A",
        "duration_estimate_minutes": 30,
        "started_at": datetime(2026, 3, 27, 17, 0, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def mock_mta_gtfs_rt_response() -> bytes:
    """Mock MTA GTFS-RT protobuf response (as JSON for testing)."""
    return json.dumps(
        {
            "entity": [
                {
                    "id": "1",
                    "trip_update": {
                        "trip": {"trip_id": "1234567", "route_id": "1"},
                        "stop_time_update": [
                            {
                                "stop_sequence": 5,
                                "stop_id": "101",
                                "arrival": {"delay": 120},
                                "departure": {"delay": 120},
                            }
                        ],
                    },
                },
                {
                    "id": "2",
                    "vehicle": {
                        "trip": {"trip_id": "7654321", "route_id": "2"},
                        "position": {
                            "latitude": 40.7128,
                            "longitude": -74.0060,
                            "speed": 12.5,
                        },
                        "timestamp": 1711561800,
                    },
                },
            ],
        }
    ).encode()


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Temporary directory for storage tests."""
    return tmp_path / "parquet_store"
