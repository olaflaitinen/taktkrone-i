"""
Unit tests for canonical schemas
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from occlm.schemas import (
    Message,
    OCCDialogueSample,
    Operator,
    Provenance,
    RealtimeEvent,
)


class TestProvenance:
    """Test Provenance schema"""

    def test_valid_provenance(self):
        """Test valid provenance creation"""
        prov = Provenance(
            ingestion_time=datetime.now(),
            ingestion_method="test_adapter",
            raw_source_url="https://taktkrone.ai/api",
            source_version="1.0.0",
        )
        assert prov.ingestion_method == "test_adapter"

    def test_provenance_requires_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            Provenance(ingestion_method="test_adapter")  # missing ingestion_time


class TestRealtimeEvent:
    """Test RealtimeEvent schema"""

    def test_valid_realtime_event(self):
        """Test valid realtime event creation"""
        event = RealtimeEvent(
            id="test_event_001",
            schema_version="1.0.0",
            timestamp=datetime.now(),
            operator=Operator.MTA_NYCT,
            source="test_source",
            event_type="trip_update",
            provenance=Provenance(
                ingestion_time=datetime.now(), ingestion_method="test"
            ),
        )
        assert event.operator == Operator.MTA_NYCT
        assert event.event_type == "trip_update"

    def test_realtime_event_with_optional_fields(self):
        """Test event with optional fields"""
        event = RealtimeEvent(
            id="test_event_002",
            schema_version="1.0.0",
            timestamp=datetime.now(),
            operator=Operator.MBTA,
            source="test_source",
            event_type="delay_event",
            provenance=Provenance(
                ingestion_time=datetime.now(), ingestion_method="test"
            ),
            route_id="Red",
            trip_id="trip_123",
            delay_seconds=240,
            confidence=0.85,
        )
        assert event.route_id == "Red"
        assert event.delay_seconds == 240
        assert event.confidence == 0.85

    def test_invalid_event_type(self):
        """Test that invalid event type is rejected"""
        with pytest.raises(ValidationError):
            RealtimeEvent(
                id="test_event_003",
                timestamp=datetime.now(),
                operator=Operator.MTA_NYCT,
                source="test",
                event_type="invalid_type",  # Not in enum
                provenance=Provenance(
                    ingestion_time=datetime.now(), ingestion_method="test"
                ),
            )


class TestOCCDialogueSample:
    """Test OCCDialogueSample schema"""

    def test_valid_dialogue_sample(self):
        """Test valid dialogue sample creation"""
        sample = OCCDialogueSample(
            id="sample_001",
            schema_version="1.0.0",
            timestamp=datetime.now(),
            operator=Operator.MTA_NYCT,
            source="synthetic",
            task_type="disruption_diagnosis",
            messages=[
                Message(role="system", content="You are an expert OCC analyst."),
                Message(role="user", content="What is causing the delay?"),
                Message(
                    role="assistant",
                    content="The delay appears to be caused by a signal failure.",
                ),
            ],
            metadata={"difficulty": "medium", "split": "train"},
        )
        assert len(sample.messages) == 3
        assert sample.task_type == "disruption_diagnosis"
        assert sample.metadata["difficulty"] == "medium"

    def test_dialogue_requires_metadata_fields(self):
        """Test that metadata must include required fields"""
        with pytest.raises(ValidationError):
            OCCDialogueSample(
                id="sample_002",
                schema_version="1.0.0",
                timestamp=datetime.now(),
                operator=Operator.MBTA,
                source="synthetic",
                task_type="situation_summarization",
                messages=[
                    Message(role="user", content="Test"),
                    Message(role="assistant", content="Response"),
                ],
                metadata={},  # Missing 'difficulty' and 'split'
            )

    def test_dialogue_requires_minimum_messages(self):
        """Test that at least 2 messages are required"""
        with pytest.raises(ValidationError):
            OCCDialogueSample(
                id="sample_003",
                schema_version="1.0.0",
                timestamp=datetime.now(),
                operator=Operator.BART,
                source="synthetic",
                task_type="recovery_planning",
                messages=[Message(role="user", content="Only one message")],
                metadata={"difficulty": "easy", "split": "train"},
            )


class TestMessage:
    """Test Message schema"""

    def test_valid_message(self):
        """Test valid message creation"""
        msg = Message(role="user", content="Test message")
        assert msg.role == "user"
        assert msg.content == "Test message"

    def test_message_with_name(self):
        """Test message with optional name"""
        msg = Message(role="assistant", content="Response", name="dispatcher_1")
        assert msg.name == "dispatcher_1"

    def test_invalid_role(self):
        """Test that invalid role is rejected"""
        with pytest.raises(ValidationError):
            Message(role="invalid_role", content="Test")

    def test_empty_content_rejected(self):
        """Test that empty content is rejected"""
        with pytest.raises(ValidationError):
            Message(role="user", content="")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
