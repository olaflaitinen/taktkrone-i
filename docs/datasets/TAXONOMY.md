# TAKTKRONE-I Dataset Taxonomy

**Version:** 1.0.0
**Last Updated:** 2026-03-27

---

## Overview

This document defines the complete classification taxonomy for TAKTKRONE-I training and evaluation data. Every dataset sample is classified along multiple dimensions to enable filtering, balancing, and analysis.

---

## 1. Primary Dimensions

### 1.1 Operator

The transit operator context for the scenario.

| Code | Operator | Region | Network Type |
|------|----------|--------|--------------|
| `mta_nyct` | MTA New York City Transit | New York, USA | Heavy metro |
| `mbta` | Massachusetts Bay Transportation Authority | Boston, USA | Heavy metro + light rail |
| `wmata` | Washington Metropolitan Area Transit Authority | Washington DC, USA | Heavy metro |
| `bart` | Bay Area Rapid Transit | San Francisco, USA | Heavy metro |
| `tfl` | Transport for London Underground | London, UK | Heavy metro |
| `generic` | Generic/Multi-operator | N/A | Synthetic |

### 1.2 Line

Specific transit line within operator network.

**Line Classification:**
- Trunk line (high frequency, high capacity)
- Branch line (lower frequency, branches from trunk)
- Shuttle (short connector service)
- Express (limited stops)
- Local (all stops)

### 1.3 Topology Type

Network topology characteristics of the scenario location.

| Type | Description |
|------|-------------|
| `linear` | Simple linear segment without branches |
| `branching` | Line splits into branches |
| `junction` | Multiple lines intersect |
| `terminal` | End-of-line terminal |
| `loop` | Circular or loop configuration |
| `crossover_zone` | Area with crossover infrastructure |
| `interlining` | Multiple services share track |

### 1.4 Terminal Complexity

Complexity of terminal operations involved.

| Level | Description |
|-------|-------------|
| `simple` | Single platform, simple turnback |
| `moderate` | Multiple platforms, standard crossover |
| `complex` | Multiple platforms, multiple crossovers, storage tracks |
| `major` | Major terminal with extensive infrastructure |
| `none` | Scenario does not involve terminal |

### 1.5 Service Pattern

Service pattern context for the scenario.

| Pattern | Description |
|---------|-------------|
| `peak_am` | Morning peak service |
| `peak_pm` | Evening peak service |
| `midday` | Midday off-peak service |
| `evening` | Evening off-peak service |
| `overnight` | Late night/early morning service |
| `weekend` | Weekend service pattern |
| `holiday` | Holiday service pattern |
| `special_event` | Special event enhanced service |

---

## 2. Incident Classification

### 2.1 Incident Type

Primary classification of disruption or operational event.

| Code | Category | Description | Typical Duration | Typical Severity |
|------|----------|-------------|------------------|------------------|
| `SIG` | Signalling Degradation | Signal system failures, interlocking issues | 15-60 min | Medium-High |
| `THS` | Train Held in Station | Extended dwell, door issues, passenger issues | 5-15 min | Low-Medium |
| `TDS` | Train Disabled in Service | Vehicle breakdown, mechanical failure | 30-120 min | High |
| `TCG` | Terminal Congestion | Backup at terminal, insufficient turnback capacity | 15-45 min | Medium |
| `CXU` | Crossover Unavailable | Switch failure, track work blocking crossover | 30-180 min | Medium-High |
| `SOC` | Station Overcrowding | Platform capacity issues, crowd control | 10-30 min | Low-Medium |
| `PLT` | Platform Incident | Object on track, person on trackway | 15-60 min | High-Critical |
| `PME` | Police/Medical Event | Police activity, medical emergency | 10-45 min | Medium-High |
| `PWR` | Power Restriction | Third rail issues, power supply problems | 30-120 min | High |
| `WTH` | Weather Effect | Flooding, heat restrictions, ice | 60-480 min | Medium-High |
| `PWO` | Planned Work Overlap | Scheduled maintenance causing conflict | Variable | Low-Medium |
| `RSS` | Rolling Stock Shortage | Insufficient trains for service | 60-240 min | Medium |
| `TUP` | Turnback Path Unavailable | Cannot complete scheduled turnaround | 30-90 min | Medium |
| `CRW` | Crew Dependency | Operator unavailability | 15-60 min | Low-Medium |
| `RPL` | Network Ripple Delay | Cascaded delay from upstream | Variable | Low-Medium |
| `PSS` | Partial Suspension | Segment of line out of service | 60-480 min | High-Critical |
| `BAS` | Baseline/No Issue | Normal operations reference | N/A | None |

### 2.2 Incident Sub-Types

Detailed classification within primary categories.

**SIG - Signalling Degradation:**
- `SIG_TRACK_CIRCUIT` - Track circuit failure
- `SIG_INTERLOCKING` - Interlocking malfunction
- `SIG_ATP` - Automatic train protection issue
- `SIG_COMMUNICATION` - Signal communication failure
- `SIG_POWER` - Signal power failure

**TDS - Train Disabled in Service:**
- `TDS_PROPULSION` - Propulsion system failure
- `TDS_BRAKE` - Brake system issue
- `TDS_DOOR` - Door mechanism failure
- `TDS_HVAC` - HVAC system failure
- `TDS_COUPLING` - Coupling/uncoupling issue

**PWR - Power Restriction:**
- `PWR_THIRD_RAIL` - Third rail/contact rail issue
- `PWR_SUBSTATION` - Substation failure
- `PWR_CABLE` - Power cable damage
- `PWR_WEATHER` - Weather-related power issue

### 2.3 Severity

Impact severity classification.

| Level | Code | Delay Impact | Scope | Response Priority |
|-------|------|--------------|-------|-------------------|
| Low | `low` | < 5 min avg | Single train | Monitor |
| Medium | `medium` | 5-15 min avg | Multiple trains | Active management |
| High | `high` | 15-30 min avg | Line segment | Urgent intervention |
| Critical | `critical` | > 30 min avg | Multiple lines | Emergency response |

### 2.4 Duration

Expected or actual duration classification.

| Class | Range | Examples |
|-------|-------|----------|
| `brief` | < 10 min | Minor door issue, brief signal reset |
| `short` | 10-30 min | Platform incident clearance, simple mechanical |
| `moderate` | 30-60 min | Signal repair, disabled train removal |
| `extended` | 60-180 min | Major mechanical, infrastructure repair |
| `prolonged` | > 180 min | Major incident, infrastructure failure |

### 2.5 Passenger Impact

Assessment of impact on passengers.

| Level | Description | Indicators |
|-------|-------------|------------|
| `minimal` | Few passengers affected | Off-peak, low ridership station |
| `low` | Some inconvenience | Minor delays, alternatives available |
| `moderate` | Noticeable impact | Significant delays, crowding |
| `high` | Major disruption | Large delays, service changes |
| `severe` | Widespread impact | Extended outage, mass delays |

---

## 3. Response and Recovery Classification

### 3.1 Recovery Stage

Stage in the disruption lifecycle.

| Stage | Description |
|-------|-------------|
| `detection` | Incident just detected |
| `assessment` | Evaluating impact and options |
| `response` | Active intervention underway |
| `stabilization` | Situation contained, normalizing |
| `recovery` | Restoring normal service |
| `post_incident` | After-action phase |

### 3.2 Action Types

Categories of operational interventions.

| Code | Action Type | Description |
|------|-------------|-------------|
| `HOLD` | Hold Train | Delay train at station |
| `EXPR` | Express Operation | Skip stops |
| `SHRT` | Short Turn | Reverse before terminal |
| `SKIP` | Skip Stop | Bypass specific station |
| `ADDL` | Additional Train | Dispatch extra service |
| `REDU` | Reduce Frequency | Decrease service level |
| `SWTC` | Switch Track | Change operating track |
| `SHFT` | Platform Shift | Change platform assignment |
| `BRDG` | Bridge Service | Provide alternative transport |
| `COMM` | Communication | Passenger information |
| `ESCL` | Escalation | Escalate to higher authority |
| `MNTR` | Monitor | Watch and wait |
| `VERI` | Verification | Confirm with field staff |

---

## 4. Data Quality Classification

### 4.1 Telemetry Completeness

Availability of operational data.

| Level | Description | Missing Data |
|-------|-------------|--------------|
| `full` | All data available | None |
| `high` | Most data available | < 10% missing |
| `moderate` | Some gaps | 10-30% missing |
| `low` | Significant gaps | 30-50% missing |
| `minimal` | Very limited data | > 50% missing |

### 4.2 Ambiguity Level

Degree of uncertainty in scenario.

| Level | Description |
|-------|-------------|
| `clear` | Situation unambiguous |
| `minor_ambiguity` | Some uncertainty, resolvable |
| `moderate_ambiguity` | Multiple interpretations possible |
| `high_ambiguity` | Significant uncertainty |
| `contradictory` | Conflicting information |

### 4.3 Confidence Target

Expected confidence level for model output.

| Level | Description | Confidence Range |
|-------|-------------|------------------|
| `very_high` | Near certain response expected | 0.90-1.00 |
| `high` | High confidence expected | 0.75-0.90 |
| `moderate` | Reasonable confidence expected | 0.50-0.75 |
| `low` | Low confidence acceptable | 0.25-0.50 |
| `abstain` | Abstention appropriate | < 0.25 |

---

## 5. Output Classification

### 5.1 Output Mode

Type of model output expected.

| Mode | Description |
|------|-------------|
| `text_summary` | Free-form text summary |
| `structured_only` | Structured data only |
| `text_with_structure` | Both text and structured |
| `action_recommendation` | Ranked action list |
| `explanation` | Explanatory response |
| `refusal` | Appropriate refusal |
| `clarification_request` | Request for more information |

### 5.2 Task Type

Specific task being performed (see Dataset Strategy for full list).

| Code | Task |
|------|------|
| `SUM` | Incident Summarization |
| `DRH` | Delay Root-Cause Hypothesis |
| `HCS` | Headway Control Suggestion |
| `DAE` | Dwell Anomaly Explanation |
| `TFR` | Turnback Feasibility Reasoning |
| `DCR` | Dispatch Conflict Resolution |
| `LRS` | Line Recovery Strategy |
| `SEX` | Structured Extraction |
| `CAC` | Counterfactual Action Comparison |
| `AAR` | After-Action Review |
| `CRP` | Confidence Reporting |
| `SRF` | Safe Refusal |

---

## 6. Dataset Split Classification

### 6.1 Evaluation Split

Dataset partition assignment.

| Split | Purpose |
|-------|---------|
| `train` | Model training |
| `validation` | Hyperparameter tuning |
| `test` | Final evaluation |
| `benchmark` | Benchmark-specific evaluation |
| `adversarial` | Adversarial testing |

### 6.2 Difficulty Level

Estimated reasoning difficulty.

| Level | Description | Criteria |
|-------|-------------|----------|
| `easy` | Straightforward scenario | Single factor, clear solution |
| `medium` | Moderate complexity | Multiple factors, some tradeoffs |
| `hard` | Complex reasoning required | Many factors, competing objectives |
| `expert` | Expert-level difficulty | Novel situations, subtle tradeoffs |

---

## 7. Provenance Classification

### 7.1 Data Source Type

Origin of the data.

| Type | Description |
|------|-------------|
| `synthetic_template` | Generated from scenario template |
| `synthetic_simulation` | Generated from simulation |
| `synthetic_paraphrase` | Paraphrased from existing data |
| `public_gtfs` | Derived from public GTFS data |
| `public_alert` | Derived from public service alerts |
| `annotated_historical` | Annotated historical data |
| `expert_authored` | Authored by domain experts |

### 7.2 Generation Method

Specific generation approach used.

| Method | Description |
|--------|-------------|
| `rule_based` | Rule-based template generation |
| `simulation` | Simulation-based generation |
| `paraphrase` | Controlled paraphrase |
| `counterfactual` | Counterfactual branching |
| `perturbation` | Perturbation injection |
| `negative` | Negative sample generation |
| `manual` | Manual authoring |

### 7.3 Validation Status

Quality validation state.

| Status | Description |
|--------|-------------|
| `not_validated` | Not yet validated |
| `auto_passed` | Passed automated validation |
| `auto_failed` | Failed automated validation |
| `human_reviewed` | Human reviewed |
| `expert_validated` | Expert validated |
| `gold_standard` | Gold standard quality |

---

## 8. Taxonomy Application

### 8.1 Sample Metadata Structure

Every sample carries full taxonomy classification:

```json
{
  "taxonomy": {
    "operator": "mta_nyct",
    "line": "1",
    "topology_type": "linear",
    "terminal_complexity": "complex",
    "service_pattern": "peak_pm",
    "incident_type": "SIG",
    "incident_subtype": "SIG_TRACK_CIRCUIT",
    "severity": "medium",
    "duration_class": "moderate",
    "passenger_impact": "moderate",
    "recovery_stage": "response",
    "telemetry_completeness": "full",
    "ambiguity_level": "minor_ambiguity",
    "confidence_target": "high",
    "output_mode": "action_recommendation",
    "task_type": "HCS",
    "split": "train",
    "difficulty": "medium",
    "source_type": "synthetic_template",
    "generation_method": "rule_based",
    "validation_status": "auto_passed"
  }
}
```

### 8.2 Filtering Examples

**Filter for training headway control on MTA:**
```python
samples = dataset.filter(
    operator="mta_nyct",
    task_type="HCS",
    split="train",
    validation_status="auto_passed"
)
```

**Filter for hard evaluation scenarios:**
```python
samples = dataset.filter(
    split="test",
    difficulty=["hard", "expert"],
    validation_status="gold_standard"
)
```

**Filter for safety-critical scenarios:**
```python
samples = dataset.filter(
    task_type="SRF",
    incident_type=["PLT", "PME"],
    severity=["high", "critical"]
)
```

### 8.3 Balance Monitoring

Track distribution across key dimensions:

```python
monitor_balance(
    dimensions=["incident_type", "severity", "operator", "task_type"],
    target_distribution="uniform",  # or specific distribution
    alert_threshold=0.2  # Alert if deviation > 20%
)
```

---

## 9. Taxonomy Governance

### 9.1 Extension Process

To add new taxonomy values:

1. Document new value with description
2. Define relationships to existing values
3. Update schema validation
4. Update monitoring dashboards
5. Version taxonomy document

### 9.2 Deprecation Process

To deprecate taxonomy values:

1. Mark as deprecated with replacement
2. Add migration mapping
3. Update generators to use replacement
4. Maintain backward compatibility for 2 versions

### 9.3 Version Control

Taxonomy versions follow semantic versioning:
- MAJOR: Breaking changes to structure
- MINOR: New values added
- PATCH: Description updates, bug fixes

---

**Document Version:** 1.0.0
**Taxonomy Version:** 1.0.0
**Last Updated:** 2026-03-27
