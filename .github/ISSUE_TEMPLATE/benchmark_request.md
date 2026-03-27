---
name: New Benchmark Request
about: Propose a new evaluation benchmark for TAKTKRONE-I
title: '[BENCHMARK] '
labels: enhancement, phase-4
assignees: ''
---

## Benchmark Overview

**Benchmark Name:** [e.g., IncidentTriage-Eval]

**Category:**
- [ ] Summarization
- [ ] Classification / Diagnosis
- [ ] Recommendation / Ranking
- [ ] Factuality / Consistency
- [ ] Safety / Guardrails
- [ ] Retrieval Quality
- [ ] Other:

## Motivation

### What capability does this benchmark evaluate?

<!-- Describe the specific OCC assistant capability being tested -->

### Why is this important?

<!-- Explain the operational relevance of this capability -->

## Benchmark Design

### Task Description

<!-- Describe the task the model must perform -->

### Input Format

```json
{
  "example_input": "Describe the input format"
}
```

### Expected Output Format

```json
{
  "example_output": "Describe the expected output format"
}
```

### Evaluation Metrics

<!-- List the metrics to be used -->

| Metric | Description | Target Range |
|--------|-------------|--------------|
| e.g., Accuracy | Classification accuracy | > 85% |
| | | |

## Dataset Requirements

### Data Source

- [ ] Synthetic generation
- [ ] Real historical data
- [ ] Expert annotation
- [ ] Combination

### Dataset Size

- Training set: [if applicable]
- Validation set:
- Test set:

### Annotation Requirements

<!-- Describe any human annotation needed -->

## Implementation Notes

### Similar Existing Benchmarks

<!-- List any similar benchmarks in NLP / transit domains -->

### Complexity Estimate

- [ ] Simple (few days)
- [ ] Medium (1-2 weeks)
- [ ] Complex (> 2 weeks)

### Dependencies

<!-- List any special dependencies needed -->

## Example Instances

### Easy Example

```json
// Provide an easy test case
```

### Hard Example

```json
// Provide a challenging test case
```

## Additional Context

<!-- Any other relevant information -->
