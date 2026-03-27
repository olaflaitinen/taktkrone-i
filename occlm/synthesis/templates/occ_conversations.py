"""
OCC conversation templates for synthetic dialogue generation.

Provides parameterized dialogue templates representing realistic
operator-dispatcher conversations for various incident types.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "DialogueTurn",
    "ConversationTemplate",
    "CONVERSATION_TEMPLATES",
    "get_conversation_template",
]


@dataclass
class DialogueTurn:
    """
    Single turn in a multi-turn conversation.

    Attributes:
        speaker: Role of speaker (operator or dispatcher)
        message: Template message with production-values
        templates: Alternative message templates for variation
        actions: Optional list of operational actions mentioned
    """

    speaker: str
    message: str
    templates: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate speaker is valid role."""
        valid_speakers = {"operator", "dispatcher", "occ", "field"}
        if self.speaker not in valid_speakers:
            raise ValueError(
                f"speaker must be one of {valid_speakers}"
            )


@dataclass
class ConversationTemplate:
    """
    Template for multi-turn OCC conversation.

    Attributes:
        name: Human-readable name
        incident_type: Type of incident (signal_failure, etc.)
        difficulty: Difficulty level (easy, medium, hard)
        turns: List of DialogueTurn exchanges
        duration_estimate: Estimated conversation length in turns
        context_requirements: Required scenario context fields
        expected_resolution: Optimal resolution action
    """

    name: str
    incident_type: str
    difficulty: str
    turns: List[DialogueTurn] = field(default_factory=list)
    duration_estimate: int = 5
    context_requirements: List[str] = field(default_factory=list)
    expected_resolution: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate template structure."""
        valid_difficulties = {"easy", "medium", "hard"}
        if self.difficulty not in valid_difficulties:
            raise ValueError(
                f"difficulty must be one of {valid_difficulties}"
            )

        if len(self.turns) < 2:
            raise ValueError("ConversationTemplate must have >= 2 turns")


# =============================================================================
# CONVERSATION TEMPLATES REGISTRY
# =============================================================================

CONVERSATION_TEMPLATES: Dict[str, ConversationTemplate] = {
    "signal_failure_response": ConversationTemplate(
        name="Signal Failure Response",
        incident_type="signal_failure",
        difficulty="medium",
        duration_estimate=6,
        context_requirements=[
            "signal_location",
            "affected_tracks",
            "trains_affected",
        ],
        expected_resolution="short_turn",
        turns=[
            DialogueTurn(
                speaker="field",
                message=(
                    "Dispatch, we have a {{signal_issue_type}} failure "
                    "at {{signal_location}} on {{affected_tracks}} tracks."
                ),
                templates=[
                    "Signal problem reported at {{signal_location}} - "
                    "{{signal_issue_type}} issue",
                    "{{signal_issue_type}} failure at {{signal_location}}, "
                    "both tracks affected",
                ],
                actions=["incident_detection"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Copy. How many trains are currently affected at "
                    "{{signal_location}}?"
                ),
                templates=[
                    "Roger that. Current train impact?",
                    "Acknowledged. {{signal_location}} - how many trains "
                    "held?",
                ],
                actions=["status_query"],
            ),
            DialogueTurn(
                speaker="field",
                message=(
                    "{{trains_affected}} trains held between "
                    "{{start_station}} and {{end_station}}. Maintainer "
                    "en route, ETA {{maintainer_eta}} minutes."
                ),
                templates=[
                    "{{trains_affected}} trains in queue. Maintenance "
                    "ETA {{maintainer_eta}} min",
                    "We have {{trains_affected}} train backup. "
                    "Technician arriving in {{maintainer_eta}} minutes",
                ],
                actions=["status_update", "resource_notification"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Understood. We're implementing short turns at "
                    "{{short_turn_before}} and {{short_turn_after}} "
                    "to maintain headways."
                ),
                templates=[
                    "Short turning at {{short_turn_before}}, maintain "
                    "service on both segments",
                    "Deploying short turns to keep frequency - "
                    "{{short_turn_before}} and {{short_turn_after}}",
                ],
                actions=["short_turn_decision", "service_plan"],
            ),
            DialogueTurn(
                speaker="field",
                message=(
                    "Copy, shorting at {{short_turn_before}} and "
                    "{{short_turn_after}}. Communicating with operators."
                ),
                templates=[
                    "Roger, shorting. Notifying crews now.",
                    "Acknowledged. Short turns at those locations. "
                    "Crew communication in progress.",
                ],
                actions=["communication", "crew_coordination"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Good. Monitor repair progress. Once maintainer "
                    "clears the signal, resume through service at "
                    "{{resume_time_estimate}}."
                ),
                templates=[
                    "Stay on the signal repair. Resume through service "
                    "once cleared.",
                    "Keep watch on repair ETA. Restore through service "
                    "immediately when ready.",
                ],
                actions=["monitoring", "recovery_plan"],
            ),
        ],
    ),
    "medical_emergency_response": ConversationTemplate(
        name="Medical Emergency Response",
        incident_type="medical_emergency",
        difficulty="hard",
        duration_estimate=7,
        context_requirements=[
            "emergency_location",
            "passenger_condition",
            "train_id",
        ],
        expected_resolution="hold_train",
        turns=[
            DialogueTurn(
                speaker="operator",
                message=(
                    "Dispatch, medical emergency at {{emergency_location}}, "
                    "train {{train_id}}. Passenger unresponsive."
                ),
                templates=[
                    "We have a medical situation at {{emergency_location}}. "
                    "Passenger needs assistance.",
                    "Medical emergency on train {{train_id}} at "
                    "{{emergency_location}}",
                ],
                actions=["incident_detection", "emergency_alert"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Copy. Holding all service for emergency at "
                    "{{emergency_location}}. EMS dispatched to platform."
                ),
                templates=[
                    "Acknowledged. Freezing service, EMS en route.",
                    "Roger. Holding service. Emergency personnel dispatched "
                    "to {{emergency_location}}",
                ],
                actions=["hold_decision", "emergency_services_alert"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Passenger is {{passenger_condition}}. Doors held open "
                    "at platform {{station_id}}. {{onboard_passengers}} "
                    "passengers on board."
                ),
                templates=[
                    "Passenger condition: {{passenger_condition}}. "
                    "{{onboard_passengers}} passengers aboard.",
                    "Patient appears {{passenger_condition}}. {{onboard_passengers}} "
                    "customers on this train.",
                ],
                actions=["status_update", "passenger_count"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Understood. Hold service until EMS arrives and clears "
                    "patient. Notify customers of medical emergency delay."
                ),
                templates=[
                    "Hold service for emergency response. Announce to passengers.",
                    "Maintain hold. Make PA announcement about medical emergency.",
                ],
                actions=["communication", "customer_notification"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "EMS arrived at {{station_id}}. Removing patient to "
                    "platform. {{remaining_passengers}} passengers remain."
                ),
                templates=[
                    "Paramedics on platform, patient being transferred.",
                    "EMS is removing patient. {{remaining_passengers}} passengers "
                    "staying on board.",
                ],
                actions=["emergency_response", "passenger_update"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Good. Once patient is clear, resume service and provide "
                    "updates to passengers on delay impact."
                ),
                templates=[
                    "Resume service once clear. Brief passengers on impact.",
                    "Clear to proceed once EMS is done. Apologize for delay.",
                ],
                actions=["service_resume", "communication"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Patient clear, resuming service now. Providing delay "
                    "notices to all passengers."
                ),
                templates=[
                    "Patient is clear, service resuming.",
                    "EMS transported patient, we're moving service. "
                    "Apologizing to passengers.",
                ],
                actions=["service_resume", "delay_notification"],
            ),
        ],
    ),
    "delay_escalation": ConversationTemplate(
        name="Delay Escalation",
        incident_type="passenger_incident",
        difficulty="easy",
        duration_estimate=4,
        context_requirements=["initial_delay", "delay_reason"],
        expected_resolution="communication",
        turns=[
            DialogueTurn(
                speaker="operator",
                message=(
                    "Dispatch, running approximately {{initial_delay}} "
                    "minutes late due to {{delay_reason}}."
                ),
                templates=[
                    "We're running {{initial_delay}} minutes behind schedule.",
                    "About {{initial_delay}} min delay. Reason: "
                    "{{delay_reason}}",
                ],
                actions=["status_report"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Copy, {{initial_delay}} minute delay due to "
                    "{{delay_reason}}. Continue through normal stops."
                ),
                templates=[
                    "Understood, {{initial_delay}} min delay acknowledged.",
                    "Roger that delay. Continue to next stop normally.",
                ],
                actions=["delay_acknowledgment"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Continuing to {{next_stop}}. Passengers are aware "
                    "of delay situation."
                ),
                templates=[
                    "Moving to {{next_stop}} now. Passengers notified.",
                    "Proceeding to next station. Made PA announcement.",
                ],
                actions=["communication", "passenger_notification"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Maintain service. Expect {{expected_end_delay}} "
                    "minutes recovered by end of line."
                ),
                templates=[
                    "Keep it moving. Should recover by terminal.",
                    "Service will catch up toward end of route.",
                ],
                actions=["monitoring"],
            ),
        ],
    ),
    "passenger_assistance": ConversationTemplate(
        name="Passenger Assistance",
        incident_type="passenger_incident",
        difficulty="easy",
        duration_estimate=3,
        context_requirements=["assistance_type", "location"],
        expected_resolution="hold_train",
        turns=[
            DialogueTurn(
                speaker="operator",
                message=(
                    "Need assistance at {{location}}. "
                    "{{assistance_type}} - holding for responders."
                ),
                templates=[
                    "Requesting assistance at {{location}} - "
                    "{{assistance_type}}",
                    "Help needed at {{location}}, {{assistance_type}}. "
                    "Train on hold.",
                ],
                actions=["assistance_request"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Copy. Station personnel being sent to {{location}}. "
                    "Maintain hold."
                ),
                templates=[
                    "Station staff dispatched to {{location}}.",
                    "Personnel en route to assist at {{location}}.",
                ],
                actions=["resource_dispatch"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Station agent arrived, {{assistance_type}} resolved. "
                    "Resuming service."
                ),
                templates=[
                    "Personnel here, situation handled. Moving now.",
                    "Assistance provided, we're cleared to go.",
                ],
                actions=["service_resume"],
            ),
        ],
    ),
    "coordination_between_lines": ConversationTemplate(
        name="Coordination Between Lines",
        incident_type="system_error",
        difficulty="medium",
        duration_estimate=5,
        context_requirements=[
            "affected_lines",
            "transfer_point",
            "coordination_action",
        ],
        expected_resolution="communication",
        turns=[
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "All lines, situation at {{transfer_point}} - "
                    "coordination required for {{coordination_action}}."
                ),
                templates=[
                    "Lines {{affected_lines}}, coordination needed at "
                    "{{transfer_point}}",
                    "Multi-line coordination at {{transfer_point}}. "
                    "{{coordination_action}} required.",
                ],
                actions=["multi_line_alert"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "{{line_id}} acknowledges. How do we proceed at "
                    "{{transfer_point}}?"
                ),
                templates=[
                    "{{line_id}} ready. What's the protocol?",
                    "Line {{line_id}} standing by for instruction.",
                ],
                actions=["acknowledge"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "{{line_id}}: {{coordination_action}} at "
                    "{{transfer_point}}. Line {{other_line}} will {{other_action}}."
                ),
                templates=[
                    "{{line_id}}, do {{coordination_action}}. "
                    "{{other_line}} will coordinate.",
                    "{{coordination_action}} from your line at "
                    "{{transfer_point}}, {{other_line}} to {{other_action}}",
                ],
                actions=["instruction"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Copy {{coordination_action}} at {{transfer_point}}. "
                    "Coordinating with {{other_line}}."
                ),
                templates=[
                    "Roger, doing {{coordination_action}}.",
                    "Will coordinate {{coordination_action}} with "
                    "{{other_line}}.",
                ],
                actions=["coordination_action"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Good coordination. All lines maintain current "
                    "status and continue monitoring."
                ),
                templates=[
                    "Excellent coordination, maintain current state.",
                    "Good work. Continue normal service.",
                ],
                actions=["monitoring"],
            ),
        ],
    ),
    "schedule_recovery": ConversationTemplate(
        name="Schedule Recovery",
        incident_type="crowding",
        difficulty="medium",
        duration_estimate=4,
        context_requirements=["recovery_strategy", "target_headway"],
        expected_resolution="monitor",
        turns=[
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Recovering schedule now. Target is {{target_headway}} "
                    "minute headways by {{target_time}}."
                ),
                templates=[
                    "Starting schedule recovery to {{target_headway}} "
                    "minute headways",
                    "Recovery plan: restore to {{target_headway}} min "
                    "headways",
                ],
                actions=["recovery_plan"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Understood. We're at {{current_headway}} minute "
                    "headways now. What's our action?"
                ),
                templates=[
                    "Currently {{current_headway}} min apart. What do "
                    "we do?",
                    "Running {{current_headway}} minute headways now. "
                    "Awaiting recovery plan.",
                ],
                actions=["status_query"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "{{recovery_strategy}} to restore headway recovery. "
                    "Continue monitoring until we reach {{target_headway}}."
                ),
                templates=[
                    "Execute {{recovery_strategy}}. Monitor until headway "
                    "is normal.",
                    "Implement {{recovery_strategy}}. Watch for recovery.",
                ],
                actions=["recovery_action"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Executing {{recovery_strategy}}. Continuing to "
                    "monitor headway status."
                ),
                templates=[
                    "Implementing {{recovery_strategy}} now.",
                    "Executing plan, monitoring closely.",
                ],
                actions=["recovery_implementation", "monitoring"],
            ),
        ],
    ),
    "system_restart": ConversationTemplate(
        name="System Restart",
        incident_type="system_error",
        difficulty="hard",
        duration_estimate=6,
        context_requirements=["system_type", "restart_duration"],
        expected_resolution="monitor",
        turns=[
            DialogueTurn(
                speaker="field",
                message=(
                    "{{system_type}} system failure detected. "
                    "Initiating controlled shutdown."
                ),
                templates=[
                    "{{system_type}} issue. Beginning shutdown sequence.",
                    "{{system_type}} failure. Shutdown initiated.",
                ],
                actions=["system_shutdown"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Copy {{system_type}} shutdown. Place all trains into "
                    "safe hold status."
                ),
                templates=[
                    "Acknowledged. Shutting down {{system_type}}. "
                    "Holding all trains.",
                    "Roger, {{system_type}} shutdown. Safe hold all trains.",
                ],
                actions=["safe_hold"],
            ),
            DialogueTurn(
                speaker="field",
                message=(
                    "All trains in safe hold. {{system_type}} restart "
                    "beginning now."
                ),
                templates=[
                    "Trains safe. Restarting {{system_type}}.",
                    "All safe, reboot sequence starting.",
                ],
                actions=["system_restart"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Restart in progress. ETA {{restart_duration}} "
                    "minutes for full recovery."
                ),
                templates=[
                    "Restarting now, {{restart_duration}} min to full "
                    "recovery",
                    "System reboot, expect {{restart_duration}} minute "
                    "restart window",
                ],
                actions=["monitoring"],
            ),
            DialogueTurn(
                speaker="field",
                message=(
                    "{{system_type}} system restart complete. Systems "
                    "nominal. Ready to resume service."
                ),
                templates=[
                    "Restart complete, all systems green.",
                    "{{system_type}} operational again, ready to proceed.",
                ],
                actions=["system_recovery"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Excellent. Resuming service gradually. Monitor "
                    "system stability."
                ),
                templates=[
                    "Good. Resume service, watch for any issues.",
                    "Clear to proceed. Monitor system performance.",
                ],
                actions=["service_resume", "monitoring"],
            ),
        ],
    ),
    "crowd_management": ConversationTemplate(
        name="Crowd Management",
        incident_type="crowding",
        difficulty="medium",
        duration_estimate=4,
        context_requirements=["crowded_location", "capacity_percent"],
        expected_resolution="hold_train",
        turns=[
            DialogueTurn(
                speaker="operator",
                message=(
                    "{{crowded_location}} is at {{capacity_percent}}% "
                    "capacity. Cannot accept more passengers safely."
                ),
                templates=[
                    "{{crowded_location}} overcrowded, {{capacity_percent}}% "
                    "full.",
                    "Extremely crowded at {{crowded_location}}, "
                    "{{capacity_percent}}% capacity.",
                ],
                actions=["capacity_report"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Understood. Hold at previous stop for crowding "
                    "management. Skip station if necessary."
                ),
                templates=[
                    "Hold before {{crowded_location}} until it clears.",
                    "Skip or hold before that station until cleared.",
                ],
                actions=["hold_decision"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Holding at {{previous_stop}}. Station staff managing "
                    "{{crowded_location}} egress."
                ),
                templates=[
                    "Holding. Staff helping passengers exit crowded station.",
                    "On hold. Station staff assisting crowd management.",
                ],
                actions=["crowding_mitigation"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Good. Continue hold until {{crowded_location}} clears. "
                    "Inform passengers of cause."
                ),
                templates=[
                    "Keep hold. Announce crowding reason to passengers.",
                    "Maintain hold, brief passengers on crowding situation.",
                ],
                actions=["communication"],
            ),
        ],
    ),
    "weather_response": ConversationTemplate(
        name="Weather Response",
        incident_type="weather_related",
        difficulty="medium",
        duration_estimate=5,
        context_requirements=["weather_type", "affected_areas"],
        expected_resolution="communication",
        turns=[
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Weather alert: {{weather_type}} in {{affected_areas}}. "
                    "Implement {{weather_protocol}}."
                ),
                templates=[
                    "{{weather_type}} developing in {{affected_areas}}. "
                    "Protocol {{weather_protocol}}.",
                    "Weather update: {{weather_type}} at {{affected_areas}}. "
                    "Follow {{weather_protocol}}.",
                ],
                actions=["weather_alert"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Copy weather protocol. Reducing speed in "
                    "{{affected_areas}}."
                ),
                templates=[
                    "Acknowledged, implementing {{weather_protocol}}.",
                    "Roger, speed reduction for {{weather_type}} at "
                    "{{affected_areas}}.",
                ],
                actions=["speed_reduction"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "All trains monitor conditions. Report any issues "
                    "immediately."
                ),
                templates=[
                    "Monitor conditions closely, report problems right away.",
                    "Watch for any weather-related issues, alert dispatch.",
                ],
                actions=["monitoring"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Continuing with caution. Currently passing "
                    "{{affected_areas}} at reduced speed."
                ),
                templates=[
                    "Proceeding slowly through {{affected_areas}}.",
                    "In weather area now, cautious operation.",
                ],
                actions=["cautious_operation"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Good. Once clear of {{affected_areas}}, resume normal "
                    "speed and operations."
                ),
                templates=[
                    "Clear of weather zone, normal speed OK.",
                    "Once past {{affected_areas}}, return to normal service.",
                ],
                actions=["monitoring"],
            ),
        ],
    ),
    "security_incident_response": ConversationTemplate(
        name="Security Incident Response",
        incident_type="security_incident",
        difficulty="hard",
        duration_estimate=6,
        context_requirements=["security_type", "location", "threat_level"],
        expected_resolution="hold_train",
        turns=[
            DialogueTurn(
                speaker="operator",
                message=(
                    "Security incident at {{location}} - {{security_type}}. "
                    "Train on hold, doors locked."
                ),
                templates=[
                    "Security issue at {{location}}: {{security_type}}. "
                    "Holding, doors secured.",
                    "Suspicious activity at {{location}}. Train stopped, "
                    "locked down.",
                ],
                actions=["security_alert", "safe_hold"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Acknowledged security incident at {{location}}. "
                    "Police and transit police en route."
                ),
                templates=[
                    "Calling police to {{location}} now.",
                    "Security response dispatched to {{location}}.",
                ],
                actions=["police_dispatch"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "{{security_type}} situation ongoing. {{passenger_count}} "
                    "passengers safe on train."
                ),
                templates=[
                    "Situation developing. {{passenger_count}} passengers "
                    "aboard, safe.",
                    "{{passenger_count}} passengers on board, maintaining "
                    "hold.",
                ],
                actions=["passenger_safety"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Hold position. Do not release passengers or open doors "
                    "until police clear situation."
                ),
                templates=[
                    "Maintain hold, keep doors locked until all-clear.",
                    "Stay put. Police will signal when situation is clear.",
                ],
                actions=["security_protocol"],
            ),
            DialogueTurn(
                speaker="operator",
                message=(
                    "Police arrived at {{location}}. Situation being assessed."
                ),
                templates=[
                    "Officers on scene now.",
                    "Police arrived, situation under control.",
                ],
                actions=["police_response"],
            ),
            DialogueTurn(
                speaker="dispatcher",
                message=(
                    "Once police clear, resume service and document incident "
                    "for report."
                ),
                templates=[
                    "Proceed once police clear. File incident report.",
                    "Resume service when cleared, report details.",
                ],
                actions=["service_resume", "incident_reporting"],
            ),
        ],
    ),
}


def get_conversation_template(
    template_name: str,
) -> ConversationTemplate:
    """
    Retrieve a conversation template by name.

    Args:
        template_name: Name of template to retrieve

    Returns:
        The requested ConversationTemplate

    Raises:
        KeyError: If template not found
    """
    if template_name not in CONVERSATION_TEMPLATES:
        raise KeyError(f"Unknown conversation template: {template_name}")
    return CONVERSATION_TEMPLATES[template_name]


def list_templates() -> List[str]:
    """
    List all available conversation templates.

    Returns:
        List of template names
    """
    return list(CONVERSATION_TEMPLATES.keys())


def get_templates_by_incident(
    incident_type: str,
) -> List[ConversationTemplate]:
    """
    Get all templates for a specific incident type.

    Args:
        incident_type: Type of incident

    Returns:
        List of matching ConversationTemplate objects
    """
    return [
        t for t in CONVERSATION_TEMPLATES.values()
        if t.incident_type == incident_type
    ]
