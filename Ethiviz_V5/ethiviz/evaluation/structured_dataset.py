from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np

@dataclass
class CulturalDataset:
    """
    Wrapper analogous to AIF360's BinaryLabelDataset.
    Accepts pandas DataFrames with protected attribute columns and maps them
    to cultural lens groupings for fairness evaluation.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'income': [1,0,1,0], 'race': [1,0,1,0], 'gender': [1,1,0,0]})
        >>> ds = CulturalDataset(df=df, label_col='income',
        ...     protected_attrs={'race': 'western_v1', 'gender': 'ubuntu_v1'})
        >>> result = ds.fairness_metrics()
    """
    df: Any  # pd.DataFrame
    label_col: str
    protected_attrs: dict[str, str]
    favorable_label: int | str = 1
    unfavorable_label: int | str = 0

    def fairness_metrics(self) -> "GroupFairnessResult":
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        y_true = self.df[self.label_col].tolist()
        group_memberships = {
            tradition_id: self.df[attr_col].tolist()
            for attr_col, tradition_id in self.protected_attrs.items()
            if attr_col in self.df.columns
        }
        calc = GroupFairnessCalculator()
        return calc.compute(y_true, y_true, group_memberships, int(self.favorable_label))

    def compare_with(self, other: "CulturalDataset") -> dict[str, Any]:
        """Compare fairness metrics between this dataset and another."""
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        self_metrics = self.fairness_metrics()
        other_metrics = other.fairness_metrics()
        comparison: dict[str, Any] = {}
        all_traditions = set(self_metrics.per_tradition) | set(other_metrics.per_tradition)
        for tid in all_traditions:
            a = self_metrics.per_tradition.get(tid)
            b = other_metrics.per_tradition.get(tid)
            comparison[tid] = {
                "self_spd": a.spd if a else None,
                "other_spd": b.spd if b else None,
                "spd_delta": (b.spd - a.spd) if (a and b) else None,
                "self_severity": a.severity if a else None,
                "other_severity": b.severity if b else None,
            }
        return comparison


class ModelBiasEvaluator:
    """
    Evaluates any sklearn-compatible classifier's predictions against a CulturalDataset.
    Generates before/after mitigation comparison reports.

    Example:
        >>> from sklearn.linear_model import LogisticRegression
        >>> from ethiviz.evaluation.structured_dataset import CulturalDataset, ModelBiasEvaluator
        >>> evaluator = ModelBiasEvaluator()
        >>> pre = evaluator.evaluate(model, dataset)
        >>> post = evaluator.evaluate(model, mitigated_dataset)
        >>> report = evaluator.compare(pre, post)
    """

    def evaluate(
        self,
        model: Any,
        dataset: CulturalDataset,
        feature_cols: list[str] | None = None,
    ) -> dict[str, Any]:
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator

        df = dataset.df
        protected = list(dataset.protected_attrs.keys())
        if feature_cols is None:
            feature_cols = [c for c in df.columns if c != dataset.label_col and c not in protected]

        X = df[feature_cols].values if feature_cols else np.zeros((len(df), 1))
        y_true = df[dataset.label_col].tolist()
        y_pred = model.predict(X).tolist()

        group_memberships = {
            tradition_id: df[attr_col].tolist()
            for attr_col, tradition_id in dataset.protected_attrs.items()
            if attr_col in df.columns
        }
        calc = GroupFairnessCalculator()
        fairness = calc.compute(y_true, y_pred, group_memberships, int(dataset.favorable_label))
        return {"y_pred": y_pred, "fairness_result": fairness}

    def compare(
        self,
        pre_result: dict[str, Any],
        post_result: dict[str, Any],
    ) -> dict[str, Any]:
        pre_f = pre_result["fairness_result"]
        post_f = post_result["fairness_result"]
        comparison: dict[str, Any] = {}
        for tid in pre_f.per_tradition:
            pre_s = pre_f.per_tradition[tid]
            post_s = post_f.per_tradition.get(tid)
            comparison[tid] = {
                "spd_before": pre_s.spd,
                "spd_after": post_s.spd if post_s else None,
                "improvement": abs(pre_s.spd) - abs(post_s.spd) if post_s else None,
                "severity_before": pre_s.severity,
                "severity_after": post_s.severity if post_s else None,
            }
        return {"per_tradition_comparison": comparison, "summary": "Before/after mitigation comparison"}
