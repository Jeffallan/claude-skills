# Model Validation

> Reference for: ML Pipeline Expert
> Load when: Evaluation strategies, validation workflows, A/B testing, shadow deployment

---

## Overview

Model validation ensures models meet quality standards before production deployment. It encompasses offline evaluation, online testing, and continuous monitoring to catch performance degradation, data drift, and model failures.

## When to Use This Reference

- Implementing offline model evaluation strategies
- Setting up A/B testing frameworks
- Building shadow deployment pipelines
- Creating model comparison workflows
- Implementing continuous model monitoring

## When NOT to Use

- Quick model prototyping
- One-off analysis without deployment
- Models with no production requirements

---

## Offline Evaluation

### Comprehensive Evaluation Suite

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score,
)

@dataclass
class ClassificationMetrics:
    """Classification model metrics."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    confusion_matrix: np.ndarray

    def to_dict(self) -> dict:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "pr_auc": self.pr_auc,
        }


@dataclass
class RegressionMetrics:
    """Regression model metrics."""
    mse: float
    rmse: float
    mae: float
    r2: float
    mape: Optional[float]

    def to_dict(self) -> dict:
        return {
            "mse": self.mse,
            "rmse": self.rmse,
            "mae": self.mae,
            "r2": self.r2,
            "mape": self.mape,
        }


class ModelEvaluator:
    """Comprehensive model evaluation."""

    def __init__(self, task_type: str = "classification"):
        self.task_type = task_type

    def evaluate_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
        average: str = "weighted",
    ) -> ClassificationMetrics:
        """Evaluate classification model."""
        roc_auc = None
        pr_auc = None

        if y_prob is not None:
            if len(np.unique(y_true)) == 2:
                # Binary classification
                if y_prob.ndim == 2:
                    y_prob_pos = y_prob[:, 1]
                else:
                    y_prob_pos = y_prob
                roc_auc = roc_auc_score(y_true, y_prob_pos)
                pr_auc = average_precision_score(y_true, y_prob_pos)
            else:
                # Multiclass
                roc_auc = roc_auc_score(
                    y_true, y_prob, multi_class="ovr", average=average
                )

        return ClassificationMetrics(
            accuracy=accuracy_score(y_true, y_pred),
            precision=precision_score(y_true, y_pred, average=average, zero_division=0),
            recall=recall_score(y_true, y_pred, average=average, zero_division=0),
            f1=f1_score(y_true, y_pred, average=average, zero_division=0),
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=confusion_matrix(y_true, y_pred),
        )

    def evaluate_regression(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> RegressionMetrics:
        """Evaluate regression model."""
        mse = mean_squared_error(y_true, y_pred)

        # MAPE (handle zero values)
        mask = y_true != 0
        if mask.any():
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = None

        return RegressionMetrics(
            mse=mse,
            rmse=np.sqrt(mse),
            mae=mean_absolute_error(y_true, y_pred),
            r2=r2_score(y_true, y_pred),
            mape=mape,
        )

    def evaluate_by_segment(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        segments: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
    ) -> dict:
        """Evaluate model performance by segment."""
        results = {}

        for segment in np.unique(segments):
            mask = segments == segment

            if self.task_type == "classification":
                segment_prob = y_prob[mask] if y_prob is not None else None
                metrics = self.evaluate_classification(
                    y_true[mask], y_pred[mask], segment_prob
                )
            else:
                metrics = self.evaluate_regression(y_true[mask], y_pred[mask])

            results[segment] = metrics.to_dict()

        return results
```

### Cross-Validation Framework

```python
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit, cross_val_score
)
import numpy as np
from typing import Callable

class CrossValidator:
    """Cross-validation framework for model evaluation."""

    def __init__(
        self,
        n_splits: int = 5,
        shuffle: bool = True,
        random_state: int = 42,
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def validate_classification(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        stratified: bool = True,
    ) -> dict:
        """Run stratified k-fold cross-validation for classification."""
        if stratified:
            cv = StratifiedKFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=self.random_state,
            )
        else:
            cv = KFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=self.random_state,
            )

        evaluator = ModelEvaluator("classification")
        fold_metrics = []

        for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # Clone and train model
            from sklearn.base import clone
            fold_model = clone(model)
            fold_model.fit(X_train, y_train)

            y_pred = fold_model.predict(X_val)
            y_prob = None
            if hasattr(fold_model, "predict_proba"):
                y_prob = fold_model.predict_proba(X_val)

            metrics = evaluator.evaluate_classification(y_val, y_pred, y_prob)
            fold_metrics.append(metrics.to_dict())

        return self._aggregate_cv_results(fold_metrics)

    def validate_time_series(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        gap: int = 0,
    ) -> dict:
        """Run time series cross-validation."""
        cv = TimeSeriesSplit(n_splits=self.n_splits, gap=gap)
        evaluator = ModelEvaluator("regression")
        fold_metrics = []

        for train_idx, val_idx in cv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            from sklearn.base import clone
            fold_model = clone(model)
            fold_model.fit(X_train, y_train)

            y_pred = fold_model.predict(X_val)
            metrics = evaluator.evaluate_regression(y_val, y_pred)
            fold_metrics.append(metrics.to_dict())

        return self._aggregate_cv_results(fold_metrics)

    def _aggregate_cv_results(self, fold_metrics: list[dict]) -> dict:
        """Aggregate metrics across folds."""
        keys = fold_metrics[0].keys()
        aggregated = {}

        for key in keys:
            values = [m[key] for m in fold_metrics if m[key] is not None]
            if values:
                aggregated[key] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "values": values,
                }

        return aggregated
```

---

## Model Comparison

### Statistical Comparison

```python
from scipy import stats
import numpy as np
from dataclasses import dataclass

@dataclass
class ComparisonResult:
    """Model comparison statistical result."""
    model_a_mean: float
    model_b_mean: float
    difference: float
    p_value: float
    significant: bool
    confidence_interval: tuple[float, float]
    test_used: str


class ModelComparator:
    """Statistical comparison of model performance."""

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level

    def paired_t_test(
        self,
        scores_a: np.ndarray,
        scores_b: np.ndarray,
    ) -> ComparisonResult:
        """Paired t-test for CV score comparison."""
        statistic, p_value = stats.ttest_rel(scores_a, scores_b)

        differences = scores_a - scores_b
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        n = len(differences)

        # 95% confidence interval
        t_critical = stats.t.ppf(1 - self.significance_level / 2, n - 1)
        margin = t_critical * std_diff / np.sqrt(n)
        ci = (mean_diff - margin, mean_diff + margin)

        return ComparisonResult(
            model_a_mean=np.mean(scores_a),
            model_b_mean=np.mean(scores_b),
            difference=mean_diff,
            p_value=p_value,
            significant=p_value < self.significance_level,
            confidence_interval=ci,
            test_used="paired_t_test",
        )

    def wilcoxon_test(
        self,
        scores_a: np.ndarray,
        scores_b: np.ndarray,
    ) -> ComparisonResult:
        """Wilcoxon signed-rank test (non-parametric)."""
        statistic, p_value = stats.wilcoxon(scores_a, scores_b)

        differences = scores_a - scores_b
        mean_diff = np.mean(differences)

        # Bootstrap confidence interval
        ci = self._bootstrap_ci(differences)

        return ComparisonResult(
            model_a_mean=np.mean(scores_a),
            model_b_mean=np.mean(scores_b),
            difference=mean_diff,
            p_value=p_value,
            significant=p_value < self.significance_level,
            confidence_interval=ci,
            test_used="wilcoxon",
        )

    def mcnemar_test(
        self,
        y_true: np.ndarray,
        pred_a: np.ndarray,
        pred_b: np.ndarray,
    ) -> ComparisonResult:
        """McNemar's test for classifier comparison."""
        # Build contingency table
        correct_a = (pred_a == y_true)
        correct_b = (pred_b == y_true)

        # b: A correct, B wrong; c: A wrong, B correct
        b = np.sum(correct_a & ~correct_b)
        c = np.sum(~correct_a & correct_b)

        if b + c < 25:
            # Use exact binomial test for small samples
            p_value = stats.binom_test(b, b + c, 0.5)
        else:
            # Use chi-square approximation
            statistic = (abs(b - c) - 1) ** 2 / (b + c)
            p_value = 1 - stats.chi2.cdf(statistic, 1)

        acc_a = np.mean(correct_a)
        acc_b = np.mean(correct_b)

        return ComparisonResult(
            model_a_mean=acc_a,
            model_b_mean=acc_b,
            difference=acc_a - acc_b,
            p_value=p_value,
            significant=p_value < self.significance_level,
            confidence_interval=(None, None),
            test_used="mcnemar",
        )

    def _bootstrap_ci(
        self,
        data: np.ndarray,
        n_bootstrap: int = 10000,
        alpha: float = 0.05,
    ) -> tuple[float, float]:
        """Calculate bootstrap confidence interval."""
        bootstrapped_means = []

        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=len(data), replace=True)
            bootstrapped_means.append(np.mean(sample))

        lower = np.percentile(bootstrapped_means, alpha / 2 * 100)
        upper = np.percentile(bootstrapped_means, (1 - alpha / 2) * 100)

        return (lower, upper)
```

---

## A/B Testing

### Online Experiment Framework

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import hashlib
import json

@dataclass
class Experiment:
    """A/B test experiment configuration."""
    experiment_id: str
    name: str
    control_model: str
    treatment_model: str
    traffic_split: float  # Fraction to treatment
    start_time: datetime
    end_time: Optional[datetime]
    metrics: list[str]
    minimum_sample_size: int
    status: str = "active"


class ABTestRouter:
    """Route traffic between control and treatment."""

    def __init__(self, experiment: Experiment):
        self.experiment = experiment

    def get_variant(self, user_id: str) -> str:
        """Deterministically assign user to variant."""
        # Hash user_id for consistent assignment
        hash_input = f"{self.experiment.experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = hash_value / (2**128)

        if normalized < self.experiment.traffic_split:
            return "treatment"
        return "control"

    def get_model(self, user_id: str) -> str:
        """Get model to use for user."""
        variant = self.get_variant(user_id)

        if variant == "treatment":
            return self.experiment.treatment_model
        return self.experiment.control_model


class ABTestAnalyzer:
    """Analyze A/B test results."""

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level

    def analyze_conversion(
        self,
        control_conversions: int,
        control_total: int,
        treatment_conversions: int,
        treatment_total: int,
    ) -> dict:
        """Analyze conversion rate experiment."""
        control_rate = control_conversions / control_total
        treatment_rate = treatment_conversions / treatment_total

        # Two-proportion z-test
        pooled_rate = (control_conversions + treatment_conversions) / (
            control_total + treatment_total
        )
        se = np.sqrt(
            pooled_rate * (1 - pooled_rate) * (1/control_total + 1/treatment_total)
        )

        z_stat = (treatment_rate - control_rate) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        # Relative lift
        lift = (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0

        # Confidence interval for difference
        se_diff = np.sqrt(
            control_rate * (1 - control_rate) / control_total +
            treatment_rate * (1 - treatment_rate) / treatment_total
        )
        z_critical = stats.norm.ppf(1 - self.significance_level / 2)
        ci = (
            (treatment_rate - control_rate) - z_critical * se_diff,
            (treatment_rate - control_rate) + z_critical * se_diff,
        )

        return {
            "control_rate": control_rate,
            "treatment_rate": treatment_rate,
            "absolute_difference": treatment_rate - control_rate,
            "relative_lift": lift,
            "p_value": p_value,
            "significant": p_value < self.significance_level,
            "confidence_interval": ci,
            "control_sample_size": control_total,
            "treatment_sample_size": treatment_total,
        }

    def analyze_continuous_metric(
        self,
        control_values: np.ndarray,
        treatment_values: np.ndarray,
    ) -> dict:
        """Analyze continuous metric (e.g., revenue, time)."""
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)

        # Welch's t-test (unequal variances)
        statistic, p_value = stats.ttest_ind(
            treatment_values, control_values, equal_var=False
        )

        lift = (treatment_mean - control_mean) / control_mean if control_mean > 0 else 0

        # Confidence interval
        se_diff = np.sqrt(
            np.var(control_values) / len(control_values) +
            np.var(treatment_values) / len(treatment_values)
        )
        t_critical = stats.t.ppf(
            1 - self.significance_level / 2,
            min(len(control_values), len(treatment_values)) - 1
        )
        ci = (
            (treatment_mean - control_mean) - t_critical * se_diff,
            (treatment_mean - control_mean) + t_critical * se_diff,
        )

        return {
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "absolute_difference": treatment_mean - control_mean,
            "relative_lift": lift,
            "p_value": p_value,
            "significant": p_value < self.significance_level,
            "confidence_interval": ci,
            "control_sample_size": len(control_values),
            "treatment_sample_size": len(treatment_values),
        }

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8,
    ) -> int:
        """Calculate required sample size per variant."""
        alpha = self.significance_level
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        p_bar = (p1 + p2) / 2

        n = (
            (z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) +
             z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 /
            (p2 - p1) ** 2
        )

        return int(np.ceil(n))
```

---

## Shadow Deployment

### Shadow Mode Pipeline

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class PredictionComparison:
    """Comparison of production and shadow predictions."""
    request_id: str
    timestamp: datetime
    production_prediction: Any
    shadow_prediction: Any
    production_latency_ms: float
    shadow_latency_ms: float
    agreement: bool
    features: Optional[dict] = None


class ShadowDeployment:
    """Shadow deployment for model validation."""

    def __init__(
        self,
        production_model,
        shadow_model,
        log_path: str = "/var/log/shadow_predictions.jsonl",
    ):
        self.production_model = production_model
        self.shadow_model = shadow_model
        self.log_path = log_path
        self.comparisons: list[PredictionComparison] = []

    def predict(
        self,
        features: dict,
        request_id: str = None,
    ) -> Any:
        """Get production prediction, run shadow in parallel."""
        import time
        import uuid
        import concurrent.futures

        request_id = request_id or str(uuid.uuid4())

        # Production prediction (synchronous, used for response)
        prod_start = time.time()
        production_pred = self.production_model.predict(features)
        prod_latency = (time.time() - prod_start) * 1000

        # Shadow prediction (async, logged but not returned)
        def run_shadow():
            shadow_start = time.time()
            shadow_pred = self.shadow_model.predict(features)
            shadow_latency = (time.time() - shadow_start) * 1000
            return shadow_pred, shadow_latency

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_shadow)

            try:
                shadow_pred, shadow_latency = future.result(timeout=5.0)

                comparison = PredictionComparison(
                    request_id=request_id,
                    timestamp=datetime.utcnow(),
                    production_prediction=production_pred,
                    shadow_prediction=shadow_pred,
                    production_latency_ms=prod_latency,
                    shadow_latency_ms=shadow_latency,
                    agreement=self._check_agreement(production_pred, shadow_pred),
                    features=features,
                )

                self._log_comparison(comparison)

            except concurrent.futures.TimeoutError:
                logger.warning(f"Shadow prediction timed out for {request_id}")

        return production_pred

    def _check_agreement(self, prod_pred: Any, shadow_pred: Any) -> bool:
        """Check if predictions agree."""
        if isinstance(prod_pred, (list, np.ndarray)):
            return np.allclose(prod_pred, shadow_pred, rtol=1e-3)
        return prod_pred == shadow_pred

    def _log_comparison(self, comparison: PredictionComparison) -> None:
        """Log comparison to file."""
        log_entry = {
            "request_id": comparison.request_id,
            "timestamp": comparison.timestamp.isoformat(),
            "production_prediction": str(comparison.production_prediction),
            "shadow_prediction": str(comparison.shadow_prediction),
            "production_latency_ms": comparison.production_latency_ms,
            "shadow_latency_ms": comparison.shadow_latency_ms,
            "agreement": comparison.agreement,
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        self.comparisons.append(comparison)

    def analyze_shadow_performance(self) -> dict:
        """Analyze shadow model performance."""
        if not self.comparisons:
            return {}

        agreements = [c.agreement for c in self.comparisons]
        prod_latencies = [c.production_latency_ms for c in self.comparisons]
        shadow_latencies = [c.shadow_latency_ms for c in self.comparisons]

        return {
            "total_comparisons": len(self.comparisons),
            "agreement_rate": np.mean(agreements),
            "production_latency_p50": np.percentile(prod_latencies, 50),
            "production_latency_p99": np.percentile(prod_latencies, 99),
            "shadow_latency_p50": np.percentile(shadow_latencies, 50),
            "shadow_latency_p99": np.percentile(shadow_latencies, 99),
            "latency_difference_mean": np.mean(
                [s - p for s, p in zip(shadow_latencies, prod_latencies)]
            ),
        }
```

---

## Validation Pipeline Integration

### Complete Validation Workflow

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    status: ValidationStatus
    message: str
    details: Optional[dict] = None


class ModelValidator:
    """Complete model validation workflow."""

    def __init__(
        self,
        accuracy_threshold: float = 0.8,
        latency_threshold_ms: float = 100,
        drift_threshold: float = 0.2,
    ):
        self.accuracy_threshold = accuracy_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.drift_threshold = drift_threshold
        self.results: list[ValidationResult] = []

    def validate_performance(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> ValidationResult:
        """Validate model performance metrics."""
        evaluator = ModelEvaluator("classification")
        metrics = evaluator.evaluate_classification(y_true, y_pred)

        if metrics.accuracy >= self.accuracy_threshold:
            status = ValidationStatus.PASSED
            message = f"Accuracy {metrics.accuracy:.4f} meets threshold"
        else:
            status = ValidationStatus.FAILED
            message = f"Accuracy {metrics.accuracy:.4f} below threshold {self.accuracy_threshold}"

        result = ValidationResult(
            check_name="performance",
            status=status,
            message=message,
            details=metrics.to_dict(),
        )
        self.results.append(result)
        return result

    def validate_latency(
        self,
        model,
        sample_input: np.ndarray,
        n_iterations: int = 100,
    ) -> ValidationResult:
        """Validate inference latency."""
        import time

        latencies = []
        for _ in range(n_iterations):
            start = time.time()
            model.predict(sample_input)
            latencies.append((time.time() - start) * 1000)

        p50 = np.percentile(latencies, 50)
        p99 = np.percentile(latencies, 99)

        if p99 <= self.latency_threshold_ms:
            status = ValidationStatus.PASSED
            message = f"P99 latency {p99:.2f}ms meets threshold"
        elif p50 <= self.latency_threshold_ms:
            status = ValidationStatus.WARNING
            message = f"P50 OK but P99 {p99:.2f}ms exceeds threshold"
        else:
            status = ValidationStatus.FAILED
            message = f"P99 latency {p99:.2f}ms exceeds threshold"

        result = ValidationResult(
            check_name="latency",
            status=status,
            message=message,
            details={"p50_ms": p50, "p99_ms": p99, "mean_ms": np.mean(latencies)},
        )
        self.results.append(result)
        return result

    def validate_data_compatibility(
        self,
        model,
        expected_features: list[str],
        sample_data: pd.DataFrame,
    ) -> ValidationResult:
        """Validate model accepts expected input format."""
        missing_features = set(expected_features) - set(sample_data.columns)
        extra_features = set(sample_data.columns) - set(expected_features)

        if missing_features:
            status = ValidationStatus.FAILED
            message = f"Missing features: {missing_features}"
        elif extra_features:
            status = ValidationStatus.WARNING
            message = f"Extra features will be ignored: {extra_features}"
        else:
            status = ValidationStatus.PASSED
            message = "All expected features present"

        # Try inference
        try:
            model.predict(sample_data[expected_features].head(1))
        except Exception as e:
            status = ValidationStatus.FAILED
            message = f"Inference failed: {str(e)}"

        result = ValidationResult(
            check_name="data_compatibility",
            status=status,
            message=message,
            details={
                "missing_features": list(missing_features),
                "extra_features": list(extra_features),
            },
        )
        self.results.append(result)
        return result

    def validate_vs_baseline(
        self,
        y_true: np.ndarray,
        new_pred: np.ndarray,
        baseline_pred: np.ndarray,
    ) -> ValidationResult:
        """Validate new model vs baseline."""
        comparator = ModelComparator()
        comparison = comparator.mcnemar_test(y_true, new_pred, baseline_pred)

        new_acc = accuracy_score(y_true, new_pred)
        baseline_acc = accuracy_score(y_true, baseline_pred)

        if new_acc >= baseline_acc:
            if comparison.significant:
                status = ValidationStatus.PASSED
                message = f"Significant improvement: {new_acc:.4f} vs {baseline_acc:.4f}"
            else:
                status = ValidationStatus.WARNING
                message = f"Improvement not significant: {new_acc:.4f} vs {baseline_acc:.4f}"
        else:
            if comparison.significant:
                status = ValidationStatus.FAILED
                message = f"Significant regression: {new_acc:.4f} vs {baseline_acc:.4f}"
            else:
                status = ValidationStatus.WARNING
                message = f"Minor regression: {new_acc:.4f} vs {baseline_acc:.4f}"

        result = ValidationResult(
            check_name="baseline_comparison",
            status=status,
            message=message,
            details={
                "new_accuracy": new_acc,
                "baseline_accuracy": baseline_acc,
                "p_value": comparison.p_value,
            },
        )
        self.results.append(result)
        return result

    def get_summary(self) -> dict:
        """Get validation summary."""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)

        overall_status = (
            ValidationStatus.FAILED if failed > 0
            else ValidationStatus.WARNING if warnings > 0
            else ValidationStatus.PASSED
        )

        return {
            "overall_status": overall_status.value,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "results": [
                {
                    "check": r.check_name,
                    "status": r.status.value,
                    "message": r.message,
                }
                for r in self.results
            ],
        }
```

---

## Best Practices

### Validation Checklist

```python
VALIDATION_CHECKLIST = {
    "offline": [
        "Accuracy/performance metrics meet threshold",
        "Cross-validation shows consistent performance",
        "Model outperforms or matches baseline",
        "Metrics stable across data segments",
    ],
    "pre_deployment": [
        "Inference latency within SLA",
        "Memory usage acceptable",
        "Input/output schema validated",
        "Model serialization/loading works",
    ],
    "shadow": [
        "Shadow predictions logged successfully",
        "Agreement rate with production acceptable",
        "No latency regression",
        "Error rate within bounds",
    ],
    "ab_test": [
        "Sufficient sample size reached",
        "Statistical significance achieved",
        "No negative impact on guardrail metrics",
        "Business metrics improved",
    ],
}
```

---

## Related References

- `training-pipelines.md` - Model training before validation
- `experiment-tracking.md` - Logging validation results
- `pipeline-orchestration.md` - Automated validation workflows
- `feature-engineering.md` - Feature validation

## Cross-Reference Skills

- **Data Engineer** - Data quality validation
- **DevOps Engineer** - Deployment pipeline integration
