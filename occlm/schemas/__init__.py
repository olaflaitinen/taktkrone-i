"""
Pydantic schemas for canonical data contracts.

All schemas correspond to JSON Schema definitions in data_contracts/
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class Operator(str, Enum):
    """Supported transit operators"""

    MTA_NYCT = "mta_nyct"
    MBTA = "mbta"
    WMATA = "wmata"
    BART = "bart"
    TFL = "tfl"
    GENERIC = "generic"


class Provenance(BaseModel):
    """Data provenance and ingestion metadata"""

    ingestion_time: datetime = Field(description="When data was ingested")
    ingestion_method: str = Field(description="Adapter or method used")
    raw_source_url: Optional[str] = Field(default=None, description="Source API URL")
    source_version: Optional[str] = Field(
        default=None, description="Source data version"
    )


class GeoLocation(BaseModel):
    """Geographic coordinates"""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    bearing: Optional[float] = Field(default=None, ge=0, le=360)


class RealtimeEvent(BaseModel):
    """Canonical realtime transit operational event"""

    id: str = Field(description="Unique event identifier")
    schema_version: Literal["1.0.0"] = "1.0.0"
    timestamp: datetime = Field(description="Event occurrence time")
    operator: Operator
    source: str = Field(description="Data source identifier")
    event_type: Literal[
        "trip_update",
        "vehicle_position",
        "service_alert",
        "arrival_prediction",
        "departure_prediction",
        "delay_event",
        "cancellation",
        "additional_trip",
        "vehicle_status_change",
    ]
    provenance: Provenance

    route_id: Optional[str] = None
    trip_id: Optional[str] = None
    stop_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    direction_id: Optional[Literal[0, 1]] = None
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    delay_seconds: Optional[int] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    geo_location: Optional[GeoLocation] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "evt_mta_20260327_001",
                "schema_version": "1.0.0",
                "timestamp": "2026-03-27T17:30:00Z",
                "operator": "mta_nyct",
                "source": "gtfs_rt_trip_updates",
                "event_type": "trip_update",
                "provenance": {
                    "ingestion_time": "2026-03-27T17:30:15Z",
                    "ingestion_method": "mta_gtfs_rt_adapter",
                },
                "route_id": "1",
                "delay_seconds": 240,
            }
        }


class NetworkSnapshot(BaseModel):
    """Point-in-time snapshot of network operational state"""

    id: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    timestamp: datetime
    operator: Operator
    source: str
    provenance: Provenance

    active_trips: List[Dict[str, Any]] = Field(default_factory=list)
    vehicle_positions: List[Dict[str, Any]] = Field(default_factory=list)
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    line_status: Dict[str, str] = Field(default_factory=dict)
    network_metrics: Dict[str, Any] = Field(default_factory=dict)


class IncidentRecord(BaseModel):
    """Transit disruption or incident event"""

    id: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    timestamp: datetime
    operator: Operator
    source: str
    incident_type: Literal[
        "signal_failure",
        "track_obstruction",
        "vehicle_breakdown",
        "power_outage",
        "police_activity",
        "medical_emergency",
        "weather_impact",
        "crowding",
        "door_malfunction",
        "unauthorized_person_on_tracks",
        "infrastructure_degradation",
        "equipment_failure",
        "crew_unavailability",
        "planned_maintenance",
        "other",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    status: Literal["active", "monitoring", "resolved", "cleared"]

    title: Optional[str] = None
    description: Optional[str] = None
    affected_entities: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Any] = Field(default_factory=dict)
    timeline: Dict[str, datetime] = Field(default_factory=dict)
    impact: Dict[str, Any] = Field(default_factory=dict)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    root_cause: Optional[Dict[str, Any]] = None
    provenance: Optional[Provenance] = None
    tags: List[str] = Field(default_factory=list)


class Message(BaseModel):
    """Single message in a dialogue"""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    name: Optional[str] = None


class OCCDialogueSample(BaseModel):
    """Instruction tuning sample for training"""

    id: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    timestamp: datetime
    operator: Operator
    source: Literal["synthetic", "historical", "human_annotated", "simulation"]
    task_type: Literal[
        "situation_summarization",
        "disruption_diagnosis",
        "recovery_planning",
        "headway_regulation",
        "turnback_management",
        "conflict_resolution",
        "after_action_review",
        "information_extraction",
        "question_answering",
    ]
    messages: List[Message] = Field(min_length=2)
    metadata: Dict[str, Any] = Field(
        description="Must include difficulty and split fields"
    )
    ground_truth: Optional[Dict[str, Any]] = None
    context_data: Optional[Dict[str, Any]] = None

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required metadata fields exist"""
        required = ["difficulty", "split"]
        for field in required:
            if field not in v:
                raise ValueError(f"Metadata must include '{field}' field")
        return v


class ActionRecommendation(BaseModel):
    """Structured output from model for OCC recommendations"""

    id: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    timestamp: datetime
    operator: Operator
    request_context: Dict[str, Any]
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]] = Field(min_length=1)
    uncertainties: List[Dict[str, Any]] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    retrieval_references: List[Dict[str, Any]] = Field(default_factory=list)
    model_metadata: Optional[Dict[str, Any]] = None
    human_oversight: Optional[Dict[str, Any]] = None


__all__ = [
    "Operator",
    "Provenance",
    "GeoLocation",
    "RealtimeEvent",
    "NetworkSnapshot",
    "IncidentRecord",
    "Message",
    "OCCDialogueSample",
    "ActionRecommendation",
]
