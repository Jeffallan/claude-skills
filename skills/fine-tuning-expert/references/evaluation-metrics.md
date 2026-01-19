# Evaluation Metrics for Fine-Tuned Models

> Reference for: Fine-Tuning Expert
> Load when: Benchmarking, metrics, model comparison, evaluation frameworks, testing

---

## Overview

Proper evaluation is critical for understanding fine-tuning success. This reference covers metrics, benchmarking strategies, and evaluation frameworks for fine-tuned language models.

## Core Metrics

### Perplexity

```python
import torch
import math
from transformers import AutoModelForCausalLM, AutoTokenizer
from torch.utils.data import DataLoader
from tqdm import tqdm

def calculate_perplexity(
    model,
    tokenizer,
    texts: list[str],
    batch_size: int = 8,
    max_length: int = 2048
) -> float:
    """
    Calculate perplexity on a test set.

    Lower perplexity = better language modeling performance.
    """
    model.eval()
    total_loss = 0
    total_tokens = 0

    encodings = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding=True,
        return_tensors="pt"
    )

    dataset = torch.utils.data.TensorDataset(
        encodings["input_ids"],
        encodings["attention_mask"]
    )
    dataloader = DataLoader(dataset, batch_size=batch_size)

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Calculating perplexity"):
            input_ids, attention_mask = batch
            input_ids = input_ids.to(model.device)
            attention_mask = attention_mask.to(model.device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=input_ids
            )

            # Count actual tokens (not padding)
            num_tokens = attention_mask.sum().item()
            total_loss += outputs.loss.item() * num_tokens
            total_tokens += num_tokens

    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)

    return perplexity

# Usage
# perplexity = calculate_perplexity(model, tokenizer, test_texts)
# print(f"Perplexity: {perplexity:.2f}")
```

### Generation-Based Metrics

```python
from evaluate import load
import numpy as np

def evaluate_generation(
    model,
    tokenizer,
    test_examples: list[dict],
    max_new_tokens: int = 256
) -> dict:
    """
    Evaluate model generation quality with multiple metrics.

    Args:
        test_examples: List of {"input": str, "reference": str}
    """
    # Load metrics
    bleu = load("bleu")
    rouge = load("rouge")
    bertscore = load("bertscore")

    predictions = []
    references = []

    model.eval()
    for example in tqdm(test_examples, desc="Generating"):
        inputs = tokenizer(example["input"], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,  # Greedy for reproducibility
                pad_token_id=tokenizer.pad_token_id
            )

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove input from prediction if model includes it
        prediction = prediction[len(example["input"]):].strip()

        predictions.append(prediction)
        references.append(example["reference"])

    # Calculate metrics
    results = {}

    # BLEU (0-100, higher is better)
    bleu_result = bleu.compute(predictions=predictions, references=[[r] for r in references])
    results["bleu"] = bleu_result["bleu"] * 100

    # ROUGE (0-1, higher is better)
    rouge_result = rouge.compute(predictions=predictions, references=references)
    results["rouge1"] = rouge_result["rouge1"]
    results["rouge2"] = rouge_result["rouge2"]
    results["rougeL"] = rouge_result["rougeL"]

    # BERTScore (0-1, higher is better)
    bertscore_result = bertscore.compute(
        predictions=predictions,
        references=references,
        lang="en"
    )
    results["bertscore_f1"] = np.mean(bertscore_result["f1"])

    return results

# Example
# metrics = evaluate_generation(model, tokenizer, test_data)
# print(f"BLEU: {metrics['bleu']:.2f}, ROUGE-L: {metrics['rougeL']:.4f}")
```

### Task-Specific Metrics

```python
from sklearn.metrics import accuracy_score, f1_score, classification_report
import re

def evaluate_classification(
    model,
    tokenizer,
    test_examples: list[dict],
    labels: list[str]
) -> dict:
    """
    Evaluate fine-tuned model on classification task.

    Args:
        test_examples: List of {"input": str, "label": str}
        labels: List of valid label strings
    """
    predictions = []
    true_labels = []

    model.eval()
    for example in tqdm(test_examples, desc="Classifying"):
        inputs = tokenizer(example["input"], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id
            )

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        prediction = prediction[len(example["input"]):].strip().lower()

        # Extract label from prediction
        predicted_label = None
        for label in labels:
            if label.lower() in prediction:
                predicted_label = label
                break

        if predicted_label is None:
            predicted_label = labels[0]  # Default to first label

        predictions.append(predicted_label)
        true_labels.append(example["label"])

    return {
        "accuracy": accuracy_score(true_labels, predictions),
        "f1_macro": f1_score(true_labels, predictions, average="macro"),
        "f1_weighted": f1_score(true_labels, predictions, average="weighted"),
        "classification_report": classification_report(true_labels, predictions)
    }

def evaluate_extraction(
    model,
    tokenizer,
    test_examples: list[dict]
) -> dict:
    """
    Evaluate information extraction tasks.

    Args:
        test_examples: List of {"input": str, "expected_entities": list[str]}
    """
    total_precision = 0
    total_recall = 0
    total_f1 = 0

    for example in test_examples:
        inputs = tokenizer(example["input"], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=256, do_sample=False)

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        prediction = prediction[len(example["input"]):].strip()

        # Extract entities (customize based on output format)
        predicted_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', prediction))
        expected_entities = set(example["expected_entities"])

        # Calculate metrics
        if len(predicted_entities) > 0:
            precision = len(predicted_entities & expected_entities) / len(predicted_entities)
        else:
            precision = 0

        if len(expected_entities) > 0:
            recall = len(predicted_entities & expected_entities) / len(expected_entities)
        else:
            recall = 1.0

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0

        total_precision += precision
        total_recall += recall
        total_f1 += f1

    n = len(test_examples)
    return {
        "precision": total_precision / n,
        "recall": total_recall / n,
        "f1": total_f1 / n
    }
```

## Evaluation Framework

```python
from dataclasses import dataclass, field
from typing import Callable, Any
import json
from datetime import datetime

@dataclass
class EvaluationSuite:
    """Complete evaluation suite for fine-tuned models."""
    name: str
    metrics: dict[str, Callable] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)

    def add_metric(self, name: str, metric_fn: Callable):
        """Add a metric to the suite."""
        self.metrics[name] = metric_fn

    def run(self, model, tokenizer, test_data: dict) -> dict:
        """Run all metrics and return results."""
        self.results = {
            "model_name": getattr(model.config, "_name_or_path", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }

        for metric_name, metric_fn in self.metrics.items():
            print(f"Running {metric_name}...")
            try:
                result = metric_fn(model, tokenizer, test_data.get(metric_name, test_data))
                self.results["metrics"][metric_name] = result
            except Exception as e:
                self.results["metrics"][metric_name] = {"error": str(e)}

        return self.results

    def save_results(self, path: str):
        """Save results to JSON file."""
        with open(path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

    def compare_with(self, other_results: dict) -> dict:
        """Compare results with another evaluation."""
        comparison = {}
        for metric_name, value in self.results["metrics"].items():
            if metric_name in other_results.get("metrics", {}):
                other_value = other_results["metrics"][metric_name]
                if isinstance(value, (int, float)) and isinstance(other_value, (int, float)):
                    comparison[metric_name] = {
                        "current": value,
                        "baseline": other_value,
                        "delta": value - other_value,
                        "delta_pct": ((value - other_value) / other_value * 100)
                                     if other_value != 0 else 0
                    }
        return comparison

# Usage example
def create_evaluation_suite() -> EvaluationSuite:
    suite = EvaluationSuite(name="fine_tuning_eval")

    # Add perplexity
    suite.add_metric("perplexity", lambda m, t, d: calculate_perplexity(m, t, d["texts"]))

    # Add generation metrics
    suite.add_metric("generation", lambda m, t, d: evaluate_generation(m, t, d["generation"]))

    return suite

# Run evaluation
# suite = create_evaluation_suite()
# results = suite.run(model, tokenizer, test_data)
# suite.save_results("eval_results.json")
```

## Model Comparison

```python
import pandas as pd
from typing import Optional

class ModelComparison:
    """Compare multiple fine-tuned models."""

    def __init__(self):
        self.models = {}
        self.results = {}

    def add_model(self, name: str, model, tokenizer, adapter_path: Optional[str] = None):
        """Register a model for comparison."""
        self.models[name] = {
            "model": model,
            "tokenizer": tokenizer,
            "adapter_path": adapter_path
        }

    def evaluate_all(self, test_data: dict, metrics: list[str]) -> pd.DataFrame:
        """Evaluate all models and return comparison DataFrame."""
        all_results = []

        for model_name, model_info in self.models.items():
            model = model_info["model"]
            tokenizer = model_info["tokenizer"]

            model_results = {"model": model_name}

            for metric in metrics:
                if metric == "perplexity":
                    model_results["perplexity"] = calculate_perplexity(
                        model, tokenizer, test_data["texts"]
                    )
                elif metric == "generation":
                    gen_metrics = evaluate_generation(
                        model, tokenizer, test_data["generation"]
                    )
                    model_results.update(gen_metrics)

            all_results.append(model_results)
            self.results[model_name] = model_results

        return pd.DataFrame(all_results)

    def get_best_model(self, metric: str, higher_is_better: bool = True) -> str:
        """Return name of best performing model for a metric."""
        if not self.results:
            raise ValueError("No results available. Run evaluate_all first.")

        values = {name: r.get(metric, float('-inf') if higher_is_better else float('inf'))
                  for name, r in self.results.items()}

        if higher_is_better:
            return max(values, key=values.get)
        else:
            return min(values, key=values.get)

# Usage
# comparison = ModelComparison()
# comparison.add_model("base", base_model, tokenizer)
# comparison.add_model("lora_r8", lora_model_r8, tokenizer)
# comparison.add_model("lora_r16", lora_model_r16, tokenizer)
# df = comparison.evaluate_all(test_data, ["perplexity", "generation"])
# print(df)
```

## LLM-as-Judge Evaluation

```python
from openai import OpenAI
import json

def llm_judge_evaluation(
    predictions: list[str],
    references: list[str],
    inputs: list[str],
    judge_model: str = "gpt-4o",
    criteria: list[str] = None
) -> list[dict]:
    """
    Use LLM as judge to evaluate generation quality.

    Args:
        predictions: Model outputs
        references: Reference/gold outputs
        inputs: Original inputs
        judge_model: Model to use as judge
        criteria: Evaluation criteria (default: helpfulness, accuracy, coherence)
    """
    if criteria is None:
        criteria = ["helpfulness", "accuracy", "coherence", "relevance"]

    client = OpenAI()

    judge_prompt = """You are an expert evaluator. Rate the following model response on a scale of 1-5 for each criterion.

Input: {input}

Reference Response: {reference}

Model Response: {prediction}

Rate the model response on these criteria (1=poor, 5=excellent):
{criteria_list}

Return your ratings as JSON: {{"criterion_name": score, ...}}
Also include a brief explanation for each rating."""

    results = []

    for input_text, pred, ref in zip(inputs, predictions, references):
        prompt = judge_prompt.format(
            input=input_text,
            reference=ref,
            prediction=pred,
            criteria_list="\n".join(f"- {c}" for c in criteria)
        )

        response = client.chat.completions.create(
            model=judge_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Parse response
        try:
            content = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                scores = json.loads(json_match.group())
            else:
                scores = {c: 3 for c in criteria}  # Default scores
        except:
            scores = {c: 3 for c in criteria}

        results.append({
            "input": input_text,
            "prediction": pred,
            "reference": ref,
            "scores": scores,
            "raw_response": content
        })

    # Aggregate scores
    aggregated = {c: [] for c in criteria}
    for r in results:
        for c in criteria:
            if c in r["scores"]:
                aggregated[c].append(r["scores"][c])

    summary = {c: sum(scores) / len(scores) if scores else 0
               for c, scores in aggregated.items()}

    return {
        "individual_results": results,
        "summary": summary
    }
```

## Benchmark Suites

```python
from lm_eval import evaluator
from lm_eval.models.huggingface import HFLM

def run_standard_benchmarks(
    model,
    tokenizer,
    tasks: list[str] = None,
    num_fewshot: int = 0
) -> dict:
    """
    Run standard LLM benchmarks using lm-evaluation-harness.

    Args:
        model: HuggingFace model
        tokenizer: Tokenizer
        tasks: List of tasks (default: common benchmarks)
        num_fewshot: Number of few-shot examples
    """
    if tasks is None:
        tasks = [
            "hellaswag",      # Commonsense reasoning
            "arc_easy",       # Science questions
            "arc_challenge",  # Harder science questions
            "winogrande",     # Commonsense reasoning
            "mmlu",           # Multi-task language understanding
            "truthfulqa_mc",  # Truthfulness
        ]

    # Wrap model for lm-eval
    lm = HFLM(pretrained=model, tokenizer=tokenizer)

    results = evaluator.simple_evaluate(
        model=lm,
        tasks=tasks,
        num_fewshot=num_fewshot,
        batch_size="auto"
    )

    # Extract key metrics
    summary = {}
    for task in tasks:
        if task in results["results"]:
            task_results = results["results"][task]
            # Get primary metric (usually accuracy)
            for key, value in task_results.items():
                if "acc" in key or "accuracy" in key:
                    summary[task] = value
                    break

    return {
        "full_results": results,
        "summary": summary
    }

# Usage with common benchmarks
BENCHMARK_TASKS = {
    "reasoning": ["hellaswag", "winogrande", "arc_easy", "arc_challenge"],
    "knowledge": ["mmlu", "triviaqa"],
    "code": ["humaneval", "mbpp"],
    "math": ["gsm8k", "math"],
    "safety": ["truthfulqa_mc", "toxigen"]
}
```

## Quick Reference

### Metric Selection by Task

| Task Type | Primary Metrics | Secondary Metrics |
|-----------|-----------------|-------------------|
| General Fine-Tuning | Perplexity, Loss | ROUGE, BLEU |
| Classification | Accuracy, F1 | Precision, Recall |
| Generation | ROUGE-L, BERTScore | Human eval, LLM-as-judge |
| Summarization | ROUGE-1/2/L | BERTScore, factuality |
| Translation | BLEU, chrF | TER, COMET |
| Code | pass@k, HumanEval | CodeBLEU |
| Chat/Assistant | LLM-as-judge | User preference |

### Interpreting Results

| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|------------|------|-----------|
| Perplexity | >50 | 20-50 | 10-20 | <10 |
| BLEU | <20 | 20-40 | 40-60 | >60 |
| ROUGE-L | <0.3 | 0.3-0.5 | 0.5-0.7 | >0.7 |
| BERTScore F1 | <0.7 | 0.7-0.85 | 0.85-0.92 | >0.92 |
| Accuracy | <0.6 | 0.6-0.8 | 0.8-0.9 | >0.9 |

## Related References

- `hyperparameter-tuning.md` - Adjusting training based on eval results
- `dataset-preparation.md` - Creating evaluation sets
- `deployment-optimization.md` - Production evaluation considerations
