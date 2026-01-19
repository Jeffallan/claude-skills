# Dataset Preparation for Fine-Tuning

> Reference for: Fine-Tuning Expert
> Load when: Training data formatting, quality checks, dataset creation, data validation

---

## Overview

Dataset quality is the most important factor in fine-tuning success. This reference covers data formatting, validation, cleaning, and best practices for creating high-quality training data.

## Dataset Formats

### Alpaca Format (Instruction-Response)

```python
# Single-turn instruction format
alpaca_example = {
    "instruction": "Summarize the following article in 2-3 sentences.",
    "input": "The article text goes here...",
    "output": "The summary goes here."
}

# Without input field
alpaca_no_input = {
    "instruction": "What are the three primary colors?",
    "input": "",
    "output": "The three primary colors are red, blue, and yellow."
}
```

### ShareGPT Format (Multi-Turn Conversations)

```python
# Multi-turn conversation format
sharegpt_example = {
    "conversations": [
        {"from": "human", "value": "What is machine learning?"},
        {"from": "gpt", "value": "Machine learning is a subset of AI that enables..."},
        {"from": "human", "value": "Can you give me an example?"},
        {"from": "gpt", "value": "A common example is email spam filtering..."}
    ]
}

# Alternative format with roles
openai_format = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is..."}
    ]
}
```

### Converting Between Formats

```python
from typing import TypedDict
from datasets import Dataset

class AlpacaExample(TypedDict):
    instruction: str
    input: str
    output: str

class ShareGPTExample(TypedDict):
    conversations: list[dict[str, str]]

def alpaca_to_sharegpt(example: AlpacaExample) -> ShareGPTExample:
    """Convert Alpaca format to ShareGPT multi-turn format."""
    user_content = example["instruction"]
    if example.get("input"):
        user_content += f"\n\n{example['input']}"

    return {
        "conversations": [
            {"from": "human", "value": user_content},
            {"from": "gpt", "value": example["output"]}
        ]
    }

def sharegpt_to_messages(example: ShareGPTExample, system_prompt: str = "") -> dict:
    """Convert ShareGPT to OpenAI messages format."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    role_map = {"human": "user", "gpt": "assistant", "system": "system"}
    for turn in example["conversations"]:
        messages.append({
            "role": role_map.get(turn["from"], turn["from"]),
            "content": turn["value"]
        })

    return {"messages": messages}
```

## Formatting for Training

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")

def format_instruction_prompt(
    instruction: str,
    input_text: str = "",
    response: str = "",
    system_prompt: str = "You are a helpful assistant."
) -> str:
    """Format for Llama 3.1 Instruct chat template."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{instruction}\n{input_text}".strip()},
    ]
    if response:
        messages.append({"role": "assistant", "content": response})

    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=not response  # Add prompt if no response
    )

# Example usage
formatted = format_instruction_prompt(
    instruction="Translate to French:",
    input_text="Hello, how are you?",
    response="Bonjour, comment allez-vous?"
)
```

## Dataset Validation

```python
from dataclasses import dataclass
from collections import Counter
import re

@dataclass
class DatasetStats:
    total_examples: int
    avg_input_length: float
    avg_output_length: float
    max_input_length: int
    max_output_length: int
    empty_inputs: int
    empty_outputs: int
    duplicate_count: int
    language_distribution: dict

def validate_dataset(examples: list[dict], tokenizer) -> tuple[DatasetStats, list[str]]:
    """
    Validate dataset and return statistics and warnings.

    Args:
        examples: List of training examples
        tokenizer: Tokenizer for length calculations

    Returns:
        Tuple of (stats, warnings)
    """
    warnings = []
    input_lengths = []
    output_lengths = []
    seen_inputs = set()
    duplicates = 0

    for i, ex in enumerate(examples):
        # Check for required fields
        if "instruction" not in ex and "messages" not in ex:
            warnings.append(f"Example {i}: Missing instruction or messages field")
            continue

        # Get input/output text
        if "instruction" in ex:
            input_text = f"{ex.get('instruction', '')} {ex.get('input', '')}".strip()
            output_text = ex.get("output", "")
        else:
            input_text = " ".join(m["content"] for m in ex["messages"] if m["role"] == "user")
            output_text = " ".join(m["content"] for m in ex["messages"] if m["role"] == "assistant")

        # Check for empty fields
        if not input_text:
            warnings.append(f"Example {i}: Empty input")
        if not output_text:
            warnings.append(f"Example {i}: Empty output")

        # Check lengths
        input_len = len(tokenizer.encode(input_text))
        output_len = len(tokenizer.encode(output_text))
        input_lengths.append(input_len)
        output_lengths.append(output_len)

        if input_len + output_len > 4096:
            warnings.append(f"Example {i}: Total length {input_len + output_len} exceeds 4096")

        # Check for duplicates
        input_hash = hash(input_text)
        if input_hash in seen_inputs:
            duplicates += 1
        seen_inputs.add(input_hash)

    stats = DatasetStats(
        total_examples=len(examples),
        avg_input_length=sum(input_lengths) / len(input_lengths) if input_lengths else 0,
        avg_output_length=sum(output_lengths) / len(output_lengths) if output_lengths else 0,
        max_input_length=max(input_lengths) if input_lengths else 0,
        max_output_length=max(output_lengths) if output_lengths else 0,
        empty_inputs=sum(1 for w in warnings if "Empty input" in w),
        empty_outputs=sum(1 for w in warnings if "Empty output" in w),
        duplicate_count=duplicates,
        language_distribution={}  # Implement language detection if needed
    )

    return stats, warnings
```

## Data Quality Checks

```python
import re
from typing import Callable

def create_quality_filter(
    min_input_tokens: int = 10,
    max_input_tokens: int = 2048,
    min_output_tokens: int = 5,
    max_output_tokens: int = 2048,
    custom_filters: list[Callable[[dict], bool]] = None
) -> Callable[[dict, AutoTokenizer], bool]:
    """
    Create a quality filter function for dataset examples.

    Returns True if example passes all quality checks.
    """
    def quality_filter(example: dict, tokenizer) -> bool:
        if "instruction" in example:
            input_text = f"{example.get('instruction', '')} {example.get('input', '')}".strip()
            output_text = example.get("output", "")
        else:
            input_text = " ".join(m["content"] for m in example.get("messages", []) if m["role"] == "user")
            output_text = " ".join(m["content"] for m in example.get("messages", []) if m["role"] == "assistant")

        # Length checks
        input_tokens = len(tokenizer.encode(input_text))
        output_tokens = len(tokenizer.encode(output_text))

        if not (min_input_tokens <= input_tokens <= max_input_tokens):
            return False
        if not (min_output_tokens <= output_tokens <= max_output_tokens):
            return False

        # Quality checks
        if not output_text.strip():
            return False

        # Check for common issues
        bad_patterns = [
            r"I cannot",
            r"I'm sorry, but",
            r"As an AI",
            r"I don't have access",
            r"\[.*\]$",  # Trailing brackets
        ]
        for pattern in bad_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                return False

        # Custom filters
        if custom_filters:
            for filter_fn in custom_filters:
                if not filter_fn(example):
                    return False

        return True

    return quality_filter

# Usage
quality_filter = create_quality_filter(min_output_tokens=20)
filtered_dataset = [ex for ex in dataset if quality_filter(ex, tokenizer)]
```

## Deduplication

```python
from datasketch import MinHash, MinHashLSH
import hashlib

def exact_dedup(examples: list[dict], key_field: str = "instruction") -> list[dict]:
    """Remove exact duplicates based on a key field."""
    seen = set()
    unique = []
    for ex in examples:
        key = ex.get(key_field, "")
        if key not in seen:
            seen.add(key)
            unique.append(ex)
    return unique

def fuzzy_dedup(
    examples: list[dict],
    key_field: str = "output",
    threshold: float = 0.8,
    num_perm: int = 128
) -> list[dict]:
    """
    Remove near-duplicate examples using MinHash LSH.

    Args:
        examples: List of examples
        key_field: Field to check for similarity
        threshold: Jaccard similarity threshold (0-1)
        num_perm: Number of permutations for MinHash
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    unique = []

    for i, ex in enumerate(examples):
        text = ex.get(key_field, "")
        words = text.lower().split()

        # Create MinHash
        m = MinHash(num_perm=num_perm)
        for word in words:
            m.update(word.encode('utf-8'))

        # Check for near-duplicates
        result = lsh.query(m)
        if not result:
            lsh.insert(str(i), m)
            unique.append(ex)

    return unique

# Combined deduplication pipeline
def deduplicate_dataset(examples: list[dict]) -> list[dict]:
    """Full deduplication pipeline."""
    print(f"Starting examples: {len(examples)}")

    # Step 1: Exact deduplication on input
    examples = exact_dedup(examples, key_field="instruction")
    print(f"After exact dedup on instruction: {len(examples)}")

    # Step 2: Fuzzy deduplication on output
    examples = fuzzy_dedup(examples, key_field="output", threshold=0.85)
    print(f"After fuzzy dedup on output: {len(examples)}")

    return examples
```

## Train/Validation Split

```python
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
import random

def create_stratified_split(
    examples: list[dict],
    test_size: float = 0.1,
    stratify_field: str = None,
    seed: int = 42
) -> DatasetDict:
    """
    Create train/validation split with optional stratification.

    Args:
        examples: List of examples
        test_size: Fraction for validation set
        stratify_field: Field to stratify by (e.g., "category")
        seed: Random seed for reproducibility
    """
    if stratify_field and all(stratify_field in ex for ex in examples):
        stratify = [ex[stratify_field] for ex in examples]
        train_examples, val_examples = train_test_split(
            examples,
            test_size=test_size,
            stratify=stratify,
            random_state=seed
        )
    else:
        random.seed(seed)
        shuffled = examples.copy()
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * (1 - test_size))
        train_examples = shuffled[:split_idx]
        val_examples = shuffled[split_idx:]

    return DatasetDict({
        "train": Dataset.from_list(train_examples),
        "validation": Dataset.from_list(val_examples)
    })
```

## Data Augmentation

```python
import random

def augment_instruction(example: dict) -> list[dict]:
    """Generate augmented versions of an instruction example."""
    augmented = [example]

    instruction = example.get("instruction", "")
    input_text = example.get("input", "")
    output = example.get("output", "")

    # Instruction paraphrasing templates
    prefixes = [
        "",
        "Please ",
        "Can you ",
        "I need you to ",
        "Your task is to ",
    ]
    suffixes = [
        "",
        " Be concise.",
        " Provide a detailed response.",
        " Think step by step.",
    ]

    # Generate variations
    for prefix in random.sample(prefixes, min(2, len(prefixes))):
        for suffix in random.sample(suffixes, min(2, len(suffixes))):
            new_instruction = f"{prefix}{instruction[0].lower() if prefix else instruction[0]}{instruction[1:]}{suffix}"
            if new_instruction != instruction:
                augmented.append({
                    "instruction": new_instruction.strip(),
                    "input": input_text,
                    "output": output
                })

    return augmented

def augment_dataset(examples: list[dict], augmentation_factor: float = 1.5) -> list[dict]:
    """
    Augment dataset to reach target size.

    Args:
        examples: Original examples
        augmentation_factor: Target size as multiple of original
    """
    augmented = []
    target_size = int(len(examples) * augmentation_factor)

    for ex in examples:
        variations = augment_instruction(ex)
        augmented.extend(variations)

    # Deduplicate and trim to target
    augmented = exact_dedup(augmented, "instruction")
    random.shuffle(augmented)
    return augmented[:target_size]
```

## Loading and Saving Datasets

```python
from datasets import load_dataset, Dataset
import json

def load_custom_dataset(path: str) -> Dataset:
    """Load dataset from various formats."""
    if path.endswith(".jsonl"):
        return load_dataset("json", data_files=path, split="train")
    elif path.endswith(".json"):
        with open(path, "r") as f:
            data = json.load(f)
        return Dataset.from_list(data)
    elif path.endswith(".parquet"):
        return load_dataset("parquet", data_files=path, split="train")
    else:
        # Try loading from Hugging Face Hub
        return load_dataset(path, split="train")

def save_dataset(dataset: Dataset, path: str, format: str = "jsonl"):
    """Save dataset in specified format."""
    if format == "jsonl":
        dataset.to_json(path, orient="records", lines=True)
    elif format == "parquet":
        dataset.to_parquet(path)
    elif format == "json":
        with open(path, "w") as f:
            json.dump(list(dataset), f, indent=2)
```

## Dataset Size Guidelines

| Task Type | Minimum Examples | Recommended | Notes |
|-----------|------------------|-------------|-------|
| Classification | 100 per class | 500+ per class | Balance classes |
| Instruction Following | 1,000 | 5,000-10,000 | Diverse instructions |
| Domain Adaptation | 5,000 | 20,000+ | High-quality domain data |
| Code Generation | 2,000 | 10,000+ | Include edge cases |
| Multi-turn Chat | 1,000 conversations | 5,000+ | Varied conversation lengths |

## Quick Reference

```python
# Complete dataset preparation pipeline
from datasets import Dataset

def prepare_dataset(raw_data_path: str, output_path: str, tokenizer) -> Dataset:
    """Full dataset preparation pipeline."""
    # 1. Load raw data
    examples = load_custom_dataset(raw_data_path)

    # 2. Validate
    stats, warnings = validate_dataset(list(examples), tokenizer)
    print(f"Dataset stats: {stats}")
    if warnings[:10]:  # Show first 10 warnings
        print(f"Sample warnings: {warnings[:10]}")

    # 3. Filter for quality
    quality_filter = create_quality_filter()
    examples = [ex for ex in examples if quality_filter(ex, tokenizer)]
    print(f"After quality filter: {len(examples)}")

    # 4. Deduplicate
    examples = deduplicate_dataset(examples)
    print(f"After deduplication: {len(examples)}")

    # 5. Split
    dataset = create_stratified_split(examples, test_size=0.1)

    # 6. Save
    dataset["train"].to_json(f"{output_path}/train.jsonl", lines=True)
    dataset["validation"].to_json(f"{output_path}/val.jsonl", lines=True)

    return dataset

# Usage
dataset = prepare_dataset("raw_data.jsonl", "./processed", tokenizer)
```

## Related References

- `lora-peft.md` - Training configuration
- `evaluation-metrics.md` - Measuring dataset quality impact
- `hyperparameter-tuning.md` - Adjusting training for dataset size
