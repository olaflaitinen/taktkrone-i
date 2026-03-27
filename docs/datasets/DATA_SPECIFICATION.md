# Data Specification for TAKTKRONE-I

## Overview

This document defines the data specifications, collection procedures, and quality standards for all data used in TAKTKRONE-I training, evaluation, and operation.

## Data Categories

### 1. Operational Data (Real or Simulated)

#### 1.1 Incident Records

**Purpose:** Core operational incidents logged by transit systems

**Schema Reference:** `data_contracts/incident_record.schema.json`

**Fields:**
- `incident_id`: Unique identifier
- `incident_type`: Category (signal_failure, medical_emergency, power_outage, etc.)
- `location`: Station/line identifier
- `timestamp`: RFC 3339 format with timezone
- `severity`: low, medium, high, critical
- `affected_resources`: Lines, stations, personnel
- `root_cause`: Identified cause (if known post-incident)
- `resolution_time_minutes`: Duration to resolution

**Collection Points:**
- OCC incident management system
- Real-time monitoring dashboards
- Maintenance reports
- Operator radio logs

**Retention:** Indefinite (compressed after 6 months)

**Example:**
```json
{
  "incident_id": "INC-2024-001234",
  "incident_type": "signal_failure",
  "location": "Station-A_Track-1N",
  "timestamp": "2024-01-15T14:30:00Z",
  "severity": "high",
  "root_cause": "Power supply module failure",
  "resolution_time_minutes": 18
}
```

### 2. Dialogue Data (OCC Communications)

#### 2.1 Radio Transcripts & Chat Logs

**Purpose:** Preserve OCC decision-making conversations for training

**Schema Reference:** `data_contracts/occ_dialogue_sample.schema.json`

**Fields:**
- `dialogue_id`: Unique identifier
- `incident_id`: Reference to parent incident
- `participants`: List of {id, role, department}
- `turns`: Chronological list of exchanges
- `metadata`: Time of day, system status, constraints
- `outcome`: Resolution and lessons learned

**Collection & Processing:**
1. **Raw Collection**: Recorded during incidents
2. **Anonymization**: Remove names, specific locations (use generic identifiers)
3. **Transcription**: Automatic speech-to-text + human review
4. **Annotation**: Mark critical decision points
5. **Validation**: Check for accuracy and completeness

**Privacy Requirements:**
- Remove personally identifiable information (PII)
- Use position/department, not person names
- Anonymize specific system details if sensitive
- Redact sensitive business practices
- Ensure compliance with local privacy regulations

**Retention:** 7 years (regulatory requirement in many transit systems)

**Example:**
```json
{
  "dialogue_id": "DIAL-2024-05623",
  "incident_id": "INC-2024-001234",
  "participants": [
    {"id": "OP-001", "role": "train_operator", "department": "operations"},
    {"id": "DISP-001", "role": "occ_dispatcher", "department": "dispatching"}
  ],
  "turns": [
    {
      "turn_number": 1,
      "speaker_id": "OP-001",
      "message": "Signal failure detected on Track 1 northbound",
      "timestamp_offset_seconds": 0
    },
    {
      "turn_number": 2,
      "speaker_id": "DISP-001",
      "message": "Copy. Maintenance team dispatched. Hold your train.",
      "timestamp_offset_seconds": 15
    }
  ],
  "metadata": {
    "time_of_day": "afternoon_peak",
    "passenger_load": "high",
    "weather": "clear"
  }
}
```

### 3. Action Recommendations

**Purpose:** Ground truth for model recommendation training

**Schema Reference:** `data_contracts/action_recommendation.schema.json`

**Fields:**
- `action_id`: Unique identifier
- `incident_id`: Reference to triggering incident
- `recommended_actions`: Prioritized list of actions
- `rationale`: Explanation for recommendations
- `confidence_score`: 0.0-1.0 confidence
- `safety_checks`: Validated against safety policies
- `outcome`: Whether action was implemented and result

**Authority:**
- Must be validated by experienced OCC supervisors
- Can be historical (post-incident) or real-time
- Should include expert commentary on alternative approaches

**Example:**
```json
{
  "action_id": "REC-2024-08912",
  "incident_id": "INC-2024-001234",
  "recommended_actions": [
    {
      "priority": 1,
      "action": "dispatch_maintenance",
      "target": "signal_repair_team",
      "urgency": "high",
      "expected_duration_minutes": 15
    },
    {
      "priority": 2,
      "action": "communicate_to_passengers",
      "urgency": "medium"
    }
  ],
  "safety_checks": {
    "passenger_safety": "safe",
    "personnel_safety": "safe",
    "equipment_integrity": "safe"
  }
}
```

### 4. Synthetic Scenarios

**Purpose:** Generate additional training data when real data is insufficient

**Schema Reference:** `data_contracts/synthetic_scenario.schema.json`

**Generation Process:**
1. **Template-based**: Use `occlm/synthesis/templates/`
2. **Variation**: Combine real incidents with realistic modifications
3. **Validation**: Verify plausibility with domain experts
4. **Annotation**: Generate ground-truth recommendations

**Constraints:**
- Never train on purely fictional scenarios without expert review
- Maintain statistical similarity to historical data
- Clearly label synthetic data in metadata
- Regular spot-check by transit domain experts

**Usage:**
```python
from occlm.simulation import ScenarioGenerator

generator = ScenarioGenerator(
    template="signal_failure_morning_rush",
    variations=100
)
scenarios = generator.generate()
```

## Data Quality Standards

### 1. Completeness

| Field | Acceptable Missing | Notes |
|-------|-------------------|-------|
| incident_id | 0% | Critical for tracking |
| timestamp | 0% | Required for temporal analysis |
| incident_type | <5% | Use "unknown" category for ambiguous cases |
| location | <10% | May be incomplete in early reports |
| root_cause | <40% | Often unknown until post-incident analysis |
| resolution_time | <5% | Critical for performance analysis |

### 2. Accuracy

**Incident Classification:**
- Primary classifier: >90% accuracy (multi-expert agreement)
- For ambiguous cases: Use "inconclusive" category
- Regular re-audit: 5% random sample validates

**Timestamp Accuracy:**
- Precision: +/- 1 minute for incidents
- Precision: +/- 5 seconds for dialogue turns
- All timestamps in UTC

**Location Accuracy:**
- Must be reconcilable with system topology
- Geographic coordinates within 50 meters
- Regular validation against master system map

### 3. Consistency

- Incident type taxonomy: Enforce controlled vocabulary
- Location identifiers: Centralized master list
- Timestamps: UTC normalization
- Role names: Standardized vocabulary

### 4. Validation Pipeline

```python
# All data must pass validation:
from occlm.schemas import validate_data

incidents = load_jsonl("incidents.jsonl")
for incident in incidents:
    if not validate_data(incident, "incident_record"):
        log_validation_error(incident)
        # Automatically segregate for manual review
```

## Data Collection Protocol

### Opt-in Data Contribution

**For Transit Operators:**

1. **Register Scenario**:
   - Use GitHub issue template: `.github/ISSUE_TEMPLATE/operator_scenario.md`
   - Include anonymized incident details
   - Explain key learning points

2. **Anonymization Checklist**:
   ```
   [OK] No actual station names (use "Station-A")
   [OK] No specific dates (use relative times)
   [OK] No personnel names
   [OK] No sensitive system details
   [OK] No personally identifiable information
   ```

3. **Review Process**:
   - Project maintainers review for quality
   - Anonymization verification
   - Inclusion in training dataset
   - Contributor credit in release notes

### Legal & Ethics

- **Data Contributor Agreement**: Contributors retain ownership; grant project a license
- **Privacy Compliance**: GDPR, HIPAA, local regulations
- **Ethical Review**: Scenarios reviewed for problematic patterns
- **Attribution**: Contributors credited (with consent)

## Dataset Statistics (Target)

### Training Dataset

| Metric | Target | Priority |
|--------|--------|----------|
| Total incidents | 10,000+ | High |
| Dialogue turn exchanges | 50,000+ | High |
| Unique incident types | 50+ | Medium |
| Avg. incident duration (min) | 30-120 | Medium |
| Synthetic data ratio | <20% | High |
| Data coverage (by incident type) | >80% | High |

### Evaluation Datasets

| Benchmark | Size | Difficulty |
|-----------|------|-----------|
| Triage-Easy | 100 | Easy actions, clear incidents |
| Triage-Medium | 200 | Mixed scenarios, must prioritize |
| Triage-Hard | 100 | Ambiguous, multiple factors |
| Safety-Critical | 50 | Safety-sensitive decisions |
| Operator-Feedback | 200 | Real operator judgments |

## Data Access & Security

### Access Levels

**Level 1 (Public):**
- Anonymized incident statistics
- Aggregate metrics
- Published benchmarks

**Level 2 (Contributor):**
- Full synthetic scenarios
- Template-based data
- Training examples

**Level 3 (Core Team):**
- Real incident dialogues
- Sensitive OCC communications
- Proprietary data from transit partners

### Storage

- **Development**: Unencrypted local storage, `.gitignored`
- **Production**: Encrypted at rest, access controlled
- **Backups**: Encrypted, geographically redundant

### Retention & Deletion

- **Default Retention**: 7 years
- **Deletion Request**: Support per-incident deletion
- **Anonymization Decay**: Re-anonymize after 3 years

## Data Pipeline

```
┌─────────────────┐
│  Raw Data       │ (OCC systems, logs, recordings)
└────────┬────────┘
         │
    ┌────▼─────┐
    │Collection│ - Consolidate from sources
    │Protocol  │ - Timestamp standardization
    │          │ - De-duplication
    └────┬─────┘
         │
    ┌────▼─────────────┐
    │Anonymization    │ - PII removal
    │& Privacy Filter │ - Sensitive data redaction
    │                 │ - Legal review
    └────┬─────────────┘
         │
    ┌────▼──────────────┐
    │Quality Validation│ - Schema check
    │                  │ - Completeness check
    │                  │ - Accuracy verification
    └────┬──────────────┘
         │
    ┌────▼──────────┐
    │Data Labeling  │ - Expert annotation
    │& Annotation   │ - Ground truth
    │               │ - Confidence scores
    └────┬──────────┘
         │
    ┌────▼──────────────┐
    │Final Dataset      │ (JSONL, versioned)
    │Training/Eval Sets │
    └───────────────────┘
```

## Data Versioning

Datasets are versioned:

```
data/
├── v1.0-initial-collection/
│   ├── metadata.yaml
│   ├── incidents.jsonl
│   ├── dialogues.jsonl
│   └── splits/ (train/val/test)
├── v1.0-expanded-scenarios/
│   └── ...
└── v1.0-production-release/
    └── ...
```

Each version includes:
- Dataset card (Hugging Face format)
- Collection methodology
- Quality metrics
- Known limitations
- Suggested split ratios

---

**Last Updated:** 2024-01-15
**Version:** 0.1 (Draft)
