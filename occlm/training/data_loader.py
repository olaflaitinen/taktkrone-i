"""
TAKTKRONE-I OCC Training Data Loader.

Handles loading, processing, and batching of OCC dialogue samples for training.
"""

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

try:
    from datasets import Dataset, Datasetload_dataset
except ImportError:
    Dataset = None
    DatasetDict = None
    load_dataset = None

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class OCCDialogueSample(BaseModel):
    """Schema for OCC dialogue samples."""

    dialogue_id: str = Field(description="Unique dialogue identifier")
    operator: str = Field(description="Transit operator code")
    incident_type: str = Field(description="Type of incident/scenario")
    difficulty: str = Field(
        default="medium",
        description="Difficulty level"
    )
    timestamp: str = Field(description="Dialogue timestamp")
    messages: list[dict[str, str]] = Field(
        description="List of message dicts with role and content"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata"
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: list[dict[str, str]]) -> list[
        dict[str, str]
    ]:
        """Validate message structure."""
        if not v:
            raise ValueError("messages cannot be empty")
        for msg in v:
            if "role" not in msg or "content" not in msg:
                raise ValueError(
                    "Each message must have role and content"
                )
        return v


class OCCDataLoader:
    """Data loader for OCC training samples."""

    def __init__(
        self,
        max_seq_length: int = 4096,
        tokenizer: Any | None = None,
    ):
        """
        Initialize data loader.

        Args:
            max_seq_length: Maximum sequence length for tokenization
            tokenizer: Optional tokenizer for token counting
        """
        self.max_seq_length = max_seq_length
        self.tokenizer = tokenizer
        self.statistics: dict[str, Any] = {}

    def load_datasets(
        self,
        train_path: str | Path,
        val_path: str | Path | None = None,
        test_path: str | Path | None = None,
    ) -> tuple[Dataset | None, Dataset | None, Dataset | None]:
        """
        Load training, validation, and test datasets from JSONL files.

        Args:
            train_path: Path to training JSONL file
            val_path: Path to validation JSONL file (optional)
            test_path: Path to test JSONL file (optional)

        Returns:
            Tuple of (train_dataset, val_dataset, test_dataset)

        Raises:
            FileNotFoundError: If required files not found
            ValueError: If dataset is empty or invalid
        """
        train_path = Path(train_path)
        if not train_path.exists():
            raise FileNotFoundError(f"Training file not found: {train_path}")

        train_dataset = self._load_jsonl(train_path)
        logger.info(f"Loaded {len(train_dataset)} training samples")

        val_dataset = None
        if val_path:
            val_path = Path(val_path)
            if val_path.exists():
                val_dataset = self._load_jsonl(val_path)
                logger.info(
                    f"Loaded {len(val_dataset)} validation samples"
                )

        test_dataset = None
        if test_path:
            test_path = Path(test_path)
            if test_path.exists():
                test_dataset = self._load_jsonl(test_path)
                logger.info(f"Loaded {len(test_dataset)} test samples")

        return train_dataset, val_dataset, test_dataset

    def _load_jsonl(self, path: Path) -> Dataset:
        """Load JSONL file and validate schema."""
        if Dataset is None:
            raise ImportError(
                "datasets library required: pip install datasets"
            )

        data = []
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    sample = json.loads(line)
                    sample = OCCDialogueSample(**sample)
                    data.append(sample.model_dump())
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        f"Skipping line {line_num} in {path}: {e}"
                    )
                    continue

        if not data:
            raise ValueError(f"No valid samples found in {path}")

        return Dataset.from_list(data)

    def create_prompt_response_pairs(
        self,
        dialogue: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Create prompt-response pairs for supervised fine-tuning.

        Args:
            dialogue: Dialogue sample from dataset

        Returns:
            List of dicts with 'prompt' and 'response' keys
        """
        pairs = []
        messages = dialogue.get("messages", [])

        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user":
                prompt = messages[i]["content"]
                # Find corresponding assistant response
                for j in range(i + 1, len(messages)):
                    if messages[j]["role"] == "assistant":
                        response = messages[j]["content"]
                        pairs.append({
                            "prompt": prompt,
                            "response": response,
                            "dialogue_id": dialogue.get(
                                "dialogue_id", "unknown"
                            ),
                        })
                        break

        return pairs

    def apply_chat_template(
        self,
        dialogue: dict[str, Any],
        template: str = "chatml",
    ) -> str:
        """
        Apply chat template to format dialogue for model.

        Args:
            dialogue: Dialogue sample
            template: Template type ('chatml', 'llama3', 'mistral')

        Returns:
            Formatted dialogue string

        Raises:
            ValueError: If template not supported
        """
        templates = {
            "chatml": self._format_chatml,
            "llama3": self._format_llama3,
            "mistral": self._format_mistral,
        }

        if template not in templates:
            raise ValueError(
                f"Unsupported template: {template}. "
                f"Choose from {list(templates.keys())}"
            )

        formatter = templates[template]
        return formatter(dialogue)

    def _format_chatml(self, dialogue: dict[str, Any]) -> str:
        """Format dialogue using ChatML template."""
        text = ""
        for message in dialogue.get("messages", []):
            role = message["role"]
            content = message["content"]
            text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        return text

    def _format_llama3(self, dialogue: dict[str, Any]) -> str:
        """Format dialogue using Llama3 template."""
        text = "<|begin_of_text|>"
        for message in dialogue.get("messages", []):
            role = message["role"]
            content = message["content"]
            text += (
                f"<|start_header_id|>{role}<|end_header_id|>\n"
                f"{content}<|eot_id|>"
            )
        return text

    def _format_mistral(self, dialogue: dict[str, Any]) -> str:
        """Format dialogue using Mistral template."""
        text = ""
        for message in dialogue.get("messages", []):
            if message["role"] == "user":
                text += f"[INST] {message['content']} [/INST]"
            elif message["role"] == "assistant":
                text += f"{message['content']}</s>"
        return text

    def create_data_loader(
        self,
        dataset: Dataset,
        batch_size: int = 32,
        shuffle: bool = True,
        template: str = "chatml",
    ) -> Iterator[dict[str, Any]]:
        """
        Create batch iterator for dataset.

        Args:
            dataset: HuggingFace Dataset
            batch_size: Batch size for iteration
            shuffle: Whether to shuffle dataset
            template: Chat template to apply

        Yields:
            Batch dicts with input_ids, attention_mask, labels
        """
        if shuffle:
            dataset = dataset.shuffle()

        indices = list(range(len(dataset)))
        for i in range(0, len(indices), batch_size):
            batch_indices = indices[i : i + batch_size]
            batch_samples = [dataset[idx] for idx in batch_indices]

            # Format samples
            formatted = []
            for sample in batch_samples:
                text = self.apply_chat_template(sample, template)
                formatted.append({"text": text})

            # Tokenize if tokenizer available
            if self.tokenizer:
                batch_dict = self._tokenize_batch(formatted)
            else:
                batch_dict = {"texts": [s["text"] for s in formatted]}

            yield batch_dict

    def _tokenize_batch(
        self,
        batch_samples: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Tokenize batch with padding and truncation."""
        texts = [s["text"] for s in batch_samples]

        encodings = self.tokenizer(
            texts,
            truncation=True,
            max_length=self.max_seq_length,
            padding="max_length",
            return_tensors="pt",
        )

        # Create labels (same as input_ids for causal LM)
        encodings["labels"] = encodings["input_ids"].clone()
        # Mask padding tokens
        encodings["labels"][
            encodings["labels"] == self.tokenizer.pad_token_id
        ] = -100

        return encodings

    def get_statistics(
        self,
        dataset: Dataset | None = None,
    ) -> dict[str, Any]:
        """
        Compute dataset statistics.

        Args:
            dataset: Optional dataset to analyze

        Returns:
            Dict with counts, distributions, and length statistics
        """
        if dataset is None:
            return self.statistics

        stats = {
            "num_samples": len(dataset),
            "columns": dataset.column_names,
        }

        # Count by operator
        if "operator" in dataset.column_names:
            operators = dataset["operator"]
            operator_counts = {}
            for op in operators:
                operator_counts[op] = operator_counts.get(op, 0) + 1
            stats["operator_distribution"] = operator_counts

        # Count by incident type
        if "incident_type" in dataset.column_names:
            types = dataset["incident_type"]
            type_counts = {}
            for t in types:
                type_counts[t] = type_counts.get(t, 0) + 1
            stats["incident_type_distribution"] = type_counts

        # Count by difficulty
        if "difficulty" in dataset.column_names:
            difficulties = dataset["difficulty"]
            diff_counts = {}
            for d in difficulties:
                diff_counts[d] = diff_counts.get(d, 0) + 1
            stats["difficulty_distribution"] = diff_counts

        # Compute message length statistics
        if "messages" in dataset.column_names:
            msg_lengths = []
            for sample in dataset:
                msg_lengths.append(len(sample.get("messages", [])))
            stats["avg_messages_per_dialogue"] = (
                sum(msg_lengths) / len(msg_lengths)
                if msg_lengths
                else 0
            )
            stats["max_messages"] = max(msg_lengths) if msg_lengths else 0
            stats["min_messages"] = min(msg_lengths) if msg_lengths else 0

        self.statistics = stats
        return stats

    def filter_dataset(
        self,
        dataset: Dataset,
        difficulty: list[str] | None = None,
        incident_type: list[str] | None = None,
        operator: list[str] | None = None,
    ) -> Dataset:
        """
        Filter dataset by specified criteria.

        Args:
            dataset: Dataset to filter
            difficulty: List of difficulty levels to keep
            incident_type: List of incident types to keep
            operator: List of operators to keep

        Returns:
            Filtered dataset
        """
        def filter_fn(sample: dict[str, Any]) -> bool:
            if (
                difficulty
                and sample.get("difficulty") not in difficulty
            ):
                return False
            if (
                incident_type
                and sample.get("incident_type") not in incident_type
            ):
                return False
            if operator and sample.get("operator") not in operator:
                return False
            return True

        return dataset.filter(filter_fn)


__all__ = [
    "OCCDataLoader",
    "OCCDialogueSample",
]
