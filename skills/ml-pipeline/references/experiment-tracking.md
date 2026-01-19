# Experiment Tracking

> Reference for: ML Pipeline Expert
> Load when: MLflow, Weights & Biases, experiment logging, model registry

---

## Overview

Experiment tracking enables reproducibility, comparison, and collaboration in ML development. It captures hyperparameters, metrics, artifacts, and model versions to ensure every experiment can be reproduced and compared.

## When to Use This Reference

- Setting up MLflow for experiment tracking
- Implementing Weights & Biases integration
- Creating model registries and versioning
- Comparing experiments and selecting models
- Building custom tracking solutions

## When NOT to Use

- Quick one-off experiments without reproducibility needs
- Simple scripts without hyperparameters
- Non-ML projects

---

## MLflow Integration

### Basic Experiment Tracking

```python
import mlflow
from mlflow.tracking import MlflowClient
from pathlib import Path
import json

class MLflowTracker:
    """MLflow experiment tracking wrapper."""

    def __init__(
        self,
        experiment_name: str,
        tracking_uri: str = "http://localhost:5000",
        artifact_location: str = None,
    ):
        mlflow.set_tracking_uri(tracking_uri)

        # Create or get experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            self.experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location=artifact_location,
            )
        else:
            self.experiment_id = experiment.experiment_id

        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()
        self.run = None

    def start_run(
        self,
        run_name: str = None,
        tags: dict = None,
        nested: bool = False,
    ) -> str:
        """Start a new MLflow run."""
        self.run = mlflow.start_run(
            run_name=run_name,
            experiment_id=self.experiment_id,
            nested=nested,
        )

        if tags:
            mlflow.set_tags(tags)

        return self.run.info.run_id

    def end_run(self, status: str = "FINISHED") -> None:
        """End the current run."""
        mlflow.end_run(status=status)
        self.run = None

    def log_params(self, params: dict) -> None:
        """Log hyperparameters."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict, step: int = None) -> None:
        """Log metrics with optional step."""
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)

    def log_artifact(self, local_path: str, artifact_path: str = None) -> None:
        """Log file or directory as artifact."""
        mlflow.log_artifact(local_path, artifact_path)

    def log_model(
        self,
        model,
        artifact_path: str,
        registered_model_name: str = None,
        signature=None,
        input_example=None,
    ) -> str:
        """Log model with optional registration."""
        from mlflow.models import infer_signature

        if signature is None and input_example is not None:
            signature = infer_signature(input_example, model.predict(input_example))

        model_info = mlflow.sklearn.log_model(
            model,
            artifact_path=artifact_path,
            registered_model_name=registered_model_name,
            signature=signature,
            input_example=input_example,
        )

        return model_info.model_uri


# Usage example
def train_with_mlflow(
    model,
    X_train,
    y_train,
    X_val,
    y_val,
    params: dict,
):
    """Complete training run with MLflow tracking."""
    tracker = MLflowTracker("my_experiment")

    tracker.start_run(
        run_name=f"run_{params['model_type']}",
        tags={
            "model_type": params["model_type"],
            "dataset_version": "v1.0",
            "author": "ml-team",
        },
    )

    try:
        # Log parameters
        tracker.log_params(params)

        # Train model
        model.fit(X_train, y_train)

        # Evaluate and log metrics
        train_score = model.score(X_train, y_train)
        val_score = model.score(X_val, y_val)

        tracker.log_metrics({
            "train_accuracy": train_score,
            "val_accuracy": val_score,
        })

        # Log model
        model_uri = tracker.log_model(
            model,
            artifact_path="model",
            registered_model_name="my_model",
            input_example=X_train[:5],
        )

        tracker.end_run()
        return model_uri

    except Exception as e:
        tracker.end_run(status="FAILED")
        raise
```

### PyTorch Model Logging

```python
import mlflow.pytorch
import torch

def log_pytorch_model(
    model: torch.nn.Module,
    artifact_path: str,
    registered_model_name: str = None,
    sample_input: torch.Tensor = None,
) -> str:
    """Log PyTorch model with signature inference."""
    from mlflow.models import infer_signature

    # Create signature from sample input
    signature = None
    if sample_input is not None:
        model.eval()
        with torch.no_grad():
            sample_output = model(sample_input)

        signature = infer_signature(
            sample_input.numpy(),
            sample_output.numpy(),
        )

    model_info = mlflow.pytorch.log_model(
        model,
        artifact_path=artifact_path,
        registered_model_name=registered_model_name,
        signature=signature,
    )

    return model_info.model_uri


def load_pytorch_model(model_uri: str, device: str = "cpu") -> torch.nn.Module:
    """Load PyTorch model from MLflow."""
    model = mlflow.pytorch.load_model(model_uri, map_location=device)
    return model
```

### Model Registry Operations

```python
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion

class ModelRegistry:
    """MLflow Model Registry wrapper."""

    def __init__(self, tracking_uri: str = "http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()

    def register_model(
        self,
        model_uri: str,
        name: str,
        tags: dict = None,
        description: str = None,
    ) -> ModelVersion:
        """Register a new model version."""
        result = mlflow.register_model(model_uri, name)

        if tags:
            for key, value in tags.items():
                self.client.set_model_version_tag(name, result.version, key, value)

        if description:
            self.client.update_model_version(
                name,
                result.version,
                description=description,
            )

        return result

    def transition_model_stage(
        self,
        name: str,
        version: str,
        stage: str,
        archive_existing: bool = True,
    ) -> ModelVersion:
        """Transition model to new stage (Staging, Production, Archived)."""
        return self.client.transition_model_version_stage(
            name=name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing,
        )

    def get_latest_version(
        self,
        name: str,
        stages: list[str] = None,
    ) -> list[ModelVersion]:
        """Get latest model versions by stage."""
        return self.client.get_latest_versions(name, stages=stages)

    def load_production_model(self, name: str) -> any:
        """Load the production model."""
        model_uri = f"models:/{name}/Production"
        return mlflow.pyfunc.load_model(model_uri)

    def compare_versions(
        self,
        name: str,
        version_a: str,
        version_b: str,
    ) -> dict:
        """Compare two model versions."""
        v_a = self.client.get_model_version(name, version_a)
        v_b = self.client.get_model_version(name, version_b)

        run_a = self.client.get_run(v_a.run_id)
        run_b = self.client.get_run(v_b.run_id)

        return {
            "version_a": {
                "version": version_a,
                "metrics": run_a.data.metrics,
                "params": run_a.data.params,
            },
            "version_b": {
                "version": version_b,
                "metrics": run_b.data.metrics,
                "params": run_b.data.params,
            },
        }
```

---

## Weights & Biases Integration

### Basic W&B Tracking

```python
import wandb
from pathlib import Path

class WandbTracker:
    """Weights & Biases experiment tracking wrapper."""

    def __init__(
        self,
        project: str,
        entity: str = None,
        config: dict = None,
    ):
        self.project = project
        self.entity = entity
        self.config = config
        self.run = None

    def start_run(
        self,
        name: str = None,
        tags: list[str] = None,
        group: str = None,
        job_type: str = "train",
        resume: str = None,
    ) -> wandb.Run:
        """Initialize W&B run."""
        self.run = wandb.init(
            project=self.project,
            entity=self.entity,
            name=name,
            config=self.config,
            tags=tags,
            group=group,
            job_type=job_type,
            resume=resume,
        )
        return self.run

    def log(self, data: dict, step: int = None, commit: bool = True) -> None:
        """Log metrics and data."""
        wandb.log(data, step=step, commit=commit)

    def log_artifact(
        self,
        name: str,
        artifact_type: str,
        path: str,
        metadata: dict = None,
    ) -> wandb.Artifact:
        """Log artifact (model, dataset, etc.)."""
        artifact = wandb.Artifact(
            name=name,
            type=artifact_type,
            metadata=metadata,
        )

        if Path(path).is_dir():
            artifact.add_dir(path)
        else:
            artifact.add_file(path)

        self.run.log_artifact(artifact)
        return artifact

    def log_model(
        self,
        model_path: str,
        name: str,
        metadata: dict = None,
        aliases: list[str] = None,
    ) -> wandb.Artifact:
        """Log model artifact with aliases."""
        artifact = wandb.Artifact(
            name=name,
            type="model",
            metadata=metadata,
        )

        if Path(model_path).is_dir():
            artifact.add_dir(model_path)
        else:
            artifact.add_file(model_path)

        self.run.log_artifact(artifact, aliases=aliases or ["latest"])
        return artifact

    def watch_model(
        self,
        model,
        log: str = "all",
        log_freq: int = 100,
    ) -> None:
        """Watch model for gradient and parameter logging."""
        wandb.watch(model, log=log, log_freq=log_freq)

    def finish(self, exit_code: int = 0) -> None:
        """Finish the run."""
        wandb.finish(exit_code=exit_code)


# Usage with PyTorch
def train_with_wandb(
    model: torch.nn.Module,
    train_loader,
    val_loader,
    config: dict,
):
    """Training with W&B tracking."""
    tracker = WandbTracker(
        project="my-project",
        config=config,
    )

    tracker.start_run(
        name=f"experiment_{config['model_type']}",
        tags=["baseline", config["model_type"]],
        group="hyperparameter_search",
    )

    # Watch model gradients
    tracker.watch_model(model)

    for epoch in range(config["epochs"]):
        model.train()
        for batch_idx, (data, target) in enumerate(train_loader):
            # Training step
            loss = train_step(model, data, target)

            tracker.log({
                "train/loss": loss,
                "train/epoch": epoch,
            })

        # Validation
        val_metrics = evaluate(model, val_loader)
        tracker.log({
            "val/loss": val_metrics["loss"],
            "val/accuracy": val_metrics["accuracy"],
            "epoch": epoch,
        })

    # Save and log model
    torch.save(model.state_dict(), "model.pt")
    tracker.log_model(
        "model.pt",
        name="trained_model",
        metadata={"accuracy": val_metrics["accuracy"]},
        aliases=["latest", "best"],
    )

    tracker.finish()
```

### W&B Sweeps for Hyperparameter Tuning

```python
import wandb

sweep_config = {
    "method": "bayes",  # bayes, grid, random
    "metric": {
        "name": "val/loss",
        "goal": "minimize",
    },
    "parameters": {
        "learning_rate": {
            "distribution": "log_uniform_values",
            "min": 1e-5,
            "max": 1e-2,
        },
        "batch_size": {
            "values": [16, 32, 64, 128],
        },
        "hidden_size": {
            "values": [128, 256, 512],
        },
        "dropout": {
            "distribution": "uniform",
            "min": 0.1,
            "max": 0.5,
        },
    },
    "early_terminate": {
        "type": "hyperband",
        "min_iter": 3,
    },
}


def sweep_train():
    """Training function for sweep."""
    with wandb.init() as run:
        config = wandb.config

        model = build_model(
            hidden_size=config.hidden_size,
            dropout=config.dropout,
        )

        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
        )

        train_loader = DataLoader(train_dataset, batch_size=config.batch_size)

        for epoch in range(10):
            loss = train_epoch(model, train_loader, optimizer)
            val_loss = evaluate(model, val_loader)

            wandb.log({
                "train/loss": loss,
                "val/loss": val_loss,
                "epoch": epoch,
            })


# Run sweep
sweep_id = wandb.sweep(sweep_config, project="my-project")
wandb.agent(sweep_id, function=sweep_train, count=50)
```

---

## Custom Experiment Tracking

### Lightweight Tracker

```python
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import uuid

@dataclass
class Experiment:
    """Experiment metadata and results."""
    experiment_id: str
    name: str
    params: dict
    metrics: dict = field(default_factory=dict)
    artifacts: list = field(default_factory=list)
    tags: dict = field(default_factory=dict)
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    status: str = "running"

    def to_dict(self) -> dict:
        return asdict(self)


class SimpleTracker:
    """Lightweight file-based experiment tracker."""

    def __init__(self, experiments_dir: str = "./experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.current_experiment: Optional[Experiment] = None

    def start_experiment(
        self,
        name: str,
        params: dict,
        tags: dict = None,
    ) -> Experiment:
        """Start a new experiment."""
        experiment_id = str(uuid.uuid4())[:8]

        self.current_experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            params=params,
            tags=tags or {},
        )

        # Create experiment directory
        exp_dir = self.experiments_dir / experiment_id
        exp_dir.mkdir(exist_ok=True)

        self._save_experiment()
        return self.current_experiment

    def log_metrics(self, metrics: dict, step: int = None) -> None:
        """Log metrics to current experiment."""
        if self.current_experiment is None:
            raise ValueError("No active experiment")

        for key, value in metrics.items():
            if key not in self.current_experiment.metrics:
                self.current_experiment.metrics[key] = []

            self.current_experiment.metrics[key].append({
                "value": value,
                "step": step,
                "timestamp": datetime.utcnow().isoformat(),
            })

        self._save_experiment()

    def log_artifact(self, path: str, name: str = None) -> str:
        """Copy artifact to experiment directory."""
        if self.current_experiment is None:
            raise ValueError("No active experiment")

        import shutil

        source = Path(path)
        artifact_name = name or source.name
        exp_dir = self.experiments_dir / self.current_experiment.experiment_id
        dest = exp_dir / "artifacts" / artifact_name

        dest.parent.mkdir(parents=True, exist_ok=True)

        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)

        self.current_experiment.artifacts.append(str(dest))
        self._save_experiment()

        return str(dest)

    def end_experiment(self, status: str = "completed") -> None:
        """End current experiment."""
        if self.current_experiment is None:
            return

        self.current_experiment.status = status
        self.current_experiment.end_time = datetime.utcnow().isoformat()
        self._save_experiment()
        self.current_experiment = None

    def _save_experiment(self) -> None:
        """Save experiment to JSON file."""
        if self.current_experiment is None:
            return

        exp_dir = self.experiments_dir / self.current_experiment.experiment_id
        with open(exp_dir / "experiment.json", "w") as f:
            json.dump(self.current_experiment.to_dict(), f, indent=2)

    def load_experiment(self, experiment_id: str) -> Experiment:
        """Load experiment by ID."""
        exp_file = self.experiments_dir / experiment_id / "experiment.json"
        with open(exp_file) as f:
            data = json.load(f)
        return Experiment(**data)

    def list_experiments(self, tags: dict = None) -> list[Experiment]:
        """List all experiments, optionally filtered by tags."""
        experiments = []

        for exp_dir in self.experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue

            exp_file = exp_dir / "experiment.json"
            if not exp_file.exists():
                continue

            exp = self.load_experiment(exp_dir.name)

            if tags:
                if not all(exp.tags.get(k) == v for k, v in tags.items()):
                    continue

            experiments.append(exp)

        return sorted(experiments, key=lambda x: x.start_time, reverse=True)

    def compare_experiments(self, experiment_ids: list[str]) -> dict:
        """Compare metrics across experiments."""
        comparison = {}

        for exp_id in experiment_ids:
            exp = self.load_experiment(exp_id)
            comparison[exp_id] = {
                "name": exp.name,
                "params": exp.params,
                "final_metrics": {
                    k: v[-1]["value"] if v else None
                    for k, v in exp.metrics.items()
                },
            }

        return comparison
```

---

## Experiment Comparison and Analysis

### Metrics Comparison

```python
import pandas as pd
import matplotlib.pyplot as plt
from mlflow.tracking import MlflowClient

def compare_runs(
    experiment_name: str,
    metric_keys: list[str],
    n_runs: int = 10,
) -> pd.DataFrame:
    """Compare recent runs in an experiment."""
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=n_runs,
    )

    data = []
    for run in runs:
        row = {
            "run_id": run.info.run_id,
            "run_name": run.info.run_name,
            "status": run.info.status,
            "start_time": run.info.start_time,
        }
        row.update(run.data.params)
        row.update({k: run.data.metrics.get(k) for k in metric_keys})
        data.append(row)

    return pd.DataFrame(data)


def plot_metric_comparison(
    runs_df: pd.DataFrame,
    metric: str,
    group_by: str = None,
) -> plt.Figure:
    """Plot metric comparison across runs."""
    fig, ax = plt.subplots(figsize=(10, 6))

    if group_by:
        for group, group_df in runs_df.groupby(group_by):
            ax.bar(group_df["run_name"], group_df[metric], label=str(group))
        ax.legend(title=group_by)
    else:
        ax.bar(runs_df["run_name"], runs_df[metric])

    ax.set_xlabel("Run")
    ax.set_ylabel(metric)
    ax.set_title(f"Comparison of {metric}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    return fig
```

---

## Best Practices

### What to Track

```python
# Always track:
REQUIRED_PARAMS = [
    "learning_rate",
    "batch_size",
    "epochs",
    "model_architecture",
    "optimizer",
    "random_seed",
    "dataset_version",
]

REQUIRED_METRICS = [
    "train_loss",
    "val_loss",
    "train_accuracy",
    "val_accuracy",
]

REQUIRED_ARTIFACTS = [
    "model_checkpoint",
    "training_config",
    "requirements.txt",
]

# Recommended tags
RECOMMENDED_TAGS = {
    "author": "username",
    "environment": "dev|staging|prod",
    "model_type": "classification|regression|etc",
    "dataset": "dataset_name",
    "git_commit": "commit_hash",
}
```

### Experiment Naming Conventions

```python
# Good naming patterns
run_name = f"{model_type}_{dataset}_{timestamp}"
run_name = f"exp_{experiment_number:03d}_{description}"
run_name = f"{feature_flag}_{ablation_type}_{seed}"

# Organize with groups and tags
tags = {
    "project": "recommendation_engine",
    "sprint": "sprint_42",
    "hypothesis": "larger_embedding_helps",
}
```

---

## Related References

- `training-pipelines.md` - Integrating tracking with training
- `model-validation.md` - Validating tracked models
- `pipeline-orchestration.md` - Tracking in automated pipelines

## Cross-Reference Skills

- **DevOps Engineer** - MLflow server deployment
- **Data Engineer** - Artifact storage integration
