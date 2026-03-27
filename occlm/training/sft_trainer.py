"""
TAKTKRONE-I Supervised Fine-Tuning Trainer.

Implements supervised fine-tuning trainer for OCC models using
transformers and TRL libraries.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

try:
    import torch
    from torch.utils.data import DataLoader
except ImportError:
    torch = None
    DataLoader = None

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
    )
except ImportError:
    AutoModelForCausalLM = None
    AutoTokenizer = None
    TrainingArguments = None
    Trainer = None

from .config import TrainingConfig, HyperparametersConfig

logger = logging.getLogger(__name__)


class TrainingState(BaseModel):
    """Training state tracking."""

    current_step: int = 0
    current_epoch: int = 0
    best_eval_loss: float = float("inf")
    best_checkpoint: Optional[str] = None
    total_steps: int = 0


class OCCTrainer:
    """Supervised fine-tuning trainer for OCC models."""

    def __init__(
        self,
        config: TrainingConfig,
        device: Optional[str] = None,
    ):
        """
        Initialize SFT trainer.

        Args:
            config: Training configuration object with model,
                hyperparameters, and dataset settings
            device: Device to use ('cuda', 'cpu', or None for auto).
                Defaults to CUDA if available, else CPU.

        Raises:
            ImportError: If transformers library not available

        Example:
            config = TrainingConfig(...)
            trainer = OCCTrainer(config)
            trainer.load_model_and_tokenizer()
        """
        if AutoModelForCausalLM is None:
            raise ImportError(
                "transformers library required: pip install transformers"
            )

        self.config = config
        self.device = device or (
            "cuda" if torch and torch.cuda.is_available() else "cpu"
        )
        logger.info(f"Using device: {self.device}")

        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.state = TrainingState()

        # Metrics tracking
        self.train_losses: List[float] = []
        self.eval_losses: List[float] = []
        self.learning_rates: List[float] = []

    def load_model_and_tokenizer(self) -> None:
        """Load model and tokenizer from config."""
        logger.info(f"Loading model: {self.config.model.model_id}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model.model_id,
            trust_remote_code=self.config.model.trust_remote_code,
        )

        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        torch_dtype = self._get_torch_dtype()
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model.model_id,
            torch_dtype=torch_dtype,
            device_map=self.device,
            trust_remote_code=self.config.model.trust_remote_code,
        )

        logger.info(f"Model loaded: {self.model.__class__.__name__}")
        logger.info(
            f"Model size: "
            f"{sum(p.numel() for p in self.model.parameters()) / 1e6:.1f}M"
        )

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

    def train(
        self,
        train_dataset: Any,
        eval_dataset: Optional[Any] = None,
        data_collator: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute training loop.

        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
            data_collator: Custom data collator function

        Returns:
            Dict with training metrics
        """
        if self.model is None:
            self.load_model_and_tokenizer()

        logger.info("Starting training...")

        # Get training arguments
        training_args = self.config.to_training_arguments()

        # Create trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
            callbacks=[
                self._create_tracking_callback(),
            ],
        )

        # Train
        train_result = self.trainer.train()

        logger.info(f"Training completed")
        logger.info(
            f"Final train loss: {train_result.training_loss:.4f}"
        )

        return train_result.metrics

    def _create_tracking_callback(self) -> Any:
        """Create callback for tracking training metrics."""
        from transformers import TrainerCallback

        trainer_self = self

        class TrackingCallback(TrainerCallback):
            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs is None:
                    return
                if "loss" in logs:
                    trainer_self.train_losses.append(logs["loss"])
                if "eval_loss" in logs:
                    trainer_self.eval_losses.append(logs["eval_loss"])
                    if (
                        logs["eval_loss"]
                        < trainer_self.state.best_eval_loss
                    ):
                        trainer_self.state.best_eval_loss = logs[
                            "eval_loss"
                        ]

        return TrackingCallback()

    def evaluate(
        self,
        eval_dataset: Any,
        data_collator: Optional[Callable] = None,
    ) -> Dict[str, float]:
        """
        Evaluate model on dataset.

        Args:
            eval_dataset: Evaluation dataset
            data_collator: Optional data collator

        Returns:
            Dict with evaluation metrics (loss, perplexity, etc.)
        """
        if self.model is None:
            raise RuntimeError(
                "Model not loaded. Call load_model_and_tokenizer() first."
            )

        logger.info("Running evaluation...")

        if self.trainer is None:
            # Create minimal trainer for evaluation
            training_args = TrainingArguments(
                output_dir=str(
                    self.config.experiment_output_dir
                ),
                per_device_eval_batch_size=(
                    self.config.hyperparameters.batch_size
                ),
            )
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                eval_dataset=eval_dataset,
                data_collator=data_collator,
                tokenizer=self.tokenizer,
            )

        metrics = self.trainer.evaluate()

        # Compute perplexity
        if "eval_loss" in metrics:
            metrics["eval_perplexity"] = (
                torch.exp(torch.tensor(metrics["eval_loss"]))
                if torch
                else float("nan")
            )

        logger.info(f"Evaluation metrics: {metrics}")
        return metrics

    def save_checkpoint(
        self,
        path: Union[str, Path],
        include_config: bool = True,
    ) -> None:
        """
        Save model checkpoint.

        Args:
            path: Directory to save checkpoint
            include_config: Whether to save config

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError(
                "Model not loaded. Nothing to save."
            )

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving checkpoint to {path}")

        # Save model
        self.model.save_pretrained(str(path / "model"))

        # Save tokenizer
        if self.tokenizer:
            self.tokenizer.save_pretrained(str(path / "tokenizer"))

        # Save training state
        state_dict = {
            "step": self.state.current_step,
            "epoch": self.state.current_epoch,
            "best_eval_loss": self.state.best_eval_loss,
            "train_losses": self.train_losses,
            "eval_losses": self.eval_losses,
        }
        with open(path / "training_state.json", "w") as f:
            json.dump(state_dict, f, indent=2)

        # Optionally save config
        if include_config:
            with open(path / "training_config.json", "w") as f:
                json.dump(self.config.model_dump(), f, indent=2)

        logger.info(f"Checkpoint saved to {path}")

    def load_checkpoint(
        self,
        path: Union[str, Path],
    ) -> None:
        """
        Load model from checkpoint.

        Args:
            path: Directory containing checkpoint

        Raises:
            FileNotFoundError: If checkpoint not found
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")

        logger.info(f"Loading checkpoint from {path}")

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            str(path / "model"),
            device_map=self.device,
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(path / "tokenizer")
        )

        # Load training state
        state_file = path / "training_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state_dict = json.load(f)
                self.state.current_step = state_dict.get(
                    "step", 0
                )
                self.state.current_epoch = state_dict.get(
                    "epoch", 0
                )
                self.state.best_eval_loss = state_dict.get(
                    "best_eval_loss", float("inf")
                )
                self.train_losses = state_dict.get(
                    "train_losses", []
                )
                self.eval_losses = state_dict.get(
                    "eval_losses", []
                )

        logger.info(f"Checkpoint loaded from {path}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of training metrics."""
        summary = {
            "num_training_steps": self.state.current_step,
            "num_epochs": self.state.current_epoch,
            "best_eval_loss": self.state.best_eval_loss,
        }

        if self.train_losses:
            summary["final_train_loss"] = self.train_losses[-1]
            summary["avg_train_loss"] = (
                sum(self.train_losses) / len(self.train_losses)
            )

        if self.eval_losses:
            summary["final_eval_loss"] = self.eval_losses[-1]
            summary["avg_eval_loss"] = (
                sum(self.eval_losses) / len(self.eval_losses)
            )

        return summary

    def push_to_hub(
        self,
        repo_id: str,
        commit_message: str = "Checkpoint from TAKTKRONE-I training",
    ) -> None:
        """
        Push model to Hugging Face Hub.

        Args:
            repo_id: Hub repository ID (e.g., username/repo-name)
            commit_message: Commit message for push
        """
        if self.model is None:
            raise RuntimeError(
                "Model not loaded. Nothing to push."
            )

        logger.info(f"Pushing model to {repo_id}...")
        self.model.push_to_hub(
            repo_id,
            commit_message=commit_message,
        )
        if self.tokenizer:
            self.tokenizer.push_to_hub(repo_id)
        logger.info(f"Model pushed to {repo_id}")

    def compute_training_stats(
        self,
    ) -> Dict[str, Any]:
        """
        Compute comprehensive training statistics.

        Returns:
            Dict with detailed training statistics including loss,
            learning rates, convergence metrics, etc.
        """
        stats = {
            "total_training_steps": (
                self.state.current_step
            ),
            "total_epochs": self.state.current_epoch,
            "best_eval_loss": (
                self.state.best_eval_loss
            ),
        }

        if self.train_losses:
            stats["first_train_loss"] = (
                self.train_losses[0]
            )
            stats["last_train_loss"] = (
                self.train_losses[-1]
            )
            stats["avg_train_loss"] = (
                sum(self.train_losses) / len(self.train_losses)
            )
            stats["min_train_loss"] = (
                min(self.train_losses)
            )
            stats["max_train_loss"] = (
                max(self.train_losses)
            )

        if self.eval_losses:
            stats["first_eval_loss"] = (
                self.eval_losses[0]
            )
            stats["last_eval_loss"] = (
                self.eval_losses[-1]
            )
            stats["avg_eval_loss"] = (
                sum(self.eval_losses) / len(self.eval_losses)
            )

        if self.learning_rates:
            stats["learning_rate_samples"] = (
                len(self.learning_rates)
            )
            stats["final_learning_rate"] = (
                self.learning_rates[-1]
            )

        return stats

    def create_loss_plot(
        self,
        output_path: Union[str, Path],
    ) -> None:
        """
        Create visualization of training and eval loss curves.

        Args:
            output_path: Path to save plot figure

        Raises:
            ImportError: If matplotlib not available
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning(
                "matplotlib not available for plotting"
            )
            return

        output_path = Path(output_path)

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Training loss
        if self.train_losses:
            axes[0].plot(self.train_losses)
            axes[0].set_title("Training Loss")
            axes[0].set_xlabel("Step")
            axes[0].set_ylabel("Loss")
            axes[0].grid(True)

        # Eval loss
        if self.eval_losses:
            axes[1].plot(self.eval_losses)
            axes[1].set_title("Evaluation Loss")
            axes[1].set_xlabel("Evaluation Step")
            axes[1].set_ylabel("Loss")
            axes[1].grid(True)

        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()

        logger.info(f"Loss plot saved to {output_path}")

    def validate_checkpoint(
        self,
        checkpoint_path: Union[str, Path],
    ) -> Dict[str, Any]:
        """
        Validate saved checkpoint is loadable.

        Args:
            checkpoint_path: Path to checkpoint to validate

        Returns:
            Dict with validation results

        Raises:
            FileNotFoundError: If checkpoint not found
        """
        checkpoint_path = Path(checkpoint_path)

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found: {checkpoint_path}"
            )

        validation = {
            "checkpoint_path": str(checkpoint_path),
            "model_exists": (
                (checkpoint_path / "model").exists()
            ),
            "tokenizer_exists": (
                (checkpoint_path / "tokenizer").exists()
            ),
            "config_exists": (
                (checkpoint_path / "training_config.json").exists()
            ),
            "state_exists": (
                (checkpoint_path / "training_state.json").exists()
            ),
        }

        # Check if checkpoint is loadable
        try:
            if validation["model_exists"]:
                _ = AutoModelForCausalLM.from_pretrained(
                    str(checkpoint_path / "model")
                )
                validation["model_loadable"] = True
            else:
                validation["model_loadable"] = False
        except Exception as e:
            validation["model_loadable"] = False
            validation["model_load_error"] = str(e)

        try:
            if validation["tokenizer_exists"]:
                _ = AutoTokenizer.from_pretrained(
                    str(checkpoint_path / "tokenizer")
                )
                validation["tokenizer_loadable"] = True
            else:
                validation["tokenizer_loadable"] = False
        except Exception as e:
            validation["tokenizer_loadable"] = False
            validation["tokenizer_load_error"] = str(e)

        return validation

    def log_model_architecture(self) -> Dict[str, Any]:
        """
        Log model architecture information.

        Returns:
            Dict containing model architecture details

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        info = {
            "model_class": (
                self.model.__class__.__name__
            ),
            "model_architecture": (
                str(self.model.config)
            ),
        }

        # Count parameters by layer type if available
        if hasattr(self.model, "config"):
            config_dict = self.model.config.to_dict()
            info["hidden_size"] = config_dict.get(
                "hidden_size"
            )
            info["num_layers"] = config_dict.get(
                "num_hidden_layers"
            )
            info["vocab_size"] = config_dict.get(
                "vocab_size"
            )

        logger.info(f"Model architecture: {info}")
        return info

    def create_optimization_report(
        self,
    ) -> Dict[str, Any]:
        """
        Create detailed optimization report.

        Returns:
            Dict with optimization metrics and recommendations
        """
        report = {
            "config_method": (
                self.config.method.value
            ),
            "learning_rate": (
                self.config.hyperparameters.learning_rate
            ),
            "batch_size": (
                self.config.hyperparameters.batch_size
            ),
            "gradient_accumulation": (
                self.config.hyperparameters.gradient_accumulation_steps
            ),
            "effective_batch_size": (
                self.config.hyperparameters.effective_batch_size
            ),
        }

        # Add optimization recommendations
        recommendations = []

        if self.train_losses and len(self.train_losses) > 1:
            # Check for divergence
            if any(
                loss > 100 for loss in self.train_losses[-10:]
            ):
                recommendations.append(
                    "Loss diverging. Consider reducing "
                    "learning rate."
                )

            # Check for plateau
            if len(self.train_losses) >= 20:
                recent_avg = (
                    sum(self.train_losses[-10:]) / 10
                )
                older_avg = (
                    sum(self.train_losses[-20:-10]) / 10
                )
                if abs(recent_avg - older_avg) < 0.01:
                    recommendations.append(
                        "Loss plateauing. Training may be "
                        "complete."
                    )

        if not recommendations:
            recommendations.append(
                "Training appears stable. Continue monitoring."
            )

        report["recommendations"] = recommendations
        return report


__all__ = [
    "OCCTrainer",
    "TrainingState",
]
