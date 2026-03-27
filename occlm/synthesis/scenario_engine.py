"""
Scenario engine for generating complete synthetic transit scenarios.

Combines topology simulation and disruption patterns to generate
realistic multi-turn operational scenarios with incident progression.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import random
import uuid

from occlm.synthesis.disruption_patterns import (
    get_template,
    DISRUPTION_TEMPLATES,
)
from occlm.synthesis.topology_simulator import TopologySimulator

__all__ = [
    "ScenarioEngine",
]


class ScenarioEngine:
    """
    Generates complete synthetic transit disruption scenarios.

    Combines topology simulation and disruption patterns to create
    realistic scenarios with incident progression, affected routes,
    and passenger impact estimates.
    """

    def __init__(
        self,
        topology_simulator: Optional[TopologySimulator] = None,
        random_seed: Optional[int] = None,
    ) -> None:
        """
        Initialize scenario engine.

        Args:
            topology_simulator: Optional TopologySimulator instance
            random_seed: Optional seed for reproducibility
        """
        self.topology_simulator = topology_simulator
        if random_seed is not None:
            random.seed(random_seed)

        self.generated_scenarios: List[Dict[str, Any]] = []

    def generate_delay_scenario(
        self,
        num_scenarios: int = 10,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate delay disruption scenarios.

        Args:
            num_scenarios: Number of scenarios to generate
            difficulty: Filter by difficulty (easy, medium, hard)

        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        incident_types = [
            "signal_failure",
            "medical_emergency",
            "passenger_incident",
            "equipment_failure",
        ]

        for _ in range(num_scenarios):
            incident_type = random.choice(incident_types)
            scenario = self._generate_single_scenario(
                incident_type=incident_type,
                scenario_type="delay",
            )
            scenarios.append(scenario)

        self.generated_scenarios.extend(scenarios)
        return scenarios

    def generate_bunching_scenario(
        self,
        num_scenarios: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate train bunching scenarios.

        Scenarios where multiple trains accumulate due to upstream
        delays or dwell time extensions.

        Args:
            num_scenarios: Number of scenarios to generate

        Returns:
            List of bunching scenario dictionaries
        """
        scenarios = []

        for _ in range(num_scenarios):
            scenario = self._generate_single_scenario(
                incident_type="passenger_incident",
                scenario_type="bunching",
            )

            num_trains = random.randint(2, 5)
            scenario["incident_details"]["num_bunched_trains"] = (
                num_trains
            )
            scenario["incident_details"]["headway_deviation"] = (
                random.randint(50, 150)
            )

            scenarios.append(scenario)

        self.generated_scenarios.extend(scenarios)
        return scenarios

    def generate_turnback_scenario(
        self,
        num_scenarios: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate terminal turnback disruption scenarios.

        Scenarios where turnback delays or congestion affect service
        frequency and create cascading delays.

        Args:
            num_scenarios: Number of scenarios to generate

        Returns:
            List of turnback scenario dictionaries
        """
        scenarios = []

        for _ in range(num_scenarios):
            scenario = self._generate_single_scenario(
                incident_type="equipment_failure",
                scenario_type="turnback",
            )

            scenario["incident_details"]["turnback_location"] = (
                random.choice(["north_terminal", "south_terminal"])
            )
            scenario["incident_details"]["trains_waiting"] = (
                random.randint(1, 6)
            )
            scenario["incident_details"]["dwell_time_minutes"] = (
                random.randint(5, 15)
            )

            scenarios.append(scenario)

        self.generated_scenarios.extend(scenarios)
        return scenarios

    def generate_conflict_scenario(
        self,
        num_scenarios: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate operational conflict scenarios.

        Scenarios with resource conflicts, crossover conflicts, or
        schedule conflicts requiring dispatcher decisions.

        Args:
            num_scenarios: Number of scenarios to generate

        Returns:
            List of conflict scenario dictionaries
        """
        scenarios = []
        conflict_types = [
            "crossover_conflict",
            "platform_conflict",
            "schedule_conflict",
        ]

        for _ in range(num_scenarios):
            scenario = self._generate_single_scenario(
                incident_type="system_error",
                scenario_type="conflict",
            )

            scenario["incident_details"]["conflict_type"] = (
                random.choice(conflict_types)
            )
            scenario["incident_details"]["involved_routes"] = [
                random.choice(["1", "2", "3", "A", "B"])
                for _ in range(random.randint(2, 3))
            ]
            scenario["incident_details"]["resolution_options"] = (
                random.randint(2, 4)
            )

            scenarios.append(scenario)

        self.generated_scenarios.extend(scenarios)
        return scenarios

    def _generate_single_scenario(
        self,
        incident_type: str,
        scenario_type: str,
    ) -> Dict[str, Any]:
        """
        Generate a single complete scenario.

        Args:
            incident_type: Type of disruption
            scenario_type: Category of scenario

        Returns:
            Complete scenario dictionary
        """
        template = get_template(incident_type)
        incident_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc)

        duration = random.randint(
            template.duration_minutes[0],
            template.duration_minutes[1],
        )

        affected_routes = random.sample(
            template.affected_lines,
            min(random.randint(1, 2), len(template.affected_lines)),
        )

        incident_details = {
            "type": incident_type,
            "duration_minutes": duration,
            "severity": template.severity,
            "location": random.choice(
                template.affected_stops
                if template.affected_stops
                else ["station_1", "station_2"]
            ),
            "affected_routes": affected_routes,
            "root_cause": random.choice(template.root_causes),
        }

        initial_state = {
            "timestamp": timestamp.isoformat(),
            "network_status": "normal",
            "affected_routes": affected_routes,
            "active_incidents": 1,
        }

        progression = self._generate_incident_progression(
            incident_details
        )

        affected_stops = self._get_affected_stops(affected_routes)

        passenger_impact = self._estimate_passenger_impact(
            incident_details, duration, affected_stops
        )

        return {
            "incident_id": incident_id,
            "timestamp": timestamp.isoformat(),
            "scenario_type": scenario_type,
            "initial_state": initial_state,
            "incident_details": incident_details,
            "progression": progression,
            "affected_routes": affected_routes,
            "affected_stops": affected_stops,
            "passenger_impact": passenger_impact,
        }

    def _generate_incident_progression(
        self,
        disruption: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate timeline of incident events.

        Args:
            disruption: Disruption details

        Returns:
            List of progression events with timestamps
        """
        progression = []
        base_time = datetime.now(timezone.utc)
        duration = disruption.get("duration_minutes", 30)

        # Initial detection
        progression.append({
            "time_offset_minutes": 0,
            "event": "incident_detected",
            "description": f"Disruption detected: {disruption['type']}",
            "severity": disruption.get("severity", "medium"),
        })

        # Escalation (if high severity)
        if disruption.get("severity") in ["high", "critical"]:
            progression.append({
                "time_offset_minutes": 2,
                "event": "escalation",
                "description": "Escalating to senior dispatcher",
            })

        # Delay impact at various checkpoints
        checkpoints = [5, 10, 15, 25]
        for checkpoint in checkpoints:
            if checkpoint < duration:
                progression.append({
                    "time_offset_minutes": checkpoint,
                    "event": "status_update",
                    "description": (
                        f"Delay impact: "
                        f"{random.randint(5, 30)} minutes"
                    ),
                    "delay_minutes": random.randint(5, 30),
                })

        # Recovery begins
        if duration > 10:
            progression.append({
                "time_offset_minutes": duration - 5,
                "event": "recovery_initiated",
                "description": "Beginning service restoration",
            })

        # Resolution
        progression.append({
            "time_offset_minutes": duration,
            "event": "incident_resolved",
            "description": "Service fully restored",
            "final_delay": sum(
                e.get("delay_minutes", 0) for e in progression
            ),
        })

        return progression

    def _get_affected_stops(self, routes: List[str]) -> List[str]:
        """
        Get list of stops affected by disruption.

        Args:
            routes: List of affected route IDs

        Returns:
            List of affected stop IDs
        """
        stop_mapping = {
            "1": ["station_1", "station_2", "station_3"],
            "2": ["station_4", "station_5", "station_6"],
            "3": ["station_7", "station_8"],
            "A": ["stop_a1", "stop_a2", "stop_a3"],
            "B": ["stop_b1", "stop_b2"],
        }

        affected_stops = []
        for route in routes:
            affected_stops.extend(
                stop_mapping.get(route, ["unknown_stop"])
            )

        return list(set(affected_stops))

    def _estimate_passenger_impact(
        self,
        incident: Dict[str, Any],
        duration: int,
        affected_stops: List[str],
    ) -> Dict[str, Any]:
        """
        Estimate passenger impact of disruption.

        Args:
            incident: Incident details
            duration: Duration in minutes
            affected_stops: List of affected stops

        Returns:
            Passenger impact estimate
        """
        severity = incident.get("severity", "medium")

        base_affected_passengers = {
            "low": 100,
            "medium": 500,
            "high": 2000,
            "critical": 5000,
        }.get(severity, 500)

        # Adjust for duration and stops
        affected_passengers = (
            base_affected_passengers
            * (1 + duration / 60)
            * (1 + len(affected_stops) / 5)
        )

        # Passenger minutes of delay
        delay_impact = sum(
            e.get("delay_minutes", 0)
            for e in self._generate_incident_progression(incident)
        )
        passenger_minutes = int(affected_passengers * delay_impact / 10)

        return {
            "estimated_affected_passengers": int(affected_passengers),
            "passenger_minutes_delay": passenger_minutes,
            "severity_level": severity,
            "service_level_reduction": {
                "low": 0.1,
                "medium": 0.3,
                "high": 0.6,
                "critical": 0.9,
            }.get(severity, 0.3),
        }

    def get_scenario_stats(self) -> Dict[str, Any]:
        """
        Get statistics about generated scenarios.

        Returns:
            Dict with scenario generation statistics
        """
        if not self.generated_scenarios:
            return {"count": 0}

        return {
            "count": len(self.generated_scenarios),
            "scenario_types": list(
                set(
                    s.get("scenario_type") for s in
                    self.generated_scenarios
                )
            ),
            "incident_types": list(
                set(
                    s.get("incident_details", {}).get("type")
                    for s in self.generated_scenarios
                )
            ),
            "avg_affected_routes": (
                sum(
                    len(s.get("affected_routes", []))
                    for s in self.generated_scenarios
                )
                / len(self.generated_scenarios)
                if self.generated_scenarios
                else 0
            ),
        }
