"""
Data storage backends for normalized transit data.

Provides interfaces for persisting normalized transit data including
real-time events, incidents, and network snapshots.
"""

from occlm.storage.parquet_store import ParquetStore

__all__ = ["ParquetStore"]
