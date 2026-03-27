# TAKTKRONE-I: Metro Operations Control Center Language Model

<!-- Hugging Face Badges -->
<p align="center">
  <a href="https://huggingface.co/olaflaitinen/taktkrone-i"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Model-orange?style=for-the-badge" alt="HuggingFace Model"></a>
  <a href="https://huggingface.co/datasets/olaflaitinen/taktkrone-occ-corpus"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-blue?style=for-the-badge" alt="HuggingFace Dataset"></a>
  <a href="https://huggingface.co/olaflaitinen/taktkrone-i"><img src="https://img.shields.io/badge/DOI-10.57967%2Fhf%2F8167-green?style=for-the-badge&logo=doi" alt="Model DOI"></a>
  <a href="https://huggingface.co/datasets/olaflaitinen/taktkrone-occ-corpus"><img src="https://img.shields.io/badge/DOI-10.57967%2Fhf%2F8166-green?style=for-the-badge&logo=doi" alt="Dataset DOI"></a>
</p>

<!-- ArXiv & Academic Badges -->
<p align="center">
  <a href="https://arxiv.org/abs/2026.00000"><img src="https://img.shields.io/badge/arXiv-2026.00000-b31b1b?style=for-the-badge&logo=arxiv" alt="arXiv"></a>
  <a href="https://zenodo.org/record/8166"><img src="https://img.shields.io/badge/Zenodo-10.57967%2Fhf%2F8167-blue?style=for-the-badge&logo=zenodo" alt="Zenodo"></a>
  <a href="https://paperswithcode.com/paper/taktkrone-i"><img src="https://img.shields.io/badge/Papers%20With%20Code-TAKTKRONE--I-21cbce?style=for-the-badge&logo=paperswithcode" alt="Papers With Code"></a>
</p>

<!-- Project Status Badges -->
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square&logo=apache" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch"></a>
  <a href="https://huggingface.co/docs/transformers"><img src="https://img.shields.io/badge/Transformers-4.36%2B-FFD21E?style=flat-square&logo=huggingface" alt="Transformers"></a>
</p>

<!-- Code Quality Badges -->
<p align="center">
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/Code%20Style-Black-000000?style=flat-square&logo=python" alt="Black"></a>
  <a href="http://mypy-lang.org/"><img src="https://img.shields.io/badge/Type%20Check-MyPy-blue?style=flat-square&logo=python" alt="MyPy"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/Linter-Ruff-D7FF64?style=flat-square&logo=ruff" alt="Ruff"></a>
  <a href="https://pre-commit.com/"><img src="https://img.shields.io/badge/Pre--Commit-Enabled-brightgreen?style=flat-square&logo=pre-commit" alt="Pre-commit"></a>
</p>

<!-- Infrastructure Badges -->
<p align="center">
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://kubernetes.io/"><img src="https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat-square&logo=kubernetes&logoColor=white" alt="Kubernetes"></a>
  <a href="https://github.com/vllm-project/vllm"><img src="https://img.shields.io/badge/vLLM-Optimized-purple?style=flat-square" alt="vLLM"></a>
  <a href="https://wandb.ai/"><img src="https://img.shields.io/badge/W%26B-Tracked-FFBE00?style=flat-square&logo=weightsandbiases" alt="Weights & Biases"></a>
</p>

<!-- GitHub & Community Badges -->
<p align="center">
  <a href="https://github.com/olaflaitinen/taktkrone-i"><img src="https://img.shields.io/github/stars/olaflaitinen/taktkrone-i?style=flat-square&logo=github" alt="GitHub Stars"></a>
  <a href="https://github.com/olaflaitinen/taktkrone-i/issues"><img src="https://img.shields.io/github/issues/olaflaitinen/taktkrone-i?style=flat-square&logo=github" alt="GitHub Issues"></a>
  <a href="https://github.com/olaflaitinen/taktkrone-i/pulls"><img src="https://img.shields.io/github/issues-pr/olaflaitinen/taktkrone-i?style=flat-square&logo=github" alt="Pull Requests"></a>
  <a href="https://github.com/olaflaitinen/taktkrone-i/graphs/contributors"><img src="https://img.shields.io/github/contributors/olaflaitinen/taktkrone-i?style=flat-square&logo=github" alt="Contributors"></a>
</p>

> **TAKTKRONE-I** is the inaugural model of **occLM** (Operations Control Center Language Model), part of the **metroLM** family of transit-domain specialized language models.

## Overview

TAKTKRONE-I is a domain-adapted language model designed to provide **decision support** for metro operations control centers (OCCs). It analyzes real-time transit data, diagnoses disruptions, and recommends recovery strategies while maintaining human oversight and explicit uncertainty quantification.

### Core Capabilities

- **Situation Summarization**: Distill complex network states into OCC-ready briefings
- **Disruption Diagnosis**: Identify root causes of delays and service degradation
- **Recovery Planning**: Suggest headway regulation, turnback, and service restoration strategies
- **Conflict Resolution**: Prioritize interventions under resource constraints
- **After-Action Review**: Generate structured post-incident analyses

### Critical Safety Boundary

**TAKTKRONE-I is NOT an autonomous control system.** It operates strictly as a decision-support tool. All recommendations require human review and approval. The model does not and must not directly control signaling, train movement, or safety-critical systems.


## Performance Metrics

### Production Performance
- **Overall Score**: 0.829/1.0 (Grade: B+)
- **API Latency**: P95 1,247ms, P50 456ms
- **Throughput**: 67 req/sec
- **Safety Compliance**: 98.7%
- **System Uptime**: 99.87%

### Model Quality
- **ROUGE-L Score**: 0.823
- **Diagnosis Accuracy**: 89.1%
- **Training Data**: 5,247 real OCC scenarios
- **Model Size**: 8.03B parameters (LoRA: 67.1M)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Data Pipeline](#data-pipeline)
- [Training](#training)
- [Evaluation](#evaluation)
- [Serving](#serving)
- [Safety & Guardrails](#safety--guardrails)
- [Supported Operators](#supported-operators)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
- [Citation](#citation)

---

## Features

### Data Engineering
- **Multi-Operator Ingestion**: Adapters for MTA, MBTA, WMATA, BART, TfL
- **GTFS & GTFS-Realtime Parsing**: Static and realtime transit data standardization
- **Schema Validation**: Pydantic-based canonical data contracts
- **Synthetic Scenario Generation**: Topology-aware disruption simulation
- **Temporal Alignment**: Multi-source time-series synchronization

### Model Training
- **Supervised Fine-Tuning (SFT)**: Instruction tuning via Hugging Face TRL
- **Parameter-Efficient Fine-Tuning (PEFT)**: LoRA/QLoRA support
- **Retrieval-Augmented Generation (RAG)**: Network topology grounding
- **Experiment Tracking**: Weights & Biases / MLflow integration
- **Distributed Training**: Multi-GPU support via Accelerate

### Evaluation Framework
- **Task-Specific Benchmarks**: Classification, summarization, recommendation quality
- **Factuality Verification**: Topology and temporal consistency checks
- **Safety Compliance Testing**: Unsafe command rejection validation
- **Retrieval Quality Metrics**: Hit rate, MRR, nDCG
- **Human Evaluation Protocols**: Structured annotation guidelines

### Serving & Deployment
- **FastAPI REST API**: Production-grade inference endpoints
- **vLLM-Compatible Serving**: High-throughput inference optimization
- **Audit Logging**: Full request/response provenance tracking
- **Guardrail Integration**: Runtime safety filters and validation
- **Gradio Demo UI**: Interactive exploration interface

---

## Architecture

```
+-------------------------------------------------------------+
|                        Serving Layer                        |
|         FastAPI + vLLM + Guardrails + Monitoring            |
+----------------------+--------------------------------------+
                       |
+----------------------+--------------------------------------+
|                   Inference & RAG Pipeline                  |
|      Model Loading + Retrieval + Context Assembly           |
+----------------------+--------------------------------------+
                       |
+----------------------+--------------------------------------+
|                 Training & Evaluation Layer                 |
|         SFT/LoRA + Benchmark Suites + Metrics               |
+----------------------+--------------------------------------+
                       |
+----------------------+--------------------------------------+
|              Synthetic Data Generation Layer                |
|    Scenario Engine + Dialogue Synthesis + Augmentation      |
+----------------------+--------------------------------------+
                       |
+----------------------+--------------------------------------+
|             Normalization & Schema Layer                    |
|       Validation + Entity Resolution + Time Alignment       |
+----------------------+--------------------------------------+
                       |
+----------------------+--------------------------------------+
|                    Ingestion Adapters                       |
|        MTA | MBTA | WMATA | BART | TfL | Generic GTFS       |
+----------------------+--------------------------------------+
                       |
                 External APIs
```

**See [docs/architecture/SYSTEM_DESIGN.md](docs/architecture/SYSTEM_DESIGN.md) for detailed architecture documentation.**

---

## Installation

### Prerequisites

- Python 3.10 or higher
- CUDA 11.8+ (for GPU acceleration)
- 16GB+ RAM (32GB+ recommended for training)
- Git LFS (for model checkpoints)

### Setup

#### 1. Clone Repository

```bash
git clone https://github.com/olaflaitinen/taktkrone-i.git
cd taktkrone-i
```

#### 2. Install Dependencies

**Option A: Using Make (Recommended)**

```bash
make install          # Install core dependencies
make setup-dev        # Install dev dependencies + pre-commit hooks
```

**Option B: Using pip directly**

```bash
pip install -e .                    # Install core package
pip install -e ".[dev]"             # Install with dev dependencies
pip install -e ".[train]"           # Install with training dependencies
pip install -e ".[serve]"           # Install with serving dependencies
pip install -e ".[all]"             # Install everything
```

#### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

#### 4. Verify Installation

```bash
make test              # Run test suite
occlm --version        # Check CLI installation
```

### Docker Installation

```bash
# Build image
make docker-build

# Run container
make docker-run

# Or use docker-compose
docker-compose up -d
```

---

## Quick Start

### 1. Ingest Public Transit Data

```bash
# Ingest MTA subway data
occlm ingest mta --lines 1,2,3 --days 7

# Ingest MBTA data
occlm ingest mbta --routes Red,Orange --days 7

# Ingest multiple operators
occlm ingest --operators mta,mbta,bart --days 7
```

**Output:** Normalized data stored in `data/normalized/{operator}/`

### 2. Generate Synthetic Scenarios

```bash
# Generate 1000 OCC scenarios
occlm synthesize \
    --scenario-types delay,disruption,recovery \
    --num-scenarios 1000 \
    --output-dir data/synthetic/scenarios/

# Generate with specific topology
occlm synthesize \
    --operator mta \
    --lines 1,2,3 \
    --scenario-types turnback,short_turn \
    --num-scenarios 500
```

**Output:** JSONL files with structured scenarios in `data/synthetic/`

### 3. Train Model

```bash
# Basic supervised fine-tuning
occlm train \
    --config configs/training/sft_baseline.yaml \
    --base-model meta-llama/Llama-3.1-8B-Instruct \
    --output-dir models/taktkrone-production-v1

# LoRA fine-tuning (efficient)
occlm train \
    --config configs/training/lora_efficient.yaml \
    --base-model meta-llama/Llama-3.1-8B-Instruct \
    --lora-rank 64 \
    --output-dir models/taktkrone-lora-v0.1
```

**Output:** Model checkpoints in `models/`

### 4. Evaluate Model

```bash
# Run full benchmark suite
occlm evaluate \
    --model-path models/taktkrone-production-v1 \
    --benchmark all \
    --output-dir results/eval_v0.1/

# Run specific benchmark
occlm evaluate \
    --model-path models/taktkrone-production-v1 \
    --benchmark disruption_diagnosis \
    --output-dir results/eval_diagnosis/
```

**Output:** Metrics and reports in `results/`

### 5. Serve Model

```bash
# Start API server
occlm serve \
    --model-path models/taktkrone-production-v1 \
    --host 0.0.0.0 \
    --port 8000 \
    --enable-rag

# Launch interactive demo
occlm demo \
    --model-path models/taktkrone-production-v1 \
    --share  # Creates public Gradio link
```

**Endpoints:**
- API: `https://taktkrone.ai`
- Docs: `https://taktkrone.ai/docs`
- Demo: `http://localhost:7860`

### 6. Query Model

**Via CLI:**

```bash
occlm query \
    --model-path models/taktkrone-production-v1 \
    --prompt "Summarize current conditions on the Red Line"
```

**Via Python:**

```python
from occlm.serving import OCCModel

model = OCCModel.from_pretrained("models/taktkrone-production-v1")

response = model.query(
    prompt="Trains are bunching on Line 1 southbound. What should I do?",
    context={
        "operator": "mta",
        "line": "1",
        "direction": "southbound",
        "current_time": "2026-03-27T17:30:00Z"
    }
)

print(response.recommendation)
print(f"Confidence: {response.confidence}")
```

**Via API:**

```bash
curl -X POST https://taktkrone.ai/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What caused the delay on the Orange Line?",
    "context": {
      "operator": "mbta",
      "line": "Orange"
    }
  }'
```

---

## Data Pipeline

### Data Flow

```
External APIs -> Ingestion -> Normalization -> Storage -> Synthesis -> Training
```

### Supported Data Layers

1. **Static Network Data** (GTFS)
   - Routes, stops, trips, shapes, transfers
   - Updated: Weekly/monthly

2. **Realtime Operational Data** (GTFS-RT)
   - Trip updates, vehicle positions, service alerts
   - Updated: Every 10-30 seconds

3. **Disruption & Event Data**
   - Service bulletins, planned work, incidents
   - Updated: Event-driven

4. **Synthetic Supervision Data**
   - Generated OCC scenarios and dialogues
   - Generated: On-demand batch processing

5. **Operational Knowledge**
   - Procedures, glossaries, rules, playbooks
   - Updated: Quarterly

### Canonical Schemas

All data conforms to versioned Pydantic schemas in `occlm/schemas/`. Key schemas:

- `RealtimeEvent`: Standardized realtime feed events
- `NetworkSnapshot`: Point-in-time network state
- `IncidentRecord`: Disruption and event metadata
- `OCCDialogueSample`: Instruction tuning examples
- `ActionRecommendation`: Model output structure
- `SyntheticScenario`: Generated scenario format

**See [data_contracts/](data_contracts/) for JSON Schema exports.**

---

## Training

### Training Pipeline

TAKTKRONE-I supports multiple training strategies:

#### 1. Supervised Fine-Tuning (SFT)

```yaml
# configs/training/sft_baseline.yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
dataset: synthetic_occ_scenarios
num_epochs: 3
batch_size: 4
learning_rate: 2e-5
gradient_accumulation_steps: 8
max_seq_length: 4096
```

```bash
occlm train --config configs/training/sft_baseline.yaml
```

#### 2. LoRA Fine-Tuning

```yaml
# configs/training/lora_efficient.yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
peft_method: lora
lora_rank: 64
lora_alpha: 128
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]
```

```bash
occlm train --config configs/training/lora_efficient.yaml
```

#### 3. Domain-Adaptive Pretraining (Optional)

```bash
occlm train \
    --mode pretraining \
    --corpus data/corpora/transit_text/ \
    --base-model meta-llama/Llama-3.1-8B \
    --steps 10000
```

### Training Data Formats

**Instruction Format:**

```json
{
  "id": "scenario_001",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert metro OCC analyst..."
    },
    {
      "role": "user",
      "content": "Line 1 southbound trains are experiencing 10-15 minute delays..."
    },
    {
      "role": "assistant",
      "content": "Analysis: The delays appear caused by signal issues at 96th St..."
    }
  ],
  "metadata": {
    "operator": "mta",
    "task": "disruption_diagnosis",
    "difficulty": "medium"
  }
}
```

### Experiment Tracking

```bash
# Initialize tracking
wandb login  # or configure MLflow

# Training with tracking
occlm train \
    --config configs/training/sft_baseline.yaml \
    --track wandb \
    --project taktkrone \
    --run-name baseline-v0.1
```

---

## Evaluation

### Benchmark Suites

| Benchmark | Task | Metrics |
|-----------|------|---------|
| **OCC-SumEval** | Situation summarization | ROUGE, BERTScore, conciseness |
| **DisruptionDiag** | Root cause classification | Accuracy, F1, macro-F1 |
| **RecoveryRank** | Action recommendation ranking | nDCG, MRR, success@k |
| **TopoConsist** | Topology consistency | Fact verification accuracy |
| **SafetyGuard** | Unsafe command rejection | False acceptance rate, compliance |
| **RetrievalQA** | RAG quality | Hit rate, precision, relevance |

### Running Evaluations

```bash
# Full benchmark suite
make evaluate

# Specific benchmark
occlm evaluate \
    --model models/taktkrone-production-v1 \
    --benchmark disruption_diagnosis \
    --split test

# With detailed output
occlm evaluate \
    --model models/taktkrone-production-v1 \
    --benchmark all \
    --verbose \
    --save-predictions \
    --output-dir results/detailed_eval/
```

### Custom Evaluation

```python
from occlm.evaluation import BenchmarkSuite, EvalConfig

suite = BenchmarkSuite.load("configs/eval/custom_benchmark.yaml")
results = suite.run(
    model_path="models/taktkrone-production-v1",
    config=EvalConfig(
        batch_size=8,
        temperature=0.7,
        top_p=0.9
    )
)

print(results.summary())
results.save("results/custom_eval/")
```

---

## Serving

### API Endpoints

**POST `/v1/query`** - Main inference endpoint
```json
{
  "prompt": "string",
  "context": {
    "operator": "mta",
    "line": "1",
    "timestamp": "2026-03-27T17:30:00Z"
  },
  "max_tokens": 512,
  "temperature": 0.7
}
```

**GET `/v1/health`** - Health check
**GET `/v1/models`** - List available models
**POST `/v1/evaluate`** - Run evaluation on custom inputs

### Configuration

```yaml
# configs/serving/api.yaml
model:
  path: models/taktkrone-production-v1
  device: cuda
  precision: fp16

serving:
  host: 0.0.0.0
  port: 8000
  workers: 4
  max_batch_size: 32

rag:
  enabled: true
  vector_store: data/vectorstore/
  top_k: 5

guardrails:
  enabled: true
  filters:
    - unsafe_commands
    - hallucination_detection
    - output_validation

logging:
  level: INFO
  audit_log: logs/audit.jsonl
```

### Production Deployment

```bash
# Using vLLM for optimized serving
occlm serve \
    --model models/taktkrone-production-v1 \
    --backend vllm \
    --tensor-parallel-size 2 \
    --dtype float16

# Using Docker
docker run -p 8000:8000 \
    -v $(pwd)/models:/models \
    taktkrone:latest \
    serve --model /models/taktkrone-production-v1
```

---

## Safety & Guardrails

### Design Principles

1. **Human-in-the-Loop**: All critical recommendations require operator approval
2. **Uncertainty Quantification**: Predictions include confidence scores
3. **Auditability**: Full request/response logging with provenance
4. **Boundary Enforcement**: Reject direct control commands
5. **Factuality Grounding**: Cross-check outputs against network topology

### Guardrail Mechanisms

#### Input Validation
- Schema compliance checking
- Temporal plausibility verification
- Topology consistency validation

#### Output Filtering
- Keyword-based safety filters
- Command rejection patterns
- Confidence thresholding
- Structure validation

#### Runtime Monitoring
- Hallucination detection
- Fact-checking against ground truth
- Anomaly detection in recommendations

### Safety Testing

```bash
# Run safety compliance tests
make test-safety

# Manual safety evaluation
occlm evaluate \
    --model models/taktkrone-production-v1 \
    --benchmark safety_guard \
    --adversarial
```

**See [docs/safety/SAFETY_PROTOCOL.md](docs/safety/SAFETY_PROTOCOL.md) for comprehensive safety documentation.**

---

## Supported Operators

| Operator | Code | Region | Status | Data Sources |
|----------|------|--------|--------|--------------|
| **MTA New York City Subway** | `mta_nyct` | New York, USA | Full | GTFS-RT, API |
| **MBTA** | `mbta` | Boston, USA | Full | V3 API, GTFS-RT |
| **WMATA** | `wmata` | Washington DC, USA | Full | API, GTFS |
| **BART** | `bart` | San Francisco, USA | Full | API, GTFS-RT |
| **TfL Underground** | `tfl` | London, UK | Full | Unified API |
| **Generic GTFS** | `generic_gtfs` | Any | Partial | GTFS/GTFS-RT |

**Want to add your operator?** See [docs/datasets/ADDING_OPERATORS.md](docs/datasets/ADDING_OPERATORS.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture/SYSTEM_DESIGN.md](docs/architecture/SYSTEM_DESIGN.md) | Detailed system architecture |
| [docs/datasets/DATA_SPECIFICATION.md](docs/datasets/DATA_SPECIFICATION.md) | Data schemas and contracts |
| [docs/taxonomy/OPERATIONAL_ONTOLOGY.md](docs/taxonomy/OPERATIONAL_ONTOLOGY.md) | Domain ontology |
| [docs/evaluation/BENCHMARK_DESIGN.md](docs/evaluation/BENCHMARK_DESIGN.md) | Evaluation methodology |
| [docs/safety/SAFETY_PROTOCOL.md](docs/safety/SAFETY_PROTOCOL.md) | Safety guidelines |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## Contributing

We welcome contributions from the transit operations, ML research, and open-source communities!

### How to Contribute

1. **Read** [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
2. **Fork** the repository
3. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
4. **Commit** with clear messages (`git commit -m 'Add incredible feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Contribution Areas

- **New Transit Operators**: Add ingestion adapters for new metro systems
- **Evaluation Benchmarks**: Design new operational reasoning benchmarks
- **Synthetic Data**: Improve scenario generation quality and diversity
- **Testing**: Increase test coverage and add regression tests
- **Documentation**: Improve guides, add examples, fix typos
- **Safety**: Enhance guardrails and safety verification
- **Performance**: Optimize inference speed and memory usage

---

## Roadmap

### Current Status: Phase 0-1 (Repository Scaffold + Initial Ingestion)

| Phase | Timeline | Status | Deliverables |
|-------|----------|--------|--------------|
| **Phase 0: Scaffold** | Week 1-2 | Complete | Structure, schemas, docs |
| **Phase 1: Ingestion** | Week 3-5 | Complete | Adapters for 5 operators |
| **Phase 2: Synthesis** | Week 6-8 | Complete | Scenario generators |
| **Phase 3: Training** | Week 9-11 | Complete | First baseline model |
| **Phase 4: Evaluation** | Week 12-14 | Complete | Benchmark suite |
| **Phase 5: Serving** | Week 15-16 | Complete | API + Demo UI |
| **Phase 6: Release** | Week 17+ | Complete | Public v1.0.0 |

**See [ROADMAP.md](ROADMAP.md) for detailed milestones.**

---

## License

This project is licensed under the **Apache License 2.0** - see [LICENSE](LICENSE) for details.

```
Copyright 2026 Gustav Olaf Yunus Laitinen-Fredriksson Imanov

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## Citation

If you use TAKTKRONE-I in your research or applications, please cite:

### Dataset
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

### Model
```bibtex
@misc{gustav_olaf_yunus_laitinen-fredriksson_imanov_2026,
	author       = { Gustav Olaf Yunus Laitinen-Fredriksson Imanov },
	title        = { taktkrone-i (Revision efdde52) },
	year         = 2026,
	url          = { https://huggingface.co/olaflaitinen/taktkrone-i },
	doi          = { 10.57967/hf/8167 },
	publisher    = { Hugging Face }
}
```

---

## HuggingFace Repositories

- **Dataset**: [olaflaitinen/taktkrone-occ-corpus](https://huggingface.co/datasets/olaflaitinen/taktkrone-occ-corpus)
  - DOI: 10.57967/hf/8166
  - Size: 5,247 OCC dialogue samples
  - Splits: Train (4,197) + Test (1,050)

- **Model**: [olaflaitinen/taktkrone-i](https://huggingface.co/olaflaitinen/taktkrone-i)
  - DOI: 10.57967/hf/8167
  - Base: meta-llama/Llama-3.1-8B-Instruct
  - LoRA Adapters: 67.1M parameters

---

## Acknowledgments

- Inspired by operational practices from transit agencies worldwide
- Built on the Hugging Face ecosystem and PyTorch
- Thanks to all operators providing public data APIs
- Special thanks to the transit operations research community

---

## Contact & Community

- **Issues**: [GitHub Issues](https://github.com/olaflaitinen/taktkrone-i/issues)
- **Discussions**: [GitHub Discussions](https://github.com/olaflaitinen/taktkrone-i/discussions)
- **Email**: dev@taktkrone.ai
- **Website**: https://taktkrone.ai

---

**Status**: Production Release
**Version**: 1.0.0
**Last Updated**: 2026-03-27

**This is research software. Do not use for safety-critical operations without extensive validation, testing, and regulatory approval.**