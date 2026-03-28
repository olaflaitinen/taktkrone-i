from __future__ import annotations

import zipfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from occlm.ingestion import IngestionAdapter
from occlm.ingestion.adapters import (
    BARTAdapter,
    GenericGTFSAdapter,
    MBTAAdapter,
    TfLAdapter,
    WMATAAdapter,
)
from occlm.ingestion.parsers import GTFSStaticParser
from occlm.schemas import NetworkSnapshot, RealtimeEvent


class BaseURLAdapter(IngestionAdapter):
    BASE_URL = "https://example.com/base"

    def __init__(self) -> None:
        super().__init__("base")

    def fetch_realtime_events(
        self, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> Iterator[RealtimeEvent]:
        return super().fetch_realtime_events(start_time, end_time)

    def fetch_network_snapshot(
        self, timestamp: datetime | None = None
    ) -> NetworkSnapshot:
        return super().fetch_network_snapshot(timestamp)

    def fetch_incidents(
        self,
        active_only: bool = True,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list:
        return super().fetch_incidents(active_only, start_time, end_time)

    def fetch_static_network(self) -> dict:
        return super().fetch_static_network()

    def validate_connection(self) -> bool:
        super().validate_connection()
        return True


class BaseGTFSRTAdapter(BaseURLAdapter):
    BASE_URL = None
    BASE_GTFS_RT_URL = "https://example.com/gtfs-rt"

    def __init__(self) -> None:
        super().__init__()
        self.operator_code = "gtfs_rt"


@pytest.mark.parametrize(
    ("adapter_cls", "expected_operator"),
    [
        (BARTAdapter, "bart"),
        (MBTAAdapter, "mbta"),
        (TfLAdapter, "tfl"),
        (WMATAAdapter, "wmata"),
    ],
)
def test_operator_adapters_placeholder_behaviour(
    adapter_cls: type,
    expected_operator: str,
) -> None:
    adapter = adapter_cls(api_key="test-key")

    metadata = adapter.get_metadata()

    assert metadata["operator_code"] == expected_operator
    assert metadata["adapter_class"] == adapter_cls.__name__
    assert metadata["supported_lines"] == adapter.get_supported_lines()
    assert metadata["base_url"].startswith("https://")
    assert adapter.validate_connection() is False

    with pytest.raises(NotImplementedError):
        list(adapter.fetch_realtime_events())
    with pytest.raises(NotImplementedError):
        adapter.fetch_network_snapshot()
    with pytest.raises(NotImplementedError):
        adapter.fetch_incidents()
    with pytest.raises(NotImplementedError):
        adapter.fetch_static_network()


def test_ingestion_adapter_base_metadata_paths() -> None:
    base_url_adapter = BaseURLAdapter()
    gtfs_rt_adapter = BaseGTFSRTAdapter()

    base_metadata = base_url_adapter.get_metadata()
    gtfs_rt_metadata = gtfs_rt_adapter.get_metadata()

    assert base_url_adapter.get_supported_lines() == []
    assert base_url_adapter.fetch_realtime_events() is None
    assert base_url_adapter.fetch_network_snapshot() is None
    assert base_url_adapter.fetch_incidents() is None
    assert base_url_adapter.fetch_static_network() is None
    assert base_url_adapter.validate_connection() is True

    assert base_metadata["base_url"] == "https://example.com/base"
    assert gtfs_rt_metadata["base_url"] == "https://example.com/gtfs-rt"


def test_generic_gtfs_adapter_validation_and_defaults() -> None:
    with pytest.raises(ValueError, match="config is required"):
        GenericGTFSAdapter("demo", "key", {})

    with pytest.raises(ValueError, match="gtfs_rt_urls"):
        GenericGTFSAdapter("demo", "key", {"gtfs_url": "https://example.com/feed.zip"})

    adapter = GenericGTFSAdapter(
        "demo",
        "key",
        {
            "gtfs_url": "https://example.com/feed.zip",
            "gtfs_rt_urls": {"trip_updates": "https://example.com/trips.pb"},
        },
    )

    assert adapter.validate_connection() is False
    assert adapter.get_supported_lines() == []

    with pytest.raises(NotImplementedError):
        list(adapter.fetch_realtime_events())
    with pytest.raises(NotImplementedError):
        adapter.fetch_network_snapshot()
    with pytest.raises(NotImplementedError):
        adapter.fetch_incidents()
    with pytest.raises(NotImplementedError):
        adapter.fetch_static_network()


def test_gtfs_static_parser_loads_local_feed_and_validates(tmp_path: Path) -> None:
    feed_path = tmp_path / "sample_gtfs.zip"
    with zipfile.ZipFile(feed_path, "w") as archive:
        archive.writestr(
            "stops.txt",
            "\n".join(
                [
                    "stop_id,stop_name,stop_lat,stop_lon,location_type",
                    "S1,Station 1,40.0,-73.0,0",
                    "S2,Station 2,41.0,-74.0,1",
                ]
            ),
        )
        archive.writestr(
            "routes.txt",
            "\n".join(
                [
                    "route_id,route_short_name,route_long_name,route_type",
                    "R1,1,Line 1,1",
                ]
            ),
        )
        archive.writestr(
            "trips.txt",
            "\n".join(
                [
                    "route_id,service_id,trip_id,direction_id",
                    "R1,WKD,T1,0",
                ]
            ),
        )
        archive.writestr(
            "stop_times.txt",
            "\n".join(
                [
                    "trip_id,arrival_time,departure_time,stop_id,stop_sequence",
                    "T1,08:00:00,08:00:00,S1,1",
                    "T1,08:05:00,08:05:00,S2,2",
                ]
            ),
        )

    parser = GTFSStaticParser(cache_dir=str(tmp_path / "cache"))
    parser.load_feed(str(feed_path))

    topology = parser.get_network_topology()
    assert topology["statistics"]["total_stops"] == 2
    assert topology["statistics"]["total_routes"] == 1
    assert set(topology["route_stops"]["R1"]) == {"S1", "S2"}
    assert topology["stop_connections"]["S1"] == ["S2"]
    assert parser.validate_topology() == []

    parser.stop_times.append(
        {"trip_id": "UNKNOWN", "stop_id": "S9", "stop_sequence": 3}
    )
    parser.trips["BAD"] = parser.trips["T1"].model_copy(update={"route_id": "MISSING"})
    errors = parser.validate_topology()
    assert any("unknown route" in error for error in errors)
    assert any("unknown trip" in error for error in errors)
    assert any("unknown stop" in error for error in errors)


def test_gtfs_static_parser_handles_missing_files_and_missing_feed(
    tmp_path: Path,
) -> None:
    parser = GTFSStaticParser(cache_dir=str(tmp_path / "cache"))

    with pytest.raises(FileNotFoundError):
        parser.load_feed(str(tmp_path / "does_not_exist.zip"))

    broken_feed = tmp_path / "broken.zip"
    with zipfile.ZipFile(broken_feed, "w") as archive:
        archive.writestr(
            "routes.txt", "route_id,route_short_name,route_long_name,route_type\n"
        )
        archive.writestr("trips.txt", "route_id,service_id,trip_id\n")
        archive.writestr("stop_times.txt", "trip_id,stop_id,stop_sequence\n")

    with pytest.raises(ValueError, match="Required GTFS file missing"):
        parser.load_feed(str(broken_feed))


def test_gtfs_static_parser_uses_fresh_cache_without_downloading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    parser = GTFSStaticParser(cache_dir=str(tmp_path))
    url = "https://example.com/feed.zip"
    cache_file = tmp_path / f"gtfs_{hash(url)}.zip"
    cache_file.write_bytes(b"cached")

    def fail_get(*args, **kwargs):
        raise AssertionError("requests.get should not be called for fresh cache")

    monkeypatch.setattr("occlm.ingestion.parsers.gtfs_static.requests.get", fail_get)

    assert parser._download_feed(url) == cache_file
