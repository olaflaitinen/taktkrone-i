"""
Base adapter interface for transit data ingestion.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from occlm.schemas import IncidentRecord, NetworkSnapshot, RealtimeEvent


class IngestionAdapter(ABC):
    """
    Abstract base class for operator-specific data ingestion adapters.

    Each adapter implements ingestion logic for a specific transit operator's
    data sources (GTFS, GTFS-RT, custom APIs, etc.)
    """

    def __init__(
        self,
        operator_code: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize adapter.

        Args:
            operator_code: Operator identifier (e.g., "mta_nyct")
            api_key: Optional API key for authenticated endpoints
            config: Optional configuration dictionary
        """
        self.operator_code = operator_code
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    def fetch_realtime_events(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Iterator[RealtimeEvent]:
        """
        Fetch realtime operational events.

        Args:
            start_time: Optional start of time window
            end_time: Optional end of time window

        Yields:
            RealtimeEvent objects
        """
        pass

    @abstractmethod
    def fetch_network_snapshot(self, timestamp: Optional[datetime] = None) -> NetworkSnapshot:
        """
        Fetch current network state snapshot.

        Args:
            timestamp: Specific time to snapshot (default: now)

        Returns:
            NetworkSnapshot object
        """
        pass

    @abstractmethod
    def fetch_incidents(
        self,
        active_only: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[IncidentRecord]:
        """
        Fetch disruption and incident records.

        Args:
            active_only: Only return active incidents
            start_time: Optional start of time window
            end_time: Optional end of time window

        Returns:
            List of IncidentRecord objects
        """
        pass

    @abstractmethod
    def fetch_static_network(self) -> Dict[str, Any]:
        """
        Fetch static network topology (GTFS or equivalent).

        Returns:
            Dictionary with network topology data
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that adapter can connect to data sources.

        Returns:
            True if connection successful
        """
        pass

    def get_supported_lines(self) -> List[str]:
        """
        Get list of supported lines/routes for this operator.

        Returns:
            List of line/route identifiers
        """
        return []

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        return {
            "operator_code": self.operator_code,
            "adapter_class": self.__class__.__name__,
            "supported_lines": self.get_supported_lines(),
            "config": self.config,
        }


__all__ = ["IngestionAdapter"]
