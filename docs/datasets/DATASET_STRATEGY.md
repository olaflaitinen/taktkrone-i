# TAKTKRONE-I Dataset Strategy

**Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Design Specification

---

## Executive Summary

This document defines the complete dataset strategy for TAKTKRONE-I, the metro Operations Control Center language model. The strategy establishes five supervision layers, defines dataset families for each operational task, specifies synthetic generation methods, and establishes quality governance for training data.

**Core Principle:** The dataset must reflect how a real metro OCC thinks, writes, escalates, and evaluates options. It must not resemble a generic transportation QA dataset.

---

## 1. Dataset Architecture Overview

### 1.1 Five Supervision Layers

```
Layer 5: Evaluation Gold Sets
    |
Layer 4: Instruction Tuning Samples
    |
Layer 3: Synthetic OCC Reasoning Traces
    |
Layer 2: Event Normalization
    |
Layer 1: Public Transit State Data
```

### 1.2 Data Flow

```
Public APIs --> Ingestion --> Normalization --> Synthesis --> Instruction --> Evaluation
     |              |              |               |             |              |
   GTFS-RT      Adapters      Canonical       Scenario      Training       Benchmark
   Alerts       Parsers       Schemas         Engine        Format         Suites
```

### 1.3 Storage Organization

```
data/
  raw/
    {operator}/
      gtfs_static/
      gtfs_rt/
      alerts/
      incidents/
  normalized/
    {operator}/
      realtime_events/
      network_snapshots/
      incidents/
  synthetic/
    scenarios/
    dialogues/
    reasoning_traces/
  training/
    instruction_tuning/
    retrieval_corpus/
  evaluation/
    benchmarks/
    gold_sets/
    adversarial/
```

---

## 2. Layer 1: Public Transit State Data

### 2.1 Static Network Data (GTFS)

**Sources:**
- MTA GTFS Static
- MBTA GTFS
- WMATA GTFS
- BART GTFS
- TfL Reference Data

**Entities:**
| Entity | Description | Update Frequency |
|--------|-------------|------------------|
| `stops.txt` | Station and platform locations | Monthly |
| `routes.txt` | Line definitions | Monthly |
| `trips.txt` | Scheduled trip patterns | Weekly |
| `stop_times.txt` | Scheduled arrival/departure | Weekly |
| `shapes.txt` | Geographic route alignment | Monthly |
| `transfers.txt` | Transfer connections | Monthly |
| `pathways.txt` | In-station navigation | Quarterly |

**Usage in Dataset:**
- Network topology validation
- Station relationship inference
- Terminal and crossover identification
- Service pattern derivation

### 2.2 Realtime Operational Data (GTFS-RT)

**Feed Types:**
| Feed | Content | Polling Interval |
|------|---------|------------------|
| TripUpdate | Arrival/departure predictions, delays | 15 seconds |
| VehiclePosition | Train locations, bearing, speed | 15 seconds |
| ServiceAlert | Disruption notifications | 30 seconds |

**Derived Features:**
- Current headways per line segment
- Delay propagation patterns
- Bunching detection
- Gap detection
- Dwell time anomalies

### 2.3 Supplementary State Data

**Where Available:**
- Elevator/escalator status
- Platform crowding estimates
- Line status summaries
- Planned work schedules
- Weather conditions

---

## 3. Layer 2: Event Normalization

### 3.1 Disruption Event Taxonomy

Every realtime event and alert is normalized to a canonical disruption taxonomy:

**Primary Incident Categories:**

| Code | Category | Description |
|------|----------|-------------|
| `SIG` | Signalling Degradation | Signal failures, interlocking issues |
| `THS` | Train Held in Station | Extended dwell, door issues, passenger issues |
| `TDS` | Train Disabled in Service | Vehicle breakdown, mechanical failure |
| `TCG` | Terminal Congestion | Backup at terminal, insufficient turnback capacity |
| `CXU` | Crossover Unavailable | Switch failure, track work blocking crossover |
| `SOC` | Station Overcrowding | Platform capacity issues, crowd control |
| `PLT` | Platform Incident | Object on track, person on trackway |
| `PME` | Police/Medical Event | Police activity, medical emergency |
| `PWR` | Power Restriction | Third rail issues, power supply problems |
| `WTH` | Weather Effect | Flooding, heat restrictions, ice |
| `PWO` | Planned Work Overlap | Scheduled maintenance causing conflict |
| `RSS` | Rolling Stock Shortage | Insufficient trains for service |
| `TUP` | Turnback Path Unavailable | Cannot complete scheduled turnaround |
| `CRW` | Crew Dependency | Operator unavailability (if tracked) |
| `RPL` | Network Ripple Delay | Cascaded delay from upstream |
| `PSS` | Partial Suspension | Segment of line out of service |
| `BAS` | Baseline/No Issue | Normal operations reference |

### 3.2 Event Normalization Schema

```json
{
  "event_id": "evt_20260327_001",
  "timestamp_utc": "2026-03-27T17:30:00Z",
  "operator": "mta_nyct",
  "incident_type": "SIG",
  "severity": "high",
  "status": "active",
  "affected_lines": ["1"],
  "affected_stations": ["96th St", "86th St"],
  "affected_direction": "southbound",
  "description_raw": "Signal problems at 96 St causing delays",
  "description_normalized": "Signal failure at 96th St affecting southbound Line 1 service",
  "estimated_duration_minutes": 30,
  "passenger_impact": "high",
  "source": "gtfs_rt_service_alert",
  "provenance": {
    "ingestion_time": "2026-03-27T17:30:15Z",
    "raw_alert_id": "MTA_ALERT_12345"
  }
}
```

### 3.3 Normalization Rules

1. **Temporal Alignment:** All timestamps converted to UTC
2. **Entity Resolution:** Station names mapped to canonical IDs
3. **Severity Inference:** When not provided, infer from delay magnitude and scope
4. **Duration Estimation:** Default estimates based on incident type
5. **Impact Assessment:** Passenger impact derived from time of day and affected stations

---

## 4. Layer 3: Synthetic OCC Reasoning Traces

### 4.1 Reasoning Trace Structure

Each synthetic OCC reasoning trace captures the full decision-making process:

```
Incident Briefing
    |
    v
Operational Hypotheses
    |
    v
Action Candidates
    |
    v
Selected Intervention
    |
    v
Justification
    |
    v
Expected KPI Change
    |
    v
Risks and Alternatives
    |
    v
Escalation Recommendation
```

### 4.2 Reasoning Trace Schema

```json
{
  "trace_id": "trace_20260327_001",
  "timestamp_utc": "2026-03-27T17:30:00Z",
  "operator": "mta_nyct",
  "scenario_type": "headway_bunching",

  "incident_briefing": {
    "summary": "Three southbound Line 1 trains bunched between 96th St and 72nd St",
    "observed_state": {
      "headway_leading": 180,
      "headway_trailing_1": 90,
      "headway_trailing_2": 120,
      "scheduled_headway": 360
    },
    "trigger_time": "2026-03-27T17:25:00Z",
    "telemetry_completeness": "full"
  },

  "operational_hypotheses": [
    {
      "hypothesis_id": "hyp_01",
      "description": "Signal delay at 96th St caused initial gap compression",
      "confidence": 0.75,
      "supporting_evidence": ["Delays consistently originating at 96th St"],
      "contradicting_evidence": []
    },
    {
      "hypothesis_id": "hyp_02",
      "description": "Extended dwell at 96th St due to crowding",
      "confidence": 0.20,
      "supporting_evidence": ["Evening peak period"],
      "contradicting_evidence": ["No dwell anomaly alerts"]
    }
  ],

  "action_candidates": [
    {
      "action_id": "act_01",
      "action_type": "hold_train",
      "description": "Hold leading train at 42nd St for 4 minutes",
      "feasibility": "high",
      "expected_benefit": "Restore 5-minute headways within 20 minutes",
      "expected_cost": "Platform crowding at 42nd St during hold",
      "constraints_satisfied": true
    },
    {
      "action_id": "act_02",
      "action_type": "express_operation",
      "description": "Run trailing train express from 72nd St to 42nd St",
      "feasibility": "medium",
      "expected_benefit": "Faster gap closure",
      "expected_cost": "Skipped stops, passenger inconvenience",
      "constraints_satisfied": true
    },
    {
      "action_id": "act_03",
      "action_type": "short_turn",
      "description": "Short turn middle train at Chambers St",
      "feasibility": "low",
      "expected_benefit": "Reduce southbound bunching",
      "expected_cost": "Service gap in downtown section",
      "constraints_satisfied": false,
      "constraint_violation": "Crossover at Chambers under maintenance"
    }
  ],

  "selected_intervention": {
    "primary_action": "act_01",
    "secondary_action": null,
    "selection_rationale": "Holding action is least disruptive and high confidence of success given headway spacing"
  },

  "justification": {
    "text": "Recommending 4-minute hold at 42nd St for the leading train. This creates separation from the trailing bunch while positioned at a high-capacity station that can absorb temporary crowding. The trailing trains will naturally spread during the hold period. Signal status at 96th St should be verified with maintainer to prevent recurrence.",
    "key_factors": [
      "Leading train position allows hold without exacerbating bunch",
      "42nd St has high platform capacity",
      "Expected restoration within 20 minutes"
    ]
  },

  "expected_kpi_change": {
    "headway_variance_reduction": 0.6,
    "time_to_normal_operations_minutes": 20,
    "passenger_delay_minutes_total": 450,
    "confidence": 0.82
  },

  "risks_and_alternatives": {
    "primary_risks": [
      "Platform crowding exceeds comfort threshold",
      "Signal issue recurs after restoration"
    ],
    "fallback_action": "If hold exceeds 6 minutes, switch to short turn at 14th St",
    "alternatives_rejected": [
      {
        "action": "Express operation",
        "rejection_reason": "Skipped stops create downstream crowding"
      }
    ]
  },

  "escalation_recommendation": {
    "escalate": false,
    "escalation_level": null,
    "escalation_reason": null,
    "human_review_recommended": true,
    "review_reason": "Standard headway intervention, recommend verification of signal status"
  },

  "metadata": {
    "generation_method": "rule_based_scenario_engine",
    "template_id": "bunching_hold_intervention",
    "difficulty": "medium",
    "topology_validated": true,
    "quality_score": 0.91
  }
}
```

### 4.3 Reasoning Trace Generation

**Generation Methods:**

1. **Rule-Based Templates:** Parameterized scenario templates with controlled randomization
2. **Delay Propagation Simulation:** Physics-based delay cascade modeling
3. **Multi-Train Interaction:** Agent-based train movement simulation
4. **Perturbation Injection:** Realistic noise and uncertainty addition

---

## 5. Layer 4: Instruction Tuning Samples

### 5.1 Sample Structure

```json
{
  "sample_id": "sample_20260327_001",
  "source_type": "synthetic",
  "source_operator": "mta_nyct",
  "timestamp_utc": "2026-03-27T17:30:00Z",
  "task_type": "headway_regulation",
  "incident_type": "bunching",

  "messages": [
    {
      "role": "system",
      "content": "You are an expert metro OCC analyst providing decision support..."
    },
    {
      "role": "user",
      "content": "Line 1 southbound trains are bunching between 96th St and 72nd St. Three trains are within 4 minutes of each other instead of the scheduled 6-minute headway. What should we do?"
    },
    {
      "role": "assistant",
      "content": "Analysis:\n\nThree southbound Line 1 trains are bunched..."
    }
  ],

  "network_state_summary": {
    "lines_affected": ["1"],
    "severity": "medium",
    "time_of_day": "evening_peak"
  },

  "raw_input_payload": {
    "trip_updates": [...],
    "current_positions": [...]
  },

  "retrieval_context": [
    {
      "document_id": "proc_headway_regulation_v2",
      "title": "Headway Regulation Procedures",
      "snippet": "For bunching scenarios, holding the leading train..."
    }
  ],

  "expected_output_text": "Analysis:\n\nThree southbound Line 1 trains...",

  "expected_output_structured": {
    "diagnosis": "signal_delay_induced_bunching",
    "recommended_action": "hold_leading_train",
    "confidence": 0.82,
    "safety_notes": ["Monitor platform crowding"]
  },

  "confidence_label": "high",
  "safety_review_flag": false,
  "split": "train",

  "provenance": {
    "reasoning_trace_id": "trace_20260327_001",
    "generation_timestamp": "2026-03-27T10:00:00Z",
    "generator_version": "1.0.0"
  },

  "synthetic_generation_method": "rule_based_scenario_engine",
  "validator_status": "passed"
}
```

### 5.2 Task Types

| Task Code | Task Name | Description |
|-----------|-----------|-------------|
| `SUM` | Incident Summarization | Summarize network state and incidents |
| `DRH` | Delay Root-Cause Hypothesis | Generate hypotheses for delay causes |
| `HCS` | Headway Control Suggestion | Recommend headway regulation actions |
| `DAE` | Dwell Anomaly Explanation | Explain unusual dwell times |
| `TFR` | Turnback Feasibility Reasoning | Assess terminal turnback options |
| `DCR` | Dispatch Conflict Resolution | Resolve competing operational demands |
| `LRS` | Line Recovery Strategy | Plan service recovery |
| `SEX` | Structured Extraction | Extract structured data from text |
| `CAC` | Counterfactual Action Comparison | Compare alternative actions |
| `AAR` | After-Action Review | Generate post-incident analysis |
| `CRP` | Confidence Reporting | Quantify uncertainty |
| `SRF` | Safe Refusal | Refuse when appropriate |

### 5.3 Special Sample Types

**Refusal Cases:**
- Insufficient telemetry to make recommendation
- Request for safety-critical direct command
- Out-of-scope request (non-transit)
- Request requiring unavailable authority

**Uncertainty Cases:**
- Incomplete vehicle position data
- Conflicting information sources
- Ambiguous incident descriptions
- Novel scenario types

---

## 6. Layer 5: Evaluation Gold Sets

### 6.1 Benchmark Categories

| Category | Description | Metrics |
|----------|-------------|---------|
| Extraction | Structured data extraction from text | F1, Exact Match |
| Reasoning | Operational reasoning quality | Accuracy, Plausibility |
| Recommendation | Action recommendation quality | nDCG, MRR |
| Calibration | Confidence calibration | ECE, Brier Score |
| Safety | Unsafe command rejection | FAR, Compliance |
| Robustness | Performance under perturbation | Consistency |
| Retrieval | RAG quality | Hit Rate, Relevance |
| Explanation | Explanation quality | Human Eval |

### 6.2 Gold Set Requirements

**Per Benchmark:**
- Minimum 500 samples
- Human-validated labels
- Adversarial variants included
- Edge cases represented
- Topology-validated

**Split Strategy:**
- No operator overlap between train and test
- No scenario template overlap between train and test
- Temporal stratification within operator

---

## 7. Dataset Families

### 7.1 Family A: State to Summary

**Task Definition:**
Transform network state data into human-readable OCC situation summary.

**Input Schema:**
```json
{
  "network_snapshot": {...},
  "active_alerts": [...],
  "recent_events": [...],
  "time_window_minutes": 30
}
```

**Target Schema:**
```json
{
  "summary_text": "string",
  "key_issues": ["string"],
  "severity_assessment": "low|medium|high|critical",
  "lines_affected": ["string"],
  "recommended_focus": "string"
}
```

**Label Generation:**
- Template-based summary generation
- Controlled paraphrase expansion
- Human review for gold set

**Failure Modes:**
- Missing critical alerts
- Incorrect severity assessment
- Topology errors in descriptions
- Stale information presented as current

**Evaluation Method:**
- ROUGE against reference summaries
- Factuality verification against source data
- Human evaluation of completeness

### 7.2 Family B: State to Action Recommendation

**Task Definition:**
Given network state and incident context, recommend operational interventions.

**Input Schema:**
```json
{
  "incident_context": {...},
  "network_state": {...},
  "constraints": {...},
  "available_actions": [...]
}
```

**Target Schema:**
```json
{
  "recommendations": [
    {
      "action_type": "string",
      "priority": 1,
      "rationale": "string",
      "confidence": 0.85,
      "risks": ["string"]
    }
  ],
  "uncertainties": [...],
  "safety_notes": [...]
}
```

**Label Generation:**
- Rule-based optimal action derivation
- Simulation-based outcome verification
- Expert review for complex scenarios

**Failure Modes:**
- Recommending infeasible actions
- Missing constraint violations
- Overconfident recommendations
- Missing safety considerations

**Evaluation Method:**
- Action ranking metrics (nDCG, MRR)
- Constraint satisfaction rate
- Safety compliance score

### 7.3 Family C: Advisory Text to Structured Event

**Task Definition:**
Extract structured incident information from free-text advisories.

**Input Schema:**
```json
{
  "advisory_text": "string",
  "source": "string",
  "timestamp": "datetime"
}
```

**Target Schema:**
```json
{
  "incident_type": "string",
  "affected_lines": ["string"],
  "affected_stations": ["string"],
  "direction": "string",
  "severity": "string",
  "estimated_duration": "string",
  "cause": "string"
}
```

**Label Generation:**
- Regex and NER extraction
- Human annotation
- Cross-validation with structured alerts

**Failure Modes:**
- Missing entities
- Incorrect entity association
- Hallucinated information
- Parsing ambiguity errors

**Evaluation Method:**
- Entity-level F1
- Relation extraction accuracy
- Schema validity rate

### 7.4 Family D: Incident Timeline to After-Action Review

**Task Definition:**
Generate structured after-action review from incident timeline.

**Input Schema:**
```json
{
  "incident_timeline": [...],
  "actions_taken": [...],
  "outcomes": {...},
  "kpis": {...}
}
```

**Target Schema:**
```json
{
  "executive_summary": "string",
  "incident_chronology": [...],
  "response_assessment": {...},
  "lessons_learned": [...],
  "recommendations": [...]
}
```

**Label Generation:**
- Template-based review generation
- Controlled narrative construction
- Expert review validation

**Failure Modes:**
- Chronology errors
- Incorrect causality attribution
- Missing key events
- Inconsistent with outcome data

**Evaluation Method:**
- Temporal consistency checks
- Factual accuracy verification
- Human evaluation of quality

### 7.5 Family E: Incomplete Telemetry to Uncertainty-Aware Response

**Task Definition:**
Respond appropriately when telemetry is incomplete or unreliable.

**Input Schema:**
```json
{
  "query": "string",
  "available_data": {...},
  "missing_data": ["string"],
  "data_quality_flags": {...}
}
```

**Target Schema:**
```json
{
  "response": "string",
  "confidence": 0.4,
  "data_limitations": ["string"],
  "additional_data_needed": ["string"],
  "conditional_recommendations": [...]
}
```

**Label Generation:**
- Systematic data masking
- Uncertainty propagation modeling
- Expert annotation of appropriate responses

**Failure Modes:**
- Overconfident with limited data
- Fabricating missing information
- Not acknowledging uncertainty
- Not requesting additional data

**Evaluation Method:**
- Calibration metrics
- Appropriate abstention rate
- Human evaluation of uncertainty communication

### 7.6 Family F: Unsafe Request to Refusal

**Task Definition:**
Appropriately refuse unsafe, unauthorized, or out-of-scope requests.

**Input Schema:**
```json
{
  "request": "string",
  "request_type": "string",
  "context": {...}
}
```

**Target Schema:**
```json
{
  "action": "refuse",
  "refusal_reason": "string",
  "safe_alternative": "string",
  "escalation_path": "string"
}
```

**Label Generation:**
- Adversarial request generation
- Policy-based refusal rules
- Safety team review

**Failure Modes:**
- Failing to refuse unsafe requests
- Over-refusing benign requests
- Unclear refusal reasoning
- No alternative suggested

**Evaluation Method:**
- False acceptance rate
- False rejection rate
- Refusal appropriateness score

### 7.7 Family G: Counterfactual Action Ranking

**Task Definition:**
Rank alternative actions and explain tradeoffs.

**Input Schema:**
```json
{
  "scenario": {...},
  "candidate_actions": [...],
  "evaluation_criteria": [...]
}
```

**Target Schema:**
```json
{
  "ranked_actions": [...],
  "pairwise_comparisons": [...],
  "tradeoff_analysis": {...},
  "recommended_action": "string"
}
```

**Label Generation:**
- Simulation-based outcome evaluation
- Multi-criteria ranking
- Expert preference annotation

**Failure Modes:**
- Incorrect ranking
- Missing tradeoff considerations
- Inconsistent pairwise comparisons
- Constraint violations in ranking

**Evaluation Method:**
- Ranking correlation metrics
- Consistency checks
- Human preference alignment

### 7.8 Family H: Retrieval-Grounded Explanation

**Task Definition:**
Generate explanation grounded in retrieved operational knowledge.

**Input Schema:**
```json
{
  "query": "string",
  "retrieved_documents": [...],
  "context": {...}
}
```

**Target Schema:**
```json
{
  "explanation": "string",
  "citations": [...],
  "confidence": 0.9,
  "grounding_assessment": "fully_grounded|partially_grounded|ungrounded"
}
```

**Label Generation:**
- Citation verification
- Grounding classification
- Expert quality annotation

**Failure Modes:**
- Incorrect citations
- Hallucinated information
- Ignoring retrieved context
- Over-reliance on retrieval

**Evaluation Method:**
- Citation accuracy
- Grounding rate
- Human evaluation of explanation quality

---

## 8. Synthetic Generation Methods

### 8.1 Rule-Based Scenario Templates

**Approach:**
Parameterized templates capturing common OCC scenarios with controlled randomization.

**Template Structure:**
```python
class ScenarioTemplate:
    name: str
    incident_type: str
    parameters: Dict[str, ParameterSpec]
    topology_constraints: List[Constraint]
    narrative_template: str
    action_options: List[ActionTemplate]
    outcome_model: OutcomeModel
```

**Template Library:**
- `bunching_single_line` - Train bunching on single line
- `bunching_junction` - Bunching at junction point
- `terminal_congestion` - Terminal capacity issues
- `signal_failure_segment` - Signal failure on track segment
- `disabled_train_mainline` - Train breakdown on mainline
- `disabled_train_terminal` - Train breakdown at terminal
- `crossover_unavailable` - Crossover blocked
- `planned_work_conflict` - Scheduled work causing issues
- `weather_speed_restriction` - Weather-related restrictions
- `partial_suspension` - Segment out of service
- `station_overcrowding` - Platform capacity issues
- `multi_incident_compound` - Multiple concurrent incidents

### 8.2 Delay Propagation Simulation

**Approach:**
Physics-based simulation of delay cascading through network.

**Model Components:**
- Train dynamics (acceleration, braking, dwell)
- Block signaling constraints
- Headway maintenance logic
- Recovery buffer consumption
- Passenger loading effects

**Parameters:**
- Initial delay magnitude
- Delay location
- Time of day (demand profile)
- Recovery strategy

### 8.3 Terminal Turnback Constraint Simulation

**Approach:**
Model terminal capacity and turnback feasibility.

**Constraints Modeled:**
- Platform track availability
- Crossover capacity
- Minimum turnback time
- Crew change requirements
- Layover requirements

### 8.4 Multi-Train Interaction Simulation

**Approach:**
Agent-based simulation of train interactions.

**Agents:**
- Individual trains with state and goals
- Dispatcher with global view
- Passengers (aggregate demand)

**Interactions:**
- Headway enforcement
- Holding decisions
- Short turn coordination
- Express operation conflicts

### 8.5 Perturbed Advisory Rewriting

**Approach:**
Generate paraphrases of service advisories preserving operational meaning.

**Perturbation Types:**
- Lexical substitution (synonyms)
- Syntactic restructuring
- Detail level variation
- Formality adjustment

**Quality Assurance:**
- Semantic similarity threshold
- Entity preservation check
- Operational meaning verification

### 8.6 Controlled Paraphrase Generation

**Approach:**
Generate diverse phrasings of operational content.

**Controls:**
- Target vocabulary level
- Length constraints
- Technical terminology density
- Formality register

### 8.7 Counterfactual Action Branching

**Approach:**
Generate alternative action trajectories from decision points.

**Process:**
1. Identify decision points in scenario
2. Enumerate feasible alternatives
3. Simulate outcomes for each branch
4. Generate comparative analysis

### 8.8 Negative Sample Generation

**Approach:**
Generate incorrect outputs for contrastive learning.

**Negative Types:**
- Topology violations
- Temporal inconsistencies
- Constraint violations
- Hallucinated data
- Unsafe recommendations
- Overconfident responses

### 8.9 Missing Telemetry Simulation

**Approach:**
Systematically mask data to test uncertainty handling.

**Masking Patterns:**
- Single data source outage
- Regional coverage gap
- Stale data (time lag)
- Conflicting values
- Low confidence readings

### 8.10 Contradictory Evidence Simulation

**Approach:**
Generate scenarios with conflicting information.

**Contradiction Types:**
- Alert vs. realtime data mismatch
- Multiple conflicting alerts
- Historical pattern violation
- Sensor disagreement

---

## 9. Data Quality Requirements

### 9.1 Topology Validation

**Requirement:** No synthetic sample should contradict topology constraints.

**Checks:**
- Station existence on specified line
- Correct station ordering
- Valid terminal identification
- Crossover location accuracy
- Transfer connection validity

### 9.2 Operational Plausibility

**Requirement:** All train movement assumptions must remain operationally plausible.

**Checks:**
- Realistic travel times
- Feasible acceleration/braking
- Valid headway values
- Achievable dwell times
- Plausible delay magnitudes

### 9.3 Observation vs. Inference Distinction

**Requirement:** Every recommendation must distinguish observed data from inferred interpretation.

**Checks:**
- Clear labeling of data sources
- Explicit inference markers
- Confidence attribution
- Evidence citation

### 9.4 Abstention Support

**Requirement:** Low-information cases must explicitly support abstention.

**Checks:**
- Abstention triggers present
- Request-for-context options
- Uncertainty acknowledgment
- Data limitation disclosure

### 9.5 Severity Distribution

**Requirement:** Scenarios should span both minor disturbances and network-wide disruption.

**Target Distribution:**
| Severity | Percentage |
|----------|------------|
| Minor | 40% |
| Moderate | 35% |
| Major | 20% |
| Critical | 5% |

### 9.6 Class Balance

**Requirement:** Monitor and maintain class balance across key dimensions.

**Monitored Dimensions:**
- Task type
- Incident type
- Operator
- Severity
- Time of day
- Action type recommended

### 9.7 Diversity Metrics

**Requirement:** Synthetic diversity should be measured and maintained.

**Metrics:**
- Unique scenario count
- Parameter value coverage
- Narrative diversity (embedding space)
- Action recommendation diversity

---

## 10. Train/Validation/Test Split Strategy

### 10.1 Split Ratios

| Split | Percentage | Purpose |
|-------|------------|---------|
| Train | 80% | Model training |
| Validation | 10% | Hyperparameter tuning |
| Test | 10% | Final evaluation |

### 10.2 Split Constraints

**Operator Stratification:**
- Each operator present in all splits
- Test set has held-out operators for generalization testing

**Scenario Template Separation:**
- Some templates held out entirely for test
- Prevents template memorization

**Temporal Stratification:**
- Within-operator temporal diversity
- Recent scenarios in test set

**Difficulty Stratification:**
- Difficulty levels balanced across splits
- Expert-level scenarios in all splits

### 10.3 Data Leakage Prevention

**Prohibited Overlaps:**
- No exact scenario matches across splits
- No paraphrase pairs across splits
- No sequential scenarios from same incident

---

## 11. Dataset Metrics and Monitoring

### 11.1 Dataset Statistics

**Track Per Version:**
- Total sample count
- Samples per task type
- Samples per operator
- Samples per incident type
- Average sample length
- Vocabulary statistics
- Entity coverage

### 11.2 Quality Metrics

**Track Per Version:**
- Topology validation pass rate
- Plausibility check pass rate
- Human quality score sample
- Diversity indices
- Class balance metrics

### 11.3 Generation Monitoring

**Track Per Run:**
- Samples generated
- Generation failures
- Constraint violations
- Quality filter rejections
- Time per sample

---

## 12. Dataset Versioning

### 12.1 Version Scheme

```
MAJOR.MINOR.PATCH

MAJOR: Schema breaking changes
MINOR: New task types, operators, significant additions
PATCH: Bug fixes, quality improvements, small additions
```

### 12.2 Version Changelog

Each version includes:
- Summary of changes
- Sample count deltas
- Quality metric changes
- Known issues
- Migration notes

### 12.3 Reproducibility

**Required for Reproducibility:**
- Random seeds documented
- Template versions locked
- Generation parameters recorded
- Validator versions noted
- Source data versions tracked

---

## 13. Dataset Governance

### 13.1 Data Provenance

**Track for Every Sample:**
- Source data version
- Generation method
- Template ID (if applicable)
- Generation timestamp
- Validator version
- Quality scores

### 13.2 Quality Review Process

**Review Stages:**
1. Automated validation
2. Quality scoring
3. Human spot-check (sampling)
4. Expert review (gold sets)

### 13.3 Issue Tracking

**Track Issues:**
- Quality problems discovered
- Topology errors
- Implausibility reports
- User feedback
- Resolution status

### 13.4 Update Policy

**Update Triggers:**
- New operators added
- Quality issues discovered
- Task types expanded
- Template library updated
- Evaluation gaps identified

---

## 14. Integration with Private Data

### 14.1 Extension Points

**Designed for Future Integration:**
- Schema extensibility for proprietary fields
- Adapter interface for private feeds
- Configurable topology databases
- Rule override mechanism
- Private template injection

### 14.2 Privacy Considerations

**When Integrating Private Data:**
- PII detection and removal
- Aggregation requirements
- Access control integration
- Audit logging
- Data retention policies

---

## Appendix A: Sample Count Targets

| Task Type | Train | Validation | Test | Total |
|-----------|-------|------------|------|-------|
| Incident Summarization | 8,000 | 1,000 | 1,000 | 10,000 |
| Delay Root-Cause | 8,000 | 1,000 | 1,000 | 10,000 |
| Headway Control | 6,400 | 800 | 800 | 8,000 |
| Dwell Anomaly | 4,000 | 500 | 500 | 5,000 |
| Turnback Feasibility | 4,000 | 500 | 500 | 5,000 |
| Dispatch Conflict | 4,000 | 500 | 500 | 5,000 |
| Line Recovery | 4,800 | 600 | 600 | 6,000 |
| Structured Extraction | 8,000 | 1,000 | 1,000 | 10,000 |
| Counterfactual Comparison | 4,000 | 500 | 500 | 5,000 |
| After-Action Review | 3,200 | 400 | 400 | 4,000 |
| Confidence Reporting | 4,000 | 500 | 500 | 5,000 |
| Safe Refusal | 2,400 | 300 | 300 | 3,000 |
| **Total** | **60,800** | **7,600** | **7,600** | **76,000** |

---

## Appendix B: Operator Coverage Targets

| Operator | Percentage | Sample Target |
|----------|------------|---------------|
| MTA NYCT | 30% | 22,800 |
| MBTA | 20% | 15,200 |
| WMATA | 15% | 11,400 |
| BART | 15% | 11,400 |
| TfL | 15% | 11,400 |
| Generic/Multi | 5% | 3,800 |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Design Specification
