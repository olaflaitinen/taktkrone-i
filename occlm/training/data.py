"""
TAKTKRONE-I Training Data Loading and Processing.

Handles loading, preprocessing, and formatting of training data.
"""

import json
import logging
from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict
from transformers import PreTrainedTokenizer

from .config import DatasetConfig

logger = logging.getLogger(__name__)


# Chat templates for different formats
CHAT_TEMPLATES = {
    "chatml": """{% for message in messages %}{% if message['role'] == 'system' %}<|im_start|>system
{{ message['content'] }}<|im_end|>
{% elif message['role'] == 'user' %}<|im_start|>user
{{ message['content'] }}<|im_end|>
{% elif message['role'] == 'assistant' %}<|im_start|>assistant
{{ message['content'] }}<|im_end|>
{% endif %}{% endfor %}{% if add_generation_prompt %}<|im_start|>assistant
{% endif %}""",

    "llama3": """{% for message in messages %}{% if message['role'] == 'system' %}<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{{ message['content'] }}<|eot_id|>{% elif message['role'] == 'user' %}<|start_header_id|>user<|end_header_id|}

{{ message['content'] }}<|eot_id|>{% elif message['role'] == 'assistant' %}<|start_header_id|>assistant<|end_header_id|>

{{ message['content'] }}<|eot_id|>{% endif %}{% endfor %}{% if add_generation_prompt %}<|start_header_id|>assistant<|end_header_id|>

{% endif %}""",

    "mistral": """{% for message in messages %}{% if message['role'] == 'user' %}[INST] {{ message['content'] }} [/INST]{% elif message['role'] == 'assistant' %}{{ message['content'] }}</s>{% endif %}{% endfor %}""",
}


def load_occ_dataset(
    config: DatasetConfig,
    tokenizer: PreTrainedTokenizer | None = None,
) -> DatasetDict:
    """
    Load OCC training dataset.

    Args:
        config: Dataset configuration
        tokenizer: Tokenizer for text processing (optional)

    Returns:
        DatasetDict with train/eval/test splits
    """
    datasets = {}

    # Load training data
    if config.train_path:
        logger.info(f"Loading training data from {config.train_path}")
        datasets["train"] = load_jsonl_dataset(
            config.train_path,
            max_samples=config.max_samples,
            shuffle=config.shuffle,
            seed=config.seed,
        )

    # Load evaluation data
    if config.eval_path:
        logger.info(f"Loading evaluation data from {config.eval_path}")
        datasets["validation"] = load_jsonl_dataset(
            config.eval_path,
            max_samples=None,  # Don't limit eval set
            shuffle=False,
        )

    # Load test data
    if config.test_path:
        logger.info(f"Loading test data from {config.test_path}")
        datasets["test"] = load_jsonl_dataset(
            config.test_path,
            max_samples=None,
            shuffle=False,
        )

    # Apply filters
    if config.filter_by_operator:
        for split in datasets:
            datasets[split] = datasets[split].filter(
                lambda x: x.get("operator") in config.filter_by_operator
            )

    if config.filter_by_task_type:
        for split in datasets:
            datasets[split] = datasets[split].filter(
                lambda x: x.get("task_type") in config.filter_by_task_type
            )

    return DatasetDict(datasets)


def load_jsonl_dataset(
    path: str | Path,
    max_samples: int | None = None,
    shuffle: bool = False,
    seed: int = 42,
) -> Dataset:
    """
    Load dataset from JSONL file.

    Args:
        path: Path to JSONL file
        max_samples: Maximum samples to load
        shuffle: Whether to shuffle data
        seed: Random seed for shuffling

    Returns:
        HuggingFace Dataset
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    # Load JSONL
    data = []
    with open(path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    dataset = Dataset.from_list(data)

    # Shuffle if requested
    if shuffle:
        dataset = dataset.shuffle(seed=seed)

    # Limit samples if requested
    if max_samples and max_samples < len(dataset):
        dataset = dataset.select(range(max_samples))

    return dataset


def format_occ_messages(
    sample: dict[str, Any],
    system_prompt: str | None = None,
) -> list[dict[str, str]]:
    """
    Format OCC sample into chat messages.

    Args:
        sample: Raw sample from dataset
        system_prompt: Optional system prompt override

    Returns:
        List of message dicts with role and content
    """
    messages = []

    # Add system prompt
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    elif "system_prompt" in sample:
        messages.append({"role": "system", "content": sample["system_prompt"]})
    else:
        messages.append({
            "role": "system",
            "content": get_default_system_prompt(sample.get("operator", "generic"))
        })

    # Handle different sample formats
    if "messages" in sample:
        # Already in message format
        for msg in sample["messages"]:
            if msg["role"] != "system":  # Skip if we already added system
                messages.append(msg)

    elif "instruction_sample" in sample:
        # Nested instruction sample format
        inst = sample["instruction_sample"]
        if "messages" in inst:
            for msg in inst["messages"]:
                if msg["role"] != "system":
                    messages.append(msg)

    elif "user_query" in sample and "response" in sample:
        # Simple query/response format
        messages.append({"role": "user", "content": sample["user_query"]})
        messages.append({"role": "assistant", "content": sample["response"]})

    return messages


def get_default_system_prompt(operator: str = "generic") -> str:
    """Get default system prompt for operator"""
    return f"""You are an Operations Control Center (OCC) advisor for {operator} metro operations.

Your role is to:
1. Analyze operational situations based on provided data
2. Identify likely causes of disruptions
3. Recommend appropriate actions
4. Quantify uncertainty in your assessments
5. Flag safety considerations

Important guidelines:
- You provide decision SUPPORT, not autonomous control
- All recommendations require human review and approval
- Never fabricate data - if information is unavailable, say so
- Always include confidence levels and uncertainties
- Prioritize safety over efficiency

Respond with structured analysis including:
- Summary of the situation
- Observed facts from provided data
- Inferred hypotheses with confidence levels
- Recommended actions with rationale
- Key uncertainties and risks"""


def preprocess_for_training(
    dataset: Dataset,
    tokenizer: PreTrainedTokenizer,
    config: DatasetConfig,
) -> Dataset:
    """
    Preprocess dataset for training.

    Args:
        dataset: Raw dataset
        tokenizer: Tokenizer to use
        config: Dataset configuration

    Returns:
        Preprocessed dataset ready for training
    """
    # Set chat template if needed
    if tokenizer.chat_template is None:
        template = CHAT_TEMPLATES.get(config.chat_template)
        if template:
            tokenizer.chat_template = template

    def process_sample(sample: dict) -> dict:
        """Process single sample"""
        messages = format_occ_messages(sample)

        # Apply chat template
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )

        # Add EOS if configured
        if config.add_eos and not text.endswith(tokenizer.eos_token or ""):
            text += tokenizer.eos_token or ""

        return {"text": text}

    # Process all samples
    processed = dataset.map(
        process_sample,
        remove_columns=dataset.column_names,
        desc="Formatting samples"
    )

    return processed


def create_train_test_split(
    dataset: Dataset,
    test_size: float = 0.1,
    seed: int = 42,
) -> DatasetDict:
    """
    Create train/test split from single dataset.

    Args:
        dataset: Dataset to split
        test_size: Fraction for test set
        seed: Random seed

    Returns:
        DatasetDict with train and test splits
    """
    split = dataset.train_test_split(test_size=test_size, seed=seed)
    return DatasetDict({
        "train": split["train"],
        "validation": split["test"]
    })


class DataCollatorForOCC:
    """Custom data collator for OCC training"""

    def __init__(
        self,
        tokenizer: PreTrainedTokenizer,
        max_length: int = 4096,
        padding: str = "max_length",
        return_tensors: str = "pt",
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.padding = padding
        self.return_tensors = return_tensors

    def __call__(self, features: list[dict]) -> dict:
        """Collate batch of features"""
        # Extract texts
        texts = [f["text"] for f in features]

        # Tokenize
        batch = self.tokenizer(
            texts,
            padding=self.padding,
            truncation=True,
            max_length=self.max_length,
            return_tensors=self.return_tensors,
        )

        # Create labels (same as input_ids for causal LM)
        batch["labels"] = batch["input_ids"].clone()

        # Mask padding tokens in labels
        batch["labels"][batch["labels"] == self.tokenizer.pad_token_id] = -100

        return batch


def get_dataset_statistics(dataset: Dataset) -> dict[str, Any]:
    """
    Compute statistics about dataset.

    Args:
        dataset: Dataset to analyze

    Returns:
        Dictionary of statistics
    """
    stats = {
        "num_samples": len(dataset),
        "columns": dataset.column_names,
    }

    # Count by operator if present
    if "operator" in dataset.column_names:
        operators = dataset["operator"]
        stats["operator_distribution"] = {}
        for op in set(operators):
            stats["operator_distribution"][op] = operators.count(op)

    # Count by task type if present
    if "task_type" in dataset.column_names:
        task_types = dataset["task_type"]
        stats["task_type_distribution"] = {}
        for tt in set(task_types):
            stats["task_type_distribution"][tt] = task_types.count(tt)

    return stats
