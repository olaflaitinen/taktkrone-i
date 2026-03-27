"""
TAKTKRONE-I LoRA Parameter-Efficient Fine-Tuning.

Implements LoRA and QLoRA training using PEFT library for
memory-efficient fine-tuning.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

try:
    import torch
except ImportError:
    torch = None

try:
    from peft import LoraConfig, get_peft_model
    from peft import TaskType
except ImportError:
    LoraConfig = None
    get_peft_model = None
    TaskType = None

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
        Trainer,
    )
except ImportError:
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None
    TrainingArguments = None
    Trainer = None

from .config import TrainingConfig, QuantizationConfig, LoRAConfig

logger = logging.getLogger(__name__)


class LoRATrainer:
    """Parameter-efficient fine-tuning with LoRA/QLoRA."""

    def __init__(
        self,
        config: TrainingConfig,
        device: Optional[str] = None,
    ):
        """
        Initialize LoRA trainer.

        Args:
            config: Training configuration with LoRA settings
            device: Device to use ('cuda', 'cpu', or None for auto)

        Raises:
            ImportError: If PEFT or transformers not available
            ValueError: If config doesn't use LoRA method
        """
        if LoraConfig is None:
            raise ImportError(
                "peft library required: pip install peft"
            )

        if config.lora is None:
            raise ValueError(
                "LoRA config required for LoRA training"
            )

        self.config = config
        self.device = device or (
            "cuda" if torch and torch.cuda.is_available() else "cpu"
        )
        logger.info(f"Using device: {self.device}")

        self.model = None
        self.tokenizer = None
        self.trainer = None

        # Track adapter status
        self.is_merged = False
        self.adapter_path = None

    def load_model_and_tokenizer(self) -> None:
        """Load base model and tokenizer."""
        logger.info(f"Loading base model: {self.config.model.model_id}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model.model_id,
            trust_remote_code=self.config.model.trust_remote_code,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Setup quantization if using QLoRA
        quantization_config = None
        if self.config.method.value == "qlora":
            quantization_config = self._get_bnb_config()

        # Load model
        load_kwargs = {
            "trust_remote_code": (
                self.config.model.trust_remote_code
            ),
            "device_map": self.device,
        }

        if quantization_config:
            load_kwargs["quantization_config"] = (
                quantization_config
            )
        else:
            load_kwargs["torch_dtype"] = (
                self._get_torch_dtype()
            )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model.model_id,
            **load_kwargs
        )

        logger.info(f"Model loaded: {self.model.__class__.__name__}")

        # Apply LoRA
        self._apply_lora()

    def _get_torch_dtype(self) -> Any:
        """Get torch dtype from config."""
        if torch is None:
            return None

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
            "auto": "auto",
        }
        return dtype_map.get(
            self.config.model.torch_dtype,
            "auto"
        )

    def _get_bnb_config(self) -> Any:
        """Get BitsAndBytes configuration for quantization."""
        if BitsAndBytesConfig is None:
            raise ImportError(
                "transformers[bitsandbytes] required "
                "for QLoRA"
            )

        if self.config.quantization is None:
            logger.warning(
                "Using default QLoRA quantization config"
            )
            self.config.quantization = QuantizationConfig()

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }

        compute_dtype = dtype_map.get(
            self.config.quantization.bnb_4bit_compute_dtype,
            torch.bfloat16,
        )

        return BitsAndBytesConfig(
            load_in_4bit=(
                self.config.quantization.load_in_4bit
            ),
            load_in_8bit=(
                self.config.quantization.load_in_8bit
            ),
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_quant_type=(
                self.config.quantization.bnb_4bit_quant_type
            ),
            bnb_4bit_use_double_quant=(
                self.config.quantization.bnb_4bit_use_double_quant
            ),
        )

    def _apply_lora(self) -> None:
        """Apply LoRA adapters to model."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        logger.info("Applying LoRA adapters...")

        lora_config = self.config.lora.to_peft_config()
        self.model = get_peft_model(self.model, lora_config)

        # Log trainable parameters
        trainable_params = sum(
            p.numel() for p in self.model.parameters()
            if p.requires_grad
        )
        total_params = sum(
            p.numel() for p in self.model.parameters()
        )
        trainable_pct = (
            100 * trainable_params / total_params
            if total_params > 0 else 0
        )

        logger.info(
            f"Trainable parameters: {trainable_params:,} / "
            f"{total_params:,} ({trainable_pct:.2f}%)"
        )
        self.model.print_trainable_parameters()

    def train(
        self,
        train_dataset: Any,
        eval_dataset: Optional[Any] = None,
        data_collator: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute LoRA training.

        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
            data_collator: Custom data collator

        Returns:
            Dict with training metrics
        """
        if self.model is None:
            self.load_model_and_tokenizer()

        logger.info("Starting LoRA training...")

        # Get training arguments
        training_args = (
            self.config.to_training_arguments()
        )

        # Create trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        # Train
        train_result = self.trainer.train()

        logger.info(f"LoRA training completed")
        logger.info(
            f"Final train loss: {train_result.training_loss:.4f}"
        )

        return train_result.metrics

    def save_lora_adapters(
        self,
        path: Union[str, Path],
        include_config: bool = True,
    ) -> None:
        """
        Save LoRA adapter weights.

        Args:
            path: Directory to save adapters
            include_config: Whether to save training config

        Raises:
            RuntimeError: If model not loaded or merged
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        if self.is_merged:
            logger.warning(
                "Model is merged. Saving full model instead "
                "of adapters."
            )

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving LoRA adapters to {path}")

        # Save adapters
        self.model.save_pretrained(str(path))

        # Save config
        if include_config:
            config_dict = {
                "lora_config": (
                    self.config.lora.model_dump()
                ),
                "model_id": (
                    self.config.model.model_id
                ),
                "training_method": (
                    self.config.method.value
                ),
            }
            with open(path / "adapter_config.json", "w") as f:
                json.dump(config_dict, f, indent=2)

        self.adapter_path = path
        logger.info(f"Adapters saved to {path}")

    def load_lora_adapters(
        self,
        model: Optional[Any] = None,
        path: Optional[Union[str, Path]] = None,
    ) -> Any:
        """
        Load LoRA adapters onto model.

        Args:
            model: Model to load adapters onto (uses self.model if None)
            path: Path to adapter checkpoint

        Returns:
            Model with loaded adapters
        """
        if path is None:
            path = self.adapter_path

        if path is None:
            raise ValueError(
                "path must be provided or adapters must be saved"
            )

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Adapter checkpoint not found: {path}"
            )

        if model is None:
            model = self.model

        logger.info(f"Loading LoRA adapters from {path}")

        # Load adapters using PeftModel
        from peft import PeftModel

        model_with_adapters = PeftModel.from_pretrained(
            model,
            str(path),
        )

        logger.info(
            "LoRA adapters loaded successfully"
        )
        return model_with_adapters

    def merge_lora_weights(self) -> Any:
        """
        Merge LoRA weights into base model.

        Returns:
            Model with merged weights

        Raises:
            RuntimeError: If model not loaded or already merged
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        if self.is_merged:
            logger.warning("Model already merged")
            return self.model

        logger.info("Merging LoRA weights into base model...")

        merged_model = self.model.merge_and_unload()
        self.is_merged = True

        logger.info("LoRA weights merged successfully")
        return merged_model

    def save_merged_model(
        self,
        path: Union[str, Path],
    ) -> None:
        """
        Save merged model.

        Args:
            path: Directory to save merged model

        Raises:
            RuntimeError: If model not loaded or not merged
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        if not self.is_merged:
            logger.info(
                "Merging model before saving..."
            )
            self.merge_lora_weights()

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving merged model to {path}")

        self.model.save_pretrained(str(path))
        if self.tokenizer:
            self.tokenizer.save_pretrained(str(path))

        logger.info(f"Merged model saved to {path}")

    def get_trainable_parameters_count(self) -> Dict[
        str, int
    ]:
        """Get count of trainable and total parameters."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        trainable_params = sum(
            p.numel()
            for p in self.model.parameters()
            if p.requires_grad
        )
        total_params = sum(
            p.numel() for p in self.model.parameters()
        )

        return {
            "trainable": trainable_params,
            "total": total_params,
            "trainable_pct": (
                100 * trainable_params / total_params
                if total_params > 0 else 0
            ),
        }

    def create_adapter_summary(self) -> Dict[str, Any]:
        """
        Create summary of LoRA adapter configuration.

        Returns:
            Dict with adapter configuration summary
        """
        summary = {
            "training_method": (
                self.config.method.value
            ),
            "is_merged": self.is_merged,
            "adapter_path": str(self.adapter_path)
            if self.adapter_path else None,
        }

        if self.config.lora:
            lora_config = self.config.lora
            summary["lora_rank"] = lora_config.r
            summary["lora_alpha"] = (
                lora_config.lora_alpha
            )
            summary["lora_dropout"] = (
                lora_config.lora_dropout
            )
            summary["target_modules"] = (
                lora_config.target_modules
            )

        if self.config.method.value == "qlora":
            summary["quantization_enabled"] = True
            if self.config.quantization:
                quant_config = self.config.quantization
                summary[
                    "quantization_dtype"
                ] = (
                    quant_config.bnb_4bit_compute_dtype
                )
                summary[
                    "quantization_type"
                ] = (
                    quant_config.bnb_4bit_quant_type
                )
        else:
            summary["quantization_enabled"] = False

        return summary

    def inspect_adapter_weights(
        self,
    ) -> Dict[str, Any]:
        """
        Inspect LoRA adapter weights for debugging.

        Returns:
            Dict with adapter weight statistics

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        inspector = {
            "total_modules": 0,
            "lora_modules": 0,
            "module_statistics": {},
        }

        for name, module in self.model.named_modules():
            if hasattr(module, "lora_A"):
                inspector["lora_modules"] += 1
                inspector["module_statistics"][name] = {
                    "lora_A_shape": (
                        module.lora_A[0].weight.shape
                    ),
                    "lora_B_shape": (
                        module.lora_B[0].weight.shape
                    ),
                }

        inspector["total_modules"] = (
            len(list(self.model.named_modules()))
        )

        return inspector

    def estimate_memory_usage(self) -> Dict[str, float]:
        """
        Estimate memory usage during training.

        Returns:
            Dict with memory estimates in GB

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        if torch is None:
            return {"error": "torch not available"}

        estimates = {}

        # Model weights
        model_params = sum(
            p.numel() for p in self.model.parameters()
        )
        model_size_gb = (model_params * 4) / (
            1024 ** 3
        )  # Assuming float32
        estimates["model_weights_gb"] = (
            model_size_gb
        )

        # Gradient storage (same as weights for training)
        estimates["gradients_gb"] = model_size_gb

        # Optimizer states (varies by optimizer)
        estimates["optimizer_states_gb"] = (
            model_size_gb * 2
        )  # Conservative estimate

        # LoRA adapters
        trainable_params = sum(
            p.numel()
            for p in self.model.parameters()
            if p.requires_grad
        )
        adapter_size_gb = (trainable_params * 4) / (
            1024 ** 3
        )
        estimates["lora_adapters_gb"] = (
            adapter_size_gb
        )

        # Batch size memory (rough estimate)
        batch_memory_gb = 0.1  # Placeholder
        estimates["estimated_batch_gb"] = (
            batch_memory_gb
        )

        # Total
        estimates["total_estimated_gb"] = sum(
            [
                v for k, v in estimates.items()
                if k != "total_estimated_gb"
                and isinstance(v, (int, float))
            ]
        )

        return estimates

    def validate_trainer_setup(self) -> Dict[
        str, Any
    ]:
        """
        Validate trainer configuration before training.

        Returns:
            Dict with validation results
        """
        validation = {
            "model_loaded": self.model is not None,
            "tokenizer_loaded": (
                self.tokenizer is not None
            ),
            "config_valid": True,
        }

        if self.model and self.tokenizer:
            validation["model_dtype"] = str(
                self.model.dtype
            )
            validation[
                "model_device"
            ] = str(
                next(self.model.parameters()).device
            )

        # Check LoRA configuration
        if self.config.lora:
            validation[
                "lora_config_valid"
            ] = True
            validation[
                "lora_modules"
            ] = (
                len(self.config.lora.target_modules)
            )

        # Check hyperparameters
        hp = self.config.hyperparameters
        validation["batch_size"] = hp.batch_size
        validation[
            "learning_rate"
        ] = hp.learning_rate
        validation[
            "num_epochs"
        ] = hp.num_epochs
        validation[
            "effective_batch_size"
        ] = hp.effective_batch_size

        return validation


__all__ = [
    "LoRATrainer",
]
