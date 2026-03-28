from __future__ import annotations

from datetime import datetime

import pytest

from occlm.synthesis.dialogue_generator import DialogueGenerator
from occlm.synthesis.disruption_patterns import (
    DisruptionTemplate,
    get_template,
    get_templates_by_severity,
    get_templates_by_type,
)
from occlm.synthesis.quality_scorer import QualityScorer
from occlm.synthesis.scenario_engine import ScenarioEngine
from occlm.synthesis.templates import (
    Difficulty,
    get_templates_by_difficulty,
)
from occlm.synthesis.templates import (
    get_template as get_scenario_template,
)
from occlm.synthesis.templates import (
    get_templates_by_type as get_scenario_templates_by_type,
)
from occlm.synthesis.templates import (
    list_templates as list_scenario_templates,
)
from occlm.synthesis.templates.occ_conversations import (
    ConversationTemplate,
    DialogueTurn,
    get_conversation_template,
    get_templates_by_incident,
)
from occlm.synthesis.templates.occ_conversations import (
    list_templates as list_conversation_templates,
)
from occlm.synthesis.topology_simulator import (
    TopologySimulator,
    create_sample_network,
)


@pytest.fixture
def sample_network() -> dict:
    return create_sample_network()


def test_disruption_template_validation_and_helpers() -> None:
    template = DisruptionTemplate(
        name="Valid",
        incident_type="signal_failure",
        duration_minutes=(5, 10),
        severity="medium",
        affected_lines=["1"],
        affected_stops=None,
        passenger_impact="service_delay",
        probability=0.4,
    )

    assert template.root_causes == []
    assert get_template("signal_failure").incident_type == "signal_failure"
    assert any(
        t.incident_type == "signal_failure"
        for t in get_templates_by_type(["signal_failure", "missing"])
    )
    assert any(t.severity == "critical" for t in get_templates_by_severity("critical"))

    with pytest.raises(KeyError, match="Unknown incident type"):
        get_template("not_real")
    with pytest.raises(ValueError, match="probability"):
        DisruptionTemplate(
            name="BadProbability",
            incident_type="signal_failure",
            duration_minutes=(5, 10),
            severity="medium",
            affected_lines=["1"],
            affected_stops=None,
            passenger_impact="service_delay",
            probability=1.2,
        )
    with pytest.raises(ValueError, match="severity"):
        DisruptionTemplate(
            name="BadSeverity",
            incident_type="signal_failure",
            duration_minutes=(5, 10),
            severity="extreme",
            affected_lines=["1"],
            affected_stops=None,
            passenger_impact="service_delay",
            probability=0.5,
        )
    with pytest.raises(ValueError, match="passenger_impact"):
        DisruptionTemplate(
            name="BadImpact",
            incident_type="signal_failure",
            duration_minutes=(5, 10),
            severity="medium",
            affected_lines=["1"],
            affected_stops=None,
            passenger_impact="unknown",
            probability=0.5,
        )
    with pytest.raises(ValueError, match="duration_minutes"):
        DisruptionTemplate(
            name="BadDuration",
            incident_type="signal_failure",
            duration_minutes=(10, 5),
            severity="medium",
            affected_lines=["1"],
            affected_stops=None,
            passenger_impact="service_delay",
            probability=0.5,
        )


def test_conversation_and_scenario_template_helpers() -> None:
    assert (
        get_conversation_template("signal_failure_response").incident_type
        == "signal_failure"
    )
    assert "signal_failure_response" in list_conversation_templates()
    assert any(
        t.incident_type == "signal_failure"
        for t in get_templates_by_incident("signal_failure")
    )
    assert get_scenario_template("bunching_single_line").scenario_type == "bunching"
    assert "bunching_single_line" in list_scenario_templates()
    assert any(
        t.scenario_type == "bunching"
        for t in get_scenario_templates_by_type("bunching")
    )
    assert get_templates_by_difficulty(Difficulty.EASY, Difficulty.MEDIUM)

    with pytest.raises(KeyError, match="Unknown conversation template"):
        get_conversation_template("missing")
    with pytest.raises(ValueError, match="Unknown template"):
        get_scenario_template("missing")
    with pytest.raises(ValueError, match="speaker must"):
        DialogueTurn(speaker="invalid", message="hello")
    with pytest.raises(ValueError, match="difficulty must"):
        ConversationTemplate(
            name="Bad",
            incident_type="signal_failure",
            difficulty="expert",
            turns=[
                DialogueTurn(speaker="operator", message="one"),
                DialogueTurn(speaker="dispatcher", message="two"),
            ],
        )
    with pytest.raises(ValueError, match=">= 2 turns"):
        ConversationTemplate(
            name="TooShort",
            incident_type="signal_failure",
            difficulty="easy",
            turns=[DialogueTurn(speaker="operator", message="one")],
        )


def test_topology_simulator_branches(sample_network: dict) -> None:
    simulator = TopologySimulator(sample_network)

    assert simulator.get_all_routes() == ["1", "2", "3", "A", "B"]
    assert simulator.simulate_delay_propagation(12, "1", max_hops=1)["1"] == 12
    assert simulator.get_affected_routes("1") == ["1", "2", "3", "A", "B"]
    assert simulator.estimate_recovery_time("signal_failure", 10) >= 8
    assert simulator.get_network_metrics()["num_routes"] == 5
    assert simulator.validate_network() == []

    with pytest.raises(ValueError, match="must contain"):
        TopologySimulator({"routes": {}})
    with pytest.raises(ValueError, match="not in network"):
        simulator.simulate_delay_propagation(5, "Z")
    with pytest.raises(ValueError, match="not in network"):
        simulator.get_affected_routes("Z")

    warning_simulator = TopologySimulator(
        {
            "routes": {"1": {}, "2": {}},
            "connections": {"1": ["2", "3"]},
        }
    )
    warnings = warning_simulator.validate_network()
    assert any("has no connections" in warning for warning in warnings)
    assert any("non-existent route 3" in warning for warning in warnings)


def test_scenario_engine_paths(sample_network: dict) -> None:
    engine = ScenarioEngine(
        topology_simulator=TopologySimulator(sample_network), random_seed=1
    )

    assert engine.get_scenario_stats() == {"count": 0}

    bunching = engine.generate_bunching_scenario(num_scenarios=1)[0]
    turnback = engine.generate_turnback_scenario(num_scenarios=1)[0]
    conflict = engine.generate_conflict_scenario(num_scenarios=1)[0]
    delay = engine.generate_delay_scenario(num_scenarios=1)[0]

    assert "num_bunched_trains" in bunching["incident_details"]
    assert "turnback_location" in turnback["incident_details"]
    assert "conflict_type" in conflict["incident_details"]
    assert delay["scenario_type"] == "delay"

    high_progression = engine._generate_incident_progression(
        {"type": "signal_failure", "severity": "high", "duration_minutes": 8}
    )
    low_progression = engine._generate_incident_progression(
        {"type": "passenger_incident", "severity": "low", "duration_minutes": 12}
    )
    stats = engine.get_scenario_stats()

    assert any(event["event"] == "escalation" for event in high_progression)
    assert not any(event["event"] == "recovery_initiated" for event in high_progression)
    assert any(event["event"] == "recovery_initiated" for event in low_progression)
    assert engine._get_affected_stops(["Z"]) == ["unknown_stop"]
    assert (
        engine._estimate_passenger_impact(
            {"type": "signal_failure", "severity": "critical", "duration_minutes": 20},
            20,
            ["a", "b"],
        )["service_level_reduction"]
        == 0.9
    )
    assert stats["count"] == 4
    assert "delay" in stats["scenario_types"]


def test_dialogue_generator_branch_behaviour(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = DialogueGenerator(random_seed=7)
    scenario = {
        "incident_details": {
            "type": "signal_failure",
            "signal_issue_type": "relay",
            "affected_tracks": "both",
            "signal_location": "Signal 12",
            "trains_affected": 2,
        },
        "timestamp": datetime.now().isoformat(),
    }

    dialogue = generator.generate_occ_dialogue(
        scenario,
        difficulty="medium",
        template_name="signal_failure_response",
    )
    assert len(dialogue) >= 2

    assert generator._select_template("unknown").name == "Delay Escalation"

    monkeypatch.setattr(
        "occlm.synthesis.dialogue_generator.random.randint", lambda a, b: a
    )
    monkeypatch.setattr(
        "occlm.synthesis.dialogue_generator.random.choice", lambda seq: seq[0]
    )
    monkeypatch.setattr("occlm.synthesis.dialogue_generator.random.random", lambda: 0.0)

    filled = generator._slot_fill_template(
        "{{num_trains_bunched}} {{signal_location}} {{line_id}}",
        {"incident_details": {}},
    )
    medium_message = generator._vary_formality("please understand thank you", "medium")
    hard_message = generator._vary_formality(
        "please approximately understand the signal problem currently",
        "hard",
    )
    alternatives = generator._generate_alternatives("Delay problem")
    annotated = generator.annotate_dialogue_with_actions(
        [
            {"speaker": "operator", "content": "Incident detected at station"},
            {
                "speaker": "dispatcher",
                "content": "Please notify passengers",
                "actions": ["communication"],
            },
            {"speaker": "supervisor", "content": "resume service"},
        ]
    )

    assert filled == "2 Signal 1 1"
    assert medium_message == "understand thank you"
    assert "approx" in hard_message
    assert "(Over)" in hard_message
    assert len(alternatives) >= 2
    assert annotated[0]["speaker_context"] == "field_operator"
    assert annotated[0]["has_urgency"] is True
    assert annotated[1]["speaker_context"] == "occ_dispatcher"
    assert annotated[2]["speaker_context"] == "supervisor"
    assert generator._infer_actions("plain text with nothing special") == [
        "communication"
    ]
    assert (
        len(
            generator._infer_actions(
                "incident detected, hold service, notify passengers, resume service"
            )
        )
        <= 3
    )

    with pytest.raises(ValueError, match="scenario missing incident_details.type"):
        generator.generate_occ_dialogue(
            {"incident_details": {}}, template_name="signal_failure_response"
        )
    with pytest.raises(ValueError, match="No template found"):
        generator.generate_occ_dialogue(scenario, template_name="missing")


def test_quality_scorer_branch_behaviour() -> None:
    scorer = QualityScorer()
    poor_dialogue = [
        {"speaker": "operator", "content": "incident", "actions": []},
        {"speaker": "operator", "content": "incident", "actions": []},
    ]
    realistic_scenario = {
        "timestamp": datetime.now().isoformat(),
        "scenario_type": "delay",
        "incident_details": {
            "type": "signal_failure",
            "duration_minutes": 20,
            "severity": "high",
        },
        "affected_routes": ["1"],
        "passenger_impact": {"service_level_reduction": 0.6},
        "progression": [
            {"time_offset_minutes": 0, "event": "incident_detected"},
            {"time_offset_minutes": 20, "event": "incident_resolved"},
        ],
    }
    unrealistic_scenario = {
        "incident_details": {
            "type": "not_real",
            "duration_minutes": 2000,
            "severity": "severe",
        },
        "affected_routes": [],
        "passenger_impact": {},
        "progression": [
            {"time_offset_minutes": 10, "event": "wrong_start"},
            {"time_offset_minutes": 5, "event": "wrong_end"},
        ],
    }

    assert scorer.score_coherence([]) == 0.0
    assert scorer.score_coherence(poor_dialogue) < 1.0
    assert scorer.score_realism(realistic_scenario) > scorer.score_realism(
        unrealistic_scenario
    )
    assert scorer.score_diversity([])["overall_diversity"] == 0.0
    assert (
        scorer.score_diversity([realistic_scenario, realistic_scenario])[
            "route_diversity"
        ]
        > 0.0
    )
    assert scorer.score_temporal_consistency(unrealistic_scenario) < 1.0
    assert scorer.overall_score() == 0.0
    assert scorer.overall_score(poor_dialogue, realistic_scenario) > 0.0

    batch = scorer.score_batch([realistic_scenario, unrealistic_scenario])
    assert batch["total_scenarios"] == 2
    assert "diversity" in batch
