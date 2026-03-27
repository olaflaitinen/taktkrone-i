"""
Operator-specific ingestion adapters for transit data sources.

This package contains adapters for ingesting real-time and static data from
various transit operators. Each adapter implements the IngestionAdapter
interface and provides operator-specific data source handling.
"""

from occlm.ingestion.adapters.bart import BARTAdapter
from occlm.ingestion.adapters.generic_gtfs import GenericGTFSAdapter
from occlm.ingestion.adapters.mbta import MBTAAdapter
from occlm.ingestion.adapters.mta import MTAAdapter
from occlm.ingestion.adapters.tfl import TfLAdapter
from occlm.ingestion.adapters.wmata import WMATAAdapter

__all__ = [
    "MTAAdapter",
    "MBTAAdapter",
    "WMATAAdapter",
    "BARTAdapter",
    "TfLAdapter",
    "GenericGTFSAdapter",
]
