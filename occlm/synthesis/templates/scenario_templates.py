"""
Scenario template library for synthetic OCC scenario generation.

This module contains parameterized templates for generating diverse
operational scenarios for TAKTKRONE-I training and evaluation.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    """Operational action types"""

    HOLD_TRAIN = "hold_train"
    EXPRESS_OPERATION = "express_operation"
    SHORT_TURN = "short_turn"
    SKIP_STOP = "skip_stop"
    ADDITIONAL_TRAIN = "additional_train"
    REDUCE_FREQUENCY = "reduce_frequency"
    SWITCH_TRACK = "switch_track"
    PLATFORM_SHIFT = "platform_shift"
    BRIDGE_SERVICE = "bridge_service"
    COMMUNICATION = "communication"
    ESCALATION = "escalation"
    MONITOR = "monitor"
    VERIFICATION = "verification"


class Severity(str, Enum):
    """Incident severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Difficulty(str, Enum):
    """Scenario difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class ParameterSpec:
    """Specification for a template parameter"""

    name: str
    param_type: str  # int, float, str, choice, range
    default: Any
    choices: list[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None
    description: str = ""


@dataclass
class TopologyConstraint:
    """Topology constraint that must be satisfied"""

    constraint_type: str
    description: str
    check_function: Callable | None = None


@dataclass
class ActionTemplate:
    """Template for an action candidate"""

    action_type: ActionType
    description_template: str
    feasibility_conditions: list[str]
    benefit_template: str
    cost_template: str


@dataclass
class ScenarioTemplate:
    """
    Complete scenario template for generation.

    Templates define the structure and parameters for generating
    OCC scenarios. Each template produces scenarios of a specific
    type (bunching, signal failure, etc.) with controlled randomization.
    """

    name: str
    template_id: str
    version: str
    description: str

    # Classification
    incident_type: str
    scenario_type: str
    difficulty_range: tuple[Difficulty, Difficulty]
    severity_range: tuple[Severity, Severity]

    # Parameters
    parameters: list[ParameterSpec] = field(default_factory=list)

    # Constraints
    topology_constraints: list[TopologyConstraint] = field(default_factory=list)

    # Narrative templates
    briefing_template: str = ""
    user_query_templates: list[str] = field(default_factory=list)

    # Action options
    action_templates: list[ActionTemplate] = field(default_factory=list)

    # Output configuration
    recommended_actions: list[ActionType] = field(default_factory=list)
    confidence_range: tuple[float, float] = (0.7, 0.95)


# =============================================================================
# TEMPLATE LIBRARY
# =============================================================================

BUNCHING_SINGLE_LINE = ScenarioTemplate(
    name="Single Line Train Bunching",
    template_id="bunching_single_line",
    version="1.0.0",
    description="Multiple trains bunched on a single line segment",
    incident_type="RPL",
    scenario_type="bunching",
    difficulty_range=(Difficulty.EASY, Difficulty.MEDIUM),
    severity_range=(Severity.LOW, Severity.MEDIUM),
    parameters=[
        ParameterSpec(
            name="num_trains_bunched",
            param_type="range",
            default=3,
            min_value=2,
            max_value=5,
            description="Number of trains in the bunch",
        ),
        ParameterSpec(
            name="bunch_headway_seconds",
            param_type="range",
            default=90,
            min_value=60,
            max_value=180,
            description="Headway between bunched trains",
        ),
        ParameterSpec(
            name="scheduled_headway_seconds",
            param_type="range",
            default=360,
            min_value=240,
            max_value=600,
            description="Normal scheduled headway",
        ),
        ParameterSpec(
            name="time_of_day",
            param_type="choice",
            default="peak_pm",
            choices=["peak_am", "peak_pm", "midday", "evening"],
            description="Time of day for scenario",
        ),
        ParameterSpec(
            name="initial_cause",
            param_type="choice",
            default="signal_delay",
            choices=["signal_delay", "extended_dwell", "slow_order", "upstream_delay"],
            description="Initial cause of bunching",
        ),
    ],
    topology_constraints=[
        TopologyConstraint(
            constraint_type="linear_segment",
            description="Scenario location must be linear segment without branches",
        ),
        TopologyConstraint(
            constraint_type="sufficient_stations",
            description="At least 5 stations in affected segment",
        ),
    ],
    briefing_template="""
{num_trains_bunched} {direction} {line} trains are bunched between {start_station} and {end_station}.
The trains are operating within {bunch_headway_seconds} seconds of each other instead of the scheduled {scheduled_headway_seconds}-second headway.
Initial cause appears to be {initial_cause_description}.
Current time: {current_time}. Service pattern: {time_of_day}.
""",
    user_query_templates=[
        "{line} {direction} trains are bunching between {start_station} and {end_station}. {num_trains_bunched} trains are within {total_bunch_time} minutes of each other. What should we do?",
        "We have a bunching situation on {line} {direction}. Trains are running {bunch_headway_seconds} seconds apart instead of the normal {scheduled_headway_seconds} seconds. How do we restore headways?",
        "Multiple trains are bunched on {line}. Need recommendations for headway regulation.",
    ],
    action_templates=[
        ActionTemplate(
            action_type=ActionType.HOLD_TRAIN,
            description_template="Hold leading train at {hold_station} for {hold_duration} minutes",
            feasibility_conditions=[
                "Hold station has sufficient platform capacity",
                "Trailing trains can spread during hold",
            ],
            benefit_template="Creates separation, allows trailing trains to spread naturally",
            cost_template="Platform crowding at hold station, {delay_impact} additional passenger-minutes delay",
        ),
        ActionTemplate(
            action_type=ActionType.EXPRESS_OPERATION,
            description_template="Run trailing train express from {express_start} to {express_end}, skipping {skip_count} stops",
            feasibility_conditions=[
                "Express track available or can skip on local",
                "Skipped stations have alternative service",
            ],
            benefit_template="Faster gap closure, reduced bunch size",
            cost_template="Passengers at skipped stops must wait, potential crowding at destination",
        ),
        ActionTemplate(
            action_type=ActionType.SHORT_TURN,
            description_template="Short turn middle train at {short_turn_station}",
            feasibility_conditions=[
                "Crossover available at short turn location",
                "Service gap acceptable",
            ],
            benefit_template="Reduces bunch size, adds service to opposite direction",
            cost_template="Service gap for passengers beyond short turn point",
        ),
    ],
    recommended_actions=[ActionType.HOLD_TRAIN, ActionType.MONITOR],
    confidence_range=(0.75, 0.90),
)


SIGNAL_FAILURE_SEGMENT = ScenarioTemplate(
    name="Signal Failure on Track Segment",
    template_id="signal_failure_segment",
    version="1.0.0",
    description="Signal system failure affecting track segment operations",
    incident_type="SIG",
    scenario_type="signal_failure",
    difficulty_range=(Difficulty.MEDIUM, Difficulty.HARD),
    severity_range=(Severity.MEDIUM, Severity.HIGH),
    parameters=[
        ParameterSpec(
            name="signal_issue_type",
            param_type="choice",
            default="track_circuit",
            choices=["track_circuit", "interlocking", "communication", "atp_failure"],
            description="Type of signal failure",
        ),
        ParameterSpec(
            name="affected_tracks",
            param_type="choice",
            default="both",
            choices=["northbound", "southbound", "both"],
            description="Which tracks affected",
        ),
        ParameterSpec(
            name="estimated_repair_minutes",
            param_type="range",
            default=30,
            min_value=15,
            max_value=120,
            description="Estimated time to repair",
        ),
        ParameterSpec(
            name="trains_affected",
            param_type="range",
            default=5,
            min_value=2,
            max_value=15,
            description="Number of trains currently affected",
        ),
    ],
    topology_constraints=[
        TopologyConstraint(
            constraint_type="signal_location_valid",
            description="Signal location must exist in topology",
        ),
    ],
    briefing_template="""
Signal {signal_issue_type} at {signal_location} affecting {affected_tracks} track(s) between {start_station} and {end_station}.
{trains_affected} trains currently delayed. Maintainer en route, ETA {maintainer_eta} minutes.
Estimated repair time: {estimated_repair_minutes} minutes.
Current delays averaging {average_delay} minutes {direction}.
""",
    user_query_templates=[
        "Signal problem at {signal_location}. {trains_affected} trains held. What's our recovery strategy?",
        "We have a {signal_issue_type} failure between {start_station} and {end_station}. How do we manage service until repair?",
        "{signal_issue_type} issue causing {average_delay} minute delays. Repair estimated at {estimated_repair_minutes} minutes. Options?",
    ],
    action_templates=[
        ActionTemplate(
            action_type=ActionType.VERIFICATION,
            description_template="Verify signal status with maintainer at {signal_location}",
            feasibility_conditions=["Maintainer contactable"],
            benefit_template="Accurate information for decision making",
            cost_template="Time to confirm",
        ),
        ActionTemplate(
            action_type=ActionType.SHORT_TURN,
            description_template="Short turn trains at {short_turn_station_before} and {short_turn_station_after}",
            feasibility_conditions=["Crossovers available on both sides of failure"],
            benefit_template="Maintain service on unaffected portions of line",
            cost_template="No through service, transfer required",
        ),
        ActionTemplate(
            action_type=ActionType.BRIDGE_SERVICE,
            description_template="Implement bus bridge between {bridge_start} and {bridge_end}",
            feasibility_conditions=["Buses available", "Surface route feasible"],
            benefit_template="Maintains connectivity across affected segment",
            cost_template="Slower than rail, capacity limitations",
        ),
    ],
    recommended_actions=[
        ActionType.VERIFICATION,
        ActionType.SHORT_TURN,
        ActionType.COMMUNICATION,
    ],
    confidence_range=(0.60, 0.85),
)


TERMINAL_CONGESTION = ScenarioTemplate(
    name="Terminal Congestion",
    template_id="terminal_congestion",
    version="1.0.0",
    description="Backup at terminal due to insufficient turnback capacity",
    incident_type="TCG",
    scenario_type="terminal_congestion",
    difficulty_range=(Difficulty.MEDIUM, Difficulty.HARD),
    severity_range=(Severity.MEDIUM, Severity.HIGH),
    parameters=[
        ParameterSpec(
            name="congestion_cause",
            param_type="choice",
            default="slow_turnback",
            choices=[
                "slow_turnback",
                "operator_availability",
                "platform_occupied",
                "switch_delay",
            ],
            description="Cause of terminal congestion",
        ),
        ParameterSpec(
            name="trains_waiting",
            param_type="range",
            default=3,
            min_value=2,
            max_value=6,
            description="Trains waiting at terminal",
        ),
        ParameterSpec(
            name="turnback_time_actual",
            param_type="range",
            default=8,
            min_value=5,
            max_value=15,
            description="Actual turnback time in minutes",
        ),
        ParameterSpec(
            name="turnback_time_scheduled",
            param_type="range",
            default=4,
            min_value=3,
            max_value=6,
            description="Scheduled turnback time in minutes",
        ),
    ],
    topology_constraints=[
        TopologyConstraint(
            constraint_type="terminal_valid",
            description="Must be a valid terminal station",
        ),
        TopologyConstraint(
            constraint_type="turnback_infrastructure",
            description="Terminal must have turnback capability",
        ),
    ],
    briefing_template="""
Terminal congestion at {terminal_station}. {trains_waiting} trains waiting for turnback.
Turnback time running {turnback_time_actual} minutes vs scheduled {turnback_time_scheduled} minutes.
Cause: {congestion_cause_description}.
Delays propagating back {propagation_stations} stations. Average inbound delay: {inbound_delay} minutes.
""",
    user_query_templates=[
        "{terminal_station} terminal is backed up. {trains_waiting} trains waiting. How do we clear this?",
        "Turnback delays at {terminal_station} causing service gaps. What are our options?",
        "Terminal congestion at {terminal_station} due to {congestion_cause}. Need recovery plan.",
    ],
    action_templates=[
        ActionTemplate(
            action_type=ActionType.SHORT_TURN,
            description_template="Short turn trains at {short_turn_location} before terminal",
            feasibility_conditions=["Crossover available before terminal"],
            benefit_template="Relieves terminal pressure, maintains service frequency",
            cost_template="Reduced coverage to terminal, passenger confusion",
        ),
        ActionTemplate(
            action_type=ActionType.REDUCE_FREQUENCY,
            description_template="Temporarily reduce service to {reduced_frequency} minute headways",
            feasibility_conditions=["Passenger load acceptable at reduced frequency"],
            benefit_template="Matches service to terminal capacity",
            cost_template="Increased crowding, longer waits",
        ),
        ActionTemplate(
            action_type=ActionType.HOLD_TRAIN,
            description_template="Hold departing trains at {hold_location} until terminal clears",
            feasibility_conditions=["Mid-line station can accommodate holds"],
            benefit_template="Prevents additional congestion at terminal",
            cost_template="Delays for passengers on held trains",
        ),
    ],
    recommended_actions=[ActionType.SHORT_TURN, ActionType.COMMUNICATION],
    confidence_range=(0.70, 0.88),
)


DISABLED_TRAIN_MAINLINE = ScenarioTemplate(
    name="Disabled Train on Mainline",
    template_id="disabled_train_mainline",
    version="1.0.0",
    description="Train disabled in service on mainline requiring removal",
    incident_type="TDS",
    scenario_type="disabled_train",
    difficulty_range=(Difficulty.HARD, Difficulty.EXPERT),
    severity_range=(Severity.HIGH, Severity.CRITICAL),
    parameters=[
        ParameterSpec(
            name="failure_type",
            param_type="choice",
            default="propulsion",
            choices=["propulsion", "brake", "door", "hvac", "coupler"],
            description="Type of vehicle failure",
        ),
        ParameterSpec(
            name="can_move_under_power",
            param_type="choice",
            default=False,
            choices=[True, False],
            description="Whether train can move under own power",
        ),
        ParameterSpec(
            name="passenger_evacuation_needed",
            param_type="choice",
            default=False,
            choices=[True, False],
            description="Whether passengers need evacuation",
        ),
        ParameterSpec(
            name="rescue_train_eta",
            param_type="range",
            default=20,
            min_value=10,
            max_value=45,
            description="ETA for rescue train in minutes",
        ),
    ],
    briefing_template="""
Train {train_id} disabled at {location} due to {failure_type} failure.
Train {"can" if can_move_under_power else "cannot"} move under own power.
{passenger_count} passengers on board. {"Evacuation required." if passenger_evacuation_needed else "Passengers secure on train."}
Rescue train ETA: {rescue_train_eta} minutes.
{following_trains} trains held behind disabled train.
""",
    user_query_templates=[
        "Train disabled at {location}. Cannot move. {following_trains} trains held. What's the plan?",
        "{failure_type} failure on train at {location}. Need recovery strategy.",
        "Disabled train blocking {direction} track at {location}. How do we restore service?",
    ],
    recommended_actions=[
        ActionType.VERIFICATION,
        ActionType.SHORT_TURN,
        ActionType.BRIDGE_SERVICE,
    ],
    confidence_range=(0.55, 0.80),
)


# Template registry
TEMPLATE_REGISTRY: dict[str, ScenarioTemplate] = {
    "bunching_single_line": BUNCHING_SINGLE_LINE,
    "signal_failure_segment": SIGNAL_FAILURE_SEGMENT,
    "terminal_congestion": TERMINAL_CONGESTION,
    "disabled_train_mainline": DISABLED_TRAIN_MAINLINE,
}


def get_template(template_id: str) -> ScenarioTemplate:
    """Get template by ID"""
    if template_id not in TEMPLATE_REGISTRY:
        raise ValueError(f"Unknown template: {template_id}")
    return TEMPLATE_REGISTRY[template_id]


def list_templates() -> list[str]:
    """List all available template IDs"""
    return list(TEMPLATE_REGISTRY.keys())


def get_templates_by_type(scenario_type: str) -> list[ScenarioTemplate]:
    """Get all templates for a scenario type"""
    return [t for t in TEMPLATE_REGISTRY.values() if t.scenario_type == scenario_type]


def get_templates_by_difficulty(
    min_difficulty: Difficulty, max_difficulty: Difficulty
) -> list[ScenarioTemplate]:
    """Get templates within difficulty range"""
    difficulty_order = [
        Difficulty.EASY,
        Difficulty.MEDIUM,
        Difficulty.HARD,
        Difficulty.EXPERT,
    ]
    min_idx = difficulty_order.index(min_difficulty)
    max_idx = difficulty_order.index(max_difficulty)

    result = []
    for template in TEMPLATE_REGISTRY.values():
        t_min = difficulty_order.index(template.difficulty_range[0])
        t_max = difficulty_order.index(template.difficulty_range[1])
        if t_min <= max_idx and t_max >= min_idx:
            result.append(template)
    return result
