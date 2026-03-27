"""
Synthesis module for TAKTKRONE-I Phase 2.

Provides synthetic data generation capabilities including:
- Disruption pattern templates
- Network topology simulation
- Scenario generation
- Dialogue templates
- Dialogue generation
- Quality scoring
"""

from occlm.synthesis.disruption_patterns import (
    DisruptionTemplate,
    DISRUPTION_TEMPLATES,
    get_template,
    get_templates_by_severity,
    get_templates_by_type,
)
from occlm.synthesis.topology_simulator import (
    TopologySimulator,
    create_sample_network,
)
from occlm.synthesis.scenario_engine import ScenarioEngine
from occlm.synthesis.templates.occ_conversations import (
    ConversationTemplate,
    DialogueTurn,
    CONVERSATION_TEMPLATES,
    get_conversation_template,
    get_templates_by_incident,
    list_templates as list_conversation_templates,
)
from occlm.synthesis.dialogue_generator import DialogueGenerator
from occlm.synthesis.quality_scorer import QualityScorer

__all__ = [
    "DisruptionTemplate",
    "DISRUPTION_TEMPLATES",
    "get_template",
    "get_templates_by_severity",
    "get_templates_by_type",
    "TopologySimulator",
    "create_sample_network",
    "ScenarioEngine",
    "ConversationTemplate",
    "DialogueTurn",
    "CONVERSATION_TEMPLATES",
    "get_conversation_template",
    "get_templates_by_incident",
    "list_conversation_templates",
    "DialogueGenerator",
    "QualityScorer",
]
