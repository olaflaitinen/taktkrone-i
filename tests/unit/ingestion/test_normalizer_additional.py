from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from occlm.normalization import DataValidator, SchemaNormalizer, ValidationResult
from occlm.schemas import GeoLocation, Operator, Provenance


class PlainObject:
    def __init__(self, id: str, operator: str | None = None) -> None:
        self.id = id
        self.operator = operator


@pytest.fixture
def normalizer() -> SchemaNormalizer:
    return SchemaNormalizer(operator=Operator.MTA_NYCT, id_prefix="mta")


def test_normalizer_helper_methods(normalizer: SchemaNormalizer) -> None:
    generated_id = normalizer._generate_id()

    assert normalizer._generate_id("base") == "mta_base"
    assert generated_id.startswith("mta_")
    assert normalizer._normalize_timestamp(None).tzinfo == timezone.utc
    assert (
        normalizer._normalize_timestamp(datetime(2026, 3, 27, 17, 30, 0)).tzinfo
        == timezone.utc
    )
    assert (
        normalizer._normalize_timestamp("2026-03-27T17:30:00Z").tzinfo == timezone.utc
    )
    assert normalizer._resolve_operator(Operator.MBTA) == Operator.MBTA
    assert normalizer._resolve_operator("wmata") == Operator.WMATA
    assert normalizer._resolve_operator("unknown_operator") == Operator.MTA_NYCT
    assert normalizer._resolve_operator(123) == Operator.MTA_NYCT


def test_normalizer_builds_provenance_and_geo_location(
    normalizer: SchemaNormalizer,
) -> None:
    provenance = Provenance(
        ingestion_time=datetime(2026, 3, 27, tzinfo=timezone.utc),
        ingestion_method="fixture",
    )

    assert normalizer._build_provenance(provenance, "ignored") is provenance
    assert (
        normalizer._build_provenance(
            {
                "ingestion_time": "2026-03-27T17:30:00Z",
                "ingestion_method": "feed",
                "raw_source_url": "https://example.com",
            },
            "fallback",
        ).ingestion_method
        == "feed"
    )
    assert normalizer._build_provenance(None, "fallback").ingestion_method == "fallback"

    geo = GeoLocation(latitude=40.0, longitude=-73.0)
    assert normalizer._build_geo_location({"geo_location": geo}) is geo
    assert (
        normalizer._build_geo_location(
            {"geo_location": {"latitude": 41.0, "longitude": -74.0}}
        ).latitude
        == 41.0
    )
    assert (
        normalizer._build_geo_location(
            {"position": {"latitude": "42.0", "longitude": "-75.0", "bearing": 180}}
        ).bearing
        == 180
    )
    assert (
        normalizer._build_geo_location({"latitude": 43.0, "longitude": -76.0}).longitude
        == -76.0
    )
    assert normalizer._build_geo_location({"route_id": "1"}) is None


def test_normalizer_normalize_event_variants(
    normalizer: SchemaNormalizer,
) -> None:
    raw_event = {
        "timestamp": "2026-03-27T17:30:00Z",
        "operator": "wmata",
        "event_type": "trip_update",
        "source": "trip_updates",
        "trip": {"route_id": "Blue", "trip_id": "T1"},
        "position": {"latitude": "40.5", "longitude": "-73.9", "bearing": 90},
        "provenance": {"ingestion_time": "2026-03-27T17:31:00Z"},
        "delay_seconds": 30,
        "custom_field": "custom-value",
        "tags": ["delay"],
    }

    event = normalizer.normalize_event(raw_event, base_id="evt1")
    explicit_data_event = normalizer.normalize_event(
        {"event_type": "trip_update", "data": {"delay_seconds": 45}},
        source="manual",
        ingestion_method="unit_test",
    )

    assert event.id == "mta_evt1"
    assert event.operator == Operator.WMATA
    assert event.route_id == "Blue"
    assert event.trip_id == "T1"
    assert event.geo_location is not None
    assert event.geo_location.latitude == 40.5
    assert event.data == {"custom_field": "custom-value"}
    assert event.tags == ["delay"]
    assert explicit_data_event.data == {"delay_seconds": 45}
    assert explicit_data_event.provenance.ingestion_method == "unit_test"

    with pytest.raises(ValueError, match="event_type is required"):
        normalizer.normalize_event({"route_id": "1"})


def test_normalizer_normalize_incident_and_snapshot(
    normalizer: SchemaNormalizer,
    sample_incident_record,
) -> None:
    incident = normalizer.normalize_incident(
        sample_incident_record,
        incident_type="signal_failure",
        severity="high",
        status="active",
        source="service_alerts",
        ingestion_method="unit_test",
    )
    snapshot = normalizer.normalize_snapshot(
        {
            "operator": "mbta",
            "timestamp": "2026-03-27T17:30:00Z",
            "active_trips": [{"trip_id": "T1"}],
            "vehicle_positions": [{"vehicle_id": "V1"}],
            "active_alerts": [{"id": "A1"}],
            "line_status": {"Red": "delayed"},
            "network_metrics": {"active_incidents": 1},
            "provenance": {"ingestion_time": "2026-03-27T17:31:00Z"},
        },
        source="snapshot_feed",
        ingestion_method="unit_test",
        base_id="snap1",
    )

    assert incident.id == sample_incident_record["id"]
    assert incident.affected_entities["routes"] == ["1", "2", "3"]
    assert incident.affected_entities["stops"] == ["101", "102"]
    assert incident.timeline["started_at"].tzinfo == timezone.utc
    assert incident.provenance.ingestion_method == "mta_gtfs_rt_adapter"
    assert snapshot.id == "mta_snap1"
    assert snapshot.operator == Operator.MBTA
    assert snapshot.network_metrics["active_incidents"] == 1


def test_normalizer_batch_methods_skip_invalid_records(
    normalizer: SchemaNormalizer,
) -> None:
    events = list(
        normalizer.normalize_events_batch(
            [
                {"event_type": "trip_update", "source": "feed"},
                {"route_id": "1"},
            ],
            event_type="trip_update",
            source="feed",
            ingestion_method="unit_test",
        )
    )
    incidents = list(
        normalizer.normalize_incidents_batch(
            [
                {
                    "incident_type": "signal_failure",
                    "severity": "high",
                    "status": "active",
                },
                {"timeline": 1},
            ],
            source="alerts",
            ingestion_method="unit_test",
        )
    )

    assert len(events) == 2
    assert len(incidents) == 1


def test_data_validator_support_methods(
    normalizer: SchemaNormalizer,
    sample_realtime_event,
    sample_incident_record,
) -> None:
    validator = DataValidator()
    event = normalizer.normalize_event(sample_realtime_event)
    incident = normalizer.normalize_incident(
        sample_incident_record,
        incident_type="signal_failure",
        severity="high",
        status="active",
        source="service_alerts",
        ingestion_method="unit_test",
    )
    snapshot = normalizer.normalize_snapshot(
        {"active_trips": [{"trip_id": "T1"}]},
        source="snapshot_feed",
        ingestion_method="unit_test",
    )

    valid_result = ValidationResult(True)
    invalid_result = ValidationResult(False, ["missing route_id"])

    assert bool(valid_result) is True
    assert bool(invalid_result) is False
    assert repr(valid_result) == "ValidationResult(valid)"
    assert "invalid" in repr(invalid_result)
    assert validator.validate_realtime_event(event) == (True, [])
    assert validator.validate_incident_record(incident) == (True, [])
    assert validator.validate_network_snapshot(snapshot) == (True, [])
    assert validator.validate_topology_consistency([event], {"routes": {}}) == (
        True,
        [],
    )

    is_complete, errors = validator.validate_completeness(
        {"id": "1", "source": ""},
        ["id", "source", "operator"],
    )
    assert is_complete is False
    assert "Required field is empty: source" in errors
    assert "Missing required field: operator" in errors

    assert validator.validate_completeness(event, ["id", "source"])[0] is True
    assert validator.validate_completeness(PlainObject("abc"), ["id"])[0] is True
    assert validator.validate_completeness(123, ["id"]) == (
        False,
        ["Unsupported data type for completeness validation"],
    )

    future_event = event.model_copy(
        update={"timestamp": datetime.now(timezone.utc) + timedelta(hours=1)}
    )
    valid_ordering, ordering_errors = validator.validate_time_ordering([future_event])
    assert valid_ordering is False
    assert "future timestamp" in ordering_errors[0]

    assert validator.validate_batch([event]) == (True, [], [])

    def fake_validate_realtime_event(_event):
        return False, ["bad event"]

    validator.validate_realtime_event = fake_validate_realtime_event  # type: ignore[method-assign]
    assert validator.validate_batch([event, event]) == (
        False,
        ["bad event", "bad event"],
        [],
    )
