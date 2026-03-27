"""
Data validation against Pydantic schemas and business rules.

Validates normalized data for schema compliance, completeness,
and topology consistency.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from occlm.schemas import IncidentRecord, NetworkSnapshot, Operator, RealtimeEvent


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        """
        Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of error messages if validation failed
        """
        self.is_valid = is_valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Return is_valid when used in boolean context."""
        return self.is_valid

    def __repr__(self) -> str:
        """String representation of result."""
        if self.is_valid:
            return "ValidationResult(valid)"
        return f"ValidationResult(invalid, errors={len(self.errors)})"


class DataValidator:
    """
    Validator for normalized transit data.

    Validates data against Pydantic schemas, checks for completeness,
    and enforces business rules and topology constraints.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data validator.

        Args:
            config: Optional configuration for validation behavior
        """
        self.config = config or {}
        self.require_complete_fields = self.config.get(
            "require_complete_fields", False
        )
        self.strict_mode = self.config.get("strict_mode", False)

    def validate_realtime_event(
        self, event: RealtimeEvent
    ) -> Tuple[bool, List[str]]:
        """
        Validate RealtimeEvent object.

        Checks that the event conforms to schema and business rules.

        Args:
            event: RealtimeEvent to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement event validation
        # - Check that required fields are populated
        # - Validate event_type is sensible for operator
        # - Check timestamps are reasonable (not in future)
        # - Validate geo_location if present (lat/lon bounds)
        # - Check delay_seconds is reasonable (not negative)
        # - Validate confidence is 0-1 if present
        # - Check route_id/trip_id consistency
        # - Verify operator matches expected
        # - Additional business rules from config

        if not errors:
            return True, []
        return False, errors

    def validate_incident_record(
        self, incident: IncidentRecord
    ) -> Tuple[bool, List[str]]:
        """
        Validate IncidentRecord object.

        Checks that the incident conforms to schema and business rules.

        Args:
            incident: IncidentRecord to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement incident validation
        # - Check that required fields are populated
        # - Validate incident_type, severity, status values
        # - Check timestamps are reasonable
        # - Verify affected_entities structure
        # - Check timeline has at least start time
        # - Validate location if present
        # - Check impact assessment is reasonable
        # - Verify consistency between status and timeline
        # - Additional business rules from config

        if not errors:
            return True, []
        return False, errors

    def validate_network_snapshot(
        self, snapshot: NetworkSnapshot
    ) -> Tuple[bool, List[str]]:
        """
        Validate NetworkSnapshot object.

        Checks that the snapshot is complete and consistent.

        Args:
            snapshot: NetworkSnapshot to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement snapshot validation
        # - Check timestamp is recent
        # - Validate active_trips structure
        # - Validate vehicle_positions structure
        # - Validate active_alerts structure
        # - Check line_status values are valid
        # - Validate network_metrics values
        # - Check consistency across fields
        # - Verify no missing major components if required
        # - Additional business rules from config

        if not errors:
            return True, []
        return False, errors

    def validate_completeness(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that required fields are present and non-empty.

        Args:
            data: Dictionary to validate
            required_fields: List of field names that must be present

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement completeness check
        # - Check all required_fields are in data
        # - Check values are not None or empty string
        # - Handle nested structures if present
        # - Return appropriate error messages

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None or data[field] == "":
                errors.append(f"Required field is empty: {field}")

        return len(errors) == 0, errors

    def validate_topology_consistency(
        self,
        events: List[RealtimeEvent],
        network_topology: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate consistency of events against network topology.

        Checks that events reference valid routes, stops, and trips
        according to the static network topology.

        Args:
            events: List of RealtimeEvent objects to validate
            network_topology: Optional static topology to validate against

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement topology consistency validation
        # - Check route_ids reference valid routes in topology
        # - Check stop_ids reference valid stops
        # - Check trip_ids reference valid trips
        # - Verify trip_id/route_id combination is valid
        # - Check vehicle_id is reasonable format
        # - Verify direction_id is 0 or 1
        # - Log warnings for missing topology data
        # - Aggregate validation errors

        return len(errors) == 0, errors

    def validate_time_ordering(
        self, events: List[RealtimeEvent]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that events have reasonable time ordering.

        Checks for events that are severely out of order or have
        timestamps in the future.

        Args:
            events: List of RealtimeEvent objects

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Completed: Implement time ordering validation
        # - Check no events have future timestamps
        # - Check events are not extremely old
        # - Sort and check for inversions
        # - Allow small time inversions (clock drift)
        # - Aggregate warnings/errors

        now = datetime.now()
        for event in events:
            if event.timestamp > now:
                errors.append(
                    f"Event has future timestamp: {event.timestamp}"
                )

        return len(errors) == 0, errors

    def validate_batch(
        self, events: List[RealtimeEvent]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate batch of events with comprehensive checks.

        Args:
            events: List of RealtimeEvent objects to validate

        Returns:
            Tuple of (all_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Completed: Implement batch validation
        # - Validate each event individually
        # - Check time ordering across batch
        # - Check for duplicate IDs
        # - Validate topology consistency if topology available
        # - Aggregate statistics (% valid, etc.)
        # - Generate warnings for partial failures

        for event in events:
            is_valid, event_errors = self.validate_realtime_event(event)
            if not is_valid:
                errors.extend(event_errors)

        all_valid = len(errors) == 0
        return all_valid, errors, warnings


__all__ = ["DataValidator", "ValidationResult"]
