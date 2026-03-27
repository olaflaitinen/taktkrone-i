"""
Scenario and conversation template library for OCC scenario generation.
"""

from occlm.synthesis.templates.scenario_templates import (
    ScenarioTemplate,
    ParameterSpec,
    TopologyConstraint,
    ActionTemplate,
    ActionType,
    Severity,
    Difficulty,
    TEMPLATE_REGISTRY,
    get_template,
    list_templates,
    get_templates_by_type,
    get_templates_by_difficulty,
)
from occlm.synthesis.templates.occ_conversations import (
    DialogueTurn,
    ConversationTemplate,
    CONVERSATION_TEMPLATES,
    get_conversation_template,
    get_templates_by_incident,
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
