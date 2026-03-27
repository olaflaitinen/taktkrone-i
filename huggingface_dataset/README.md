---
license: apache-2.0
language:
- en
tags:
- transportation
- metro
- operations-control-center
- synthetic-data
- instruction-tuning
- dialogue
- llm-training
size_categories:
- 1K<n<10K
task_categories:
- text-generation
- text-classification
- question-answering
pipeline_tag: text-generation
pretty_name: TAKTKRONE OCC Dialogue Corpus
---

# TAKTKRONE OCC Dialogue Corpus

## Dataset Summary

The TAKTKRONE OCC Dialogue Corpus is a specialized dataset for training language models to assist in metro operations control center (OCC) scenarios. It contains realistic dialogue samples between operators and control center staff during various transit incidents and operational situations.

## Dataset Details

- **Created by:** Gustav Olaf Yunus Laitinen-Fredriksson Lundström-Imanov
- **Language:** English
- **License:** Apache 2.0
- **Size:** 5,247 dialogue samples
- **Format:** JSONL (JSON Lines)
- **DOI:** 10.57967/hf/8166

## Dataset Structure

### Data Fields

- `id`: Unique identifier for the dialogue
- `timestamp`: ISO timestamp of the scenario
- `operator`: Transit operator code (mta_nyct, mbta, wmata, bart, tfl)
- `source`: Data source (real or synthetic)
- `task_type`: Type of operational task
- `difficulty`: Difficulty level (easy, medium, hard)
- `messages`: List of dialogue messages with roles and content
- `ground_truth`: Expected actions and outcomes
- `metadata`: Additional scenario metadata

### Data Splits

- **Train:** 4,197 samples (80%)
- **Test:** 1,050 samples (20%)

## Dataset Creation

### Data Collection

The dataset combines:
1. **Real operational scenarios** from major metro systems
2. **Synthetic scenarios** generated using domain expertise
3. **Expert validation** by transit professionals

### Data Processing

- All personally identifiable information (PII) removed
- Timestamps normalized to UTC
- Location references anonymized
- Quality scoring and filtering applied

## Uses

### Intended Use

- Training language models for OCC assistance
- Research in transportation AI systems
- Development of operational support tools
- Educational purposes for transit operations

### Out-of-Scope Uses

- Direct operational control of transit systems
- Real-time safety-critical decisions
- Legal or compliance determinations
- Financial or business decisions

## Limitations

- Primarily focused on subway/metro systems
- English language only
- May not generalize to all operational contexts
- Requires domain expertise for proper interpretation

## Ethical Considerations

### Privacy

- All data anonymized and aggregated
- No personally identifiable information retained
- Compliance with transportation data protection regulations

### Safety

- Not intended for autonomous system control
- Human oversight required for all operational decisions
- Safety guardrails recommended for model deployment

## Citation

```bibtex
@misc{gustav_olaf_yunus_laitinen-fredriksson_imanov_2026,
	author       = { Gustav Olaf Yunus Laitinen-Fredriksson Imanov },
	title        = { taktkrone-occ-corpus (Revision 55fff5c) },
	year         = 2026,
	url          = { https://huggingface.co/datasets/olaflaitinen/taktkrone-occ-corpus },
	doi          = { 10.57967/hf/8166 },
	publisher    = { Hugging Face }
}
```

## Contact

- **Developer:** Gustav Olaf Yunus Laitinen-Fredriksson Lundström-Imanov
- **Email:** dev@taktkrone.ai
- **Website:** https://taktkrone.ai
- **Repository:** https://github.com/olaflaitinen/taktkrone-i

## DOI

10.57967/hf/8166
