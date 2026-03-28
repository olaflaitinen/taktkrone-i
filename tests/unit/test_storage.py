from __future__ import annotations

from datetime import datetime

import pytest

from occlm.storage import ParquetStore


def test_parquet_store_partition_path_and_defaults(temp_storage_path) -> None:
    store = ParquetStore(base_path=temp_storage_path)

    partition = store._get_partition_path(
        operator="mta_nyct",
        data_type="events",
        timestamp=datetime(2026, 3, 27, 17, 30, 0),
    )

    assert store.partition_by == ParquetStore.DEFAULT_PARTITION_COLS
    assert partition == (
        temp_storage_path / "events" / "mta_nyct" / "2026" / "03" / "27"
    )


def test_parquet_store_placeholder_methods_raise_and_return_defaults(
    temp_storage_path,
) -> None:
    store = ParquetStore(base_path=temp_storage_path)

    with pytest.raises(NotImplementedError):
        store.save_events([], "mta_nyct")
    with pytest.raises(NotImplementedError):
        store.save_incidents([], "mta_nyct")
    with pytest.raises(NotImplementedError):
        store.save_snapshots([], "mta_nyct")
    with pytest.raises(NotImplementedError):
        store.query_events()
    with pytest.raises(NotImplementedError):
        store.query_incidents()
    with pytest.raises(NotImplementedError):
        store.query_snapshots()

    assert store.get_statistics() == {}
    assert store.cleanup_old_data(days_to_keep=7) == {}
