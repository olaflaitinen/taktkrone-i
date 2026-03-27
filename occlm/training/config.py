"""
TAKTKRONE-I Training Configuration.

Defines configuration classes for model training using Pydantic.
"""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TrainingMethod(str, Enum):
    """Supported training methods"""
    FULL_FINETUNE = "full_finetune"
    LORA = "lora"
    QLORA = "qlora"
    PREFIX_TUNING = "prefix_tuning"
    PROMPT_TUNING = "prompt_tuning"


class Optimizer(str, Enum):
    """Supported optimizers"""
    ADAMW = "adamw"
    ADAMW_8BIT = "adamw_8bit"
    SGD = "sgd"
    ADAFACTOR = "adafactor"


class LRScheduler(str, Enum):
    """Learning rate scheduler types"""
    LINEAR = "linear"
    COSINE = "cosine"
    CONSTANT = "constant"
    CONSTANT_WITH_WARMUP = "constant_with_warmup"


class LoRAConfig(BaseModel):
    """LoRA adapter configuration"""

    r: int = Field(default=64, ge=1, le=256, description="LoRA rank")
    lora_alpha: int = Field(default=128, ge=1, description="LoRA alpha scaling")
    lora_dropout: float = Field(default=0.05, ge=0.0, le=1.0)
    target_modules: list[str] = Field(
        default=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        description="Modules to apply LoRA"
    )
    bias: Literal["none", "all", "lora_only"] = "none"
    task_type: Literal["CAUSAL_LM", "SEQ_2_SEQ_LM"] = "CAUSAL_LM"
    modules_to_save: list[str] | None = None

    def to_peft_config(self):
        """Convert to PEFT LoraConfig"""
        from peft import LoraConfig as PeftLoraConfig
        from peft import TaskType

        task_type_map = {
            "CAUSAL_LM": TaskType.CAUSAL_LM,
            "SEQ_2_SEQ_LM": TaskType.SEQ_2_SEQ_LM,
        }

        return PeftLoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            bias=self.bias,
            task_type=task_type_map[self.task_type],
            modules_to_save=self.modules_to_save,
        )


class QuantizationConfig(BaseModel):
    """Quantization configuration for QLoRA"""

    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: Literal["float16", "bfloat16", "float32"] = "bfloat16"
    bnb_4bit_quant_type: Literal["nf4", "fp4"] = "nf4"
    bnb_4bit_use_double_quant: bool = True

    def to_bnb_config(self):
        """Convert to BitsAndBytesConfig"""
        import torch
        from transformers import BitsAndBytesConfig

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }

        return BitsAndBytesConfig(
            load_in_4bit=self.load_in_4bit,
            load_in_8bit=self.load_in_8bit,
            bnb_4bit_compute_dtype=dtype_map[self.bnb_4bit_compute_dtype],
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
        )


class HyperparametersConfig(BaseModel):
    """Training hyperparameters"""

    learning_rate: float = Field(default=2e-4, gt=0, le=1.0)
    num_epochs: int = Field(default=3, ge=1, le=100)
    batch_size: int = Field(default=4, ge=1)
    gradient_accumulation_steps: int = Field(default=8, ge=1)
    warmup_ratio: float = Field(default=0.1, ge=0.0, le=1.0)
    weight_decay: float = Field(default=0.01, ge=0.0)
    max_grad_norm: float = Field(default=1.0, gt=0.0)
    optimizer: Optimizer = Optimizer.ADAMW_8BIT
    lr_scheduler_type: LRScheduler = LRScheduler.COSINE
    max_seq_length: int = Field(default=4096, ge=128, le=131072)

    # Evaluation settings
    eval_steps: int = Field(default=500, ge=1)
    save_steps: int = Field(default=500, ge=1)
    logging_steps: int = Field(default=10, ge=1)
    eval_strategy: Literal["steps", "epoch", "no"] = "steps"
    save_strategy: Literal["steps", "epoch", "no"] = "steps"
    save_total_limit: int = Field(default=3, ge=1)

    # Performance
    fp16: bool = False
    bf16: bool = True
    gradient_checkpointing: bool = True

    @property
    def effective_batch_size(self) -> int:
        """Calculate effective batch size"""
        return self.batch_size * self.gradient_accumulation_steps


class DatasetConfig(BaseModel):
    """Dataset configuration"""

    train_path: str = Field(description="Path to training data")
    eval_path: str | None = Field(default=None, description="Path to validation data")
    test_path: str | None = Field(default=None, description="Path to test data")

    dataset_version: str = "0.1.0"
    chat_template: str = "chatml"
    add_eos: bool = True
    packing: bool = True
    shuffle: bool = True
    seed: int = 42

    # Preprocessing
    max_samples: int | None = None
    filter_by_operator: list[str] | None = None
    filter_by_task_type: list[str] | None = None


class ModelConfig(BaseModel):
    """Model configuration"""

    model_id: str = Field(description="Hugging Face model ID or local path")
    model_type: Literal["pretrained", "checkpoint", "finetuned"] = "pretrained"
    revision: str | None = None
    trust_remote_code: bool = False
    torch_dtype: Literal["auto", "float16", "bfloat16", "float32"] = "auto"


class TrainingConfig(BaseModel):
    """Complete training configuration"""

    # Experiment metadata
    experiment_id: str
    experiment_name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Core configuration
    method: TrainingMethod = TrainingMethod.LORA
    model: ModelConfig
    hyperparameters: HyperparametersConfig = Field(default_factory=HyperparametersConfig)
    dataset: DatasetConfig

    # Optional method-specific configs
    lora: LoRAConfig | None = None
    quantization: QuantizationConfig | None = None

    # Output paths
    output_dir: str = "models/experiments"
    logging_dir: str | None = None

    # Tracking
    use_wandb: bool = False
    wandb_project: str = "taktkrone-i"
    use_mlflow: bool = False
    mlflow_experiment: str = "taktkrone-training"

    # Reproducibility
    seed: int = 42

    @field_validator("lora", mode="before")
    @classmethod
    def set_lora_defaults(cls, v, info):
        """Set LoRA config defaults if method requires it"""
        if info.data.get("method") in [TrainingMethod.LORA, TrainingMethod.QLORA]:
            if v is None:
                return LoRAConfig()
        return v

    @field_validator("quantization", mode="before")
    @classmethod
    def set_quant_defaults(cls, v, info):
        """Set quantization config defaults for QLoRA"""
        if info.data.get("method") == TrainingMethod.QLORA:
            if v is None:
                return QuantizationConfig()
        return v

    @property
    def experiment_output_dir(self) -> Path:
        """Get experiment-specific output directory"""
        return Path(self.output_dir) / self.experiment_id

    def to_training_arguments(self):
        """Convert to Hugging Face TrainingArguments"""
        from transformers import TrainingArguments

        hp = self.hyperparameters

        return TrainingArguments(
            output_dir=str(self.experiment_output_dir),
            num_train_epochs=hp.num_epochs,
            per_device_train_batch_size=hp.batch_size,
            per_device_eval_batch_size=hp.batch_size,
            gradient_accumulation_steps=hp.gradient_accumulation_steps,
            learning_rate=hp.learning_rate,
            weight_decay=hp.weight_decay,
            warmup_ratio=hp.warmup_ratio,
            max_grad_norm=hp.max_grad_norm,
            lr_scheduler_type=hp.lr_scheduler_type.value,
            evaluation_strategy=hp.eval_strategy,
            eval_steps=hp.eval_steps if hp.eval_strategy == "steps" else None,
            save_strategy=hp.save_strategy,
            save_steps=hp.save_steps if hp.save_strategy == "steps" else None,
            save_total_limit=hp.save_total_limit,
            logging_steps=hp.logging_steps,
            logging_dir=self.logging_dir or str(self.experiment_output_dir / "logs"),
            fp16=hp.fp16,
            bf16=hp.bf16,
            gradient_checkpointing=hp.gradient_checkpointing,
            seed=self.seed,
            report_to=self._get_report_to(),
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
        )

    def _get_report_to(self) -> list[str]:
        """Get reporting backends"""
        backends = ["tensorboard"]
        if self.use_wandb:
            backends.append("wandb")
        if self.use_mlflow:
            backends.append("mlflow")
        return backends


def load_config(config_path: str | Path) -> TrainingConfig:
    """Load training configuration from YAML file"""
    import yaml

    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    return TrainingConfig(**config_dict)


def save_config(config: TrainingConfig, output_path: str | Path) -> None:
    """Save training configuration to YAML file"""
    import yaml

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)
