"""
CLI command for model training.

Provides the `occlm train` command for fine-tuning OCC models.
"""

import json
import logging
from pathlib import Path

import typer

from occlm.training.config import (
    TrainingConfig,
    load_config,
    save_config,
)
from occlm.training.data_loader import OCCDataLoader
from occlm.training.lora_trainer import LoRATrainer
from occlm.training.sft_trainer import OCCTrainer
from occlm.training.tracking import ExperimentTracker

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def train(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML training configuration file",
        exists=True,
    ),
    train_data: Path | None = typer.Option(
        None,
        "--train-data",
        help="Override train data path",
        exists=True,
    ),
    val_data: Path | None = typer.Option(
        None,
        "--val-data",
        help="Override validation data path",
        exists=True,
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Override output directory",
    ),
    resume_from: Path | None = typer.Option(
        None,
        "--resume-from",
        help="Resume from checkpoint",
        exists=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate without training",
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Validate config and exit",
    ),
    wandb_entity: str | None = typer.Option(
        None,
        "--wandb-entity",
        help="W&B entity for tracking",
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        help="Random seed",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Fine-tune OCC model using TAKTKRONE-I training pipeline.

    Loads configuration from YAML file, prepares datasets,
    initializes model with specified method (SFT, LoRA, QLoRA),
    and runs training with tracking.

    Example:
        occlm train --config config.yaml --output-dir ./models

    The training process will:
    1. Load and validate configuration
    2. Load training datasets
    3. Initialize tracking (W&B/MLflow)
    4. Load base model and tokenizer
    5. Apply training method (SFT/LoRA/QLoRA)
    6. Execute training loop
    7. Save best checkpoint
    8. Log final metrics

    Use --dry-run to validate without training.
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)

    typer.echo("Loading training configuration...")

    # Load config
    try:
        training_config = load_config(config)
    except Exception as e:
        typer.secho(
            f"Error loading config: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Override config values if provided
    if train_data:
        training_config.dataset.train_path = str(train_data)

    if val_data:
        training_config.dataset.eval_path = str(val_data)

    if output_dir:
        training_config.output_dir = str(output_dir)

    if seed is not None:
        training_config.seed = seed

    # Validate config
    typer.echo("Validating configuration...")
    try:
        training_config = TrainingConfig(**training_config.model_dump())
    except Exception as e:
        typer.secho(
            f"Configuration validation error: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    typer.echo(
        f"Training method: {training_config.method.value}"
    )
    typer.echo(
        f"Model: {training_config.model.model_id}"
    )
    typer.echo(
        f"Output directory: "
        f"{training_config.experiment_output_dir}"
    )

    # Exit if validate-only or dry-run
    if validate_only:
        typer.secho(
            "Configuration valid. Exiting.",
            fg=typer.colors.GREEN,
        )
        raise typer.Exit(0)

    if dry_run:
        typer.secho(
            "Dry-run complete. Exiting without training.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(0)

    # Create output directory
    training_config.experiment_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save config to output dir
    save_config(
        training_config,
        training_config.experiment_output_dir / "config.yaml",
    )

    # Initialize tracking
    typer.echo("Initializing experiment tracking...")
    tracker = ExperimentTracker(
        project=training_config.wandb_project,
        entity=wandb_entity,
        run_name=training_config.experiment_name,
        tags=training_config.tags,
    )

    try:
        # Log config
        tracker.log_config(training_config.model_dump())

        # Load datasets
        typer.echo("Loading datasets...")
        loader = OCCDataLoader(
            max_seq_length=(
                training_config.hyperparameters.max_seq_length
            ),
        )

        try:
            train_dataset, val_dataset, _ = (
                loader.load_datasets(
                    train_path=training_config.dataset.train_path,
                    val_path=(
                        training_config.dataset.eval_path
                    ),
                )
            )
        except Exception as e:
            typer.secho(
                f"Error loading datasets: {e}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        # Log dataset statistics
        stats = loader.get_statistics(train_dataset)
        typer.echo(f"Dataset statistics: {stats}")
        tracker.log_config({"dataset_stats": stats})

        # Initialize trainer based on method
        typer.echo(
            f"Initializing {training_config.method.value} "
            "trainer..."
        )

        if training_config.method.value == "lora":
            trainer = LoRATrainer(
                config=training_config,
            )
        elif training_config.method.value == "qlora":
            trainer = LoRATrainer(
                config=training_config,
            )
        else:
            trainer = OCCTrainer(
                config=training_config,
            )

        # Train
        typer.echo("Starting training...")
        with typer.progressbar(
            length=100,
            label="Training",
        ) as progress:
            metrics = trainer.train(
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
            )
            progress.update(100)

        # Log metrics
        tracker.log_metrics(metrics)

        # Get summary
        if hasattr(trainer, "get_metrics_summary"):
            summary = trainer.get_metrics_summary()
        else:
            summary = metrics

        typer.secho(
            "\nTraining completed!",
            fg=typer.colors.GREEN,
        )
        typer.echo("\nMetrics:")
        for key, value in summary.items():
            if isinstance(value, float):
                typer.echo(f"  {key}: {value:.4f}")
            else:
                typer.echo(f"  {key}: {value}")

        # Save checkpoint
        checkpoint_path = (
            training_config.experiment_output_dir / "final"
        )
        typer.echo(f"Saving checkpoint to {checkpoint_path}...")
        trainer.save_checkpoint(checkpoint_path)

        # Log model
        tracker.log_model(checkpoint_path)

        if tracker.get_run_url():
            typer.echo(
                f"\nTracking: {tracker.get_run_url()}"
            )

        typer.secho(
            "\nTraining pipeline completed successfully!",
            fg=typer.colors.GREEN,
        )

    except KeyboardInterrupt:
        typer.secho(
            "\nTraining interrupted by user",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(130)

    except Exception as e:
        typer.secho(
            f"\nTraining error: {e}",
            fg=typer.colors.RED,
        )
        logger.exception("Training failed")
        raise typer.Exit(1)

    finally:
        tracker.end_run()


@app.command()
def validate_config(
    config_file: Path = typer.Argument(
        ...,
        help="Configuration file to validate",
        exists=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show full config after validation",
    ),
) -> None:
    """
    Validate a training configuration file.

    Checks that configuration has all required fields and
    proper structure for use with training.

    Example:
        occlm train validate-config config.yaml
    """
    typer.echo(f"Validating {config_file}...")

    try:
        config = load_config(config_file)
        config = TrainingConfig(**config.model_dump())
    except Exception as e:
        typer.secho(
            f"Validation failed: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    typer.secho(
        "Configuration is valid!",
        fg=typer.colors.GREEN,
    )

    if verbose:
        typer.echo("\nConfiguration:")
        config_dict = config.model_dump()
        typer.echo(json.dumps(config_dict, indent=2))


def create_app() -> typer.Typer:
    """Create and configure the CLI application."""
    return app


if __name__ == "__main__":
    app()


__all__ = ["app", "train", "validate_config", "create_app"]
