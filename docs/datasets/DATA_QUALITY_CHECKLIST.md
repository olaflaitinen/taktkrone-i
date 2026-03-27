# TAKTKRONE-I Data Quality and Governance Checklist

**Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Production Guidelines

---

## Overview

This checklist ensures data quality and governance for all TAKTKRONE-I training and evaluation data. Every dataset version must complete all applicable checks before release.

---

## 1. Pre-Generation Checks

### 1.1 Template Validation

- [ ] **Template syntax valid**: All templates parse without errors
- [ ] **Parameter ranges sensible**: Min/max values are operationally realistic
- [ ] **Topology references valid**: All station/line references exist in topology DB
- [ ] **Action types valid**: All recommended actions are in approved action taxonomy
- [ ] **Narrative templates complete**: No unfilled production values in examples

### 1.2 Configuration Review

- [ ] **Random seeds documented**: All generation uses reproducible seeds
- [ ] **Version numbers set**: Template version, generator version recorded
- [ ] **Target distributions defined**: Class balance targets specified
- [ ] **Quality thresholds set**: Minimum quality score defined

### 1.3 Dependency Verification

- [ ] **Topology database version**: Verified current and complete
- [ ] **Operating procedure version**: Referenced procedures are current
- [ ] **Terminology consistency**: Uses approved glossary terms

---

## 2. Generation Checks

### 2.1 Schema Compliance

For every generated sample:

- [ ] **Schema validation passed**: Sample conforms to JSON schema
- [ ] **Required fields present**: All required fields populated
- [ ] **Field types correct**: Values match expected types
- [ ] **Enum values valid**: Categorical fields use valid values
- [ ] **Timestamp format correct**: ISO 8601 with timezone

### 2.2 Topology Validation

- [ ] **Stations exist**: All referenced stations exist on referenced line
- [ ] **Station order correct**: Stations appear in correct sequence
- [ ] **Terminals valid**: Terminal references are actual terminals
- [ ] **Crossovers valid**: Crossover references exist in topology
- [ ] **Directions consistent**: Direction labels match topology

### 2.3 Operational Plausibility

- [ ] **Travel times realistic**: Inter-station times within normal range
- [ ] **Headways feasible**: Headway values are operationally achievable
- [ ] **Delays plausible**: Delay magnitudes are realistic for incident type
- [ ] **Dwell times reasonable**: Dwell times within normal bounds
- [ ] **Recovery times achievable**: Proposed recovery timelines are realistic

### 2.4 Logical Consistency

- [ ] **No contradictions**: Scenario elements do not contradict each other
- [ ] **Temporal consistency**: Events occur in logical time sequence
- [ ] **Causal consistency**: Causes precede effects
- [ ] **State consistency**: Network state is internally consistent

### 2.5 Narrative Quality

- [ ] **Grammar correct**: No grammatical errors in generated text
- [ ] **Terminology correct**: Uses proper operational terminology
- [ ] **Completeness**: All relevant information included
- [ ] **No hallucination**: No fabricated data or entities
- [ ] **Uncertainty acknowledged**: Appropriate hedging where needed

---

## 3. Post-Generation Validation

### 3.1 Automated Quality Checks

```python
# Run automated validation pipeline
validate_batch(
    samples=generated_samples,
    checks=[
        "schema_compliance",
        "topology_validation",
        "plausibility_check",
        "consistency_check",
        "quality_scoring"
    ],
    fail_threshold=0.95,  # 95% must pass
    log_failures=True
)
```

### 3.2 Quality Score Verification

- [ ] **Minimum score met**: All samples meet minimum quality score (0.7)
- [ ] **Score distribution reasonable**: No unexpected score clustering
- [ ] **Low scores investigated**: Samples below 0.8 manually reviewed

### 3.3 Diversity Analysis

- [ ] **Incident type coverage**: All incident types represented
- [ ] **Severity distribution**: Matches target distribution
- [ ] **Operator balance**: Operators represented per targets
- [ ] **Difficulty spread**: Range of difficulties included
- [ ] **Action diversity**: Various action types recommended

### 3.4 Edge Case Coverage

- [ ] **Boundary conditions**: Edge cases included (empty lists, max values)
- [ ] **Error scenarios**: Error handling scenarios included
- [ ] **Ambiguous cases**: Ambiguity handling scenarios included
- [ ] **Refusal cases**: Appropriate refusal scenarios included

---

## 4. Human Review Checks

### 4.1 Sampling Strategy

- [ ] **Random sample selected**: Unbiased sample for review
- [ ] **Size appropriate**: Minimum 1% or 100 samples (whichever larger)
- [ ] **Stratified by difficulty**: Proportional difficulty representation
- [ ] **Edge cases included**: Manual selection of edge cases

### 4.2 Review Criteria

For each reviewed sample, assess:

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Scenario realism | | |
| Query clarity | | |
| Response quality | | |
| Recommendation appropriateness | | |
| Uncertainty handling | | |
| Safety consideration | | |

### 4.3 Review Outcomes

- [ ] **Average score >= 3.5**: Minimum acceptable quality
- [ ] **No critical failures**: No samples with safety/factuality issues
- [ ] **Issues documented**: All identified issues logged
- [ ] **Remediation planned**: Action items for fixing issues

---

## 5. Dataset Assembly Checks

### 5.1 Split Validation

- [ ] **No leakage**: No exact duplicates across splits
- [ ] **No near-duplicates**: Paraphrase variants in same split
- [ ] **Proportions correct**: Train/val/test ratios as specified
- [ ] **Stratification maintained**: Balance preserved in each split

### 5.2 Balance Verification

| Dimension | Target | Actual | Status |
|-----------|--------|--------|--------|
| Incident types | Uniform | | |
| Severity levels | Per spec | | |
| Operators | Per spec | | |
| Task types | Per spec | | |
| Difficulty | Per spec | | |

### 5.3 Metadata Completeness

- [ ] **Provenance recorded**: Generation method, timestamp, version
- [ ] **Taxonomy complete**: All taxonomy fields populated
- [ ] **Ground truth present**: Labels for evaluation samples
- [ ] **Quality scores included**: Per-sample quality scores

---

## 6. Documentation Checks

### 6.1 Dataset Card

- [ ] **Summary complete**: Clear description of dataset
- [ ] **Intended use stated**: Use cases and limitations
- [ ] **Generation method described**: How data was created
- [ ] **Composition documented**: Size, splits, class distribution
- [ ] **Quality metrics included**: Validation results
- [ ] **Known issues documented**: Limitations and caveats

### 6.2 Changelog

- [ ] **Version number incremented**: Semantic versioning followed
- [ ] **Changes described**: What changed from previous version
- [ ] **Migration notes**: How to update from previous version

### 6.3 Schema Documentation

- [ ] **Schema files current**: JSON schemas match data format
- [ ] **Field descriptions complete**: All fields documented
- [ ] **Examples provided**: Valid example records

---

## 7. Release Checks

### 7.1 Final Validation

- [ ] **All samples validate**: 100% schema compliance
- [ ] **No PII present**: Personal information removed
- [ ] **No proprietary data**: Only public data sources
- [ ] **License compliance**: All data properly licensed

### 7.2 Packaging

- [ ] **File formats correct**: JSONL, Parquet as specified
- [ ] **Compression applied**: Large files compressed
- [ ] **Checksums generated**: SHA256 for all files
- [ ] **Directory structure correct**: Standard layout

### 7.3 Access Control

- [ ] **Permissions set**: Appropriate read/write access
- [ ] **Versioning enabled**: Dataset versions tracked
- [ ] **Backup created**: Copy in secondary location

---

## 8. Post-Release Monitoring

### 8.1 Usage Monitoring

- [ ] **Download tracking**: Monitor dataset usage
- [ ] **Issue tracking**: Monitor reported issues
- [ ] **Feedback collection**: Gather user feedback

### 8.2 Quality Monitoring

- [ ] **Error reports**: Track reported data errors
- [ ] **Model performance**: Monitor downstream model quality
- [ ] **Drift detection**: Check for data drift over time

### 8.3 Maintenance

- [ ] **Issue resolution**: Fix reported issues
- [ ] **Updates scheduled**: Plan regular refresh
- [ ] **Deprecation policy**: End-of-life planning

---

## 9. Governance Policies

### 9.1 Data Provenance

All data must have documented:
- Original source (public API, synthetic, etc.)
- Transformation history
- Generation parameters
- Quality validation results

### 9.2 Version Control

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document all changes in changelog
- Maintain backward compatibility when possible
- Provide migration guides for breaking changes

### 9.3 Quality Standards

| Metric | Minimum | Target |
|--------|---------|--------|
| Schema compliance | 100% | 100% |
| Topology validation | 99% | 100% |
| Plausibility check | 95% | 98% |
| Quality score avg | 0.75 | 0.85 |
| Human review score | 3.5/5 | 4.0/5 |

### 9.4 Issue Resolution

| Severity | Response Time | Resolution Time |
|----------|--------------|-----------------|
| Critical | 24 hours | 7 days |
| High | 3 days | 14 days |
| Medium | 7 days | 30 days |
| Low | 14 days | 60 days |

### 9.5 Retention Policy

- Active versions: 2 most recent major versions
- Archive: All versions retained in cold storage
- Deletion: Only with explicit authorization

---

## 10. Compliance Checklist

### 10.1 Ethical Considerations

- [ ] **No discriminatory content**: Data does not encode bias
- [ ] **Safety-first design**: Safety considerations embedded
- [ ] **Human oversight**: Human review in critical decisions
- [ ] **Transparency**: Generation methods documented

### 10.2 Legal Compliance

- [ ] **Copyright clear**: No copyrighted content without license
- [ ] **Terms of service**: API usage complies with ToS
- [ ] **Attribution**: Proper attribution for sources
- [ ] **License compatible**: All components license-compatible

### 10.3 Privacy

- [ ] **No PII**: No personally identifiable information
- [ ] **No location tracking**: No real user location data
- [ ] **Anonymization**: Any sensitive data anonymized
- [ ] **Consent**: Data collection had proper consent (N/A for synthetic)

---

## Quick Reference: Release Checklist

Before any dataset release, confirm:

```
[ ] All generation checks passed
[ ] Automated validation 100% pass
[ ] Human review completed (score >= 3.5)
[ ] No train/test leakage
[ ] Class balance within targets
[ ] Documentation complete
[ ] Dataset card written
[ ] Changelog updated
[ ] Checksums generated
[ ] License verified
```

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-27
