"""Unit tests for MTA adapter."""

import pytest

from occlm.ingestion.adapters import MTAAdapter


class TestMTAAdapter:
    """Test cases for MTAAdapter."""

    @pytest.fixture
    def adapter(self) -> MTAAdapter:
        """Create adapter instance."""
        return MTAAdapter(api_key="test_key_123")

    def test_adapter_initialization(self, adapter: MTAAdapter) -> None:
        """Test adapter initializes correctly."""
        assert adapter.api_key == "test_key_123"
        assert adapter is not None

    def test_supported_lines(self, adapter: MTAAdapter) -> None:
        """Test get_supported_lines returns valid lines."""
        lines = adapter.get_supported_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert "1" in lines or "A" in lines  # MTA has numbered and lettered lines

    def test_metadata(self, adapter: MTAAdapter) -> None:
        """Test get_metadata returns valid structure."""
        metadata = adapter.get_metadata()
        assert isinstance(metadata, dict)
        assert "adapter_class" in metadata
        assert "operator_code" in metadata
        assert metadata["operator_code"] == "mta_nyct"

    def test_fetch_realtime_events_not_implemented(self, adapter: MTAAdapter) -> None:
        """Test fetch_realtime_events raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            list(adapter.fetch_realtime_events())

    def test_fetch_network_snapshot_not_implemented(self, adapter: MTAAdapter) -> None:
        """Test fetch_network_snapshot raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            adapter.fetch_network_snapshot()

    def test_fetch_incidents_not_implemented(self, adapter: MTAAdapter) -> None:
        """Test fetch_incidents raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            list(adapter.fetch_incidents())

    def test_fetch_static_network_not_implemented(self, adapter: MTAAdapter) -> None:
        """Test fetch_static_network raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            adapter.fetch_static_network()

    def test_validate_connection_not_implemented(self, adapter: MTAAdapter) -> None:
        """Test validate_connection returns bool."""
        result = adapter.validate_connection()
        assert isinstance(result, bool)
