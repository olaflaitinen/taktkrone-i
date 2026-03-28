"""
Quality scoring for synthetic data evaluation.

Provides metrics for evaluating coherence, realism, diversity, and
temporal consistency of synthetic dialogue and scenarios.
"""

import statistics
from typing import Any

__all__ = [
    "QualityScorer",
]


class QualityScorer:
    """
    Scores quality of synthetic dialogue and scenarios.

    Evaluates coherence, realism, diversity, and temporal consistency
    using heuristic and keyword-based scoring methods.
    """

    def __init__(self) -> None:
        """Initialize quality scorer."""
        self.min_message_length = 5
        self.max_message_length = 500

    def score_coherence(
        self,
        dialogue: list[dict[str, Any]],
    ) -> float:
        """
        Score coherence of dialogue.

        Evaluates message ordering, logical flow, and turn-taking
        consistency.

        Args:
            dialogue: List of dialogue message dicts

        Returns:
            Coherence score (0.0-1.0)
        """
        if not dialogue or len(dialogue) < 2:
            return 0.0

        score = 1.0
        penalties = 0.0

        # Check for proper speaker alternation
        speakers = [m.get("speaker") for m in dialogue]
        for i in range(len(speakers) - 1):
            if speakers[i] == speakers[i + 1]:
                penalties += 0.1  # Same speaker twice

        # Check for reasonable message length
        lengths = [len(m.get("content", "")) for m in dialogue]
        if lengths:
            avg_length = statistics.mean(lengths)
            if avg_length < self.min_message_length:
                penalties += 0.2
            if avg_length > self.max_message_length:
                penalties += 0.15

        # Check for action-message consistency
        action_keywords = {
            "incident_detection": ["detected", "incident", "emergency"],
            "hold_decision": ["hold", "stop", "suspend"],
            "service_resume": ["resume", "proceed", "clear"],
            "communication": ["notify", "announce", "inform"],
        }

        for message in dialogue:
            content = message.get("content", "").lower()
            actions = message.get("actions", [])

            if not actions:
                penalties += 0.05

            # Check if message content matches actions
            action_found = False
            for action in actions:
                keywords = action_keywords.get(action, [])
                if any(kw in content for kw in keywords):
                    action_found = True
                    break

            if not action_found and actions:
                penalties += 0.05

        # Penalize extreme dialogue lengths
        if len(dialogue) < 3:
            penalties += 0.15
        if len(dialogue) > 20:
            penalties += 0.1

        score = max(0.0, score - penalties)
        return round(score, 3)

    def score_realism(
        self,
        scenario: dict[str, Any],
    ) -> float:
        """
        Score realism of scenario.

        Evaluates timing plausibility, known operator protocols,
        and realistic constraints.

        Args:
            scenario: Scenario dict with incident_details, timing, etc.

        Returns:
            Realism score (0.0-1.0)
        """
        score = 1.0
        penalties = 0.0

        # Check incident type validity
        valid_types = {
            "signal_failure",
            "medical_emergency",
            "mechanical_failure",
            "track_maintenance",
            "power_outage",
            "passenger_incident",
            "weather_related",
            "crowding",
            "equipment_failure",
            "staff_shortage",
            "security_incident",
            "system_error",
            "schedule_adjustment",
            "special_event",
            "infrastructure_damage",
        }

        incident_type = scenario.get("incident_details", {}).get("type")
        if incident_type not in valid_types:
            penalties += 0.3

        # Check duration plausibility
        duration = scenario.get("incident_details", {}).get("duration_minutes")
        if duration:
            if duration < 1 or duration > 1440:  # 1 day max
                penalties += 0.2

            # Type-specific duration checks
            if incident_type == "medical_emergency" and duration > 60:
                penalties += 0.1
            elif incident_type == "signal_failure" and duration > 240:
                penalties += 0.05

        # Check severity validity
        severity = scenario.get("incident_details", {}).get("severity")
        if severity not in {"low", "medium", "high", "critical"}:
            penalties += 0.2

        # Check affected routes exist
        affected_routes = scenario.get("affected_routes", [])
        if not affected_routes:
            penalties += 0.15

        # Check passenger impact estimation
        passenger_impact = scenario.get("passenger_impact", {})
        if not passenger_impact:
            penalties += 0.1
        else:
            # Impact should be proportional to severity
            service_reduction = passenger_impact.get("service_level_reduction", 0)
            if severity == "low" and service_reduction > 0.3:
                penalties += 0.1
            elif severity == "high" and service_reduction < 0.4:
                penalties += 0.1

        # Check progression timeline
        progression = scenario.get("progression", [])
        if progression:
            for event in progression:
                offset = event.get("time_offset_minutes", 0)
                if offset < 0 or offset > duration:
                    penalties += 0.05

        score = max(0.0, score - penalties)
        return round(score, 3)

    def score_diversity(
        self,
        scenarios: list[dict[str, Any]],
    ) -> dict[str, float]:
        """
        Score diversity of scenario collection.

        Evaluates coverage of incident types, locations, severities,
        and scenario types.

        Args:
            scenarios: List of scenario dicts

        Returns:
            Dict with diversity metrics
        """
        if not scenarios:
            return {
                "incident_type_diversity": 0.0,
                "severity_diversity": 0.0,
                "scenario_type_diversity": 0.0,
                "overall_diversity": 0.0,
            }

        # Count unique incident types
        incident_types = {s.get("incident_details", {}).get("type") for s in scenarios}
        incident_diversity = len(incident_types) / 15  # 15 possible types
        incident_diversity = min(1.0, incident_diversity)

        # Count unique severities
        severities = {s.get("incident_details", {}).get("severity") for s in scenarios}
        severity_diversity = len(severities) / 4  # 4 levels

        # Count unique scenario types
        scenario_types = {s.get("scenario_type") for s in scenarios}
        scenario_diversity = len(scenario_types) / 5  # 5 types
        scenario_diversity = min(1.0, scenario_diversity)

        # Affected routes diversity
        all_routes = set()
        for s in scenarios:
            all_routes.update(s.get("affected_routes", []))

        route_diversity = len(all_routes) / 10  # 10 possible routes
        route_diversity = min(1.0, route_diversity)

        overall = (
            incident_diversity
            + severity_diversity
            + scenario_diversity
            + route_diversity
        ) / 4

        return {
            "incident_type_diversity": round(incident_diversity, 3),
            "severity_diversity": round(severity_diversity, 3),
            "scenario_type_diversity": round(scenario_diversity, 3),
            "route_diversity": round(route_diversity, 3),
            "overall_diversity": round(overall, 3),
        }

    def score_temporal_consistency(
        self,
        scenario: dict[str, Any],
    ) -> float:
        """
        Score temporal consistency of scenario.

        Checks that timestamps are reasonable and progression timeline
        is logically ordered.

        Args:
            scenario: Scenario dict with timestamps and progression

        Returns:
            Temporal consistency score (0.0-1.0)
        """
        score = 1.0
        penalties = 0.0

        # Check initial timestamp exists and is valid
        timestamp = scenario.get("timestamp")
        if not timestamp:
            penalties += 0.3

        # Check progression timeline
        progression = scenario.get("progression", [])
        if not progression:
            penalties += 0.2
        else:
            offsets = [e.get("time_offset_minutes", 0) for e in progression]

            # Check ordering
            for i in range(len(offsets) - 1):
                if offsets[i] > offsets[i + 1]:
                    penalties += 0.2
                    break

            # Check duration consistency
            duration = scenario.get("incident_details", {}).get("duration_minutes")
            if duration and offsets:
                max_offset = max(offsets)
                if max_offset != duration:
                    # Final event should be at duration
                    if max_offset < duration * 0.9:
                        penalties += 0.1
                    else:
                        penalties += 0.05

        # Check initial and resolution events
        if progression:
            first_event = progression[0].get("event")
            last_event = progression[-1].get("event")

            if first_event != "incident_detected":
                penalties += 0.1
            if last_event != "incident_resolved":
                penalties += 0.1

        score = max(0.0, score - penalties)
        return round(score, 3)

    def overall_score(
        self,
        dialogue: list[dict[str, Any]] | None = None,
        scenario: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate overall quality score.

        Combines dialogue coherence and scenario realism.

        Args:
            dialogue: Optional dialogue to score
            scenario: Optional scenario to score

        Returns:
            Overall quality score (0.0-1.0)
        """
        scores = []

        if dialogue is not None:
            scores.append(self.score_coherence(dialogue))

        if scenario is not None:
            scores.append(self.score_realism(scenario))
            scores.append(self.score_temporal_consistency(scenario))

        if not scores:
            return 0.0

        return round(statistics.mean(scores), 3)

    def score_batch(
        self,
        scenarios: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Score a batch of scenarios.

        Evaluates all scenarios and returns aggregated statistics.

        Args:
            scenarios: List of scenario dicts

        Returns:
            Batch scoring results
        """
        realism_scores = [self.score_realism(s) for s in scenarios]
        temporal_scores = [self.score_temporal_consistency(s) for s in scenarios]
        diversity = self.score_diversity(scenarios)

        return {
            "total_scenarios": len(scenarios),
            "avg_realism": round(statistics.mean(realism_scores), 3)
            if realism_scores
            else 0.0,
            "min_realism": round(min(realism_scores), 3) if realism_scores else 0.0,
            "max_realism": round(max(realism_scores), 3) if realism_scores else 0.0,
            "avg_temporal_consistency": round(statistics.mean(temporal_scores), 3)
            if temporal_scores
            else 0.0,
            "diversity": diversity,
        }
