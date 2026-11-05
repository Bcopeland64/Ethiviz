from __future__ import annotations
import numpy as np
from typing import Any

class CulturalBiasTransformer:
    """
    sklearn TransformerMixin-compatible wrapper applying pre-processing debiasing.
    Drop-in for use in sklearn Pipeline steps.

    Example:
        >>> from sklearn.pipeline import Pipeline
        >>> from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        >>> pipe = Pipeline([('debias', CulturalBiasTransformer()), ('clf', LogisticRegression())])
    """

    def __init__(
        self,
        tradition_id: str = "western_v1",
        repair_level: float = 0.8,
        protected_col: int = -1,
    ) -> None:
        self.tradition_id = tradition_id
        self.repair_level = repair_level
        self.protected_col = protected_col
        self._groups: list[int] | None = None

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> "CulturalBiasTransformer":
        if self.protected_col >= 0 and self.protected_col < X.shape[1]:
            self._groups = X[:, self.protected_col].astype(int).tolist()
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        from ethiviz.mitigation.preprocessing import DisparateImpactRemover
        groups = self._groups if self._groups is not None else [1] * len(X)
        remover = DisparateImpactRemover(repair_level=self.repair_level)
        protected = [self.protected_col] if self.protected_col >= 0 else None
        repaired = remover.fit_transform(X.tolist(), groups, protected)
        return np.array(repaired)

    def fit_transform(self, X: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def get_params(self, deep: bool = True) -> dict[str, Any]:
        return {"tradition_id": self.tradition_id, "repair_level": self.repair_level, "protected_col": self.protected_col}

    def set_params(self, **params: Any) -> "CulturalBiasTransformer":
        for k, v in params.items():
            setattr(self, k, v)
        return self


class CulturalFairnessScorer:
    """
    Callable scorer compatible with sklearn's cross_val_score.
    Scores a model's fairness using SPD (lower absolute SPD = better).

    Example:
        >>> scorer = CulturalFairnessScorer(tradition_id="ubuntu_v1", group_col=0)
        >>> score = scorer(model, X_test, y_test)
    """

    def __init__(self, tradition_id: str = "western_v1", group_col: int = 0) -> None:
        self.tradition_id = tradition_id
        self.group_col = group_col

    def __call__(self, estimator: Any, X: np.ndarray, y: np.ndarray) -> float:
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        y_pred = estimator.predict(X).tolist()
        groups = X[:, self.group_col].astype(int).tolist()
        calc = GroupFairnessCalculator()
        result = calc.compute(y.tolist(), y_pred, {self.tradition_id: groups})
        score = result.per_tradition.get(self.tradition_id)
        return float(-abs(score.spd)) if score else 0.0


class EthiVizPipeline:
    """
    Pipeline subclass that sequences debiasing + evaluation.
    Compatible with sklearn Pipeline conventions.

    Example:
        >>> pipe = EthiVizPipeline(
        ...     tradition_id="ubuntu_v1",
        ...     estimator=LogisticRegression(),
        ...     repair_level=0.9,
        ... )
        >>> pipe.fit(X_train, y_train)
        >>> pipe.predict(X_test)
    """

    def __init__(
        self,
        estimator: Any,
        tradition_id: str = "western_v1",
        repair_level: float = 0.8,
        protected_col: int = -1,
    ) -> None:
        self.tradition_id = tradition_id
        self.repair_level = repair_level
        self.protected_col = protected_col
        self.estimator = estimator
        self.transformer = CulturalBiasTransformer(tradition_id, repair_level, protected_col)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EthiVizPipeline":
        X_transformed = self.transformer.fit_transform(X, y)
        self.estimator.fit(X_transformed, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.estimator.predict(self.transformer.transform(X))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.estimator.predict_proba(self.transformer.transform(X))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        return float((self.predict(X) == y).mean())
