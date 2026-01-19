# Hyperparameter Tuning for LLM Fine-Tuning

> Reference for: Fine-Tuning Expert
> Load when: Learning rates, batch sizes, schedulers, training configuration, optimization

---

## Overview

Hyperparameter selection significantly impacts fine-tuning success. This reference provides practical guidance for learning rates, batch sizes, schedulers, and optimization strategies tailored to LLM fine-tuning.

## Learning Rate Selection

### Guidelines by Fine-Tuning Method

| Method | Typical Range | Starting Point | Notes |
|--------|---------------|----------------|-------|
| Full Fine-Tuning | 1e-6 to 5e-5 | 2e-5 | Lower for larger models |
| LoRA | 1e-5 to 3e-4 | 2e-4 | Can use higher LR |
| QLoRA | 1e-5 to 2e-4 | 1e-4 | Similar to LoRA |
| Prefix Tuning | 1e-4 to 1e-2 | 3e-4 | Only training embeddings |

### Learning Rate Finder

```python
import torch
import matplotlib.pyplot as plt
from transformers import Trainer, TrainingArguments

def find_learning_rate(
    model,
    train_dataset,
    tokenizer,
    min_lr: float = 1e-7,
    max_lr: float = 1e-2,
    num_steps: int = 100
) -> tuple[list[float], list[float]]:
    """
    Find optimal learning rate using LR range test.

    Returns:
        Tuple of (learning_rates, losses)
    """
    # Create temporary training args with linearly increasing LR
    training_args = TrainingArguments(
        output_dir="./lr_finder",
        max_steps=num_steps,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=max_lr,
        warmup_steps=0,
        logging_steps=1,
        save_strategy="no",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer
    )

    # Custom LR schedule that increases exponentially
    lrs = []
    losses = []
    multiplier = (max_lr / min_lr) ** (1 / num_steps)

    current_lr = min_lr
    for step in range(num_steps):
        # Set LR
        for param_group in trainer.optimizer.param_groups:
            param_group['lr'] = current_lr

        # Training step
        loss = trainer.training_step(model, next(iter(trainer.get_train_dataloader())))

        lrs.append(current_lr)
        losses.append(loss.item())

        current_lr *= multiplier

        # Stop if loss explodes
        if loss.item() > losses[0] * 10:
            break

    return lrs, losses

def plot_lr_finder(lrs: list[float], losses: list[float]):
    """Plot learning rate finder results."""
    plt.figure(figsize=(10, 6))
    plt.semilogx(lrs, losses)
    plt.xlabel("Learning Rate")
    plt.ylabel("Loss")
    plt.title("Learning Rate Finder")

    # Find suggested LR (steepest descent)
    gradients = [(losses[i+1] - losses[i]) / (lrs[i+1] - lrs[i])
                 for i in range(len(losses) - 1)]
    suggested_idx = gradients.index(min(gradients))
    suggested_lr = lrs[suggested_idx]

    plt.axvline(x=suggested_lr, color='r', linestyle='--',
                label=f'Suggested LR: {suggested_lr:.2e}')
    plt.legend()
    plt.savefig("lr_finder.png")
    print(f"Suggested learning rate: {suggested_lr:.2e}")

    return suggested_lr
```

## Batch Size Optimization

### Effective Batch Size Calculation

```python
def calculate_training_config(
    target_batch_size: int,
    gpu_memory_gb: float,
    model_size_b: float,
    sequence_length: int = 2048,
    method: str = "qlora"
) -> dict:
    """
    Calculate optimal batch size and gradient accumulation.

    Args:
        target_batch_size: Desired effective batch size
        gpu_memory_gb: Available GPU memory
        model_size_b: Model size in billions
        sequence_length: Maximum sequence length
        method: "full", "lora", or "qlora"
    """
    # Memory estimation (rough heuristics)
    memory_per_param = {
        "full": 20,      # bf16 params + optimizer states + gradients
        "lora": 4,       # bf16 inference + small trainable
        "qlora": 1.5     # 4-bit + small trainable
    }

    base_memory_gb = model_size_b * memory_per_param[method]
    available_for_batch = gpu_memory_gb - base_memory_gb

    # Memory per sample (rough estimate)
    tokens_per_gb = 1000 * (8 / model_size_b)  # Rough scaling
    max_samples_in_memory = int(available_for_batch * tokens_per_gb / sequence_length)
    max_batch_per_device = max(1, max_samples_in_memory)

    # Calculate gradient accumulation
    gradient_accumulation = max(1, target_batch_size // max_batch_per_device)
    actual_batch_per_device = min(max_batch_per_device, target_batch_size // gradient_accumulation)

    effective_batch_size = actual_batch_per_device * gradient_accumulation

    return {
        "per_device_train_batch_size": actual_batch_per_device,
        "gradient_accumulation_steps": gradient_accumulation,
        "effective_batch_size": effective_batch_size,
        "estimated_memory_gb": base_memory_gb + (actual_batch_per_device * sequence_length / tokens_per_gb)
    }

# Example usage
config = calculate_training_config(
    target_batch_size=32,
    gpu_memory_gb=24,  # RTX 4090
    model_size_b=8,    # Llama 3.1 8B
    method="qlora"
)
print(config)
# {'per_device_train_batch_size': 4, 'gradient_accumulation_steps': 8, 'effective_batch_size': 32, ...}
```

### Batch Size Guidelines

| Dataset Size | Recommended Batch Size | Notes |
|--------------|------------------------|-------|
| < 1,000 | 8-16 | Small batch for more updates |
| 1,000 - 10,000 | 16-32 | Standard batch size |
| 10,000 - 100,000 | 32-64 | Larger batch for stability |
| > 100,000 | 64-128 | Can use larger batches |

## Learning Rate Schedulers

```python
from transformers import get_scheduler
import torch

def create_scheduler(
    optimizer,
    scheduler_type: str,
    num_training_steps: int,
    warmup_ratio: float = 0.03,
    min_lr_ratio: float = 0.1
):
    """
    Create learning rate scheduler.

    Args:
        scheduler_type: "cosine", "linear", "constant_with_warmup", "cosine_with_restarts"
        num_training_steps: Total training steps
        warmup_ratio: Fraction of steps for warmup
        min_lr_ratio: Minimum LR as fraction of max (for cosine)
    """
    num_warmup_steps = int(num_training_steps * warmup_ratio)

    if scheduler_type == "cosine":
        scheduler = get_scheduler(
            "cosine",
            optimizer=optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps
        )
    elif scheduler_type == "cosine_with_min_lr":
        # Custom cosine with minimum LR
        from torch.optim.lr_scheduler import CosineAnnealingLR, SequentialLR, LinearLR

        warmup = LinearLR(
            optimizer,
            start_factor=0.01,
            end_factor=1.0,
            total_iters=num_warmup_steps
        )
        cosine = CosineAnnealingLR(
            optimizer,
            T_max=num_training_steps - num_warmup_steps,
            eta_min=optimizer.defaults['lr'] * min_lr_ratio
        )
        scheduler = SequentialLR(
            optimizer,
            schedulers=[warmup, cosine],
            milestones=[num_warmup_steps]
        )
    elif scheduler_type == "constant_with_warmup":
        scheduler = get_scheduler(
            "constant_with_warmup",
            optimizer=optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps
        )
    else:
        scheduler = get_scheduler(
            scheduler_type,
            optimizer=optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps
        )

    return scheduler

# Scheduler comparison
SCHEDULER_GUIDE = """
Scheduler Selection:
- cosine: Best for most fine-tuning tasks, smooth decay
- linear: Good for short training runs
- constant_with_warmup: For very short fine-tuning or when LR is already optimal
- cosine_with_restarts: For longer training with periodic exploration
"""
```

### Visualizing Schedulers

```python
def visualize_schedulers(num_steps: int = 1000, warmup_ratio: float = 0.03):
    """Plot different scheduler behaviors."""
    import matplotlib.pyplot as plt

    schedulers_to_plot = ["cosine", "linear", "constant_with_warmup"]
    base_lr = 2e-4

    plt.figure(figsize=(12, 6))

    for sched_type in schedulers_to_plot:
        # Create dummy optimizer
        dummy_param = torch.nn.Parameter(torch.zeros(1))
        optimizer = torch.optim.AdamW([dummy_param], lr=base_lr)

        scheduler = create_scheduler(
            optimizer,
            scheduler_type=sched_type,
            num_training_steps=num_steps,
            warmup_ratio=warmup_ratio
        )

        lrs = []
        for _ in range(num_steps):
            lrs.append(optimizer.param_groups[0]['lr'])
            scheduler.step()

        plt.plot(lrs, label=sched_type)

    plt.xlabel("Step")
    plt.ylabel("Learning Rate")
    plt.title("Learning Rate Schedulers")
    plt.legend()
    plt.savefig("schedulers.png")
```

## Complete Training Configuration

```python
from transformers import TrainingArguments
from dataclasses import dataclass
from typing import Optional

@dataclass
class FineTuningConfig:
    """Complete fine-tuning configuration."""
    # Model
    model_name: str
    method: str = "qlora"  # "full", "lora", "qlora"

    # LoRA specific
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    # Training
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 32
    max_seq_length: int = 2048

    # Scheduler
    scheduler_type: str = "cosine"
    warmup_ratio: float = 0.03

    # Optimization
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8

    # Hardware
    gradient_checkpointing: bool = True
    bf16: bool = True
    tf32: bool = True

    # Evaluation
    eval_steps: int = 100
    save_steps: int = 100
    logging_steps: int = 10


def create_training_args(
    config: FineTuningConfig,
    output_dir: str,
    gpu_memory_gb: float
) -> TrainingArguments:
    """Create TrainingArguments from config."""

    # Calculate batch configuration
    batch_config = calculate_training_config(
        target_batch_size=config.batch_size,
        gpu_memory_gb=gpu_memory_gb,
        model_size_b=8,  # Estimate or pass as parameter
        sequence_length=config.max_seq_length,
        method=config.method
    )

    return TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config.num_epochs,

        # Batch size
        per_device_train_batch_size=batch_config["per_device_train_batch_size"],
        per_device_eval_batch_size=batch_config["per_device_train_batch_size"],
        gradient_accumulation_steps=batch_config["gradient_accumulation_steps"],

        # Learning rate
        learning_rate=config.learning_rate,
        lr_scheduler_type=config.scheduler_type,
        warmup_ratio=config.warmup_ratio,

        # Optimization
        weight_decay=config.weight_decay,
        max_grad_norm=config.max_grad_norm,
        adam_beta1=config.adam_beta1,
        adam_beta2=config.adam_beta2,
        adam_epsilon=config.adam_epsilon,
        optim="paged_adamw_8bit" if config.method == "qlora" else "adamw_torch",

        # Hardware
        gradient_checkpointing=config.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=config.bf16,
        tf32=config.tf32,

        # Evaluation and saving
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_strategy="steps",
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        # Misc
        group_by_length=True,
        report_to=["wandb"],
        run_name=f"{config.model_name.split('/')[-1]}-{config.method}"
    )
```

## Hyperparameter Search

```python
from typing import Any
import optuna
from transformers import Trainer

def hyperparameter_search(
    model_init,
    train_dataset,
    eval_dataset,
    tokenizer,
    n_trials: int = 20,
    direction: str = "minimize"
) -> dict[str, Any]:
    """
    Run hyperparameter search using Optuna.

    Args:
        model_init: Function that returns initialized model
        n_trials: Number of trials to run
        direction: "minimize" for loss, "maximize" for accuracy
    """
    def hp_space(trial: optuna.Trial) -> dict:
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 3e-4, log=True),
            "per_device_train_batch_size": trial.suggest_categorical(
                "per_device_train_batch_size", [2, 4, 8]
            ),
            "num_train_epochs": trial.suggest_int("num_train_epochs", 1, 5),
            "warmup_ratio": trial.suggest_float("warmup_ratio", 0.0, 0.1),
            "weight_decay": trial.suggest_float("weight_decay", 0.0, 0.1),
            "lr_scheduler_type": trial.suggest_categorical(
                "lr_scheduler_type", ["cosine", "linear", "constant_with_warmup"]
            )
        }

    training_args = TrainingArguments(
        output_dir="./hp_search",
        evaluation_strategy="epoch",
        save_strategy="no",
        report_to="none"
    )

    trainer = Trainer(
        model_init=model_init,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer
    )

    best_trial = trainer.hyperparameter_search(
        hp_space=hp_space,
        backend="optuna",
        n_trials=n_trials,
        direction=direction
    )

    return best_trial.hyperparameters

# Usage
# best_params = hyperparameter_search(model_init, train_ds, eval_ds, tokenizer)
```

## Monitoring Training

```python
from transformers import TrainerCallback
import wandb

class FineTuningCallback(TrainerCallback):
    """Custom callback for fine-tuning monitoring."""

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return

        # Calculate additional metrics
        if "loss" in logs and state.global_step > 0:
            # Track loss velocity
            if hasattr(self, "prev_loss"):
                loss_delta = logs["loss"] - self.prev_loss
                logs["loss_delta"] = loss_delta
            self.prev_loss = logs["loss"]

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics is None:
            return

        # Log evaluation metrics
        train_loss = state.log_history[-1].get("loss", 0) if state.log_history else 0
        eval_loss = metrics.get("eval_loss", 0)

        # Warn if overfitting
        if train_loss > 0 and eval_loss > train_loss * 1.5:
            print(f"Warning: Potential overfitting. Train loss: {train_loss:.4f}, Eval loss: {eval_loss:.4f}")

# Add to trainer
# trainer.add_callback(FineTuningCallback())
```

## Quick Reference

### Recommended Starting Configurations

**Small Dataset (<1K examples), QLoRA:**
```python
TrainingArguments(
    learning_rate=1e-4,
    num_train_epochs=5,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    weight_decay=0.05,
    max_grad_norm=0.3
)
```

**Medium Dataset (1K-10K examples), LoRA:**
```python
TrainingArguments(
    learning_rate=2e-4,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.01,
    max_grad_norm=1.0
)
```

**Large Dataset (>10K examples), Full Fine-Tuning:**
```python
TrainingArguments(
    learning_rate=2e-5,
    num_train_epochs=2,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.01,
    max_grad_norm=1.0
)
```

## Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Loss not decreasing | LR too low or too high | Use LR finder, try 10x or 0.1x |
| Loss spikes | LR too high, no warmup | Add warmup, reduce LR |
| Overfitting | Dataset too small, epochs too high | Reduce epochs, increase dropout |
| Underfitting | LR too low, rank too low (LoRA) | Increase LR, increase rank |
| OOM errors | Batch too large | Reduce batch, increase grad accum |

## Related References

- `lora-peft.md` - LoRA rank and alpha selection
- `evaluation-metrics.md` - Tracking training progress
- `dataset-preparation.md` - Dataset size impacts on hyperparameters
