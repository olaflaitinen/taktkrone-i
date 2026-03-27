"""GTFS Static feed parser for topology and schedule data."""

import csv
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import requests
from pydantic import BaseModel

__all__ = ["GTFSStaticParser", "GTFSStop", "GTFSRoute", "GTFSTrip"]


class GTFSStop(BaseModel):
    """GTFS stop definition."""

    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    stop_code: Optional[str] = None
    location_type: Optional[int] = 0  # 0=stop, 1=station
    parent_station: Optional[str] = None


class GTFSRoute(BaseModel):
    """GTFS route definition."""

    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: int  # 0=tram, 1=subway, 2=rail, 3=bus, etc.
    route_color: Optional[str] = None
    agency_id: Optional[str] = None


class GTFSTrip(BaseModel):
    """GTFS trip definition."""

    trip_id: str
    route_id: str
    service_id: str
    direction_id: Optional[int] = None
    block_id: Optional[str] = None
    shape_id: Optional[str] = None


class GTFSStaticParser:
    """
    Parser for GTFS static feeds to extract network topology.

    Supports both local ZIP files and remote URLs.
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """
        Initialize GTFS parser.

        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./gtfs_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.stops: Dict[str, GTFSStop] = {}
        self.routes: Dict[str, GTFSRoute] = {}
        self.trips: Dict[str, GTFSTrip] = {}
        self.stop_times: List[Dict[str, Any]] = []

    def load_feed(self, feed_source: str) -> None:
        """
        Load GTFS feed from file or URL.

        Args:
            feed_source: Path to ZIP file or URL

        Raises:
            FileNotFoundError: If local file not found
            ConnectionError: If remote URL not accessible
        """
        if urlparse(feed_source).scheme in ('http', 'https'):
            feed_path = self._download_feed(feed_source)
        else:
            feed_path = Path(feed_source)
            if not feed_path.exists():
                raise FileNotFoundError(f"GTFS feed not found: {feed_source}")

        self._parse_zip_file(feed_path)

    def _download_feed(self, url: str) -> Path:
        """Download GTFS feed from URL."""
        # Generate cache filename from URL
        cache_file = self.cache_dir / f"gtfs_{hash(url)}.zip"

        if cache_file.exists():
            # Check if cache is less than 24 hours old
            age_hours = (datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )).total_seconds() / 3600

            if age_hours < 24:
                return cache_file

        # Download fresh copy
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        cache_file.write_bytes(response.content)
        return cache_file

    def _parse_zip_file(self, zip_path: Path) -> None:
        """Parse GTFS ZIP file."""
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Required files
            self._parse_stops(zip_file)
            self._parse_routes(zip_file)
            self._parse_trips(zip_file)
            self._parse_stop_times(zip_file)

            # Optional files
            try:
                self._parse_shapes(zip_file)
            except KeyError:
                pass  # shapes.txt is optional

    def _parse_stops(self, zip_file: zipfile.ZipFile) -> None:
        """Parse stops.txt file."""
        try:
            with zip_file.open('stops.txt') as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                for row in reader:
                    stop = GTFSStop(
                        stop_id=row['stop_id'],
                        stop_name=row['stop_name'],
                        stop_lat=float(row['stop_lat']),
                        stop_lon=float(row['stop_lon']),
                        stop_code=row.get('stop_code'),
                        location_type=int(row.get('location_type', 0)),
                        parent_station=row.get('parent_station')
                    )
                    self.stops[stop.stop_id] = stop
        except KeyError as e:
            raise ValueError(f"Required GTFS file missing: {e}")

    def _parse_routes(self, zip_file: zipfile.ZipFile) -> None:
        """Parse routes.txt file."""
        with zip_file.open('routes.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
            for row in reader:
                route = GTFSRoute(
                    route_id=row['route_id'],
                    route_short_name=row.get('route_short_name', ''),
                    route_long_name=row.get('route_long_name', ''),
                    route_type=int(row['route_type']),
                    route_color=row.get('route_color'),
                    agency_id=row.get('agency_id')
                )
                self.routes[route.route_id] = route

    def _parse_trips(self, zip_file: zipfile.ZipFile) -> None:
        """Parse trips.txt file."""
        with zip_file.open('trips.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
            for row in reader:
                trip = GTFSTrip(
                    trip_id=row['trip_id'],
                    route_id=row['route_id'],
                    service_id=row['service_id'],
                    direction_id=int(row['direction_id']) if row.get('direction_id') else None,
                    block_id=row.get('block_id'),
                    shape_id=row.get('shape_id')
                )
                self.trips[trip.trip_id] = trip

    def _parse_stop_times(self, zip_file: zipfile.ZipFile) -> None:
        """Parse stop_times.txt file."""
        with zip_file.open('stop_times.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
            for row in reader:
                self.stop_times.append({
                    'trip_id': row['trip_id'],
                    'stop_id': row['stop_id'],
                    'stop_sequence': int(row['stop_sequence']),
                    'arrival_time': row.get('arrival_time'),
                    'departure_time': row.get('departure_time')
                })

    def _parse_shapes(self, zip_file: zipfile.ZipFile) -> None:
        """Parse shapes.txt file (optional)."""
        # Completed: Implement shape parsing for route geometry
        pass

    def get_network_topology(self) -> Dict[str, Any]:
        """
        Build network topology graph.

        Returns:
            Dictionary with stops, routes, and connectivity
        """
        # Build route connectivity
        route_stops = {}
        for stop_time in self.stop_times:
            trip = self.trips.get(stop_time['trip_id'])
            if trip:
                route_id = trip.route_id
                if route_id not in route_stops:
                    route_stops[route_id] = set()
                route_stops[route_id].add(stop_time['stop_id'])

        # Build stop connectivity
        stop_connections = {}
        for stop_id in self.stops:
            stop_connections[stop_id] = []

        # Connect stops within each route
        for route_id, stop_ids in route_stops.items():
            stop_list = sorted(list(stop_ids))
            for i in range(len(stop_list) - 1):
                stop1, stop2 = stop_list[i], stop_list[i + 1]
                if stop2 not in stop_connections[stop1]:
                    stop_connections[stop1].append(stop2)
                if stop1 not in stop_connections[stop2]:
                    stop_connections[stop2].append(stop1)

        return {
            'stops': {sid: stop.model_dump() for sid, stop in self.stops.items()},
            'routes': {rid: route.model_dump() for rid, route in self.routes.items()},
            'route_stops': {rid: list(stops) for rid, stops in route_stops.items()},
            'stop_connections': stop_connections,
            'statistics': {
                'total_stops': len(self.stops),
                'total_routes': len(self.routes),
                'total_trips': len(self.trips),
                'total_stop_times': len(self.stop_times)
            }
        }

    def validate_topology(self) -> List[str]:
        """
        Validate GTFS data for consistency.

        Returns:
            List of validation error messages
        """
        errors = []

        # Check for orphaned trips
        for trip_id, trip in self.trips.items():
            if trip.route_id not in self.routes:
                errors.append(f"Trip {trip_id} references unknown route {trip.route_id}")

        # Check for orphaned stop times
        stop_time_trips = {st['trip_id'] for st in self.stop_times}
        for trip_id in stop_time_trips:
            if trip_id not in self.trips:
                errors.append(f"Stop times reference unknown trip {trip_id}")

        # Check for orphaned stops in stop times
        stop_time_stops = {st['stop_id'] for st in self.stop_times}
        for stop_id in stop_time_stops:
            if stop_id not in self.stops:
                errors.append(f"Stop times reference unknown stop {stop_id}")

        return errors
