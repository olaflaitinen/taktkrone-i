"""
TAKTKRONE-I Training Module.

Provides model training infrastructure including:
- LoRA and QLoRA fine-tuning
- Full fine-tuning
- Training configuration management
- Dataset loading and preprocessing
- Experiment tracking
"""

from .config import (
    DatasetConfig,
    HyperparametersConfig,
    LoRAConfig,
    LRScheduler,
    ModelConfig,
    Optimizer,
    QuantizationConfig,
    TrainingConfig,
    TrainingMethod,
    load_config,
    save_config,
)
from .data import (
    DataCollatorForOCC,
    create_train_test_split,
    format_occ_messages,
    get_dataset_statistics,
    get_default_system_prompt,
    load_jsonl_dataset,
    load_occ_dataset,
    preprocess_for_training,
)
from .trainer import (
    ExperimentTrackingCallback,
    OCCTrainer,
    train_model,
)

__all__ = [
    # Config classes
    "TrainingConfig",
    "TrainingMethod",
    "ModelConfig",
    "HyperparametersConfig",
    "DatasetConfig",
    "LoRAConfig",
    "QuantizationConfig",
    "Optimizer",
    "LRScheduler",
    # Config functions
    "load_config",
    "save_config",
    # Data loading
    "load_occ_dataset",
    "load_jsonl_dataset",
    "preprocess_for_training",
    "format_occ_messages",
    "get_default_system_prompt",
    "create_train_test_split",
    "get_dataset_statistics",
    "DataCollatorForOCC",
    # Training
    "OCCTrainer",
    "train_model",
    "ExperimentTrackingCallback",
]
