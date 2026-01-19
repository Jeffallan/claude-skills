# Training Pipelines

> Reference for: ML Pipeline Expert
> Load when: Training orchestration, distributed training, hyperparameter tuning, resource management

---

## Overview

Training pipelines orchestrate the end-to-end model training process including data loading, distributed training, hyperparameter optimization, and artifact management. Production pipelines require reproducibility, scalability, and proper resource management.

## When to Use This Reference

- Setting up distributed training with PyTorch/TensorFlow
- Implementing hyperparameter tuning (Optuna, Ray Tune)
- Managing GPU/TPU resources for training
- Building reproducible training environments
- Creating checkpointing and fault-tolerant training

## When NOT to Use

- Quick model prototyping (use notebooks)
- Small models that fit in memory on single GPU
- One-off experiments without production requirements

---

## PyTorch Training Pipeline

### Complete Training Script

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import json

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Training hyperparameters and settings."""
    model_name: str
    batch_size: int = 32
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    epochs: int = 10
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    seed: int = 42
    checkpoint_dir: str = "./checkpoints"
    log_every_n_steps: int = 100
    eval_every_n_steps: int = 500
    save_every_n_steps: int = 1000
    mixed_precision: bool = True
    gradient_accumulation_steps: int = 1

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "TrainingConfig":
        return cls(**d)


class Trainer:
    """Production-grade PyTorch trainer."""

    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig,
        train_dataloader: DataLoader,
        eval_dataloader: Optional[DataLoader] = None,
        experiment_tracker=None,
    ):
        self.model = model
        self.config = config
        self.train_dataloader = train_dataloader
        self.eval_dataloader = eval_dataloader
        self.tracker = experiment_tracker

        self._setup_device()
        self._setup_training()
        self._setup_checkpointing()

    def _setup_device(self) -> None:
        """Configure device and move model."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

        if self.config.mixed_precision and self.device.type == "cuda":
            self.scaler = torch.amp.GradScaler("cuda")
        else:
            self.scaler = None

        logger.info(f"Training on device: {self.device}")

    def _setup_training(self) -> None:
        """Initialize optimizer and scheduler."""
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

        total_steps = len(self.train_dataloader) * self.config.epochs
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=total_steps,
            eta_min=self.config.learning_rate * 0.01,
        )

        self.global_step = 0
        self.best_eval_loss = float("inf")

    def _setup_checkpointing(self) -> None:
        """Create checkpoint directory."""
        self.checkpoint_dir = Path(self.config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _set_seed(self) -> None:
        """Set random seeds for reproducibility."""
        import random
        import numpy as np

        torch.manual_seed(self.config.seed)
        torch.cuda.manual_seed_all(self.config.seed)
        np.random.seed(self.config.seed)
        random.seed(self.config.seed)
        torch.backends.cudnn.deterministic = True

    def train(self) -> dict:
        """Run training loop."""
        self._set_seed()
        self.model.train()

        metrics_history = []

        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0

            for batch_idx, batch in enumerate(self.train_dataloader):
                loss = self._training_step(batch)
                epoch_loss += loss
                num_batches += 1

                if self.global_step % self.config.log_every_n_steps == 0:
                    self._log_metrics({
                        "train/loss": loss,
                        "train/lr": self.scheduler.get_last_lr()[0],
                        "train/epoch": epoch,
                    })

                if (
                    self.eval_dataloader
                    and self.global_step % self.config.eval_every_n_steps == 0
                ):
                    eval_metrics = self.evaluate()
                    self._log_metrics(eval_metrics)

                    if eval_metrics["eval/loss"] < self.best_eval_loss:
                        self.best_eval_loss = eval_metrics["eval/loss"]
                        self.save_checkpoint("best")

                if self.global_step % self.config.save_every_n_steps == 0:
                    self.save_checkpoint(f"step_{self.global_step}")

            avg_epoch_loss = epoch_loss / num_batches
            logger.info(f"Epoch {epoch}: avg_loss={avg_epoch_loss:.4f}")
            metrics_history.append({"epoch": epoch, "loss": avg_epoch_loss})

        self.save_checkpoint("final")

        return {
            "best_eval_loss": self.best_eval_loss,
            "final_train_loss": avg_epoch_loss,
            "total_steps": self.global_step,
            "metrics_history": metrics_history,
        }

    def _training_step(self, batch: dict) -> float:
        """Execute single training step."""
        batch = {k: v.to(self.device) for k, v in batch.items()}

        if self.scaler:
            with torch.amp.autocast("cuda"):
                outputs = self.model(**batch)
                loss = outputs.loss / self.config.gradient_accumulation_steps
            self.scaler.scale(loss).backward()
        else:
            outputs = self.model(**batch)
            loss = outputs.loss / self.config.gradient_accumulation_steps
            loss.backward()

        if (self.global_step + 1) % self.config.gradient_accumulation_steps == 0:
            if self.scaler:
                self.scaler.unscale_(self.optimizer)

            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.max_grad_norm,
            )

            if self.scaler:
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.optimizer.step()

            self.scheduler.step()
            self.optimizer.zero_grad()

        self.global_step += 1
        return loss.item() * self.config.gradient_accumulation_steps

    @torch.no_grad()
    def evaluate(self) -> dict:
        """Run evaluation loop."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        for batch in self.eval_dataloader:
            batch = {k: v.to(self.device) for k, v in batch.items()}

            if self.scaler:
                with torch.amp.autocast("cuda"):
                    outputs = self.model(**batch)
            else:
                outputs = self.model(**batch)

            total_loss += outputs.loss.item()
            num_batches += 1

        self.model.train()

        return {
            "eval/loss": total_loss / num_batches,
            "eval/step": self.global_step,
        }

    def save_checkpoint(self, name: str) -> Path:
        """Save model checkpoint."""
        checkpoint_path = self.checkpoint_dir / name

        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "global_step": self.global_step,
            "best_eval_loss": self.best_eval_loss,
            "config": self.config.to_dict(),
        }, checkpoint_path / "checkpoint.pt")

        # Save config separately for easy loading
        with open(checkpoint_path / "config.json", "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)

        logger.info(f"Saved checkpoint: {checkpoint_path}")
        return checkpoint_path

    def load_checkpoint(self, checkpoint_path: Path) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path / "checkpoint.pt", map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.global_step = checkpoint["global_step"]
        self.best_eval_loss = checkpoint["best_eval_loss"]

        logger.info(f"Loaded checkpoint from step {self.global_step}")

    def _log_metrics(self, metrics: dict) -> None:
        """Log metrics to tracker and console."""
        if self.tracker:
            self.tracker.log_metrics(metrics, step=self.global_step)

        logger.info(f"Step {self.global_step}: {metrics}")
```

---

## Distributed Training

### PyTorch Distributed Data Parallel

```python
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
import os

def setup_distributed() -> tuple[int, int, int]:
    """Initialize distributed training environment."""
    if "RANK" in os.environ:
        rank = int(os.environ["RANK"])
        local_rank = int(os.environ["LOCAL_RANK"])
        world_size = int(os.environ["WORLD_SIZE"])
    else:
        rank = 0
        local_rank = 0
        world_size = 1

    if world_size > 1:
        dist.init_process_group(
            backend="nccl",
            init_method="env://",
            world_size=world_size,
            rank=rank,
        )
        torch.cuda.set_device(local_rank)

    return rank, local_rank, world_size


def cleanup_distributed() -> None:
    """Cleanup distributed training."""
    if dist.is_initialized():
        dist.destroy_process_group()


class DistributedTrainer(Trainer):
    """Trainer with DDP support."""

    def __init__(self, *args, **kwargs):
        self.rank, self.local_rank, self.world_size = setup_distributed()
        super().__init__(*args, **kwargs)

    def _setup_device(self) -> None:
        """Configure device for distributed training."""
        if self.world_size > 1:
            self.device = torch.device(f"cuda:{self.local_rank}")
            self.model = self.model.to(self.device)
            self.model = DDP(
                self.model,
                device_ids=[self.local_rank],
                output_device=self.local_rank,
                find_unused_parameters=False,
            )
        else:
            super()._setup_device()

        if self.config.mixed_precision and self.device.type == "cuda":
            self.scaler = torch.amp.GradScaler("cuda")
        else:
            self.scaler = None

    def save_checkpoint(self, name: str) -> Path:
        """Only save on rank 0."""
        if self.rank == 0:
            return super().save_checkpoint(name)
        return None

    def _log_metrics(self, metrics: dict) -> None:
        """Only log on rank 0."""
        if self.rank == 0:
            super()._log_metrics(metrics)


def create_distributed_dataloader(
    dataset: Dataset,
    batch_size: int,
    world_size: int,
    rank: int,
    shuffle: bool = True,
) -> DataLoader:
    """Create DataLoader with distributed sampler."""
    sampler = DistributedSampler(
        dataset,
        num_replicas=world_size,
        rank=rank,
        shuffle=shuffle,
    )

    return DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=sampler,
        num_workers=4,
        pin_memory=True,
        drop_last=True,
    )
```

### Launch Script

```bash
#!/bin/bash
# launch_distributed.sh

NUM_GPUS=4
MASTER_PORT=29500

torchrun \
    --nproc_per_node=$NUM_GPUS \
    --master_port=$MASTER_PORT \
    train.py \
    --config config/training_config.yaml
```

---

## Hyperparameter Tuning

### Optuna Integration

```python
import optuna
from optuna.trial import Trial
from optuna.integration import PyTorchLightningPruningCallback
import mlflow

def create_objective(
    train_dataset: Dataset,
    eval_dataset: Dataset,
    model_class: type,
) -> callable:
    """Create Optuna objective function."""

    def objective(trial: Trial) -> float:
        # Sample hyperparameters
        config = TrainingConfig(
            model_name="tuned_model",
            learning_rate=trial.suggest_float("lr", 1e-5, 1e-3, log=True),
            batch_size=trial.suggest_categorical("batch_size", [16, 32, 64]),
            weight_decay=trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
            epochs=trial.suggest_int("epochs", 3, 10),
            warmup_steps=trial.suggest_int("warmup_steps", 0, 500),
        )

        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
        eval_loader = DataLoader(eval_dataset, batch_size=config.batch_size)

        # Create model
        model = model_class(
            hidden_size=trial.suggest_categorical("hidden_size", [128, 256, 512]),
            num_layers=trial.suggest_int("num_layers", 2, 6),
            dropout=trial.suggest_float("dropout", 0.1, 0.5),
        )

        # Train
        trainer = Trainer(
            model=model,
            config=config,
            train_dataloader=train_loader,
            eval_dataloader=eval_loader,
        )

        # Report intermediate values for pruning
        for epoch in range(config.epochs):
            trainer.train_epoch()
            eval_loss = trainer.evaluate()["eval/loss"]

            trial.report(eval_loss, epoch)

            if trial.should_prune():
                raise optuna.TrialPruned()

        return trainer.best_eval_loss

    return objective


def run_hyperparameter_search(
    train_dataset: Dataset,
    eval_dataset: Dataset,
    model_class: type,
    n_trials: int = 100,
    study_name: str = "hpo_study",
) -> optuna.Study:
    """Run hyperparameter optimization with Optuna."""

    # Create study with pruning
    pruner = optuna.pruners.MedianPruner(
        n_startup_trials=5,
        n_warmup_steps=3,
        interval_steps=1,
    )

    study = optuna.create_study(
        study_name=study_name,
        direction="minimize",
        pruner=pruner,
        storage=f"sqlite:///{study_name}.db",
        load_if_exists=True,
    )

    objective = create_objective(train_dataset, eval_dataset, model_class)

    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=3600 * 12,  # 12 hours
        n_jobs=1,  # Sequential for GPU
        show_progress_bar=True,
    )

    # Log best results
    logger.info(f"Best trial: {study.best_trial.params}")
    logger.info(f"Best value: {study.best_value}")

    return study
```

### Ray Tune Integration

```python
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from ray.tune.search.optuna import OptunaSearch
from ray.air import RunConfig, CheckpointConfig

def train_fn(config: dict) -> None:
    """Training function for Ray Tune."""
    from ray.train import report, get_checkpoint

    training_config = TrainingConfig(
        model_name="ray_tune_model",
        learning_rate=config["lr"],
        batch_size=config["batch_size"],
        weight_decay=config["weight_decay"],
        epochs=config["epochs"],
    )

    # Build model and dataloaders
    model = build_model(config["hidden_size"], config["num_layers"])
    train_loader, eval_loader = build_dataloaders(config["batch_size"])

    trainer = Trainer(
        model=model,
        config=training_config,
        train_dataloader=train_loader,
        eval_dataloader=eval_loader,
    )

    # Resume from checkpoint if available
    checkpoint = get_checkpoint()
    if checkpoint:
        with checkpoint.as_directory() as checkpoint_dir:
            trainer.load_checkpoint(Path(checkpoint_dir))

    for epoch in range(training_config.epochs):
        trainer.train_epoch()
        metrics = trainer.evaluate()

        # Report metrics to Ray Tune
        report(
            {"loss": metrics["eval/loss"], "epoch": epoch},
            checkpoint=Checkpoint.from_directory(trainer.checkpoint_dir),
        )


def run_ray_tune(num_samples: int = 50) -> tune.ResultGrid:
    """Run hyperparameter search with Ray Tune."""

    search_space = {
        "lr": tune.loguniform(1e-5, 1e-3),
        "batch_size": tune.choice([16, 32, 64]),
        "weight_decay": tune.loguniform(1e-5, 1e-2),
        "hidden_size": tune.choice([128, 256, 512]),
        "num_layers": tune.randint(2, 7),
        "epochs": 10,
    }

    scheduler = ASHAScheduler(
        metric="loss",
        mode="min",
        max_t=10,
        grace_period=2,
        reduction_factor=3,
    )

    tuner = tune.Tuner(
        tune.with_resources(train_fn, {"gpu": 1}),
        param_space=search_space,
        tune_config=tune.TuneConfig(
            num_samples=num_samples,
            scheduler=scheduler,
            search_alg=OptunaSearch(),
        ),
        run_config=RunConfig(
            name="hpo_experiment",
            checkpoint_config=CheckpointConfig(
                num_to_keep=3,
                checkpoint_frequency=1,
            ),
        ),
    )

    results = tuner.fit()
    best_result = results.get_best_result("loss", "min")

    logger.info(f"Best config: {best_result.config}")
    logger.info(f"Best loss: {best_result.metrics['loss']}")

    return results
```

---

## Resource Management

### GPU Memory Optimization

```python
import torch
from contextlib import contextmanager

@contextmanager
def gpu_memory_manager():
    """Context manager for GPU memory cleanup."""
    try:
        yield
    finally:
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def get_gpu_memory_usage() -> dict:
    """Get current GPU memory statistics."""
    if not torch.cuda.is_available():
        return {"available": False}

    return {
        "allocated": torch.cuda.memory_allocated() / 1e9,
        "reserved": torch.cuda.memory_reserved() / 1e9,
        "max_allocated": torch.cuda.max_memory_allocated() / 1e9,
    }


class GradientCheckpointing:
    """Enable gradient checkpointing for memory efficiency."""

    @staticmethod
    def enable(model: nn.Module, checkpoint_layers: list[str] = None) -> None:
        """Enable gradient checkpointing on specified layers."""
        if hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()
            return

        # Manual checkpointing for custom models
        from torch.utils.checkpoint import checkpoint

        def create_custom_forward(module):
            def custom_forward(*inputs):
                return checkpoint(module._original_forward, *inputs, use_reentrant=False)
            return custom_forward

        for name, module in model.named_modules():
            if checkpoint_layers and name not in checkpoint_layers:
                continue
            if hasattr(module, "forward"):
                module._original_forward = module.forward
                module.forward = create_custom_forward(module)
```

### Batch Size Finder

```python
def find_optimal_batch_size(
    model: nn.Module,
    sample_batch: dict,
    device: torch.device,
    min_batch_size: int = 1,
    max_batch_size: int = 256,
) -> int:
    """Find maximum batch size that fits in GPU memory."""

    model = model.to(device)
    optimal_batch_size = min_batch_size

    for batch_size in [2**i for i in range(int(np.log2(max_batch_size)) + 1)]:
        if batch_size < min_batch_size:
            continue

        try:
            # Create batch of target size
            batch = {
                k: v.repeat(batch_size // v.size(0) + 1, *[1] * (v.dim() - 1))[:batch_size]
                for k, v in sample_batch.items()
            }
            batch = {k: v.to(device) for k, v in batch.items()}

            # Forward pass
            with torch.amp.autocast("cuda"):
                outputs = model(**batch)
                loss = outputs.loss

            # Backward pass
            loss.backward()
            model.zero_grad()

            torch.cuda.empty_cache()
            optimal_batch_size = batch_size

        except RuntimeError as e:
            if "out of memory" in str(e):
                torch.cuda.empty_cache()
                break
            raise

    logger.info(f"Optimal batch size: {optimal_batch_size}")
    return optimal_batch_size
```

---

## Best Practices

### Training Configuration Management

```yaml
# config/training_config.yaml
model:
  name: transformer
  hidden_size: 512
  num_layers: 6
  dropout: 0.1

training:
  batch_size: 32
  learning_rate: 1e-4
  weight_decay: 0.01
  epochs: 10
  mixed_precision: true
  gradient_accumulation_steps: 4

distributed:
  enabled: true
  backend: nccl

checkpointing:
  save_every_n_steps: 1000
  keep_n_checkpoints: 3

logging:
  log_every_n_steps: 100
  eval_every_n_steps: 500
```

### Reproducibility Checklist

```python
def ensure_reproducibility(seed: int) -> None:
    """Set all random seeds for reproducibility."""
    import random
    import numpy as np
    import os

    # Python
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # CUDA
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # Environment
    os.environ["PYTHONHASHSEED"] = str(seed)

    logger.info(f"Set all random seeds to {seed}")
```

---

## Related References

- `feature-engineering.md` - Feature preparation for training
- `experiment-tracking.md` - Logging training metrics
- `pipeline-orchestration.md` - Orchestrating training pipelines
- `model-validation.md` - Validating trained models

## Cross-Reference Skills

- **DevOps Engineer** - CI/CD for training pipelines
- **Kubernetes Specialist** - K8s-based training infrastructure
