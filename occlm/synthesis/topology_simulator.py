"""
Topology simulator for delay propagation and network effects.

Simulates transit network topology and propagates disruptions through the
network graph to calculate cascading delays and affected routes.
"""

from typing import Any, Dict, List, Optional
import json

__all__ = [
    "TopologySimulator",
]


class TopologySimulator:
    """
    Simulates transit network topology and delay propagation.

    Uses a graph-based representation of the transit network to propagate
    disruptions through interconnected routes and calculate impacts.
    """

    def __init__(self, network_data: Dict[str, Any]) -> None:
        """
        Initialize topology simulator with network data.

        Args:
            network_data: Dict containing network structure with keys:
                - routes: Dict[route_id -> route_info]
                - connections: Dict[route_id -> List of connected route_ids]
                - transfer_points: List of interchange stations
                - line_dependencies: Dict describing cross-line dependencies

        Raises:
            ValueError: If network_data missing required keys
        """
        required_keys = {"routes", "connections"}
        if not all(k in network_data for k in required_keys):
            raise ValueError(
                f"network_data must contain {required_keys}"
            )

        self.network_data = network_data
        self.routes = network_data.get("routes", {})
        self.connections = network_data.get("connections", {})
        self.transfer_points = network_data.get("transfer_points", [])
        self.line_dependencies = network_data.get("line_dependencies", {})
        self._delay_cache: Dict[str, int] = {}

    def simulate_delay_propagation(
        self,
        initial_delay: int,
        route_id: str,
        max_hops: int = 3,
    ) -> Dict[str, int]:
        """
        Simulate delay propagation through network.

        Propagates an initial delay on a route through interconnected
        routes using breadth-first search.

        Args:
            initial_delay: Delay in minutes on initial route
            route_id: Route ID where disruption originates
            max_hops: Maximum network hops to propagate (default: 3)

        Returns:
            Dict mapping affected route_id to delay in minutes

        Raises:
            ValueError: If route_id not in network
        """
        if route_id not in self.routes:
            raise ValueError(f"Route {route_id} not in network")

        delays = {route_id: initial_delay}
        visited = {route_id}
        queue = [(route_id, 0, initial_delay)]

        while queue:
            current_route, hops, current_delay = queue.pop(0)

            if hops >= max_hops:
                continue

            connected_routes = self.connections.get(
                current_route, []
            )

            for next_route in connected_routes:
                if next_route in visited:
                    continue

                visited.add(next_route)

                # Decay delay with each hop
                delay_factor = max(0.5 - (hops * 0.1), 0.2)
                propagated_delay = max(
                    int(current_delay * delay_factor), 1
                )

                delays[next_route] = propagated_delay
                queue.append(
                    (next_route, hops + 1, propagated_delay)
                )

        self._delay_cache = delays
        return delays

    def get_affected_routes(self, affected_route: str) -> List[str]:
        """
        Get all routes affected by disruption on a single route.

        Returns direct connections and indirect affected routes.

        Args:
            affected_route: Route ID with active disruption

        Returns:
            List of affected route IDs
        """
        if affected_route not in self.routes:
            raise ValueError(f"Route {affected_route} not in network")

        affected = {affected_route}
        visited = {affected_route}
        queue = [affected_route]

        while queue:
            current = queue.pop(0)
            connected = self.connections.get(current, [])

            for route in connected:
                if route not in visited:
                    visited.add(route)
                    affected.add(route)
                    queue.append(route)

        return sorted(list(affected))

    def estimate_recovery_time(
        self,
        disruption_type: str,
        duration: int,
    ) -> int:
        """
        Estimate recovery time after disruption ends.

        Accounts for cascading delays and network effects that persist
        after primary disruption is resolved.

        Args:
            disruption_type: Type of disruption (signal_failure, etc.)
            duration: Duration of disruption in minutes

        Returns:
            Estimated recovery time in minutes after disruption ends
        """
        # Recovery time based on disruption type and duration
        recovery_multipliers = {
            "signal_failure": 0.8,
            "power_outage": 1.2,
            "track_maintenance": 0.5,
            "mechanical_failure": 0.9,
            "medical_emergency": 0.3,
            "passenger_incident": 0.2,
            "equipment_failure": 0.7,
            "staff_shortage": 1.0,
            "security_incident": 0.6,
            "weather_related": 0.4,
            "crowding": 0.4,
            "schedule_adjustment": 0.3,
            "infrastructure_damage": 2.0,
        }

        multiplier = recovery_multipliers.get(disruption_type, 0.5)
        base_recovery = max(int(duration * multiplier), 2)

        # Add buffer for cascading effects
        cascade_buffer = len(self._delay_cache) * 2
        return base_recovery + cascade_buffer

    def get_network_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about current network state.

        Returns:
            Dict with keys: num_routes, num_connections, avg_connectivity
        """
        num_routes = len(self.routes)
        num_connections = sum(
            len(v) for v in self.connections.values()
        )
        avg_connectivity = (
            num_connections / num_routes if num_routes > 0 else 0
        )

        return {
            "num_routes": num_routes,
            "num_connections": num_connections,
            "avg_connectivity": avg_connectivity,
            "transfer_points": len(self.transfer_points),
        }

    def validate_network(self) -> List[str]:
        """
        Validate network structure and return warnings.

        Checks for common issues like isolated routes, missing
        connections, etc.

        Returns:
            List of validation warning messages
        """
        warnings = []

        # Check for isolated routes
        for route_id in self.routes:
            if route_id not in self.connections:
                warnings.append(
                    f"Route {route_id} has no connections"
                )

        # Check for dangling connections
        all_routes = set(self.routes.keys())
        for route_id, connected in self.connections.items():
            for conn_route in connected:
                if conn_route not in all_routes:
                    warnings.append(
                        f"Route {route_id} connects to non-existent "
                        f"route {conn_route}"
                    )

        return warnings


def create_sample_network() -> Dict[str, Any]:
    """
    Create a sample transit network for testing.

    Returns:
        Sample network data structure
    """
    return {
        "routes": {
            "1": {"name": "Line 1", "type": "subway"},
            "2": {"name": "Line 2", "type": "subway"},
            "3": {"name": "Line 3", "type": "subway"},
            "A": {"name": "Line A", "type": "bus"},
            "B": {"name": "Line B", "type": "bus"},
        },
        "connections": {
            "1": ["2", "A"],
            "2": ["1", "3", "B"],
            "3": ["2"],
            "A": ["1", "B"],
            "B": ["2", "A"],
        },
        "transfer_points": ["central_station", "downtown_hub"],
        "line_dependencies": {
            "1": {"requires": ["power_line_1"]},
            "2": {"requires": ["power_line_1", "power_line_2"]},
        },
    }
