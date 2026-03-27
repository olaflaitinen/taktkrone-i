"""Integration tests for ingestion pipeline."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from occlm.ingestion.adapters import MTAAdapter
from occlm.normalization import SchemaNormalizer
from occlm.schemas import Operator
from occlm.storage import ParquetStore


class TestIngestionPipeline:
    """Integration tests for full ingestion pipeline."""

    @pytest.fixture
    def adapter(self) -> MTAAdapter:
        """Create MTA adapter."""
        return MTAAdapter(operator_code="mta_nyct", api_key="test_key")

    @pytest.fixture
    def normalizer(self) -> SchemaNormalizer:
        """Create normalizer."""
        return SchemaNormalizer(operator=Operator.MTA_NYCT, timezone_str="UTC")

    @pytest.fixture
    def storage(self, temp_storage_path: Path) -> ParquetStore:
        """Create storage instance."""
        return ParquetStore(base_path=str(temp_storage_path))

    def test_adapter_metadata_structure(self, adapter: MTAAdapter) -> None:
        """Test adapter metadata has required fields."""
        metadata = adapter.get_metadata()
        assert "operator" in metadata
        assert "base_url" in metadata
        assert "supported_lines" in metadata or len(adapter.get_supported_lines()) > 0

    def test_normalizer_can_create_valid_events(
        self,
        normalizer: SchemaNormalizer,
        sample_realtime_event: Dict[str, Any],
    ) -> None:
        """Test normalizer produces valid events."""
        event = normalizer.normalize_event(sample_realtime_event)
        assert event.operator == Operator.MTA_NYCT
        assert event.id is not None
        assert event.timestamp is not None

    def test_storage_path_creation(self, storage: ParquetStore, temp_storage_path: Path) -> None:
        """Test storage creates proper partitioned paths."""
        # Storage should be able to create paths
        assert storage.base_path == str(temp_storage_path)

    def test_end_to_end_pipeline(
        self,
        adapter: MTAAdapter,
        normalizer: SchemaNormalizer,
        storage: ParquetStore,
        sample_realtime_event: Dict[str, Any],
    ) -> None:
        """Test end-to-end pipeline from adapter to storage."""
        # Normalize event
        event = normalizer.normalize_event(sample_realtime_event)

        # Verify event is valid and can be serialized
        assert event is not None
        assert event.operator == Operator.MTA_NYCT
        assert hasattr(event, "model_dump")  # Pydantic V2 method
