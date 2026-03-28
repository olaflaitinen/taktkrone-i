"""Unit tests for data normalization."""

from __future__ import annotations

from typing import Any

import pytest

from occlm.normalization import DataValidator, SchemaNormalizer, ValidationResult
from occlm.schemas import Operator, RealtimeEvent


class TestSchemaNormalizer:
    """Test cases for SchemaNormalizer."""

    @pytest.fixture
    def normalizer(self) -> SchemaNormalizer:
        """Create normalizer instance."""
        return SchemaNormalizer(
            operator=Operator.MTA_NYCT, id_prefix="mta", timezone_str="UTC"
        )

    def test_normalizer_initialization(self, normalizer: SchemaNormalizer) -> None:
        """Test normalizer initializes correctly."""
        assert normalizer.operator == Operator.MTA_NYCT
        assert normalizer.timezone_str == "UTC"

    def test_normalize_event(
        self, normalizer: SchemaNormalizer, sample_realtime_event: dict[str, Any]
    ) -> None:
        """Test event normalization."""
        event = normalizer.normalize_event(sample_realtime_event)
        assert isinstance(event, RealtimeEvent)
        assert event.operator == Operator.MTA_NYCT
        assert event.route_id == "1"


class TestDataValidator:
    """Test cases for DataValidator."""

    @pytest.fixture
    def validator(self) -> DataValidator:
        """Create validator instance."""
        return DataValidator()

    def test_validator_initialization(self, validator: DataValidator) -> None:
        """Test validator initializes correctly."""
        assert validator is not None

    def test_validate_realtime_event(
        self, validator: DataValidator, sample_realtime_event: dict[str, Any]
    ) -> None:
        """Test realtime event validation."""
        event = RealtimeEvent(**sample_realtime_event)
        is_valid, errors = validator.validate_realtime_event(event)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        assert is_valid is True

    def test_validation_result_structure(self) -> None:
        """Test ValidationResult has correct structure."""
        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert isinstance(result.errors, list)

    def test_validate_completeness(
        self, validator: DataValidator, sample_realtime_event: dict[str, Any]
    ) -> None:
        """Test completeness validation."""
        event = RealtimeEvent(**sample_realtime_event)
        required_fields = ["id", "timestamp", "operator"]
        is_valid, errors = validator.validate_completeness(event, required_fields)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
