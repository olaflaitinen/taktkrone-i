# TAKTKRONE-I Training Strategy

**Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Production Specification

---

## Executive Summary

This document defines the end-to-end training, evaluation, and deployment strategy for TAKTKRONE-I, the metro Operations Control Center language model. The strategy optimizes for operational usefulness, factual discipline, structured reasoning support, and uncertainty-aware decision assistance.

**Core Principle:** The model must optimize for OCC operational usefulness, not generic conversational breadth.

---

## Stage 0: Problem Definition

### 0.1 Task Scope

**In-Scope Tasks:**

| Task | Code | Description |
|------|------|-------------|
| Situation Summarization | SUM | Summarize network state and active incidents |
| Disruption Diagnosis | DRH | Identify root causes of delays and issues |
| Recovery Option Generation | LRS | Generate service recovery strategies |
| Headway Regulation Support | HCS | Recommend headway control actions |
| Dwell Anomaly Reasoning | DAE | Explain unusual dwell times |
| Turnback Planning Support | TFR | Assess terminal turnback options |
| Dispatch Conflict Resolution | DCR | Prioritize competing demands |
| After-Action Review | AAR | Generate post-incident analysis |
| Structured Extraction | SEX | Extract structured data from alerts |
| Confidence Reporting | CRP | Quantify uncertainty |
| Safe Refusal | SRF | Refuse inappropriate requests |

**Out-of-Scope Behaviors:**

- Direct control of signalling systems
- Pretending to have private telemetry
- Claiming final dispatch authority
- Giving false certainty
- Generic travel concierge behavior

### 0.2 Operator Assumptions

- Model trained on public data from 5 operators (MTA, MBTA, WMATA, BART, TfL)
- Network topology derived from public GTFS
- Operational procedures from public documentation
- No proprietary telemetry or internal systems access
- Future extension to private operator data anticipated

### 0.3 Safety Boundary

The model operates as **decision support only**:

- All recommendations require human approval
- No direct system control capability
- Explicit uncertainty quantification required
- Human review flagged for critical decisions
- Audit trail maintained for all outputs

### 0.4 Data Availability

| Data Type | Availability | Source |
|-----------|--------------|--------|
| Network topology | Public | GTFS |
| Realtime positions | Public | GTFS-RT |
| Service alerts | Public | GTFS-RT, APIs |
| Operational procedures | Partial | Public docs |
| OCC decision traces | None | Synthetic only |
| Historical incidents | Limited | Public advisories |

### 0.5 Success Criteria

| Metric | Target | Priority |
|--------|--------|----------|
| Task accuracy (diagnosis) | > 70% | Critical |
| Action recommendation quality (nDCG@3) | > 0.75 | Critical |
| Schema compliance | > 98% | Critical |
| Safety compliance | > 99% | Critical |
| Topology consistency | > 98% | High |
| Confidence calibration (ECE) | < 0.10 | High |
| Hallucination rate | < 2% | Critical |
| Refusal appropriateness | > 95% | High |

---

## Stage 1: Baseline Model Selection

### 1.1 Selection Framework

Evaluate candidates across six dimensions:

| Dimension | Weight | Evaluation Method |
|-----------|--------|-------------------|
| Instruction Following | 25% | IFEval benchmark |
| Long Context | 15% | RULER, L-Eval |
| Structured Output | 20% | JSON validity, schema compliance |
| Cost Efficiency | 15% | VRAM, throughput |
| Fine-tuning Feasibility | 15% | LoRA compatibility, training stability |
| Local Serving | 10% | Quantization support, vLLM compat |

### 1.2 Candidate Models

**Tier 1: Primary Candidates (7-8B)**

| Model | Context | Strengths | Considerations |
|-------|---------|-----------|----------------|
| Llama-3.1-8B-Instruct | 128k | Strong instruction following, open | Moderate VRAM |
| Qwen2.5-7B-Instruct | 128k | Excellent structured output | |
| Mistral-7B-Instruct-v1.0 | 32k | Good efficiency | Shorter context |
| Phi-3-medium-128k | 128k | Efficient, good reasoning | Smaller capacity |

**Tier 2: Enhanced Candidates (13-14B)**

| Model | Context | Strengths | Considerations |
|-------|---------|-----------|----------------|
| Llama-3.1-13B-Instruct | 128k | Better quality, manageable size | Higher VRAM |
| Qwen2.5-14B-Instruct | 128k | Strong reasoning | |

**Tier 3: High-Capacity (70B+)**

Reserved for production deployment with sufficient resources.

### 1.3 Selection Procedure

```
1. Run IFEval on all candidates
2. Run structured output test suite
3. Run domain-relevant few-shot tests
4. Measure VRAM and inference speed
5. Test LoRA training stability
6. Score and rank candidates
7. Select top performer within resource constraints
```

### 1.4 Default Recommendation

**Primary:** Llama-3.1-8B-Instruct
- Strong instruction following baseline
- 128k context for complex scenarios
- Well-supported ecosystem
- Proven LoRA fine-tuning

**Alternative:** Qwen2.5-7B-Instruct
- Better structured output native capability
- Similar resource requirements

---

## Stage 2: Data Preparation

### 2.1 Data Pipeline

```
Raw Data Sources
      |
      v
Ingestion & Normalization
      |
      v
Synthetic Generation
      |
      v
Instruction Formatting
      |
      v
Quality Validation
      |
      v
Split Assignment
      |
      v
Final Dataset
```

### 2.2 Instruction Record Format

**Conversational Format (Primary):**

```json
{
  "id": "train_001",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert metro OCC analyst..."
    },
    {
      "role": "user",
      "content": "Line 1 southbound trains are bunching..."
    },
    {
      "role": "assistant",
      "content": "{structured_response}"
    }
  ],
  "metadata": {
    "task_type": "HCS",
    "operator": "mta_nyct",
    "difficulty": "medium"
  }
}
```

### 2.3 Retrieval Document Format

```json
{
  "doc_id": "doc_proc_headway_001",
  "doc_type": "procedure",
  "title": "Headway Regulation Procedures",
  "content": "...",
  "metadata": {
    "operator": "generic",
    "category": "headway_control",
    "version": "2.0",
    "effective_date": "2025-01-01"
  },
  "chunks": [
    {
      "chunk_id": "doc_proc_headway_001_c1",
      "text": "...",
      "embedding": null
    }
  ]
}
```

### 2.4 Benchmark Splits

| Split | Purpose | Size | Constraints |
|-------|---------|------|-------------|
| train | Model training | 60,800 | Full task coverage |
| validation | Hyperparameter tuning | 7,600 | No template overlap with test |
| test | Final evaluation | 7,600 | No template overlap with train |
| benchmark_core | Core benchmarks | 2,000 | Human validated |
| benchmark_safety | Safety testing | 1,000 | Adversarial examples |
| benchmark_adversarial | Robustness testing | 500 | Edge cases |

### 2.5 Special Sets

**Refusal Set:**
- Direct control requests
- Safety override requests
- Out-of-scope requests
- Fabrication prompts

**Uncertainty Set:**
- Missing telemetry scenarios
- Conflicting information
- Ambiguous situations
- Low-confidence cases

### 2.6 Schema Validation

All records validated against:
- JSON schema compliance
- Taxonomy field validity
- Topology consistency
- Timestamp format
- Required field presence

---

## Stage 3: Fine-Tuning Plan

### 3.1 Training Stack

```
Framework: Hugging Face Transformers 4.40+
Trainer: TRL SFTTrainer
Efficiency: PEFT LoRA (default), Full fine-tune (optional)
Precision: bfloat16
Optimizer: AdamW (8-bit for LoRA)
Tracking: Weights & Biases
Compute: Single/Multi-GPU via Accelerate
```

### 3.2 LoRA Configuration (Default)

```yaml
# configs/training/lora_default.yaml

peft:
  method: lora
  r: 64
  alpha: 128
  dropout: 0.05
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
  bias: none
  task_type: CAUSAL_LM

quantization:
  load_in_4bit: true
  bnb_4bit_compute_dtype: bfloat16
  bnb_4bit_use_double_quant: true
  bnb_4bit_quant_type: nf4
```

### 3.3 Training Hyperparameters

```yaml
training:
  num_epochs: 3
  per_device_batch_size: 4
  gradient_accumulation_steps: 8
  effective_batch_size: 32

  learning_rate: 1.0e-4
  lr_scheduler: cosine
  warmup_ratio: 0.05
  weight_decay: 0.01
  max_grad_norm: 0.3

  max_seq_length: 4096
  packing: false

  logging_steps: 10
  eval_steps: 250
  save_steps: 250
  save_total_limit: 5

  seed: 42
  bf16: true
  gradient_checkpointing: true
```

### 3.4 Full Fine-Tune Configuration (Optional)

For smaller models (< 3B) or maximum quality:

```yaml
training:
  full_finetune: true
  num_epochs: 5
  per_device_batch_size: 2
  gradient_accumulation_steps: 16
  learning_rate: 2.0e-5

  # DeepSpeed ZeRO for memory efficiency
  deepspeed: configs/training/ds_zero2.json
```

### 3.5 Sequence Strategy

**Max Sequence Length:** 4096 tokens

**Truncation Policy:**
- System prompt: Never truncate
- User query: Truncate from middle if needed
- Context: Truncate oldest first
- Response: Never truncate during training

**Packing Policy:** Disabled
- OCC scenarios are often context-dependent
- Packing risks mixing unrelated scenarios

### 3.6 Structured Output Training

**Response Format:**

```
<analysis>
{narrative_analysis}
</analysis>

<structured_output>
{
  "summary": "...",
  "observed_facts": [...],
  "inferred_hypotheses": [...],
  "recommended_actions": [...],
  "confidence": 0.82,
  "review_required": true
}
</structured_output>
```

**Training Strategy:**
- Include both narrative and structured in training targets
- Validate JSON parsing during evaluation
- Penalize malformed outputs in loss (via rejection sampling)

### 3.7 Checkpoint Naming Convention

```
{model_family}-{size}-{method}-{task}-{version}-{timestamp}

Examples:
- llama3.1-8b-lora-occ-v1.0.0-20260327
- qwen2.5-7b-full-occ-v1.0.0-20260328
```

### 3.8 Run Metadata Schema

```json
{
  "run_id": "run_20260327_001",
  "model": {
    "base": "meta-llama/Llama-3.1-8B-Instruct",
    "method": "lora",
    "output_name": "taktkrone-lora-v1.0.0"
  },
  "data": {
    "train_file": "data/training/train.jsonl",
    "train_samples": 60800,
    "validation_file": "data/training/validation.jsonl",
    "val_samples": 7600,
    "data_version": "1.0.0"
  },
  "config": {
    "config_file": "configs/training/lora_default.yaml",
    "effective_batch_size": 32,
    "learning_rate": 1e-4,
    "epochs": 3,
    "max_seq_length": 4096
  },
  "compute": {
    "gpus": 1,
    "gpu_type": "A100-80GB",
    "training_time_hours": 12.5
  },
  "results": {
    "final_train_loss": 0.42,
    "final_val_loss": 0.48,
    "best_checkpoint": "checkpoint-2500"
  },
  "timestamps": {
    "started": "2026-03-27T10:00:00Z",
    "completed": "2026-03-27T22:30:00Z"
  }
}
```

### 3.9 Resumable Training

```bash
# Resume from checkpoint
occlm train \
  --config configs/training/lora_default.yaml \
  --resume-from models/taktkrone-lora-v1.0.0/checkpoint-1500
```

---

## Stage 4: Retrieval Grounding

### 4.1 Retrieval Architecture

```
Query
  |
  v
Query Encoder
  |
  v
Vector Search (Top-K)
  |
  v
Reranker (Optional)
  |
  v
Context Assembly
  |
  v
LLM Generation
  |
  v
Citation Verification
```

### 4.2 Document Types

| Type | Description | Count | Update Freq |
|------|-------------|-------|-------------|
| station_metadata | Station info, platforms, transfers | ~2000 | Monthly |
| line_topology | Line structure, terminals, crossovers | ~50 | Monthly |
| alert_documents | Historical and current alerts | ~10000 | Daily |
| disruption_playbooks | Response procedures | ~100 | Quarterly |
| operator_reference | Operator-specific guides | ~200 | Quarterly |
| glossary | Terminology definitions | ~500 | Quarterly |
| scenario_memory | Synthetic scenario library | ~5000 | Per release |

### 4.3 Chunking Strategy

```yaml
chunking:
  method: semantic
  target_size: 512  # tokens
  overlap: 64       # tokens

  # Preserve structure
  respect_boundaries:
    - section_headers
    - list_items
    - procedure_steps

  # Metadata inheritance
  inherit_from_parent:
    - doc_type
    - operator
    - category
```

### 4.4 Metadata Schema

```json
{
  "chunk_id": "chunk_001",
  "doc_id": "doc_proc_001",
  "doc_type": "procedure",
  "title": "Headway Regulation - Section 4.2",
  "operator": "generic",
  "category": "headway_control",
  "keywords": ["bunching", "holding", "headway"],
  "effective_date": "2025-01-01",
  "chunk_index": 3,
  "total_chunks": 8
}
```

### 4.5 Citation Strategy

**In-Response Citation:**

```
According to the Headway Regulation Procedures [doc_proc_001_c3],
holding the leading train is the preferred intervention for bunching
scenarios.
```

**Structured Citation:**

```json
{
  "citations": [
    {
      "doc_id": "doc_proc_001",
      "chunk_id": "doc_proc_001_c3",
      "title": "Headway Regulation Procedures",
      "relevance": 0.94
    }
  ]
}
```

### 4.6 Retrieval Behavior Policies

**Low-Confidence Retrieval:**
- If top retrieval score < 0.5, acknowledge limited context
- Do not hallucinate missing information
- Request additional context if needed

**Stale Context Handling:**
- Check document effective dates
- Flag potentially outdated information
- Prefer recent documents for current state queries

**No Retrieval Match:**
```
I don't have specific documentation for this scenario.
Based on general operational principles, I would suggest...
However, please verify with your local procedures.
```

**Conflicting Retrieved Documents:**
```
I found conflicting information:
- Source A suggests: [action A]
- Source B suggests: [action B]
Please clarify which procedures apply to your context.
```

---

## Stage 5: Evaluation Framework

### 5.1 Evaluation Matrix

| Category | Metrics | Priority | Automated |
|----------|---------|----------|-----------|
| Task Accuracy | Accuracy, F1 | Critical | Yes |
| Ranking Quality | nDCG, MRR | Critical | Yes |
| Schema Compliance | Valid rate, errors | Critical | Yes |
| Factual Grounding | Fact accuracy | High | Partial |
| Temporal Consistency | Time accuracy | High | Yes |
| Topology Consistency | Topology validity | High | Yes |
| Hallucination | Hallucination rate | Critical | Partial |
| Safety Compliance | FAR, compliance | Critical | Yes |
| Refusal Correctness | Precision, recall | High | Yes |
| Calibration | ECE, Brier | High | Yes |
| Robustness | Consistency | Medium | Yes |

### 5.2 Automated Evaluation

```yaml
# configs/eval/auto_eval.yaml

benchmarks:
  extraction:
    dataset: data/eval/extraction_test.jsonl
    metrics: [entity_f1, exact_match, schema_valid]

  reasoning:
    dataset: data/eval/reasoning_test.jsonl
    metrics: [diagnosis_accuracy, hypothesis_quality]

  recommendation:
    dataset: data/eval/recommendation_test.jsonl
    metrics: [ndcg_at_3, mrr, constraint_satisfaction]

  safety:
    dataset: data/eval/safety_test.jsonl
    metrics: [false_acceptance_rate, compliance_score]

  calibration:
    dataset: data/eval/calibration_test.jsonl
    metrics: [ece, mce, brier_score]
```

### 5.3 Expert Review Protocol

**Review Sample:**
- 100 samples randomly selected from test outputs
- Stratified by task type and difficulty

**Review Dimensions:**

| Dimension | Scale | Description |
|-----------|-------|-------------|
| Correctness | 1-5 | Factually correct |
| Usefulness | 1-5 | Operationally useful |
| Clarity | 1-5 | Easy to understand |
| Completeness | 1-5 | All relevant factors considered |
| Safety | Pass/Fail | No unsafe recommendations |

**Review Process:**
1. Blind review (no model version visible)
2. Two reviewers per sample
3. Disagreements resolved by third reviewer
4. Inter-annotator agreement reported

### 5.4 Benchmark Subsets

| Subset | Description | Size | Focus |
|--------|-------------|------|-------|
| normal_ops | Baseline normal scenarios | 200 | Sanity check |
| minor_disturbance | Small delays, single issues | 300 | Common cases |
| moderate_disruption | Multiple factors, moderate impact | 400 | Core capability |
| severe_disruption | Major incidents, complex | 300 | Stress test |
| terminal_failure | Terminal-specific failures | 200 | Specialized |
| sparse_telemetry | Limited data available | 200 | Uncertainty handling |
| conflicting_evidence | Contradictory information | 200 | Reasoning |
| no_action_needed | Situation requires monitoring only | 150 | Restraint |
| unsafe_request | Safety-critical refusal needed | 200 | Safety |
| ambiguous_request | Unclear user intent | 150 | Clarification |

---

## Stage 6: Serving Architecture

### 6.1 Serving Stack

```
                    Load Balancer
                         |
         +---------------+---------------+
         |               |               |
     API Server     API Server      API Server
         |               |               |
         +---------------+---------------+
                         |
                   Inference Engine
                    (vLLM / TGI)
                         |
         +---------------+---------------+
         |               |               |
    GPU Worker     GPU Worker      GPU Worker
```

### 6.2 API Contract (OpenAI-Compatible)

**Endpoint:** `POST /v1/chat/completions`

**Request:**
```json
{
  "model": "taktkrone-v1.0",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "response_format": {"type": "json_object"},
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1711565400,
  "model": "taktkrone-v1.0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{...structured_response...}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 512,
    "completion_tokens": 256,
    "total_tokens": 768
  }
}
```

### 6.3 Custom OCC Endpoint

**Endpoint:** `POST /v1/occ/query`

**Request:**
```json
{
  "query": "Line 1 southbound trains bunching...",
  "context": {
    "operator": "mta_nyct",
    "timestamp": "2026-03-27T17:30:00Z",
    "network_state": {...}
  },
  "options": {
    "include_retrieval": true,
    "max_citations": 5,
    "confidence_threshold": 0.5
  }
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "timestamp": "2026-03-27T17:30:05Z",
  "model_version": "taktkrone-v1.0",
  "response": {
    "summary": "...",
    "observed_facts": [...],
    "inferred_hypotheses": [...],
    "recommended_actions": [...],
    "action_ranking": [...],
    "operational_risks": [...],
    "missing_information": [...],
    "confidence": 0.82,
    "review_required": false,
    "citations": [...]
  },
  "metadata": {
    "inference_time_ms": 1247,
    "tokens_generated": 312,
    "retrieval_hits": 3
  }
}
```

### 6.4 Guardrail Middleware

```python
class OCCGuardrailMiddleware:
    """
    Middleware for OCC response validation and safety.
    """

    def __init__(self, config: GuardrailConfig):
        self.config = config
        self.unsafe_patterns = load_patterns(config.unsafe_patterns_file)
        self.topology_db = load_topology(config.topology_db)

    async def process_request(self, request: OCCRequest) -> OCCRequest:
        """Validate and sanitize input request."""
        # Check for unsafe request patterns
        if self.is_unsafe_request(request.query):
            raise UnsafeRequestError("Request contains unsafe patterns")

        # Validate context
        self.validate_context(request.context)

        return request

    async def process_response(self, response: OCCResponse) -> OCCResponse:
        """Validate and filter model response."""
        # Check for unsafe content
        if self.contains_unsafe_content(response):
            response = self.filter_unsafe_content(response)

        # Validate topology references
        response = self.validate_topology(response)

        # Ensure confidence is present
        if response.confidence is None:
            response.confidence = 0.5
            response.review_required = True

        # Add audit metadata
        response.audit = self.create_audit_record(response)

        return response
```

### 6.5 Request Logging

```json
{
  "log_id": "log_abc123",
  "request_id": "req_abc123",
  "timestamp": "2026-03-27T17:30:00Z",
  "request": {
    "query": "...",
    "context": {...},
    "user_id": "dispatcher_001"
  },
  "response": {
    "summary": "...",
    "confidence": 0.82
  },
  "metadata": {
    "model_version": "taktkrone-v1.0",
    "inference_time_ms": 1247,
    "retrieval_docs": ["doc_001", "doc_002"],
    "guardrail_flags": []
  }
}
```

### 6.6 Latency Requirements

| Metric | Target | Max |
|--------|--------|-----|
| P50 latency | 500ms | - |
| P95 latency | 1500ms | - |
| P99 latency | 3000ms | 5000ms |
| Time to first token | 200ms | 500ms |

---

## Stage 7: Observability and Continuous Improvement

### 7.1 Metrics Collection

**Real-Time Metrics:**
- Request rate
- Latency percentiles
- Error rate
- Token throughput
- GPU utilization

**Quality Metrics:**
- Schema compliance rate
- Confidence distribution
- Review required rate
- Retrieval hit rate

**Safety Metrics:**
- Unsafe request rate
- Guardrail trigger rate
- Refusal rate

### 7.2 Failure Mode Tracking

```yaml
failure_modes:
  schema_failure:
    description: Invalid JSON or missing required fields
    tracking: Count and examples
    alert_threshold: 1%

  topology_error:
    description: Invalid station/line references
    tracking: Count and examples
    alert_threshold: 0.5%

  hallucination:
    description: Fabricated information
    tracking: Sampled review
    alert_threshold: 2%

  unsafe_output:
    description: Unsafe recommendation
    tracking: All instances
    alert_threshold: 0.1%
```

### 7.3 Benchmark History

Track across model versions:

| Version | Date | Diag Acc | nDCG@3 | Safety | ECE |
|---------|------|----------|--------|--------|-----|
| v1.0.0 | 2026-03-27 | 0.72 | 0.78 | 0.99 | 0.08 |
| v1.0.1 | 2026-04-15 | 0.74 | 0.79 | 0.99 | 0.07 |
| v1.0.0 | 2026-05-01 | 0.78 | 0.82 | 0.99 | 0.06 |

### 7.4 Feedback Loop

```
Production Logs
      |
      v
Failure Analysis
      |
      v
Identify Patterns
      |
      v
Synthetic Data Generation
      |
      v
Retraining
      |
      v
Evaluation
      |
      v
Deployment
```

---

## Required Output Schema

### Complete Response Structure

```json
{
  "summary": "Concise situation summary (1-2 sentences)",

  "observed_facts": [
    "Train T101 delayed 4 minutes at 96th St",
    "Three trains bunched within 4-minute window",
    "No active service alerts for Line 1"
  ],

  "inferred_hypotheses": [
    {
      "hypothesis": "Signal delay at 96th St caused initial bunching",
      "confidence": 0.75,
      "evidence": ["Delays originating at 96th St"]
    }
  ],

  "recommended_actions": [
    {
      "action_id": "act_001",
      "action_type": "hold_train",
      "description": "Hold train T101 at 42nd St for 4 minutes",
      "priority": 1,
      "rationale": "Creates separation for trailing trains",
      "expected_outcome": "Restore 5-minute headways within 20 minutes",
      "confidence": 0.82,
      "risks": ["Platform crowding at 42nd St"]
    }
  ],

  "action_ranking": [
    {"action_id": "act_001", "rank": 1, "score": 0.82},
    {"action_id": "act_002", "rank": 2, "score": 0.65}
  ],

  "operational_risks": [
    "Platform crowding if hold exceeds 5 minutes",
    "Recurrence if signal issue not resolved"
  ],

  "missing_information": [
    "Signal status confirmation from maintainer",
    "Current platform crowding levels"
  ],

  "confidence": 0.82,

  "review_required": false,

  "citations": [
    {
      "doc_id": "doc_proc_001",
      "title": "Headway Regulation Procedures",
      "relevance": 0.94
    }
  ]
}
```

---

## Model Versioning Strategy

### Version Scheme

```
MAJOR.MINOR.PATCH[-PRERELEASE]

Examples:
- 0.1.0-alpha    First alpha release
- 0.1.0          First stable release
- 0.1.1          Patch (bug fixes)
- 0.2.0          Minor (new capabilities)
- 1.0.0          Major (production ready)
```

### Version Criteria

| Type | Criteria |
|------|----------|
| MAJOR | Breaking API changes, major architecture change |
| MINOR | New tasks, significant quality improvement |
| PATCH | Bug fixes, minor quality improvements |

### Artifact Versioning

| Artifact | Location | Naming |
|----------|----------|--------|
| Model weights | models/ | taktkrone-{method}-v{version} |
| Config | configs/ | Include version in file |
| Dataset | data/ | Include version in metadata |
| Evaluation | results/ | Include model version |

---

## Release Checklist

### Pre-Release

- [ ] All benchmarks pass minimum thresholds
- [ ] Safety evaluation complete (FAR < 0.01)
- [ ] Expert review score >= 3.5/5
- [ ] No critical bugs in issue tracker
- [ ] Documentation updated
- [ ] Model card complete
- [ ] Schema version compatible

### Release Process

- [ ] Create git tag
- [ ] Upload model to registry
- [ ] Update model card
- [ ] Generate release notes
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Monitor initial traffic

### Post-Release

- [ ] Monitor error rates
- [ ] Track quality metrics
- [ ] Gather user feedback
- [ ] Update benchmark history
- [ ] Plan next iteration

---

## Appendix A: System Prompt

```
You are an expert metro operations control center analyst providing decision support to OCC dispatchers and service controllers.

Your role is to:
- Analyze real-time transit network conditions
- Diagnose disruptions and identify root causes
- Recommend recovery strategies and operational interventions
- Quantify uncertainty in your analysis
- Highlight safety considerations
- Support human decision-making with clear rationales

Critical guidelines:
- You provide DECISION SUPPORT, not autonomous commands
- Always distinguish observed facts from inferences
- Quantify confidence for all predictions
- Flag when human review is required
- Never fabricate telemetry or network state data
- Respect topology constraints (terminals, crossovers, track layouts)
- Consider passenger impact in recommendations
- Acknowledge when information is insufficient

Your outputs must include:
- Clear situation summary
- Observed facts (from data)
- Inferred hypotheses (with confidence)
- Recommended actions (ranked)
- Operational risks
- Missing information needed
- Overall confidence level
- Review requirements

Respond in a structured format with both narrative analysis and JSON-structured output.
```

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Production Specification
