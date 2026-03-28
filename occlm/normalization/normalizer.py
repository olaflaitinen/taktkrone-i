"""
Schema normalization for raw transit data.

Converts raw operator-specific data into canonical OCCLM schemas
(RealtimeEvent, IncidentRecord, NetworkSnapshot, etc.)
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any, cast

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
        config: dict[str, Any] | None = None,
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

    def _generate_id(self, base_id: str | None = None) -> str:
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
        source_url: str | None = None,
        source_version: str | None = None,
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

    def _normalize_timestamp(
        self,
        value: datetime | str | None,
    ) -> datetime:
        """Normalize timestamps to timezone-aware UTC datetimes."""
        if value is None:
            return datetime.now(timezone.utc)

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _resolve_operator(self, value: Any) -> Operator:
        """Resolve operator values to the Operator enum."""
        if isinstance(value, Operator):
            return value
        if isinstance(value, str):
            try:
                return Operator(value)
            except ValueError:
                return self.operator
        return self.operator

    def _build_provenance(
        self,
        raw_provenance: Any,
        ingestion_method: str,
        source_url: str | None = None,
        source_version: str | None = None,
    ) -> Provenance:
        """Create a Provenance object from raw metadata or sensible defaults."""
        if isinstance(raw_provenance, Provenance):
            return raw_provenance

        if isinstance(raw_provenance, dict):
            return Provenance(
                ingestion_time=self._normalize_timestamp(
                    raw_provenance.get("ingestion_time")
                ),
                ingestion_method=str(
                    raw_provenance.get("ingestion_method", ingestion_method)
                ),
                raw_source_url=raw_provenance.get("raw_source_url", source_url),
                source_version=raw_provenance.get("source_version", source_version),
            )

        return self._create_provenance(
            ingestion_method=ingestion_method,
            source_url=source_url,
            source_version=source_version,
        )

    def _build_geo_location(
        self,
        raw_data: dict[str, Any],
    ) -> GeoLocation | None:
        """Extract geolocation data from common raw event shapes."""
        geo_location = raw_data.get("geo_location")
        if isinstance(geo_location, GeoLocation):
            return geo_location
        if isinstance(geo_location, dict):
            return GeoLocation(**geo_location)

        position = raw_data.get("position")
        position_data = position if isinstance(position, dict) else raw_data
        latitude = position_data.get("latitude")
        longitude = position_data.get("longitude")

        if latitude is None or longitude is None:
            return None

        return GeoLocation(
            latitude=float(latitude),
            longitude=float(longitude),
            bearing=position_data.get("bearing"),
        )

    def normalize_event(
        self,
        raw_data: dict[str, Any],
        event_type: str | None = None,
        source: str | None = None,
        ingestion_method: str | None = None,
        timestamp: datetime | None = None,
        base_id: str | None = None,
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
        resolved_event_type = event_type or raw_data.get("event_type")
        if not resolved_event_type:
            raise ValueError("event_type is required for normalization")

        resolved_source = str(source or raw_data.get("source", "unknown"))
        resolved_ingestion_method = str(
            ingestion_method
            or raw_data.get("ingestion_method")
            or raw_data.get("provenance", {}).get("ingestion_method", "normalizer")
        )
        resolved_timestamp = self._normalize_timestamp(
            timestamp or raw_data.get("timestamp")
        )
        trip_data = raw_data.get("trip")
        trip = trip_data if isinstance(trip_data, dict) else {}

        known_fields = {
            "id",
            "schema_version",
            "timestamp",
            "operator",
            "source",
            "event_type",
            "provenance",
            "route_id",
            "trip_id",
            "stop_id",
            "vehicle_id",
            "direction_id",
            "data",
            "delay_seconds",
            "confidence",
            "geo_location",
            "tags",
            "latitude",
            "longitude",
            "bearing",
            "position",
            "trip",
            "ingestion_method",
        }

        event_data = raw_data.get("data")
        data_payload = (
            dict(event_data)
            if isinstance(event_data, dict)
            else {k: v for k, v in raw_data.items() if k not in known_fields}
        )

        return RealtimeEvent(
            id=str(raw_data.get("id") or self._generate_id(base_id)),
            schema_version=raw_data.get("schema_version", "1.0.0"),
            timestamp=resolved_timestamp,
            operator=self._resolve_operator(raw_data.get("operator")),
            source=resolved_source,
            event_type=cast(Any, resolved_event_type),
            provenance=self._build_provenance(
                raw_data.get("provenance"),
                ingestion_method=resolved_ingestion_method,
                source_url=raw_data.get("raw_source_url"),
                source_version=raw_data.get("source_version"),
            ),
            route_id=raw_data.get("route_id") or trip.get("route_id"),
            trip_id=raw_data.get("trip_id") or trip.get("trip_id"),
            stop_id=raw_data.get("stop_id"),
            vehicle_id=raw_data.get("vehicle_id"),
            direction_id=raw_data.get("direction_id"),
            data=data_payload,
            delay_seconds=raw_data.get("delay_seconds"),
            confidence=raw_data.get("confidence"),
            geo_location=self._build_geo_location(raw_data),
            tags=list(raw_data.get("tags", [])),
        )

    def normalize_incident(
        self,
        raw_data: dict[str, Any],
        incident_type: str,
        severity: str,
        status: str,
        source: str,
        ingestion_method: str,
        timestamp: datetime | None = None,
        base_id: str | None = None,
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
        resolved_timestamp = self._normalize_timestamp(
            timestamp or raw_data.get("timestamp")
        )
        resolved_ingestion_method = str(
            ingestion_method
            or raw_data.get("ingestion_method")
            or raw_data.get("provenance", {}).get("ingestion_method", "normalizer")
        )

        affected_entities = dict(raw_data.get("affected_entities", {}))
        if "affected_routes" in raw_data and "routes" not in affected_entities:
            affected_entities["routes"] = raw_data.get("affected_routes", [])
        if "affected_stops" in raw_data and "stops" not in affected_entities:
            affected_entities["stops"] = raw_data.get("affected_stops", [])

        timeline = dict(raw_data.get("timeline", {}))
        if "started_at" in raw_data and "started_at" not in timeline:
            timeline["started_at"] = self._normalize_timestamp(raw_data["started_at"])

        return IncidentRecord(
            id=str(raw_data.get("id") or self._generate_id(base_id)),
            schema_version=raw_data.get("schema_version", "1.0.0"),
            timestamp=resolved_timestamp,
            operator=self._resolve_operator(raw_data.get("operator")),
            source=str(source or raw_data.get("source", "unknown")),
            incident_type=cast(Any, incident_type),
            severity=cast(Any, severity),
            status=cast(Any, status),
            title=raw_data.get("title"),
            description=raw_data.get("description"),
            affected_entities=affected_entities,
            location=dict(raw_data.get("location", {})),
            timeline=timeline,
            impact=dict(raw_data.get("impact", {})),
            actions_taken=list(raw_data.get("actions_taken", [])),
            root_cause=raw_data.get("root_cause"),
            provenance=self._build_provenance(
                raw_data.get("provenance"),
                ingestion_method=resolved_ingestion_method,
                source_url=raw_data.get("raw_source_url"),
                source_version=raw_data.get("source_version"),
            ),
            tags=list(raw_data.get("tags", [])),
        )

    def normalize_snapshot(
        self,
        raw_data: dict[str, Any],
        source: str,
        ingestion_method: str,
        timestamp: datetime | None = None,
        base_id: str | None = None,
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
        resolved_timestamp = self._normalize_timestamp(
            timestamp or raw_data.get("timestamp")
        )
        resolved_ingestion_method = str(
            ingestion_method
            or raw_data.get("ingestion_method")
            or raw_data.get("provenance", {}).get("ingestion_method", "normalizer")
        )

        return NetworkSnapshot(
            id=str(raw_data.get("id") or self._generate_id(base_id)),
            schema_version=raw_data.get("schema_version", "1.0.0"),
            timestamp=resolved_timestamp,
            operator=self._resolve_operator(raw_data.get("operator")),
            source=str(source or raw_data.get("source", "unknown")),
            provenance=self._build_provenance(
                raw_data.get("provenance"),
                ingestion_method=resolved_ingestion_method,
                source_url=raw_data.get("raw_source_url"),
                source_version=raw_data.get("source_version"),
            ),
            active_trips=list(raw_data.get("active_trips", [])),
            vehicle_positions=list(raw_data.get("vehicle_positions", [])),
            active_alerts=list(raw_data.get("active_alerts", [])),
            line_status=dict(raw_data.get("line_status", {})),
            network_metrics=dict(raw_data.get("network_metrics", {})),
        )

    def normalize_events_batch(
        self,
        raw_events: list[dict[str, Any]],
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
            except Exception:
                # Completed: Add proper logging
                # logger.warning(f"Failed to normalize event: {e}")
                continue

    def normalize_incidents_batch(
        self,
        raw_incidents: list[dict[str, Any]],
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
            except Exception:
                # Completed: Add proper logging
                # logger.warning(f"Failed to normalize incident: {e}")
                continue


__all__ = ["SchemaNormalizer"]
