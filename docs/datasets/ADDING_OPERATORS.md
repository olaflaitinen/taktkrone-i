# Adding Support for New Transit Operators

This guide provides step-by-step instructions for adding support for a new transit operator to TAKTKRONE-I.

## Overview

The ingestion system uses an adapter pattern where each operator has a dedicated adapter class that inherits from `IngestionAdapter`. The adapter handles operator-specific API interactions and data formats.

## Prerequisites

- Python 3.10+
- Familiarity with RESTful APIs
- Understanding of GTFS and GTFS-RT formats (optional but helpful)
- API credentials for the transit operator's API (if available)

## Step-by-Step Guide

### Step 1: Gather Operator Information

Before implementing, collect:

1. **Operator Code**: Unique identifier (e.g., "mta_nyct", "mbta", "wmata")
2. **Operator Display Name**: Human-readable name (e.g., "Metropolitan Transportation Authority")
3. **Supported Lines**: List of transit lines (e.g., ["1", "2", "3", "A", "C", "E"])
4. **API Endpoints**:
   - GTFS-RT feed URL (if available)
   - Real-time predictions endpoint
   - Service alerts endpoint
   - Static GTFS URL
5. **Authentication**: API key, OAuth, or public access
6. **Rate Limits**: Requests per minute, throttling policies
7. **Data Format**: JSON, Protobuf, XML, or custom

### Step 2: Register the Operator

Add the new operator to the `Operator` enum in `occlm/schemas/__init__.py`:

```python
class Operator(str, Enum):
    """Supported transit operators"""
    MTA_NYCT = "mta_nyct"
    MBTA = "mbta"
    WMATA = "wmata"
    BART = "bart"
    TFL = "tfl"
    NEW_OPERATOR = "new_operator"  # Add here
```

### Step 3: Create the Adapter Class

Create a new file: `occlm/ingestion/adapters/{operator_code}.py`

**Template:**

```python
"""Ingestion adapter for NEW_OPERATOR."""

from typing import Any, Dict, Iterator, Optional

from occlm.ingestion.adapters import IngestionAdapter
from occlm.schemas import IncidentRecord, NetworkSnapshot, Operator, RealtimeEvent

__all__ = ["NewOperatorAdapter"]


class NewOperatorAdapter(IngestionAdapter):
    """
    Adapter for NEW_OPERATOR transit system.

    Handles data ingestion from NEW_OPERATOR's real-time APIs.

    Attributes:
        BASE_URL: Root API endpoint
        SUPPORTED_LINES: List of operator-specific line identifiers
    """

    BASE_URL = "https://api.newoperator.com"
    SUPPORTED_LINES = [
        "Line_A",
        "Line_B",
        # ... add all supported lines
    ]

    def __init__(
        self,
        operator_code: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize NEW_OPERATOR adapter.

        Args:
            operator_code: Operator identifier (e.g., "new_operator")
            api_key: API authentication key
            config: Additional configuration parameters
        """
        super().__init__(operator_code, api_key, config)
        # Initialize operator-specific attributes
        self.operator = Operator.NEW_OPERATOR

    def fetch_realtime_events(self) -> Iterator[RealtimeEvent]:
        """
        Fetch real-time transit events.

        Yields:
            RealtimeEvent: Individual transit events (arrivals, delays, etc.)

        Raises:
            ConnectionError: If API is unreachable
            NotImplementedError: If not yet implemented
        """
        # Implemented: Implement API calls to fetch real-time data
        raise NotImplementedError(
            "fetch_realtime_events not yet implemented for NEW_OPERATOR"
        )

    def fetch_network_snapshot(self) -> NetworkSnapshot:
        """
        Fetch current system-wide operational state.

        Returns:
            NetworkSnapshot: Current network state (all trains, service alerts, etc.)

        Raises:
            ConnectionError: If API is unreachable
            NotImplementedError: If not yet implemented
        """
        # Implemented: Implement aggregation of all system-wide data
        raise NotImplementedError(
            "fetch_network_snapshot not yet implemented for NEW_OPERATOR"
        )

    def fetch_incidents(self) -> Iterator[IncidentRecord]:
        """
        Fetch service disruptions and incidents.

        Yields:
            IncidentRecord: Service alerts, track issues, etc.

        Raises:
            ConnectionError: If API is unreachable
            NotImplementedError: If not yet implemented
        """
        # Implemented: Implement incidents/alerts parsing
        raise NotImplementedError(
            "fetch_incidents not yet implemented for NEW_OPERATOR"
        )

    def fetch_static_network(self) -> Dict[str, Any]:
        """
        Fetch static network topology and schedule data.

        Returns:
            Dict with keys:
                - "stops": List of stop definitions
                - "routes": List of route definitions
                - "trips": List of trip definitions

        Raises:
            ConnectionError: If data source is unreachable
            NotImplementedError: If not yet implemented
        """
        # Implemented: Implement GTFS or static data parsing
        raise NotImplementedError(
            "fetch_static_network not yet implemented for NEW_OPERATOR"
        )

    def validate_connection(self) -> bool:
        """
        Validate that the adapter can connect to the operator's API.

        Returns:
            True if connection successful, False otherwise

        Raises:
            NotImplementedError: If not yet implemented
        """
        # Implemented: Implement API health check
        raise NotImplementedError(
            "validate_connection not yet implemented for NEW_OPERATOR"
        )
```

### Step 4: Register the Adapter

Update `occlm/ingestion/adapters/__init__.py` to export the new adapter:

```python
from .new_operator import NewOperatorAdapter

__all__ = [
    "IngestionAdapter",
    "MTAAdapter",
    "MBTAAdapter",
    "WMATAAdapter",
    "BARTAdapter",
    "TfLAdapter",
    "GenericGTFSAdapter",
    "NewOperatorAdapter",  # Add here
]
```

### Step 5: Register in CLI

Update `occlm/cli/ingest.py` to add the operator to the registry:

```python
ADAPTER_REGISTRY = {
    "mta_nyct": MTAAdapter,
    "mbta": MBTAAdapter,
    "wmata": WMATAAdapter,
    "bart": BARTAdapter,
    "tfl": TfLAdapter,
    "new_operator": NewOperatorAdapter,  # Add here
}
```

### Step 6: Implement API Methods

For each method stub, implement the actual API calls:

**Example: `fetch_realtime_events()`**

```python
def fetch_realtime_events(self) -> Iterator[RealtimeEvent]:
    """Fetch real-time events."""
    try:
        response = requests.get(
            f"{self.BASE_URL}/realtime/events",
            params={"api_key": self.api_key},
            timeout=10,
        )
        response.raise_for_status()

        for item in response.json()["events"]:
            # Parse operator-specific format
            yield RealtimeEvent(
                id=item["event_id"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                operator=self.operator,
                source="api_realtime",
                event_type="trip_update",
                route_id=item.get("route"),
                trip_id=item.get("trip"),
                delay_seconds=item.get("delay", 0),
                provenance=Provenance(
                    ingestion_time=datetime.now(timezone.utc),
                    ingestion_method="new_operator_adapter",
                ),
            )
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch NEW_OPERATOR events: {e}")
```

### Step 7: Add Tests

Create `tests/unit/ingestion/test_new_operator.py`:

```python
"""Unit tests for NEW_OPERATOR adapter."""

import pytest
from occlm.ingestion.adapters import NewOperatorAdapter
from occlm.schemas import Operator


class TestNewOperatorAdapter:
    """Test cases for NewOperatorAdapter."""

    @pytest.fixture
    def adapter(self) -> NewOperatorAdapter:
        """Create adapter instance."""
        return NewOperatorAdapter(
            operator_code="new_operator",
            api_key="test_key",
        )

    def test_initialization(self, adapter: NewOperatorAdapter) -> None:
        """Test adapter initializes correctly."""
        assert adapter.operator_code == "new_operator"
        assert adapter.operator == Operator.NEW_OPERATOR

    def test_supported_lines(self, adapter: NewOperatorAdapter) -> None:
        """Test supported lines."""
        lines = adapter.get_supported_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_fetch_realtime_events_mock(self, adapter: NewOperatorAdapter) -> None:
        """Test fetching realtime events with mocked API."""
        # Use pytest-mock or responses library to mock HTTP responses
        with pytest.raises(NotImplementedError):
            list(adapter.fetch_realtime_events())
```

### Step 8: Document Configuration

Create example configuration in `configs/ingestion/new_operator.yaml`:

```yaml
operator: new_operator
api_key: ${NEW_OPERATOR_API_KEY}  # Reference env var
parameters:
  rate_limit_rps: 10  # requests per second
  timeout_seconds: 30
  retry_count: 3
  cache_ttl_seconds: 60

# If using generic GTFS adapter:
gtfs_url: "https://data.newoperator.com/gtfs.zip"
gtfs_rt_urls:
  - "https://api.newoperator.com/gtfs-rt/trips"
  - "https://api.newoperator.com/gtfs-rt/vehicles"
  - "https://api.newoperator.com/gtfs-rt/alerts"
```

### Step 9: Test the Integration

```bash
# Test adapter initialization
occlm ingest --operator new_operator --validate-only

# Dry-run ingestion
occlm ingest --operator new_operator --dry-run --max-events 10

# Full ingestion to local storage
occlm ingest --operator new_operator --output ./data
```

### Step 10: Submit for Contribution

If contributing to the project:

1. Create a feature branch: `git checkout -b feature/add-new-operator`
2. Implement all methods and tests
3. Ensure tests pass: `pytest tests/`
4. Ensure linting passes: `ruff check occlm/`
5. Ensure type checking passes: `mypy occlm/`
6. Commit and submit pull request

## API Response Handling Examples

### JSON API

```python
response = requests.get(f"{self.BASE_URL}/events", headers={"Authorization": f"Bearer {self.api_key}"})
data = response.json()
for event in data["events"]:
    # Process each event
```

### Protobuf Format (like GTFS-RT)

```python
from google.transit import gtfs_realtime_pb2
response = requests.get(f"{self.BASE_URL}/gtfs-rt/feed")
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)
for entity in feed.entity:
    # Process each entity
```

### XML Format

```python
import xml.etree.ElementTree as ET
response = requests.get(f"{self.BASE_URL}/feed")
root = ET.fromstring(response.content)
for item in root.findall(".//item"):
    # Process each item
```

## Error Handling Best Practices

1. **Connection Errors**: Use `tenacity` library for automatic retries with exponential backoff
2. **Rate Limiting**: Implement backoff-on-429 or queue-based rate limiting
3. **Data Validation**: Validate all incoming data against schemas
4. **Logging**: Log errors and warnings for debugging

## Performance Tips

1. **Caching**: Implement TTL-based caching for frequently accessed data
2. **Batching**: Fetch and process data in batches when possible
3. **Connection Pooling**: Reuse HTTP connections via persistent sessions
4. **Async**: Consider async HTTP clients for concurrent requests

## Troubleshooting

**Q: API returns 401 Unauthorized**
A: Check that `api_key` is set correctly and not expired

**Q: Adapter gets rate limited**
A: Implement backoff logic and respect operator's rate limits

**Q: Data validation failures**
A: Ensure operator-specific fields map correctly to canonical schemas

## References

- [GTFS Format](https://developers.google.com/transit/gtfs)
- [GTFS-Realtime Format](https://developers.google.com/transit/gtfs-realtime)
- [Canonical Schemas](../../docs/architecture/SYSTEM_DESIGN.md)
- [Data Contracts](../../data_contracts/README.md)

---

**Last Updated:** 2026-03-27
**Version:** 0.1 (Draft)
