from __future__ import annotations

from datetime import datetime, timezone

import pytest

import occlm
from occlm.analytics import (
    DashboardGenerator,
    IncidentAnalyzer,
    KPITracker,
    PerformanceAnalyzer,
    ServiceQualityAnalyzer,
)
from occlm.guardrails import (
    AuditTrail,
    ComplianceChecker,
    InputValidator,
    OutputFilter,
    PIIDetector,
    SafetyLevel,
)
from occlm.guardrails import (
    ValidationResult as SafetyValidationResult,
)
from occlm.ontology import (
    ACTION_TAXONOMY,
    INCIDENT_TAXONOMY,
    STANDARD_PROCEDURES,
    ActionType,
    IncidentType,
    OntologyManager,
    ProcedureLibrary,
    ResourceHierarchy,
    TaxonomyValidator,
)
from occlm.simulation import (
    DisruptionSimulator,
    NetworkAnalyzer,
    PassengerFlowSimulator,
    PerformanceForecaster,
    ScenarioTester,
    SimulationConfig,
    SimulationEngine,
    SimulationStatus,
    SimulationType,
    analyze_simulation_batch,
    create_disruption_scenario,
)


def test_package_lazy_imports_and_exports() -> None:
    assert occlm.__version__ == "0.1.0-alpha"
    assert "RealtimeEvent" in occlm.__all__

    synthesis_module = occlm.synthesis
    ingestion_module = occlm.ingestion

    assert hasattr(synthesis_module, "DialogueGenerator")
    assert hasattr(ingestion_module, "IngestionAdapter")

    with pytest.raises(AttributeError):
        _ = occlm.not_a_real_module


def test_analytics_module_placeholders() -> None:
    performance = PerformanceAnalyzer(operator="mta")
    incident_analyzer = IncidentAnalyzer()
    service_quality = ServiceQualityAnalyzer()
    tracker = KPITracker()
    dashboard = DashboardGenerator()

    otp = performance.analyze_on_time_performance(
        datetime(2026, 3, 1),
        datetime(2026, 3, 2),
    )
    assert otp == {"otp_percentage": 0.0, "avg_delay_minutes": 0.0}

    patterns = incident_analyzer.analyze_incident_patterns([{"type": "delay"}])
    assert patterns == {"patterns": [], "trends": []}

    assert service_quality.calculate_service_scores({"otp": 98.0}) == 0.0

    tracker.update_kpi("otp", 98.5)
    assert tracker.kpis == {"otp": 98.5}

    assert dashboard.generate_operational_dashboard() == {
        "charts": [],
        "metrics": {},
    }


def test_guardrails_module_placeholders() -> None:
    validator = InputValidator(safety_level=SafetyLevel.STRICT)
    output_filter = OutputFilter(safety_level=SafetyLevel.PERMISSIVE)
    pii_detector = PIIDetector()
    compliance = ComplianceChecker()
    audit_trail = AuditTrail()

    input_result = validator.validate_input("normal content")
    filtered_text, output_result = output_filter.filter_output("safe output")

    assert isinstance(input_result, SafetyValidationResult)
    assert input_result.is_safe is True
    assert filtered_text == "safe output"
    assert output_result.is_safe is True
    assert pii_detector.detect_pii("email test@example.com") == []
    assert "email" in pii_detector.pii_patterns
    assert compliance.check_compliance("policy text").is_safe is True

    audit_trail.log_action("filtered", {"reason": "unit test"})
    assert audit_trail.actions == []


def test_ontology_module_behaviour() -> None:
    manager = OntologyManager()
    validator = TaxonomyValidator(manager)
    procedures = ProcedureLibrary()

    signal_info = manager.get_incident_info(IncidentType.SIGNAL_FAILURE)

    assert INCIDENT_TAXONOMY[IncidentType.SIGNAL_FAILURE]["category"] == "technical"
    assert ACTION_TAXONOMY[ActionType.NOTIFY_PASSENGERS]["urgency"] == "immediate"
    assert signal_info["safety_impact"] == "medium"
    assert manager.get_recommended_actions(IncidentType.SIGNAL_FAILURE) == []
    assert validator.validate_taxonomy() == []
    assert (
        procedures.get_procedure(IncidentType.SIGNAL_FAILURE) == STANDARD_PROCEDURES[0]
    )
    assert procedures.get_procedure(IncidentType.UNKNOWN) is None

    hierarchy = ResourceHierarchy(
        resource_id="line_1",
        resource_type="line",
        parent_id=None,
        children=["station_a"],
        capabilities=["dispatch"],
    )
    assert hierarchy.children == ["station_a"]


def test_simulation_engine_and_helpers() -> None:
    engine = SimulationEngine()
    config = SimulationConfig(
        simulation_id="sim-001",
        simulation_type=SimulationType.DISRUPTION_IMPACT,
        start_time=datetime(2026, 3, 1, tzinfo=timezone.utc),
        duration_minutes=30,
        parameters={"incident": "signal_failure"},
        network_state={"routes": 2},
    )

    result = engine.run_simulation(config)

    assert result.simulation_id == "sim-001"
    assert result.status == SimulationStatus.COMPLETED
    assert engine.get_simulation_status("sim-001") == SimulationStatus.COMPLETED

    engine.active_simulations["running-1"] = config
    assert engine.get_simulation_status("running-1") == SimulationStatus.RUNNING
    assert engine.get_simulation_status("missing") is None

    disruption = DisruptionSimulator(engine).simulate_signal_failure(
        location="station_a",
        duration_minutes=10,
        affected_lines=["1"],
    )
    power = DisruptionSimulator(engine).simulate_power_outage(
        affected_stations=["station_a"],
        duration_minutes=20,
    )
    rush = PassengerFlowSimulator(engine).simulate_rush_hour()
    capacity = NetworkAnalyzer(engine).analyze_capacity(["1", "2"])
    recovery = ScenarioTester(engine).test_recovery_procedure(
        "signal_failure",
        ["short_turn"],
    )
    forecast = PerformanceForecaster(engine).forecast_performance(
        forecast_horizon_days=2,
        scenarios=[{"type": "delay"}],
    )

    for simulation_result in [disruption, power, rush, capacity, recovery, forecast]:
        assert simulation_result.status == SimulationStatus.COMPLETED

    generated = create_disruption_scenario(
        "signal_failure",
        "station_a",
        15,
        affected_lines=["1"],
    )
    assert generated.simulation_type == SimulationType.DISRUPTION_IMPACT
    assert generated.parameters["affected_lines"] == ["1"]

    empty_batch = analyze_simulation_batch([])
    assert empty_batch == {"message": "No simulation results to analyze"}

    analyzed = analyze_simulation_batch([result, disruption, power])
    assert analyzed["total_simulations"] == 3
    assert analyzed["successful_simulations"] == 3
    assert analyzed["aggregated_metrics"]["delay_minutes"]["count"] == 3
