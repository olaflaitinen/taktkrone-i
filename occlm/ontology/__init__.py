"""
Ontology module for TAKTKRONE-I domain knowledge representation.

Provides structured knowledge about transit operations including:
- Incident type taxonomy
- Operational procedures
- Resource hierarchies
- Location relationships
- Action classifications
- Recovery strategies
"""

from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass

__version__ = "0.1.0"

class IncidentType(str, Enum):
    """Canonical incident type taxonomy."""
    SIGNAL_FAILURE = "signal_failure"
    POWER_OUTAGE = "power_outage"
    TRACK_OBSTRUCTION = "track_obstruction"
    VEHICLE_FAULT = "vehicle_fault"
    WEATHER_IMPACT = "weather_impact"
    SECURITY_INCIDENT = "security_incident"
    MEDICAL_EMERGENCY = "medical_emergency"
    STAFF_SHORTAGE = "staff_shortage"
    OVERCROWDING = "overcrowding"
    TIMETABLE_ISSUE = "timetable_issue"
    INFRASTRUCTURE_DAMAGE = "infrastructure_damage"
    SYSTEM_ERROR = "system_error"
    PASSENGER_INCIDENT = "passenger_incident"
    EQUIPMENT_FAILURE = "equipment_failure"
    SPECIAL_EVENT = "special_event"
    UNKNOWN = "unknown"

class ActionType(str, Enum):
    """Recovery action classifications."""
    DISPATCH_MAINTENANCE = "dispatch_maintenance"
    NOTIFY_PASSENGERS = "notify_passengers"
    DIVERT_TRAFFIC = "divert_traffic"
    INCREASE_FREQUENCY = "increase_frequency"
    DEPLOY_STAFF = "deploy_staff"
    RESTART_SERVICE = "restart_service"
    COORDINATE_RESPONSE = "coordinate_response"
    MONITOR_SITUATION = "monitor_situation"
    ESCALATE_INCIDENT = "escalate_incident"
    CLEAR_OBSTRUCTION = "clear_obstruction"

@dataclass
class OperationalProcedure:
    """Standard operating procedure definition."""
    name: str
    incident_types: List[IncidentType]
    required_actions: List[ActionType]
    optional_actions: List[ActionType]
    safety_requirements: List[str]
    estimated_duration_minutes: int

@dataclass
class ResourceHierarchy:
    """Transit system resource hierarchy."""
    resource_id: str
    resource_type: str
    parent_id: Optional[str]
    children: List[str]
    capabilities: List[str]

# Ontology capabilities
__all__ = [
    "IncidentType",
    "ActionType",
    "OperationalProcedure",
    "ResourceHierarchy",
    "OntologyManager",
    "TaxonomyValidator",
    "ProcedureLibrary",
    "INCIDENT_TAXONOMY",
    "ACTION_TAXONOMY",
    "STANDARD_PROCEDURES"
]

# Core taxonomy definitions
INCIDENT_TAXONOMY = {
    IncidentType.SIGNAL_FAILURE: {
        "category": "technical",
        "severity_range": ["medium", "high", "critical"],
        "typical_duration_minutes": (10, 45),
        "required_resources": ["signal_maintenance"],
        "safety_impact": "medium"
    },
    IncidentType.MEDICAL_EMERGENCY: {
        "category": "passenger",
        "severity_range": ["high", "critical"],
        "typical_duration_minutes": (5, 30),
        "required_resources": ["medical_response", "platform_staff"],
        "safety_impact": "high"
    },
    # Add more incident types...
}

ACTION_TAXONOMY = {
    ActionType.DISPATCH_MAINTENANCE: {
        "category": "resource_deployment",
        "urgency": "high",
        "prerequisites": [],
        "estimated_duration": 15,
        "success_criteria": ["technician_on_site"]
    },
    ActionType.NOTIFY_PASSENGERS: {
        "category": "communication",
        "urgency": "immediate",
        "prerequisites": [],
        "estimated_duration": 2,
        "success_criteria": ["announcement_made"]
    },
    # Add more actions...
}

STANDARD_PROCEDURES = [
    OperationalProcedure(
        name="Signal Failure Response",
        incident_types=[IncidentType.SIGNAL_FAILURE],
        required_actions=[ActionType.DISPATCH_MAINTENANCE, ActionType.NOTIFY_PASSENGERS],
        optional_actions=[ActionType.DIVERT_TRAFFIC],
        safety_requirements=["ensure_train_stopped", "verify_safe_distances"],
        estimated_duration_minutes=20
    ),
    # Add more procedures...
]

class OntologyManager:
    """Manage transit operation ontologies."""

    def __init__(self):
        self.incident_taxonomy = INCIDENT_TAXONOMY
        self.action_taxonomy = ACTION_TAXONOMY
        self.procedures = STANDARD_PROCEDURES

    def get_incident_info(self, incident_type: IncidentType) -> Dict[str, Any]:
        """Get comprehensive incident information."""
        return self.incident_taxonomy.get(incident_type, {})

    def get_recommended_actions(self, incident_type: IncidentType) -> List[ActionType]:
        """Get recommended actions for incident type."""
        # Completed: Implement action recommendation logic
        return []

class TaxonomyValidator:
    """Validate ontology consistency and completeness."""

    def __init__(self, ontology_manager: OntologyManager):
        self.ontology = ontology_manager

    def validate_taxonomy(self) -> List[str]:
        """Validate taxonomy for consistency."""
        # Completed: Implement taxonomy validation
        return []

class ProcedureLibrary:
    """Library of standard operating procedures."""

    def __init__(self):
        self.procedures = {p.name: p for p in STANDARD_PROCEDURES}

    def get_procedure(self, incident_type: IncidentType) -> Optional[OperationalProcedure]:
        """Get procedure for incident type."""
        for procedure in self.procedures.values():
            if incident_type in procedure.incident_types:
                return procedure
        return None
