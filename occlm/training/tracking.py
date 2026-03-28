"""
TAKTKRONE-I Experiment Tracking and Logging.

Provides unified interface for experiment tracking using W&B and MLflow.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """Unified experiment tracking interface."""

    def __init__(
        self,
        backend: str = "auto",
        project: str = "taktkrone-i",
        entity: str | None = None,
        run_name: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
    ):
        """
        Initialize experiment tracker.

        Args:
            backend: "wandb", "mlflow", or "auto" for auto-detect
            project: Project name for tracking
            entity: Entity/workspace name (W&B specific)
            run_name: Name for the run
            tags: List of tags for run
            notes: Notes/description for run
        """
        self.backend = backend
        self.project = project
        self.entity = entity
        self.run_name = run_name
        self.tags = tags or []
        self.notes = notes

        self.tracker = None
        self.run_id = None
        self.run_url = None

        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize tracking backend."""
        if self.backend == "auto":
            # Try to detect available backend
            self.backend = self._detect_backend()

        logger.info(f"Using tracking backend: {self.backend}")

        if self.backend == "wandb":
            self._init_wandb()
        elif self.backend == "mlflow":
            self._init_mlflow()
        elif self.backend == "none":
            logger.warning("No tracking backend available")
        else:
            raise ValueError(
                f"Unknown backend: {self.backend}"
            )

    def _detect_backend(self) -> str:
        """Auto-detect available tracking backend."""
        try:
            import wandb  # noqa: F401
            return "wandb"
        except ImportError:
            pass

        try:
            import mlflow  # noqa: F401
            return "mlflow"
        except ImportError:
            pass

        logger.warning(
            "No tracking backend found. "
            "Install wandb or mlflow for tracking."
        )
        return "none"

    def _init_wandb(self) -> None:
        """Initialize W&B tracking."""
        try:
            import wandb
        except ImportError:
            raise ImportError(
                "wandb required: pip install wandb"
            )

        logger.info("Initializing Weights & Biases tracking")

        init_kwargs = {
            "project": self.project,
            "name": self.run_name,
            "tags": self.tags,
            "notes": self.notes,
        }

        if self.entity:
            init_kwargs["entity"] = self.entity

        wandb.init(**init_kwargs)
        self.tracker = wandb
        self.run_id = wandb.run.id
        self.run_url = wandb.run.url

    def _init_mlflow(self) -> None:
        """Initialize MLflow tracking."""
        try:
            import mlflow
        except ImportError:
            raise ImportError(
                "mlflow required: pip install mlflow"
            )

        logger.info("Initializing MLflow tracking")

        # Set experiment
        mlflow.set_experiment(self.project)

        # Start run
        mlflow.start_run(run_name=self.run_name)

        # Set tags
        for tag in self.tags:
            mlflow.set_tag("tag", tag)

        if self.notes:
            mlflow.set_tag("notes", self.notes)

        self.tracker = mlflow
        self.run_id = mlflow.active_run().info.run_id
        self.run_url = None  # MLflow URL needs server info

    def start_run(
        self,
        run_name: str,
        tags: list[str] | None = None,
    ) -> None:
        """
        Start a new tracking run.

        Args:
            run_name: Name for the run
            tags: Optional tags for run
        """
        self.run_name = run_name
        if tags:
            self.tags = tags

        logger.info(f"Starting run: {run_name}")

        if self.backend == "wandb" and self.tracker:
            self.tracker.finish()
            self._init_wandb()

        elif self.backend == "mlflow" and self.tracker:
            self.tracker.end_run()
            self._init_mlflow()

    def end_run(self) -> None:
        """End current tracking run."""
        if self.tracker is None:
            return

        logger.info(f"Ending run: {self.run_id}")

        if self.backend == "wandb":
            self.tracker.finish()
        elif self.backend == "mlflow":
            self.tracker.end_run()

        self.run_id = None
        self.run_url = None

    def log_config(self, config: dict[str, Any]) -> None:
        """
        Log configuration.

        Args:
            config: Configuration dictionary
        """
        if self.tracker is None:
            return

        logger.info("Logging configuration")

        if self.backend == "wandb":
            self.tracker.config.update(config)

        elif self.backend == "mlflow":
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                self.tracker.log_param(key, value)

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """
        Log metrics.

        Args:
            metrics: Dict of metric names to values
            step: Optional step/epoch number
        """
        if self.tracker is None:
            return

        if self.backend == "wandb":
            log_dict = metrics.copy()
            if step is not None:
                log_dict["step"] = step
            self.tracker.log(log_dict)

        elif self.backend == "mlflow":
            for key, value in metrics.items():
                try:
                    self.tracker.log_metric(
                        key,
                        float(value),
                        step=step,
                    )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not log metric {key}={value}"
                    )

    def log_artifact(
        self,
        artifact_path: str | Path,
        artifact_type: str | None = None,
    ) -> None:
        """
        Log artifact file.

        Args:
            artifact_path: Path to artifact file
            artifact_type: Optional artifact type
        """
        if self.tracker is None:
            return

        artifact_path = Path(artifact_path)
        if not artifact_path.exists():
            logger.warning(
                f"Artifact not found: {artifact_path}"
            )
            return

        logger.info(f"Logging artifact: {artifact_path}")

        if self.backend == "wandb":
            artifact = self.tracker.Artifact(
                name=artifact_path.stem,
                type=artifact_type or "model",
            )
            artifact.add_file(str(artifact_path))
            self.tracker.log_artifact(artifact)

        elif self.backend == "mlflow":
            self.tracker.log_artifact(str(artifact_path))

    def log_model(
        self,
        model_path: str | Path,
        model_name: str = "model",
    ) -> None:
        """
        Log model artifacts.

        Args:
            model_path: Path to model directory
            model_name: Name for the model
        """
        if self.tracker is None:
            return

        model_path = Path(model_path)
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return

        logger.info(f"Logging model: {model_name}")

        if self.backend == "wandb":
            artifact = self.tracker.Artifact(
                name=model_name,
                type="model",
            )
            artifact.add_dir(str(model_path))
            self.tracker.log_artifact(artifact)

        elif self.backend == "mlflow":
            # Log model using MLflow's log_artifacts
            self.tracker.log_artifacts(str(model_path))

    def get_run_url(self) -> str | None:
        """
        Get URL for current run.

        Returns:
            Run URL or None if unavailable
        """
        return self.run_url

    def get_run_id(self) -> str | None:
        """
        Get ID for current run.

        Returns:
            Run ID or None if not tracking
        """
        return self.run_id

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end_run()
        return False


class MultiTracker:
    """Track experiments with multiple backends simultaneously."""

    def __init__(
        self,
        backends: list[str] | None = None,
        project: str = "taktkrone-i",
    ):
        """
        Initialize multi-backend tracker.

        Args:
            backends: List of backends to use
            project: Project name
        """
        self.backends = backends or ["wandb", "mlflow"]
        self.project = project
        self.trackers: list[ExperimentTracker] = []

        self._initialize_backends()

    def _initialize_backends(self) -> None:
        """Initialize available backends."""
        for backend in self.backends:
            try:
                tracker = ExperimentTracker(
                    backend=backend,
                    project=self.project,
                )
                if tracker.backend != "none":
                    self.trackers.append(tracker)
            except Exception as e:
                logger.warning(
                    f"Could not initialize {backend}: {e}"
                )

        if not self.trackers:
            logger.warning(
                "No tracking backends initialized"
            )

    def log_config(self, config: dict[str, Any]) -> None:
        """Log config to all trackers."""
        for tracker in self.trackers:
            tracker.log_config(config)

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """Log metrics to all trackers."""
        for tracker in self.trackers:
            tracker.log_metrics(metrics, step)

    def log_artifact(
        self,
        artifact_path: str | Path,
        artifact_type: str | None = None,
    ) -> None:
        """Log artifact to all trackers."""
        for tracker in self.trackers:
            tracker.log_artifact(artifact_path, artifact_type)

    def end_runs(self) -> None:
        """End all runs."""
        for tracker in self.trackers:
            tracker.end_run()


__all__ = [
    "ExperimentTracker",
    "MultiTracker",
]
