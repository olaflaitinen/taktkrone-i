"""
Scenario and conversation template library for OCC scenario generation.
"""

from occlm.synthesis.templates.occ_conversations import (
    CONVERSATION_TEMPLATES,
    ConversationTemplate,
    DialogueTurn,
    get_conversation_template,
    get_templates_by_incident,
)
from occlm.synthesis.templates.scenario_templates import (
    TEMPLATE_REGISTRY,
    ActionTemplate,
    ActionType,
    Difficulty,
    ParameterSpec,
    ScenarioTemplate,
    Severity,
    TopologyConstraint,
    get_template,
    get_templates_by_difficulty,
    get_templates_by_type,
    list_templates,
)

__all__ = [
    "ScenarioTemplate",
    "ParameterSpec",
    "TopologyConstraint",
    "ActionTemplate",
    "ActionType",
    "Severity",
    "Difficulty",
    "TEMPLATE_REGISTRY",
    "get_template",
    "list_templates",
    "get_templates_by_type",
    "get_templates_by_difficulty",
    "DialogueTurn",
    "ConversationTemplate",
    "CONVERSATION_TEMPLATES",
    "get_conversation_template",
    "get_templates_by_incident",
]
