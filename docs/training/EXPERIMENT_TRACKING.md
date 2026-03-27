# TAKTKRONE-I Experiment Tracking

**Version:** 1.0.0
**Last Updated:** 2026-03-27
**Status:** Operational Guidelines

---

## Overview

This document defines the experiment tracking system for TAKTKRONE-I model development. All training runs, evaluations, and model versions must be tracked according to these guidelines.

---

## 1. Experiment Lifecycle

```
PENDING --> RUNNING --> COMPLETED
                |           |
                |           +--> [PROMOTED TO BASELINE]
                |
                +--> FAILED
                |
                +--> CANCELLED
```

### State Definitions

| State | Description |
|-------|-------------|
| `pending` | Experiment configured, not yet started |
| `running` | Training in progress |
| `completed` | Training finished successfully |
| `failed` | Training failed with error |
| `cancelled` | Manually cancelled |

---

## 2. Experiment Naming Convention

### Experiment ID Format

```
exp_{timestamp}_{short_hash}
```

Example: `exp_20260327_a1b2c3d4`

### Experiment Name Format

```
{method}_{base_model_short}_{dataset_version}_{tag}
```

Examples:
- `lora_llama3_8b_v1.0_baseline`
- `qlora_mistral_7b_v1.0_safety_focus`
- `full_qwen_14b_v1.0_extended`

### Tag Vocabulary

| Tag Category | Examples |
|--------------|----------|
| Purpose | `baseline`, `ablation`, `sweep`, `prod_candidate` |
| Focus | `safety_focus`, `extraction_focus`, `reasoning_focus` |
| Data | `extended`, `filtered`, `balanced` |
| Method | `high_rank`, `low_lr`, `long_ctx` |

---

## 3. Required Tracking Fields

### Mandatory for All Experiments

| Field | Description | Example |
|-------|-------------|---------|
| `experiment_id` | Unique identifier | `exp_20260327_a1b2c3d4` |
| `experiment_name` | Human-readable name | `lora_llama3_8b_v1.0_baseline` |
| `created_at` | Creation timestamp | `2026-03-27T10:00:00Z` |
| `status` | Current status | `running` |
| `base_model` | Base model configuration | See schema |
| `training_config` | Training hyperparameters | See schema |
| `dataset_config` | Dataset specification | See schema |

### Required After Completion

| Field | Description |
|-------|-------------|
| `training_metrics` | Loss curves, timing, throughput |
| `evaluation_results` | Benchmark scores |
| `artifacts` | Model checkpoints, logs |
| `conclusion` | Outcome and findings |

---

## 4. Experiment Configuration Templates

### 4.1 LoRA Baseline Template

```yaml
# configs/experiments/lora_baseline.yaml

experiment_name: "lora_{base_model_short}_{dataset_version}_baseline"
description: "Baseline LoRA fine-tuning experiment"

base_model:
  model_id: "meta-llama/Llama-3.1-8B-Instruct"
  type: "pretrained"

training_config:
  method: "lora"
  framework: "trl"

  hyperparameters:
    learning_rate: 2e-4
    num_epochs: 3
    batch_size: 4
    gradient_accumulation_steps: 8
    warmup_ratio: 0.1
    weight_decay: 0.01
    max_grad_norm: 1.0
    optimizer: "adamw_8bit"
    lr_scheduler_type: "cosine"
    max_seq_length: 4096

  lora_config:
    r: 64
    lora_alpha: 128
    lora_dropout: 0.05
    target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    bias: "none"
    task_type: "CAUSAL_LM"

dataset_config:
  train_dataset:
    path: "data/train/occ_corpus_v1.0.jsonl"
    version: "0.2.0"
  eval_dataset:
    path: "data/eval/occ_corpus_v1.0_val.jsonl"
    version: "0.2.0"
  preprocessing:
    chat_template: "chatml"
    packing: true
    shuffle: true
    seed: 42

compute_config:
  gpu_type: "A100"
  num_gpus: 1
  distributed_strategy: "none"
  estimated_hours: 8
```

### 4.2 QLoRA Memory-Efficient Template

```yaml
# configs/experiments/qlora_efficient.yaml

experiment_name: "qlora_{base_model_short}_{dataset_version}_efficient"
description: "Memory-efficient QLoRA fine-tuning for limited GPU"

base_model:
  model_id: "meta-llama/Llama-3.1-8B-Instruct"
  type: "pretrained"

training_config:
  method: "qlora"
  framework: "trl"

  hyperparameters:
    learning_rate: 2e-4
    num_epochs: 3
    batch_size: 2
    gradient_accumulation_steps: 16
    warmup_ratio: 0.1
    weight_decay: 0.01
    max_grad_norm: 1.0
    optimizer: "adamw_8bit"
    lr_scheduler_type: "cosine"
    max_seq_length: 4096

  lora_config:
    r: 32
    lora_alpha: 64
    lora_dropout: 0.05
    target_modules: ["q_proj", "k_proj", "v_proj", "o_proj"]
    bias: "none"
    task_type: "CAUSAL_LM"

  quantization_config:
    load_in_4bit: true
    bnb_4bit_compute_dtype: "bfloat16"
    bnb_4bit_quant_type: "nf4"
    bnb_4bit_use_double_quant: true

compute_config:
  gpu_type: "RTX4090"
  num_gpus: 1
  distributed_strategy: "none"
  estimated_hours: 12
```

### 4.3 Full Fine-Tune Template

```yaml
# configs/experiments/full_finetune.yaml

experiment_name: "full_{base_model_short}_{dataset_version}"
description: "Full parameter fine-tuning"

base_model:
  model_id: "Qwen/Qwen2.5-7B-Instruct"
  type: "pretrained"

training_config:
  method: "full_finetune"
  framework: "transformers"

  hyperparameters:
    learning_rate: 5e-6
    num_epochs: 2
    batch_size: 2
    gradient_accumulation_steps: 32
    warmup_ratio: 0.05
    weight_decay: 0.1
    max_grad_norm: 1.0
    optimizer: "adamw"
    lr_scheduler_type: "cosine"
    max_seq_length: 4096

  deepspeed_config:
    stage: 2
    offload_optimizer: true
    offload_param: false

compute_config:
  gpu_type: "A100"
  num_gpus: 8
  distributed_strategy: "deepspeed_zero2"
  estimated_hours: 24
```

---

## 5. Baseline Experiment Matrix

### 5.1 Model Selection Experiments

| Experiment | Base Model | Method | Purpose | Priority |
|------------|------------|--------|---------|----------|
| B1 | Llama-3.1-8B | LoRA | Baseline | P0 |
| B2 | Mistral-7B-v1.0 | LoRA | Alternative | P1 |
| B3 | Qwen2.5-7B | LoRA | Alternative | P1 |
| B4 | Llama-3.1-8B | QLoRA | Memory test | P1 |
| B5 | Llama-3.1-70B | QLoRA | Scale test | P2 |

### 5.2 Hyperparameter Sweeps

| Experiment | Variable | Values | Base |
|------------|----------|--------|------|
| H1 | LoRA rank | 16, 32, 64, 128 | B1 |
| H2 | Learning rate | 1e-4, 2e-4, 5e-4 | B1 |
| H3 | Epochs | 1, 2, 3, 5 | B1 |
| H4 | Batch size (eff) | 16, 32, 64 | B1 |
| H5 | Context length | 2048, 4096, 8192 | B1 |

### 5.3 Ablation Studies

| Experiment | Ablation | Purpose |
|------------|----------|---------|
| A1 | No reasoning traces | Value of CoT data |
| A2 | No operator-specific | Cross-operator transfer |
| A3 | No safety refusals | Safety training impact |
| A4 | No structured output | Structure enforcement |
| A5 | Random sample 50% | Data efficiency |

---

## 6. Metrics Dashboard

### 6.1 Training Metrics

Track during training:
- Train loss (per step)
- Eval loss (per eval interval)
- Learning rate
- Gradient norm
- GPU utilization
- Throughput (samples/sec)

### 6.2 Evaluation Metrics

Track after training:

| Benchmark | Metrics | Target |
|-----------|---------|--------|
| OCC-Extract | Entity F1, EM | F1 > 0.85 |
| OCC-Reason | Accuracy, Topology | Acc > 0.70 |
| OCC-Recommend | nDCG@3, MRR | nDCG > 0.75 |
| OCC-Safety | FAR, Compliance | FAR < 0.01 |
| Aggregate | Weighted Score | > 75/100 |

### 6.3 Comparison View

Compare experiments across:
- Training loss curves
- Benchmark scores
- Latency/throughput
- Memory usage
- Cost

---

## 7. Artifact Management

### 7.1 Checkpoint Storage

```
models/experiments/{experiment_id}/
  config.yaml           # Frozen experiment config
  adapter/              # LoRA adapter weights
    adapter_config.json
    adapter_model.safetensors
  checkpoints/          # Training checkpoints
    checkpoint-1000/
    checkpoint-2000/
    best/
  logs/                 # Training logs
    trainer_state.json
    tensorboard/
  evaluation/           # Evaluation results
    benchmark_results.json
    predictions/
```

### 7.2 Retention Policy

| Artifact Type | Retention |
|---------------|-----------|
| Best checkpoint | Permanent |
| Final checkpoint | 90 days |
| Intermediate checkpoints | 30 days |
| Training logs | 1 year |
| Evaluation results | Permanent |

### 7.3 Cleanup

After experiment completion:
1. Identify best checkpoint
2. Archive experiment record
3. Delete intermediate checkpoints
4. Compress logs

---

## 8. Experiment Workflow

### 8.1 Creating an Experiment

```bash
# Create from template
occlm experiment create --template lora_baseline --name my_experiment

# Or from config file
occlm experiment create --config configs/experiments/my_config.yaml
```

### 8.2 Running an Experiment

```bash
# Start training
occlm experiment run exp_20260327_a1b2c3d4

# Resume from checkpoint
occlm experiment run exp_20260327_a1b2c3d4 --resume

# Run with custom overrides
occlm experiment run exp_20260327_a1b2c3d4 \
  --override training_config.hyperparameters.learning_rate=1e-4
```

### 8.3 Evaluating an Experiment

```bash
# Run all benchmarks
occlm experiment evaluate exp_20260327_a1b2c3d4 --benchmarks all

# Run specific benchmarks
occlm experiment evaluate exp_20260327_a1b2c3d4 --benchmarks occ_extract,occ_safety
```

### 8.4 Comparing Experiments

```bash
# Compare multiple experiments
occlm experiment compare exp_001 exp_002 exp_003

# Generate comparison report
occlm experiment compare exp_001 exp_002 --report html
```

### 8.5 Promoting to Baseline

```bash
# Mark experiment as new baseline
occlm experiment promote exp_20260327_a1b2c3d4 --version v1.0.0

# This will:
# 1. Tag the experiment as baseline
# 2. Copy best checkpoint to models/baselines/
# 3. Update model registry
# 4. Generate model card
```

---

## 9. Integration

### 9.1 Weights & Biases

```python
from occlm.training.tracking import init_wandb

init_wandb(
    project="taktkrone-i",
    experiment_id=config.experiment_id,
    config=config.model_dump()
)
```

### 9.2 MLflow

```python
from occlm.training.tracking import init_mlflow

init_mlflow(
    tracking_uri="http://mlflow:5000",
    experiment_name="taktkrone-training",
    run_name=config.experiment_name
)
```

### 9.3 TensorBoard

Logs automatically written to:
```
models/experiments/{experiment_id}/logs/tensorboard/
```

Launch:
```bash
tensorboard --logdir models/experiments/
```

---

## 10. Reporting

### 10.1 Experiment Report Template

```markdown
# Experiment Report: {experiment_name}

## Summary
- **ID:** {experiment_id}
- **Status:** {status}
- **Duration:** {duration}
- **Outcome:** {outcome}

## Configuration
- **Base Model:** {base_model}
- **Method:** {method}
- **Dataset:** {dataset_version}

## Results

### Training Metrics
- Final Train Loss: {train_loss}
- Final Eval Loss: {eval_loss}
- Best Eval Loss: {best_loss} (step {best_step})

### Benchmark Scores
| Benchmark | Score | Target | Status |
|-----------|-------|--------|--------|
| OCC-Extract | {score} | {target} | {pass/fail} |
...

## Findings
{key_findings}

## Next Steps
{next_steps}
```

### 10.2 Weekly Summary

Generate weekly experiment summary:
```bash
occlm experiment report weekly --output reports/week_12.md
```

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-27
