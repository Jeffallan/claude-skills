# Pipeline Orchestration

> Reference for: ML Pipeline Expert
> Load when: Kubeflow Pipelines, Airflow, Prefect, DAG design, workflow automation

---

## Overview

Pipeline orchestration automates the end-to-end ML workflow from data ingestion through model deployment. Orchestrators manage dependencies, handle failures, enable scheduling, and provide observability across complex multi-step pipelines.

## When to Use This Reference

- Building Kubeflow Pipelines for ML workflows
- Creating Airflow DAGs for data and ML pipelines
- Implementing Prefect flows for modern orchestration
- Designing pipeline DAGs and component dependencies
- Setting up scheduled retraining workflows

## When NOT to Use

- Simple linear scripts without dependencies
- One-off data processing tasks
- Interactive development and experimentation

---

## Kubeflow Pipelines

### Pipeline Definition (KFP v2)

```python
from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Dataset, Model, Metrics
from kfp import compiler
from typing import NamedTuple

@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "scikit-learn"],
)
def load_data(
    data_path: str,
    output_dataset: Output[Dataset],
) -> None:
    """Load and validate raw data."""
    import pandas as pd

    df = pd.read_parquet(data_path)

    # Basic validation
    assert len(df) > 0, "Dataset is empty"
    assert "target" in df.columns, "Missing target column"

    df.to_parquet(output_dataset.path)
    output_dataset.metadata["num_rows"] = len(df)
    output_dataset.metadata["num_features"] = len(df.columns) - 1


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "scikit-learn"],
)
def preprocess_data(
    input_dataset: Input[Dataset],
    train_dataset: Output[Dataset],
    test_dataset: Output[Dataset],
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    """Preprocess and split data."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    df = pd.read_parquet(input_dataset.path)

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    train_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    train_df["target"] = y_train.values
    train_df.to_parquet(train_dataset.path)

    test_df = pd.DataFrame(X_test_scaled, columns=X.columns)
    test_df["target"] = y_test.values
    test_df.to_parquet(test_dataset.path)


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "scikit-learn", "joblib"],
)
def train_model(
    train_dataset: Input[Dataset],
    model_artifact: Output[Model],
    n_estimators: int = 100,
    max_depth: int = 10,
) -> None:
    """Train RandomForest model."""
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    df = pd.read_parquet(train_dataset.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
    )
    model.fit(X, y)

    joblib.dump(model, model_artifact.path)
    model_artifact.metadata["n_estimators"] = n_estimators
    model_artifact.metadata["max_depth"] = max_depth


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "scikit-learn", "joblib"],
)
def evaluate_model(
    model_artifact: Input[Model],
    test_dataset: Input[Dataset],
    metrics: Output[Metrics],
    threshold: float = 0.8,
) -> NamedTuple("Outputs", [("passed", bool), ("accuracy", float)]):
    """Evaluate model and check threshold."""
    import pandas as pd
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    import joblib
    from collections import namedtuple

    model = joblib.load(model_artifact.path)
    df = pd.read_parquet(test_dataset.path)
    X = df.drop("target", axis=1)
    y = df["target"]

    predictions = model.predict(X)

    accuracy = accuracy_score(y, predictions)
    precision = precision_score(y, predictions, average="weighted")
    recall = recall_score(y, predictions, average="weighted")
    f1 = f1_score(y, predictions, average="weighted")

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("precision", precision)
    metrics.log_metric("recall", recall)
    metrics.log_metric("f1_score", f1)

    passed = accuracy >= threshold

    Outputs = namedtuple("Outputs", ["passed", "accuracy"])
    return Outputs(passed, accuracy)


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["google-cloud-storage"],
)
def deploy_model(
    model_artifact: Input[Model],
    model_name: str,
    endpoint: str,
) -> str:
    """Deploy model to serving endpoint."""
    from google.cloud import storage
    import shutil

    # Copy model to GCS
    bucket_name = endpoint.split("/")[2]
    model_path = f"models/{model_name}/model.joblib"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(model_path)
    blob.upload_from_filename(model_artifact.path)

    return f"gs://{bucket_name}/{model_path}"


@dsl.pipeline(
    name="ml-training-pipeline",
    description="End-to-end ML training pipeline",
)
def ml_pipeline(
    data_path: str,
    n_estimators: int = 100,
    max_depth: int = 10,
    accuracy_threshold: float = 0.8,
    model_name: str = "classifier",
    endpoint: str = "gs://ml-models/serving",
) -> None:
    """Complete ML training pipeline."""

    load_task = load_data(data_path=data_path)

    preprocess_task = preprocess_data(
        input_dataset=load_task.outputs["output_dataset"],
    )

    train_task = train_model(
        train_dataset=preprocess_task.outputs["train_dataset"],
        n_estimators=n_estimators,
        max_depth=max_depth,
    )

    evaluate_task = evaluate_model(
        model_artifact=train_task.outputs["model_artifact"],
        test_dataset=preprocess_task.outputs["test_dataset"],
        threshold=accuracy_threshold,
    )

    with dsl.If(evaluate_task.outputs["passed"] == True):
        deploy_model(
            model_artifact=train_task.outputs["model_artifact"],
            model_name=model_name,
            endpoint=endpoint,
        )


# Compile pipeline
if __name__ == "__main__":
    compiler.Compiler().compile(
        ml_pipeline,
        "ml_pipeline.yaml",
    )
```

### Running Kubeflow Pipelines

```python
from kfp.client import Client

def run_pipeline(
    pipeline_file: str,
    experiment_name: str,
    run_name: str,
    parameters: dict,
) -> str:
    """Submit pipeline run to Kubeflow."""
    client = Client(host="https://kubeflow.example.com/pipeline")

    # Create or get experiment
    experiment = client.create_experiment(name=experiment_name)

    # Submit run
    run = client.create_run_from_pipeline_package(
        pipeline_file=pipeline_file,
        experiment_id=experiment.experiment_id,
        run_name=run_name,
        arguments=parameters,
    )

    return run.run_id


def schedule_pipeline(
    pipeline_file: str,
    experiment_name: str,
    schedule_name: str,
    cron_expression: str,
    parameters: dict,
) -> str:
    """Create recurring pipeline run."""
    client = Client(host="https://kubeflow.example.com/pipeline")

    experiment = client.create_experiment(name=experiment_name)

    # Create recurring run
    job = client.create_recurring_run(
        experiment_id=experiment.experiment_id,
        job_name=schedule_name,
        pipeline_package_path=pipeline_file,
        cron_expression=cron_expression,
        enabled=True,
        parameters=parameters,
    )

    return job.id
```

---

## Apache Airflow

### ML Pipeline DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import json

default_args = {
    "owner": "ml-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}


def load_data(**context):
    """Load data from source."""
    import pandas as pd

    data_path = context["params"]["data_path"]
    df = pd.read_parquet(data_path)

    # Push to XCom for downstream tasks
    output_path = f"/tmp/data_{context['run_id']}.parquet"
    df.to_parquet(output_path)

    context["ti"].xcom_push(key="data_path", value=output_path)
    context["ti"].xcom_push(key="num_rows", value=len(df))

    return output_path


def preprocess_data(**context):
    """Preprocess and split data."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    input_path = context["ti"].xcom_pull(key="data_path", task_ids="load_data")
    df = pd.read_parquet(input_path)

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save processed data
    train_path = f"/tmp/train_{context['run_id']}.parquet"
    test_path = f"/tmp/test_{context['run_id']}.parquet"

    train_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    train_df["target"] = y_train.values
    train_df.to_parquet(train_path)

    test_df = pd.DataFrame(X_test_scaled, columns=X.columns)
    test_df["target"] = y_test.values
    test_df.to_parquet(test_path)

    context["ti"].xcom_push(key="train_path", value=train_path)
    context["ti"].xcom_push(key="test_path", value=test_path)


def train_model(**context):
    """Train ML model."""
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    train_path = context["ti"].xcom_pull(key="train_path", task_ids="preprocess_data")
    df = pd.read_parquet(train_path)

    X = df.drop("target", axis=1)
    y = df["target"]

    params = context["params"]
    model = RandomForestClassifier(
        n_estimators=params.get("n_estimators", 100),
        max_depth=params.get("max_depth", 10),
        random_state=42,
    )
    model.fit(X, y)

    model_path = f"/tmp/model_{context['run_id']}.joblib"
    joblib.dump(model, model_path)

    context["ti"].xcom_push(key="model_path", value=model_path)


def evaluate_model(**context):
    """Evaluate model and return metrics."""
    import pandas as pd
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    import joblib

    model_path = context["ti"].xcom_pull(key="model_path", task_ids="train_model")
    test_path = context["ti"].xcom_pull(key="test_path", task_ids="preprocess_data")

    model = joblib.load(model_path)
    df = pd.read_parquet(test_path)

    X = df.drop("target", axis=1)
    y = df["target"]

    predictions = model.predict(X)

    metrics = {
        "accuracy": accuracy_score(y, predictions),
        "precision": precision_score(y, predictions, average="weighted"),
        "recall": recall_score(y, predictions, average="weighted"),
    }

    context["ti"].xcom_push(key="metrics", value=metrics)

    return metrics


def check_metrics_threshold(**context):
    """Branch based on model performance."""
    metrics = context["ti"].xcom_pull(key="metrics", task_ids="evaluate_model")
    threshold = context["params"].get("accuracy_threshold", 0.8)

    if metrics["accuracy"] >= threshold:
        return "deploy_model"
    return "skip_deployment"


def deploy_model(**context):
    """Deploy model to production."""
    import shutil

    model_path = context["ti"].xcom_pull(key="model_path", task_ids="train_model")
    metrics = context["ti"].xcom_pull(key="metrics", task_ids="evaluate_model")

    # In production, this would upload to model registry/serving
    deploy_path = f"/models/production/model_{context['run_id']}.joblib"
    shutil.copy(model_path, deploy_path)

    return {
        "model_path": deploy_path,
        "metrics": metrics,
        "deployed_at": datetime.utcnow().isoformat(),
    }


with DAG(
    dag_id="ml_training_pipeline",
    default_args=default_args,
    description="End-to-end ML training pipeline",
    schedule_interval="0 2 * * *",  # Daily at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ml", "training", "production"],
    params={
        "data_path": "s3://data-bucket/training_data.parquet",
        "n_estimators": 100,
        "max_depth": 10,
        "accuracy_threshold": 0.8,
    },
) as dag:

    start = EmptyOperator(task_id="start")

    load = PythonOperator(
        task_id="load_data",
        python_callable=load_data,
    )

    preprocess = PythonOperator(
        task_id="preprocess_data",
        python_callable=preprocess_data,
    )

    train = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
    )

    evaluate = PythonOperator(
        task_id="evaluate_model",
        python_callable=evaluate_model,
    )

    check_threshold = BranchPythonOperator(
        task_id="check_metrics_threshold",
        python_callable=check_metrics_threshold,
    )

    deploy = PythonOperator(
        task_id="deploy_model",
        python_callable=deploy_model,
    )

    skip = EmptyOperator(task_id="skip_deployment")

    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    start >> load >> preprocess >> train >> evaluate >> check_threshold
    check_threshold >> [deploy, skip] >> end
```

---

## Prefect

### Modern Flow-Based Pipeline

```python
from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact
from prefect.tasks import task_input_hash
from datetime import timedelta
import pandas as pd

@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def load_data(data_path: str) -> pd.DataFrame:
    """Load data with caching."""
    logger = get_run_logger()
    logger.info(f"Loading data from {data_path}")

    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} rows")

    return df


@task(retries=2)
def preprocess_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Preprocess and split data."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    logger = get_run_logger()

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    train_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    train_df["target"] = y_train.values

    test_df = pd.DataFrame(X_test_scaled, columns=X.columns)
    test_df["target"] = y_test.values

    logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

    return train_df, test_df


@task
def train_model(
    train_df: pd.DataFrame,
    n_estimators: int = 100,
    max_depth: int = 10,
):
    """Train RandomForest model."""
    from sklearn.ensemble import RandomForestClassifier

    logger = get_run_logger()

    X = train_df.drop("target", axis=1)
    y = train_df["target"]

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1,
    )

    logger.info("Training model...")
    model.fit(X, y)
    logger.info("Training complete")

    return model


@task
def evaluate_model(model, test_df: pd.DataFrame) -> dict:
    """Evaluate model and create artifact."""
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, classification_report
    )

    logger = get_run_logger()

    X = test_df.drop("target", axis=1)
    y = test_df["target"]

    predictions = model.predict(X)

    metrics = {
        "accuracy": accuracy_score(y, predictions),
        "precision": precision_score(y, predictions, average="weighted"),
        "recall": recall_score(y, predictions, average="weighted"),
        "f1_score": f1_score(y, predictions, average="weighted"),
    }

    logger.info(f"Metrics: {metrics}")

    # Create markdown artifact for Prefect UI
    report = classification_report(y, predictions)
    markdown = f"""
# Model Evaluation Report

## Metrics
| Metric | Value |
|--------|-------|
| Accuracy | {metrics['accuracy']:.4f} |
| Precision | {metrics['precision']:.4f} |
| Recall | {metrics['recall']:.4f} |
| F1 Score | {metrics['f1_score']:.4f} |

## Classification Report
```
{report}
```
"""
    create_markdown_artifact(
        key="model-evaluation",
        markdown=markdown,
        description="Model evaluation metrics",
    )

    return metrics


@task
def deploy_model(model, metrics: dict, threshold: float) -> bool:
    """Deploy model if metrics pass threshold."""
    import joblib
    from datetime import datetime

    logger = get_run_logger()

    if metrics["accuracy"] < threshold:
        logger.warning(
            f"Model accuracy {metrics['accuracy']:.4f} below threshold {threshold}"
        )
        return False

    # Save model
    model_path = f"/models/model_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Model deployed to {model_path}")

    return True


@flow(
    name="ml-training-pipeline",
    description="End-to-end ML training pipeline",
    retries=1,
    retry_delay_seconds=300,
)
def ml_training_flow(
    data_path: str,
    n_estimators: int = 100,
    max_depth: int = 10,
    accuracy_threshold: float = 0.8,
) -> dict:
    """Main ML training flow."""
    logger = get_run_logger()
    logger.info("Starting ML training pipeline")

    # Load and preprocess
    df = load_data(data_path)
    train_df, test_df = preprocess_data(df)

    # Train and evaluate
    model = train_model(train_df, n_estimators, max_depth)
    metrics = evaluate_model(model, test_df)

    # Deploy if threshold met
    deployed = deploy_model(model, metrics, accuracy_threshold)

    return {
        "metrics": metrics,
        "deployed": deployed,
    }


# Deployment configuration
if __name__ == "__main__":
    from prefect.deployments import Deployment
    from prefect.server.schemas.schedules import CronSchedule

    deployment = Deployment.build_from_flow(
        flow=ml_training_flow,
        name="daily-training",
        schedule=CronSchedule(cron="0 2 * * *"),
        parameters={
            "data_path": "s3://data/training.parquet",
            "n_estimators": 100,
            "max_depth": 10,
            "accuracy_threshold": 0.8,
        },
        tags=["ml", "production"],
        work_queue_name="ml-queue",
    )

    deployment.apply()
```

---

## DAG Design Patterns

### Parallel Processing Pattern

```python
from prefect import flow, task, unmapped
from typing import List

@task
def process_partition(partition_id: int, data_path: str) -> dict:
    """Process single data partition."""
    # Process partition
    return {"partition_id": partition_id, "records_processed": 1000}


@task
def aggregate_results(results: List[dict]) -> dict:
    """Aggregate parallel processing results."""
    total_records = sum(r["records_processed"] for r in results)
    return {"total_records": total_records}


@flow
def parallel_processing_flow(data_path: str, num_partitions: int = 4):
    """Process data in parallel partitions."""

    # Map over partitions
    partition_results = process_partition.map(
        partition_id=range(num_partitions),
        data_path=unmapped(data_path),
    )

    # Aggregate results
    final_result = aggregate_results(partition_results)

    return final_result
```

### Conditional Branching Pattern

```python
from prefect import flow, task

@task
def check_data_quality(df) -> bool:
    """Check if data meets quality standards."""
    null_ratio = df.isnull().sum().sum() / df.size
    return null_ratio < 0.1


@task
def handle_poor_quality(df):
    """Handle data that fails quality checks."""
    # Impute, clean, or alert
    pass


@task
def process_good_quality(df):
    """Process data that passes quality checks."""
    pass


@flow
def conditional_flow(data_path: str):
    """Flow with conditional branching."""
    df = load_data(data_path)
    quality_ok = check_data_quality(df)

    if quality_ok:
        result = process_good_quality(df)
    else:
        result = handle_poor_quality(df)

    return result
```

### Error Handling Pattern

```python
from prefect import flow, task
from prefect.states import Failed

@task
def risky_operation():
    """Operation that might fail."""
    import random
    if random.random() < 0.3:
        raise ValueError("Random failure")
    return "success"


@task
def fallback_operation():
    """Fallback when primary fails."""
    return "fallback_result"


@task
def send_alert(error: Exception):
    """Send alert on failure."""
    # Send to Slack, PagerDuty, etc.
    pass


@flow
def resilient_flow():
    """Flow with error handling."""
    try:
        result = risky_operation()
    except Exception as e:
        send_alert(e)
        result = fallback_operation()

    return result
```

---

## Best Practices

### Pipeline Configuration

```yaml
# pipeline_config.yaml
pipeline:
  name: ml-training
  version: "1.0.0"
  description: "Production ML training pipeline"

stages:
  - name: load_data
    timeout: 300
    retries: 3

  - name: preprocess
    timeout: 600
    retries: 2
    depends_on: [load_data]

  - name: train
    timeout: 3600
    retries: 1
    depends_on: [preprocess]
    resources:
      cpu: 4
      memory: 16Gi
      gpu: 1

  - name: evaluate
    timeout: 300
    depends_on: [train]

  - name: deploy
    timeout: 300
    depends_on: [evaluate]
    condition: "evaluate.metrics.accuracy >= 0.8"

schedule:
  cron: "0 2 * * *"
  timezone: "UTC"

notifications:
  on_failure:
    - slack: "#ml-alerts"
    - email: ml-team@company.com
  on_success:
    - slack: "#ml-notifications"
```

### Idempotency Guidelines

```python
# Good: Idempotent operations
def process_data(run_id: str, data_path: str):
    """Idempotent data processing."""
    output_path = f"s3://processed/{run_id}/data.parquet"

    # Check if already processed
    if file_exists(output_path):
        return output_path

    # Process and save
    df = pd.read_parquet(data_path)
    processed = transform(df)
    processed.to_parquet(output_path)

    return output_path
```

---

## Related References

- `training-pipelines.md` - Training components for pipelines
- `experiment-tracking.md` - Logging pipeline runs
- `feature-engineering.md` - Feature pipeline components
- `model-validation.md` - Validation stages in pipelines

## Cross-Reference Skills

- **DevOps Engineer** - CI/CD for pipeline deployment
- **Kubernetes Specialist** - Running pipelines on K8s
- **Cloud Architect** - Cloud infrastructure for orchestration
