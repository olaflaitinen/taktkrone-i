"""Unit tests for synthesis modules."""

from __future__ import annotations

from datetime import datetime

import pytest

from occlm.synthesis import (
    ConversationTemplate,
    DialogueGenerator,
    DisruptionTemplate,
    DISRUPTION_TEMPLATES,
    QualityScorer,
    ScenarioEngine,
    TopologySimulator,
)


class TestDisruptionTemplates:
    """Test disruption pattern templates."""

    def test_templates_exist(self) -> None:
        """Test that disruption templates are defined."""
        assert len(DISRUPTION_TEMPLATES) >= 15
        assert "signal_failure" in DISRUPTION_TEMPLATES
        assert "medical_emergency" in DISRUPTION_TEMPLATES

    def test_template_structure(self) -> None:
        """Test template structure is valid."""
        for _name, template in DISRUPTION_TEMPLATES.items():
            assert isinstance(template, DisruptionTemplate)
            assert template.incident_type is not None
            assert template.duration_minutes[0] <= template.duration_minutes[1]
            assert 0.0 <= template.probability <= 1.0


class TestTopologySimulator:
    """Test topology simulation."""

    @pytest.fixture
    def sample_network(self) -> dict:
        """Sample network data."""
        return {
            "stops": {
                "A": {"name": "Station A", "lat": 40.7128, "lon": -74.0060},
                "B": {"name": "Station B", "lat": 40.7589, "lon": -73.9851},
            },
            "routes": {"Line1": {"stops": ["A", "B"]}},
        }

    @pytest.fixture
    def simulator(self, sample_network: dict) -> TopologySimulator:
        """Create simulator instance."""
        return TopologySimulator(sample_network)

    def test_simulator_initialization(self, simulator: TopologySimulator) -> None:
        """Test simulator initializes correctly."""
        assert simulator.network_data is not None
        assert len(simulator.get_all_routes()) > 0

    def test_delay_propagation(self, simulator: TopologySimulator) -> None:
        """Test delay propagation simulation."""
        delays = simulator.simulate_delay_propagation(
            initial_delay=10, route_id="Line1"
        )
        assert isinstance(delays, dict)

    def test_affected_routes(self, simulator: TopologySimulator) -> None:
        """Test getting affected routes."""
        affected = simulator.get_affected_routes("Line1")
        assert isinstance(affected, list)


class TestScenarioEngine:
    """Test scenario generation."""

    @pytest.fixture
    def sample_network(self) -> dict:
        """Sample network data."""
        return {
            "stops": {"A": {"name": "Station A"}, "B": {"name": "Station B"}},
            "routes": {"Line1": {"stops": ["A", "B"]}},
        }

    @pytest.fixture
    def engine(self, sample_network: dict) -> ScenarioEngine:
        """Create engine instance."""
        return ScenarioEngine(sample_network)

    def test_engine_initialization(self, engine: ScenarioEngine) -> None:
        """Test engine initializes correctly."""
        assert engine.topology_sim is not None

    def test_generate_delay_scenario(self, engine: ScenarioEngine) -> None:
        """Test delay scenario generation."""
        scenarios = engine.generate_delay_scenario(num_scenarios=5)
        assert len(scenarios) == 5
        for scenario in scenarios:
            assert "scenario_id" in scenario
            assert "incident_type" in scenario
            assert "timestamp" in scenario


class TestDialogueGenerator:
    """Test dialogue generation."""

    @pytest.fixture
    def generator(self) -> DialogueGenerator:
        """Create generator instance."""
        return DialogueGenerator()

    def test_generator_initialization(self, generator: DialogueGenerator) -> None:
        """Test generator initializes correctly."""
        assert generator is not None

    def test_generate_dialogue(self, generator: DialogueGenerator) -> None:
        """Test dialogue generation."""
        scenario = {
            "incident_type": "signal_failure",
            "location": "Station A",
            "severity": "medium",
            "duration_minutes": 15,
        }

        dialogue = generator.generate_occ_dialogue(scenario, difficulty="medium")
        assert isinstance(dialogue, list)
        assert len(dialogue) >= 2  # At least 2 turns

        # Check dialogue structure
        for turn in dialogue:
            assert "role" in turn
            assert "content" in turn
            assert turn["role"] in ["operator", "dispatcher"]


class TestQualityScorer:
    """Test quality scoring."""

    @pytest.fixture
    def scorer(self) -> QualityScorer:
        """Create scorer instance."""
        return QualityScorer()

    @pytest.fixture
    def sample_dialogue(self) -> list:
        """Sample dialogue for testing."""
        return [
            {"role": "operator", "content": "Signal failure at Station A"},
            {"role": "dispatcher", "content": "Copy. Maintenance dispatched."},
            {"role": "operator", "content": "Understood. ETA?"},
            {"role": "dispatcher", "content": "15 minutes estimated."},
        ]

    @pytest.fixture
    def sample_scenario(self) -> dict:
        """Sample scenario for testing."""
        return {
            "incident_type": "signal_failure",
            "duration_minutes": 15,
            "severity": "medium",
            "timestamp": datetime.now().isoformat(),
        }

    def test_scorer_initialization(self, scorer: QualityScorer) -> None:
        """Test scorer initializes correctly."""
        assert scorer is not None

    def test_coherence_scoring(
        self, scorer: QualityScorer, sample_dialogue: list
    ) -> None:
        """Test coherence scoring."""
        score = scorer.score_coherence(sample_dialogue)
        assert 0.0 <= score <= 1.0

    def test_realism_scoring(
        self, scorer: QualityScorer, sample_scenario: dict
    ) -> None:
        """Test realism scoring."""
        score = scorer.score_realism(sample_scenario)
        assert 0.0 <= score <= 1.0

    def test_temporal_consistency(
        self, scorer: QualityScorer, sample_scenario: dict
    ) -> None:
        """Test temporal consistency scoring."""
        score = scorer.score_temporal_consistency(sample_scenario)
        assert 0.0 <= score <= 1.0

    def test_overall_score(
        self, scorer: QualityScorer, sample_dialogue: list, sample_scenario: dict
    ) -> None:
        """Test overall quality scoring."""
        score = scorer.overall_score(sample_dialogue, sample_scenario)
        assert 0.0 <= score <= 1.0


class TestConversationTemplates:
    """Test conversation template system."""

    def test_templates_importable(self) -> None:
        """Test that conversation templates can be imported."""
        from occlm.synthesis.templates.occ_conversations import CONVERSATION_TEMPLATES

        assert len(CONVERSATION_TEMPLATES) >= 10
        assert "signal_failure_response" in CONVERSATION_TEMPLATES

    def test_template_structure(self) -> None:
        """Test template structure is valid."""
        from occlm.synthesis.templates.occ_conversations import CONVERSATION_TEMPLATES

        for _name, template in CONVERSATION_TEMPLATES.items():
            assert isinstance(template, ConversationTemplate)
            assert template.incident_type is not None
            assert len(template.turns) >= 2
            assert template.difficulty in ["easy", "medium", "hard"]


class TestIntegration:
    """Integration tests for synthesis pipeline."""

    def test_end_to_end_synthesis(self) -> None:
        """Test complete synthesis pipeline."""
        # Create network
        network_data = {
            "stops": {"A": {"name": "Station A"}, "B": {"name": "Station B"}},
            "routes": {"Line1": {"stops": ["A", "B"]}},
        }

        # Generate scenario
        engine = ScenarioEngine(network_data)
        scenarios = engine.generate_delay_scenario(num_scenarios=1)
        assert len(scenarios) == 1

        # Generate dialogue
        generator = DialogueGenerator()
        dialogue = generator.generate_occ_dialogue(scenarios[0], difficulty="easy")
        assert len(dialogue) >= 2

        # Score quality
        scorer = QualityScorer()
        quality_score = scorer.overall_score(dialogue, scenarios[0])
        assert 0.0 <= quality_score <= 1.0

        print(f"Generated scenario: {scenarios[0]['incident_type']}")
        print(f"Dialogue turns: {len(dialogue)}")
        print(f"Quality score: {quality_score:.3f}")
