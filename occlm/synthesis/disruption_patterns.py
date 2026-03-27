"""
Disruption pattern templates for synthetic scenario generation.

Provides a registry of incident templates representing common transit
disruptions with realistic parameters for synthetic data generation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

__all__ = [
    "DisruptionTemplate",
    "DISRUPTION_TEMPLATES",
    "get_template",
    "get_templates_by_type",
    "get_templates_by_severity",
]


@dataclass
class DisruptionTemplate:
    """
    Template for a disruption scenario.

    Defines the structure and parameters for a specific incident type,
    including duration, severity, affected infrastructure, and impact
    metrics.

    Attributes:
        name: Human-readable name for the disruption
        incident_type: Type identifier (signal_failure, medical_emergency)
        duration_minutes: Tuple of (min, max) duration range in minutes
        severity: Impact level (low, medium, high, critical)
        affected_lines: List of transit line IDs affected
        affected_stops: Optional list of specific stops affected
        passenger_impact: Type of impact (service_delay, service_disruption,
            service_suspended)
        probability: Likelihood of occurrence (0.0-1.0)
        description: Detailed description of the disruption
        root_causes: List of possible root causes
        recovery_duration_minutes: (min, max) recovery time range
        cascade_probability: Likelihood of affecting other systems
    """

    name: str
    incident_type: str
    duration_minutes: tuple[int, int]
    severity: str
    affected_lines: list[str]
    affected_stops: Optional[list[str]]
    passenger_impact: str
    probability: float
    description: str = ""
    root_causes: list[str] = None
    recovery_duration_minutes: tuple[int, int] = (5, 15)
    cascade_probability: float = 0.1

    def __post_init__(self) -> None:
        """Validate template parameters."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0.0 and 1.0")

        valid_severities = {"low", "medium", "high", "critical"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"severity must be one of {valid_severities}"
            )

        valid_impacts = {
            "service_delay",
            "service_disruption",
            "service_suspended",
        }
        if self.passenger_impact not in valid_impacts:
            raise ValueError(
                f"passenger_impact must be one of {valid_impacts}"
            )

        if self.duration_minutes[0] > self.duration_minutes[1]:
            raise ValueError(
                "duration_minutes min must be <= max"
            )

        if self.root_causes is None:
            self.root_causes = []


# =============================================================================
# DISRUPTION TEMPLATES REGISTRY
# =============================================================================

DISRUPTION_TEMPLATES: Dict[str, DisruptionTemplate] = {
    "signal_failure": DisruptionTemplate(
        name="Signal Failure",
        incident_type="signal_failure",
        duration_minutes=(15, 120),
        severity="high",
        affected_lines=["1", "2", "3"],
        affected_stops=None,
        passenger_impact="service_disruption",
        probability=0.08,
        description="Signal system malfunction preventing train movement",
        root_causes=["equipment_failure", "software_glitch", "maintenance_error"],
        recovery_duration_minutes=(10, 60),
        cascade_probability=0.25,
    ),
    "medical_emergency": DisruptionTemplate(
        name="Medical Emergency",
        incident_type="medical_emergency",
        duration_minutes=(10, 30),
        severity="medium",
        affected_lines=["A", "B", "C", "D"],
        affected_stops=["main_st", "central_station"],
        passenger_impact="service_delay",
        probability=0.12,
        description="Medical incident involving passenger requiring response",
        root_causes=["passenger_collapse", "cardiac_event", "injury"],
        recovery_duration_minutes=(5, 20),
        cascade_probability=0.05,
    ),
    "track_maintenance": DisruptionTemplate(
        name="Track Maintenance",
        incident_type="track_maintenance",
        duration_minutes=(30, 180),
        severity="medium",
        affected_lines=["1", "2"],
        affected_stops=None,
        passenger_impact="service_disruption",
        probability=0.06,
        description="Scheduled or emergency track maintenance activity",
        root_causes=["scheduled_maintenance", "emergency_repair"],
        recovery_duration_minutes=(20, 120),
        cascade_probability=0.15,
    ),
    "power_outage": DisruptionTemplate(
        name="Power Outage",
        incident_type="power_outage",
        duration_minutes=(10, 60),
        severity="critical",
        affected_lines=["1", "2", "3", "4"],
        affected_stops=None,
        passenger_impact="service_suspended",
        probability=0.03,
        description="Loss of traction power affecting multiple lines",
        root_causes=["grid_failure", "substation_fault", "cable_damage"],
        recovery_duration_minutes=(15, 45),
        cascade_probability=0.4,
    ),
    "mechanical_failure": DisruptionTemplate(
        name="Mechanical Failure",
        incident_type="mechanical_failure",
        duration_minutes=(20, 90),
        severity="high",
        affected_lines=["A", "B"],
        affected_stops=None,
        passenger_impact="service_disruption",
        probability=0.07,
        description="Train propulsion or brake system failure",
        root_causes=["motor_failure", "brake_malfunction", "coupling_failure"],
        recovery_duration_minutes=(15, 60),
        cascade_probability=0.2,
    ),
    "weather_related": DisruptionTemplate(
        name="Weather Related Disruption",
        incident_type="weather_related",
        duration_minutes=(30, 180),
        severity="medium",
        affected_lines=["1", "2", "3", "4", "5"],
        affected_stops=None,
        passenger_impact="service_delay",
        probability=0.04,
        description="Service disruption due to adverse weather conditions",
        root_causes=["heavy_rain", "extreme_heat", "flooding", "snow"],
        recovery_duration_minutes=(30, 120),
        cascade_probability=0.1,
    ),
    "passenger_incident": DisruptionTemplate(
        name="Passenger Incident",
        incident_type="passenger_incident",
        duration_minutes=(5, 20),
        severity="low",
        affected_lines=["A", "B", "C"],
        affected_stops=["platform_a", "platform_b"],
        passenger_impact="service_delay",
        probability=0.15,
        description="Passenger-related issue (crowding, unruly behavior)",
        root_causes=["excessive_crowding", "passenger_dispute", "evacuation"],
        recovery_duration_minutes=(3, 15),
        cascade_probability=0.02,
    ),
    "system_error": DisruptionTemplate(
        name="System Error",
        incident_type="system_error",
        duration_minutes=(5, 45),
        severity="medium",
        affected_lines=["1", "2"],
        affected_stops=None,
        passenger_impact="service_delay",
        probability=0.05,
        description="Control system software or communication error",
        root_causes=["software_bug", "database_error", "network_failure"],
        recovery_duration_minutes=(5, 30),
        cascade_probability=0.1,
    ),
    "equipment_failure": DisruptionTemplate(
        name="Equipment Failure",
        incident_type="equipment_failure",
        duration_minutes=(15, 75),
        severity="medium",
        affected_lines=["1", "2", "3"],
        affected_stops=None,
        passenger_impact="service_disruption",
        probability=0.09,
        description="Station or line equipment malfunction",
        root_causes=["escalator_failure", "door_malfunction", "atp_failure"],
        recovery_duration_minutes=(10, 45),
        cascade_probability=0.08,
    ),
    "staff_shortage": DisruptionTemplate(
        name="Staff Shortage",
        incident_type="staff_shortage",
        duration_minutes=(60, 300),
        severity="medium",
        affected_lines=["A", "B", "C"],
        affected_stops=None,
        passenger_impact="service_disruption",
        probability=0.05,
        description="Insufficient operators or staff to maintain service",
        root_causes=["sick_leave", "no_show", "strike"],
        recovery_duration_minutes=(30, 180),
        cascade_probability=0.05,
    ),
    "security_incident": DisruptionTemplate(
        name="Security Incident",
        incident_type="security_incident",
        duration_minutes=(10, 40),
        severity="high",
        affected_lines=["1", "2", "3", "4"],
        affected_stops=["main_station", "central_hub"],
        passenger_impact="service_disruption",
        probability=0.02,
        description="Security threat requiring police or emergency response",
        root_causes=["suspicious_package", "trespasser", "assault"],
        recovery_duration_minutes=(5, 30),
        cascade_probability=0.15,
    ),
    "crowding": DisruptionTemplate(
        name="Severe Crowding",
        incident_type="crowding",
        duration_minutes=(15, 60),
        severity="low",
        affected_lines=["A", "B", "C", "D"],
        affected_stops=["main_st", "downtown"],
        passenger_impact="service_delay",
        probability=0.18,
        description="Excessive passenger loads affecting service flow",
        root_causes=["event_aftermath", "peak_demand", "reduced_service"],
        recovery_duration_minutes=(10, 40),
        cascade_probability=0.03,
    ),
    "schedule_adjustment": DisruptionTemplate(
        name="Schedule Adjustment",
        incident_type="schedule_adjustment",
        duration_minutes=(30, 120),
        severity="low",
        affected_lines=["1", "2", "3", "4"],
        affected_stops=None,
        passenger_impact="service_delay",
        probability=0.08,
        description="Temporary schedule modification or service gap",
        root_causes=["special_event", "construction", "planned_work"],
        recovery_duration_minutes=(20, 90),
        cascade_probability=0.02,
    ),
    "special_event": DisruptionTemplate(
        name="Special Event Impact",
        incident_type="special_event",
        duration_minutes=(60, 300),
        severity="medium",
        affected_lines=["1", "2", "3", "4", "5"],
        affected_stops=["event_venue", "downtown"],
        passenger_impact="service_disruption",
        probability=0.04,
        description="Service disruption due to major public event",
        root_causes=["sporting_event", "concert", "protest"],
        recovery_duration_minutes=(30, 180),
        cascade_probability=0.08,
    ),
    "infrastructure_damage": DisruptionTemplate(
        name="Infrastructure Damage",
        incident_type="infrastructure_damage",
        duration_minutes=(120, 1440),
        severity="critical",
        affected_lines=["1", "2"],
        affected_stops=None,
        passenger_impact="service_suspended",
        probability=0.01,
        description="Significant damage to tracks, bridges, or structures",
        root_causes=["accident", "derailment", "natural_disaster"],
        recovery_duration_minutes=(120, 720),
        cascade_probability=0.3,
    ),
}


def get_template(incident_type: str) -> DisruptionTemplate:
    """
    Retrieve a disruption template by incident type.

    Args:
        incident_type: Key matching template in DISRUPTION_TEMPLATES

    Returns:
        The requested DisruptionTemplate

    Raises:
        KeyError: If incident_type not found in registry
    """
    if incident_type not in DISRUPTION_TEMPLATES:
        raise KeyError(f"Unknown incident type: {incident_type}")
    return DISRUPTION_TEMPLATES[incident_type]


def get_templates_by_type(
    incident_types: list[str],
) -> list[DisruptionTemplate]:
    """
    Retrieve multiple templates by incident type.

    Args:
        incident_types: List of incident type keys

    Returns:
        List of matching DisruptionTemplate objects
    """
    templates = []
    for incident_type in incident_types:
        try:
            templates.append(get_template(incident_type))
        except KeyError:
            continue
    return templates


def get_templates_by_severity(severity: str) -> list[DisruptionTemplate]:
    """
    Retrieve all templates matching a severity level.

    Args:
        severity: Severity level (low, medium, high, critical)

    Returns:
        List of DisruptionTemplate objects with matching severity
    """
    return [
        t for t in DISRUPTION_TEMPLATES.values()
        if t.severity == severity
    ]
