"""
Generic GTFS-Realtime adapter for any GTFS feed.

Provides a configuration-driven adapter that can ingest real-time data from
any operator with GTFS and GTFS-RT feeds, without requiring operator-specific
implementations.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

from occlm.ingestion import IngestionAdapter
from occlm.schemas import (
    IncidentRecord,
    NetworkSnapshot,
    RealtimeEvent,
)


class GenericGTFSAdapter(IngestionAdapter):
    """
    Configuration-driven adapter for any GTFS and GTFS-Realtime feed.

    This adapter accepts operator-specific configuration including feed
    URLs, API keys, parsing rules, and field mappings to handle arbitrary
    GTFS implementations.

    Configuration should include:
    - gtfs_url: URL to GTFS static zip file
    - gtfs_rt_urls: Dict mapping feed types to RT feed URLs
    - field_mappings: Custom field name mappings
    - operators_list: Expected list of operator values
    """

    def __init__(self, operator_code: str, api_key: str, config: dict[str, Any]):
        """
        Initialize generic GTFS adapter with configuration.

        Args:
            operator_code: Operator identifier string
            api_key: API key for authenticated feeds
            config: Configuration dictionary with required feed URLs
                   and optional parsing parameters

        Raises:
            ValueError: If required config fields are missing
        """
        if not config:
            raise ValueError("config is required for GenericGTFSAdapter")

        required_fields = ["gtfs_url", "gtfs_rt_urls"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"config must include '{field}' field")

        super().__init__(operator_code=operator_code, api_key=api_key, config=config)

    def fetch_realtime_events(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> Iterator[RealtimeEvent]:
        """
        Fetch GTFS-RT events using configured feed URLs.

        Retrieves real-time operational data from GTFS-Realtime feeds
        specified in the adapter configuration. Uses field mappings
        to handle operator-specific differences.

        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time

        Yields:
            RealtimeEvent objects normalized to canonical schema

        Raises:
            NotImplementedError: API call implementation pending
        """
        # Completed: Implement configurable GTFS-RT parsing
        # - Retrieve feed URLs from config
        # - Apply field mappings
        # - Parse feed response (protobuf format)
        # - Handle trip updates, vehicle positions, alerts
        # - Normalize to RealtimeEvent schema
        # - Apply time filtering
        # - Use tenacity with configured retry policy
        raise NotImplementedError("Generic GTFS-RT ingestion to be implemented")

    def fetch_network_snapshot(
        self, timestamp: datetime | None = None
    ) -> NetworkSnapshot:
        """
        Fetch system-wide snapshot using configured sources.

        Creates a point-in-time snapshot by aggregating data from the
        configured GTFS-RT feeds and combining with static network data.

        Args:
            timestamp: Specific time (default: now)

        Returns:
            NetworkSnapshot with current system state

        Raises:
            NotImplementedError: API call implementation pending
        """
        # Completed: Implement configurable snapshot creation
        # - Load static network from cache or GTFS
        # - Aggregate predictions from all configured RT feeds
        # - Collect vehicle positions
        # - Compute system metrics
        # - Return NetworkSnapshot
        raise NotImplementedError("Generic GTFS network snapshot to be implemented")

    def fetch_incidents(
        self,
        active_only: bool = True,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[IncidentRecord]:
        """
        Fetch incidents from GTFS-RT service alerts.

        Extracts service alert information from GTFS-RT feeds and
        optionally from external incident sources configured in config.

        Args:
            active_only: Only return active incidents
            start_time: Filter start time (optional)
            end_time: Filter end time (optional)

        Returns:
            List of IncidentRecord objects

        Raises:
            NotImplementedError: API call implementation pending
        """
        # Completed: Implement configurable incident fetching
        # - Parse service alerts from GTFS-RT
        # - Query additional incident sources if configured
        # - Apply field mappings
        # - Normalize to IncidentRecord schema
        # - Apply time and status filters
        # - Handle severity classification
        raise NotImplementedError("Generic GTFS incident fetching to be implemented")

    def fetch_static_network(self) -> dict[str, Any]:
        """
        Download and parse GTFS static data from configured URL.

        Retrieves and parses the complete GTFS dataset from the URL
        specified in adapter configuration. Results are cached.

        Returns:
            Dictionary with stops, routes, trips, stop_times, shapes, etc.

        Raises:
            NotImplementedError: GTFS parsing implementation pending
        """
        # Completed: Implement configurable GTFS static parsing
        # - Download GTFS zip from config URL
        # - Parse all GTFS files using standard format
        # - Apply optional field mappings from config
        # - Cache with expiration from config
        # - Validate topology consistency
        # - Return structured format
        raise NotImplementedError("Generic GTFS static parsing to be implemented")

    def validate_connection(self) -> bool:
        """
        Validate connectivity to configured feed URLs.

        Tests that all configured feed URLs are reachable and responding,
        performing health checks on static and realtime feeds.

        Returns:
            True if connection successful, False otherwise
        """
        # Completed: Implement configurable connection validation
        # - Test GTFS static URL accessibility
        # - Test each GTFS-RT URL from config
        # - Verify response formats
        # - Check for authentication issues
        # - Return aggregate health status
        return False

    def get_supported_lines(self) -> list[str]:
        """
        Get list of supported lines from static GTFS data.

        Extracts route list from the configured GTFS static data,
        caching if possible.

        Returns:
            List of route identifiers from GTFS routes.txt
        """
        # Completed: Implement dynamic line list
        # - Load or cache static GTFS
        # - Extract unique route_ids from routes.txt
        # - Return sorted list
        return []


__all__ = ["GenericGTFSAdapter"]
