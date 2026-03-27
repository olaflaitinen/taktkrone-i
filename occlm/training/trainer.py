"""
TAKTKRONE-I Model Trainer.

Main training logic using TRL SFTTrainer with LoRA/QLoRA support.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    TrainerCallback,
)

from .config import TrainingConfig, TrainingMethod, load_config
from .data import (
    get_dataset_statistics,
    load_occ_dataset,
    preprocess_for_training,
)

logger = logging.getLogger(__name__)


class OCCTrainer:
    """
    TAKTKRONE-I Model Trainer.

    Handles model loading, training, and checkpoint management.
    Supports LoRA, QLoRA, and full fine-tuning methods.
    """

    def __init__(
        self,
        config: TrainingConfig | str | Path,
        resume_from_checkpoint: str | None = None,
    ):
        """
        Initialize trainer.

        Args:
            config: Training configuration or path to config file
            resume_from_checkpoint: Path to checkpoint to resume from
        """
        if isinstance(config, (str, Path)):
            config = load_config(config)

        self.config = config
        self.resume_from_checkpoint = resume_from_checkpoint

        # Initialize state
        self.model: PreTrainedModel | None = None
        self.tokenizer: PreTrainedTokenizer | None = None
        self.trainer = None
        self.experiment_dir = config.experiment_output_dir

        # Create experiment directory
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        # Save config snapshot
        self._save_config_snapshot()

        # Setup logging
        self._setup_logging()

    def _save_config_snapshot(self) -> None:
        """Save configuration snapshot for reproducibility"""
        config_path = self.experiment_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(self.config.model_dump(), f, indent=2, default=str)

    def _setup_logging(self) -> None:
        """Setup logging for training"""
        log_path = self.experiment_dir / "training.log"
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def load_model_and_tokenizer(self) -> None:
        """Load base model and tokenizer"""
        logger.info(f"Loading model: {self.config.model.model_id}")

        model_kwargs = {
            "trust_remote_code": self.config.model.trust_remote_code,
        }

        # Handle dtype
        if self.config.model.torch_dtype != "auto":
            dtype_map = {
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
                "float32": torch.float32,
            }
            model_kwargs["torch_dtype"] = dtype_map[self.config.model.torch_dtype]

        # Handle quantization for QLoRA
        if self.config.method == TrainingMethod.QLORA:
            if self.config.quantization:
                model_kwargs["quantization_config"] = \
                    self.config.quantization.to_bnb_config()
            model_kwargs["device_map"] = "auto"

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model.model_id,
            revision=self.config.model.revision,
            **model_kwargs
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model.model_id,
            revision=self.config.model.revision,
            trust_remote_code=self.config.model.trust_remote_code,
        )

        # Ensure pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Apply LoRA if configured
        if self.config.method in [TrainingMethod.LORA, TrainingMethod.QLORA]:
            self._apply_lora()

        # Enable gradient checkpointing if configured
        if self.config.hyperparameters.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()

        logger.info(f"Model loaded: {self.model.__class__.__name__}")
        logger.info(f"Trainable parameters: {self._count_trainable_params()}")

    def _apply_lora(self) -> None:
        """Apply LoRA adapters to model"""
        from peft import get_peft_model, prepare_model_for_kbit_training

        logger.info("Applying LoRA adapters")

        # Prepare for k-bit training if quantized
        if self.config.method == TrainingMethod.QLORA:
            self.model = prepare_model_for_kbit_training(self.model)

        # Apply LoRA
        if self.config.lora:
            peft_config = self.config.lora.to_peft_config()
            self.model = get_peft_model(self.model, peft_config)

            # Print trainable parameters
            self.model.print_trainable_parameters()

    def _count_trainable_params(self) -> str:
        """Count and format trainable parameters"""
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        return f"{trainable:,} / {total:,} ({100 * trainable / total:.2f}%)"

    def load_datasets(self) -> DatasetDict:
        """Load and preprocess training datasets"""
        logger.info("Loading datasets")

        # Load raw datasets
        datasets = load_occ_dataset(self.config.dataset, self.tokenizer)

        # Log statistics
        for split, ds in datasets.items():
            stats = get_dataset_statistics(ds)
            logger.info(f"Dataset {split}: {stats['num_samples']} samples")

        # Preprocess for training
        processed = {}
        for split, ds in datasets.items():
            processed[split] = preprocess_for_training(
                ds, self.tokenizer, self.config.dataset
            )

        return DatasetDict(processed)

    def setup_trainer(self, datasets: DatasetDict) -> None:
        """Setup TRL SFTTrainer"""
        from trl import SFTConfig, SFTTrainer

        logger.info("Setting up trainer")

        # Get training arguments
        training_args = self.config.to_training_arguments()

        # Create SFT config
        sft_config = SFTConfig(
            **training_args.to_dict(),
            max_seq_length=self.config.hyperparameters.max_seq_length,
            packing=self.config.dataset.packing,
            dataset_text_field="text",
        )

        # Create callbacks
        callbacks = self._create_callbacks()

        # Create trainer
        self.trainer = SFTTrainer(
            model=self.model,
            args=sft_config,
            train_dataset=datasets["train"],
            eval_dataset=datasets.get("validation"),
            tokenizer=self.tokenizer,
            callbacks=callbacks,
        )

    def _create_callbacks(self) -> list:
        """Create training callbacks"""
        callbacks = []

        # Add experiment tracking callback
        callbacks.append(ExperimentTrackingCallback(self.config))

        # Add early stopping if eval dataset exists
        if self.config.dataset.eval_path:
            from transformers import EarlyStoppingCallback
            callbacks.append(
                EarlyStoppingCallback(early_stopping_patience=3)
            )

        return callbacks

    def train(self) -> dict[str, Any]:
        """
        Run training.

        Returns:
            Training metrics
        """
        if self.model is None:
            self.load_model_and_tokenizer()

        datasets = self.load_datasets()
        self.setup_trainer(datasets)

        logger.info("Starting training")
        start_time = datetime.now()

        # Train
        train_result = self.trainer.train(
            resume_from_checkpoint=self.resume_from_checkpoint
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Log results
        metrics = train_result.metrics
        metrics["training_duration_seconds"] = duration

        logger.info(f"Training completed in {duration:.2f} seconds")
        logger.info(f"Final train loss: {metrics.get('train_loss', 'N/A')}")

        # Save final model
        self._save_model()

        # Save metrics
        self._save_metrics(metrics)

        return metrics

    def _save_model(self) -> None:
        """Save trained model and adapter"""
        logger.info("Saving model")

        # Save adapter if using LoRA
        if self.config.method in [TrainingMethod.LORA, TrainingMethod.QLORA]:
            adapter_path = self.experiment_dir / "adapter"
            self.model.save_pretrained(adapter_path)
            logger.info(f"Adapter saved to: {adapter_path}")
        else:
            # Save full model
            model_path = self.experiment_dir / "model"
            self.model.save_pretrained(model_path)
            logger.info(f"Model saved to: {model_path}")

        # Save tokenizer
        tokenizer_path = self.experiment_dir / "tokenizer"
        self.tokenizer.save_pretrained(tokenizer_path)

    def _save_metrics(self, metrics: dict[str, Any]) -> None:
        """Save training metrics"""
        metrics_path = self.experiment_dir / "training_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2, default=str)

    def evaluate(self, dataset: Dataset | None = None) -> dict[str, float]:
        """
        Evaluate model on dataset.

        Args:
            dataset: Dataset to evaluate on (uses eval dataset if None)

        Returns:
            Evaluation metrics
        """
        if self.trainer is None:
            raise RuntimeError("Trainer not initialized. Call train() first.")

        logger.info("Running evaluation")
        metrics = self.trainer.evaluate(eval_dataset=dataset)

        logger.info(f"Eval loss: {metrics.get('eval_loss', 'N/A')}")
        return metrics

    def merge_and_save(self, output_path: str | Path) -> None:
        """
        Merge LoRA adapter with base model and save.

        Args:
            output_path: Path to save merged model
        """
        if self.config.method not in [TrainingMethod.LORA, TrainingMethod.QLORA]:
            logger.warning("merge_and_save only applicable for LoRA models")
            return

        logger.info("Merging adapter with base model")

        # Merge adapter
        merged_model = self.model.merge_and_unload()

        # Save merged model
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        logger.info(f"Merged model saved to: {output_path}")


class ExperimentTrackingCallback(TrainerCallback):
    """Callback for experiment tracking"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.start_time: datetime | None = None

    def on_train_begin(self, args, state, control, **kwargs):
        """Called at start of training"""
        self.start_time = datetime.now()
        logger.info(f"Training started: {self.config.experiment_name}")

    def on_train_end(self, args, state, control, **kwargs):
        """Called at end of training"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info(f"Training ended. Duration: {duration}")

    def on_save(self, args, state, control, **kwargs):
        """Called when checkpoint is saved"""
        logger.info(f"Checkpoint saved at step {state.global_step}")

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        """Called after evaluation"""
        if metrics:
            logger.info(f"Evaluation metrics at step {state.global_step}: {metrics}")


def train_model(
    config_path: str | Path,
    resume_from: str | None = None,
) -> dict[str, Any]:
    """
    Convenience function to train model from config file.

    Args:
        config_path: Path to training configuration
        resume_from: Checkpoint to resume from

    Returns:
        Training metrics
    """
    trainer = OCCTrainer(config_path, resume_from_checkpoint=resume_from)
    return trainer.train()


def main():
    """CLI entry point for training"""
    import argparse

    parser = argparse.ArgumentParser(description="Train TAKTKRONE-I model")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--resume", help="Checkpoint to resume from")
    parser.add_argument("--merge-output", help="Path to save merged model")

    args = parser.parse_args()

    # Train
    trainer = OCCTrainer(args.config, resume_from_checkpoint=args.resume)
    metrics = trainer.train()

    # Merge if requested
    if args.merge_output:
        trainer.merge_and_save(args.merge_output)

    print(f"Training complete. Metrics: {metrics}")


if __name__ == "__main__":
    main()
