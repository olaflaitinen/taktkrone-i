---
name: Operator Scenario Contribution
about: Contribute a real-world OCC scenario for training data
title: '[SCENARIO] '
labels: data, operator-input, phase-1
assignees: ''
---

## Scenario Overview

**Incident Type:** <!-- e.g., Signal Failure, Medical Emergency, Power Outage -->

**Transit System:** <!-- e.g., NYC Subway, London Underground, anonymized -->

**Date/Time Context:** <!-- Time of day, day of week, season (anonymized) -->

**Severity:**
- [ ] Minor (no service disruption)
- [ ] Moderate (partial service impact)
- [ ] Major (significant delays)
- [ ] Critical (emergency / safety critical)

## Incident Description

### Initial Report

<!-- What was the first indication of the incident? -->

**Source:**
- [ ] Train operator radio call
- [ ] Station staff report
- [ ] Automated system alert
- [ ] Passenger complaint
- [ ] CCTV observation
- [ ] Other:

**Initial Information:**
```
# Describe what was initially known
```

## Operator Actions Taken

### Decision Timeline

<!-- Chronological list of decisions made -->

1. **[Time +0 min]**
   - **Information available:**
   - **Decision made:**
   - **Rationale:**

2. **[Time +X min]**
   - **Information available:**
   - **Decision made:**
   - **Rationale:**

3. (continue as needed)

### Communication Log

<!-- Key communications during the incident -->

| Time | To/From | Message | Purpose |
|------|---------|---------|---------|
| +0 min | Train Op → OCC | "..." | Initial report |
| | | | |

## Factors Considered

<!-- What factors influenced decisions? -->

- [ ] Passenger safety
- [ ] Schedule adherence
- [ ] Equipment protection
- [ ] Ridership load
- [ ] Weather conditions
- [ ] Special events
- [ ] Alternative routes
- [ ] Resource availability
- [ ] Other:

## Outcome

**Resolution Time:** <!-- How long until normal operations? -->

**Service Impact:**
- Trains delayed:
- Lines affected:
- Passengers affected (estimate):

**Lessons Learned:**
<!-- What went well? What could be improved? -->

## Anonymization Checklist

- [ ] No station names (use generic identifiers like "Station A")
- [ ] No specific dates (use relative times like "weekday morning peak")
- [ ] No personnel names
- [ ] No sensitive system details
- [ ] No PII

## Scenario Value

### Training Value

<!-- Why is this scenario valuable for training? -->

**Key Capabilities Demonstrated:**
- [ ] Information synthesis
- [ ] Multi-factor decision making
- [ ] Crisis communication
- [ ] Resource allocation
- [ ] Time-critical reasoning
- [ ] Safety prioritization
- [ ] Other:

### Difficulty Level

- [ ] Routine (common scenario)
- [ ] Moderate (requires judgment)
- [ ] Complex (multiple factors)
- [ ] Expert (rare/unusual)

## Structured Data Format

<!-- Optional: Provide the scenario in JSONL format -->

```json
{
  "scenario_id": "anonymous-001",
  "incident_type": "...",
  "initial_state": {...},
  "events": [...],
  "operator_actions": [...],
  "outcome": {...}
}
```

## Additional Context

<!-- Any other relevant information -->

## Consent & Attribution

- [ ] I have permission to share this scenario
- [ ] I confirm all sensitive information has been removed
- [ ] I agree to the project's data contribution terms

**Attribution (optional):**
- Years of OCC experience:
- Transit system type:
- Role:

---

**Note:** All contributed scenarios will be reviewed for anonymization compliance before inclusion in training data.
