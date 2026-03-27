"""
Schema normalization for raw transit data.

Converts raw operator-specific data into canonical OCCLM schemas
(RealtimeEvent, IncidentRecord, NetworkSnapshot, etc.)
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Union

from occlm.schemas import (
    GeoLocation,
    IncidentRecord,
    NetworkSnapshot,
    Operator,
    Provenance,
    RealtimeEvent,
)


class SchemaNormalizer:
    """
    Normalizer for converting raw data to canonical schemas.

    Handles conversion of operator-specific data formats to standardized
    OCCLM schemas, including timezone handling, ID mapping, and field
    transformation.
    """

    def __init__(
        self,
        operator: Operator,
        id_prefix: str,
        timezone_str: str = "UTC",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize schema normalizer.

        Args:
            operator: The transit operator (from Operator enum)
            id_prefix: Prefix for generated IDs (e.g., "evt_mta")
            timezone_str: IANA timezone string for the operator
            config: Optional configuration for normalization behavior
        """
        self.operator = operator
        self.id_prefix = id_prefix
        self.timezone_str = timezone_str
        self.config = config or {}
        self.id_counter = 0

    def _generate_id(self, base_id: Optional[str] = None) -> str:
        """
        Generate unique normalized ID.

        Args:
            base_id: Optional base ID to incorporate

        Returns:
            Generated ID string with operator prefix
        """
        if base_id:
            return f"{self.id_prefix}_{base_id}"
        self.id_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{self.id_prefix}_{timestamp}_{self.id_counter:06d}"

    def _create_provenance(
        self,
        ingestion_method: str,
        source_url: Optional[str] = None,
        source_version: Optional[str] = None,
    ) -> Provenance:
        """
        Create Provenance object for normalized data.

        Args:
            ingestion_method: Name of the adapter/method used
            source_url: Optional source API endpoint URL
            source_version: Optional version of source data

        Returns:
            Provenance object with current timestamp
        """
        return Provenance(
            ingestion_time=datetime.now(timezone.utc),
            ingestion_method=ingestion_method,
            raw_source_url=source_url,
            source_version=source_version,
        )

    def normalize_event(
        self,
        raw_data: Dict[str, Any],
        event_type: str,
        source: str,
        ingestion_method: str,
        timestamp: Optional[datetime] = None,
        base_id: Optional[str] = None,
    ) -> RealtimeEvent:
        """
        Normalize raw data to RealtimeEvent schema.

        Converts operator-specific real-time event data into the
        canonical RealtimeEvent format with proper validation.

        Args:
            raw_data: Raw operator-specific event data
            event_type: Type of event (from RealtimeEvent.event_type)
            source: Data source identifier
            ingestion_method: Adapter/method that provided the data
            timestamp: Event timestamp (default: now)
            base_id: Optional base for ID generation

        Returns:
            Normalized RealtimeEvent object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Completed: Implement event normalization
        # - Validate event_type is in allowed values
        # - Extract and map operator-specific fields
        # - Parse timestamps with timezone awareness
        # - Convert coordinates to GeoLocation if present
        # - Handle optional fields (delay_seconds, confidence, etc.)
        # - Validate against schema
        # - Use _generate_id and _create_provenance helpers
        raise NotImplementedError("Event normalization to be implemented")

    def normalize_incident(
        self,
        raw_data: Dict[str, Any],
        incident_type: str,
        severity: str,
        status: str,
        source: str,
        ingestion_method: str,
        timestamp: Optional[datetime] = None,
        base_id: Optional[str] = None,
    ) -> IncidentRecord:
        """
        Normalize raw data to IncidentRecord schema.

        Converts operator-specific incident/disruption data into the
        canonical IncidentRecord format.

        Args:
            raw_data: Raw operator-specific incident data
            incident_type: Type of incident (from IncidentRecord schema)
            severity: Severity level (low, medium, high, critical)
            status: Current status (active, monitoring, resolved, cleared)
            source: Data source identifier
            ingestion_method: Adapter/method that provided the data
            timestamp: Event timestamp (default: now)
            base_id: Optional base for ID generation

        Returns:
            Normalized IncidentRecord object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Completed: Implement incident normalization
        # - Validate incident_type, severity, status against allowed values
        # - Extract affected_entities (routes, stops, etc.)
        # - Extract location information
        # - Map timeline events (start, expected_resolution, etc.)
        # - Extract impact assessment
        # - Validate against schema
        # - Use _generate_id and _create_provenance helpers
        raise NotImplementedError("Incident normalization to be implemented")

    def normalize_snapshot(
        self,
        raw_data: Dict[str, Any],
        source: str,
        ingestion_method: str,
        timestamp: Optional[datetime] = None,
        base_id: Optional[str] = None,
    ) -> NetworkSnapshot:
        """
        Normalize raw data to NetworkSnapshot schema.

        Converts aggregated operator data into a canonical point-in-time
        snapshot of the entire network operational state.

        Args:
            raw_data: Raw operator-specific snapshot data
            source: Data source identifier
            ingestion_method: Adapter/method that provided the data
            timestamp: Snapshot timestamp (default: now)
            base_id: Optional base for ID generation

        Returns:
            Normalized NetworkSnapshot object

        Raises:
            ValueError: If required fields are missing
        """
        # Completed: Implement snapshot normalization
        # - Validate timestamp
        # - Extract active trips list
        # - Extract vehicle positions
        # - Extract active alerts
        # - Map line status information
        # - Calculate network metrics if not provided
        # - Validate against schema
        # - Use _generate_id and _create_provenance helpers
        raise NotImplementedError("Snapshot normalization to be implemented")

    def normalize_events_batch(
        self,
        raw_events: List[Dict[str, Any]],
        event_type: str,
        source: str,
        ingestion_method: str,
    ) -> Iterator[RealtimeEvent]:
        """
        Normalize batch of raw events efficiently.

        Args:
            raw_events: List of raw event dictionaries
            event_type: Type for all events
            source: Data source identifier
            ingestion_method: Adapter/method used

        Yields:
            Normalized RealtimeEvent objects
        """
        # Completed: Implement batch normalization
        # - Iterate through raw_events
        # - Normalize each event
        # - Yield normalized events
        # - Handle errors gracefully (log and continue)
        for raw_event in raw_events:
            try:
                yield self.normalize_event(
                    raw_event, event_type, source, ingestion_method
                )
            except Exception as e:
                # Completed: Add proper logging
                # logger.warning(f"Failed to normalize event: {e}")
                continue

    def normalize_incidents_batch(
        self,
        raw_incidents: List[Dict[str, Any]],
        source: str,
        ingestion_method: str,
    ) -> Iterator[IncidentRecord]:
        """
        Normalize batch of raw incidents efficiently.

        Args:
            raw_incidents: List of raw incident dictionaries
            source: Data source identifier
            ingestion_method: Adapter/method used

        Yields:
            Normalized IncidentRecord objects
        """
        # Completed: Implement batch normalization
        # - Iterate through raw_incidents
        # - Extract incident_type, severity, status from raw data
        # - Normalize each incident
        # - Yield normalized incidents
        # - Handle errors gracefully
        for raw_incident in raw_incidents:
            try:
                # Extract standard fields from raw_incident
                incident_type = raw_incident.get("incident_type", "other")
                severity = raw_incident.get("severity", "medium")
                status = raw_incident.get("status", "active")

                yield self.normalize_incident(
                    raw_incident,
                    incident_type,
                    severity,
                    status,
                    source,
                    ingestion_method,
                )
            except Exception as e:
                # Completed: Add proper logging
                # logger.warning(f"Failed to normalize incident: {e}")
                continue


__all__ = ["SchemaNormalizer"]
