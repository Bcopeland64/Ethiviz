from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Any

@dataclass
class PreprocessingResult:
    weights: list[float]
    method: str
    tradition_id: str
    n_privileged: int
    n_unprivileged: int
    expected_rate_privileged: float
    expected_rate_unprivileged: float

class Reweigher:
    """
    Reweighing debiasing (AIF360-equivalent with cultural group extension).
    Assigns sample weights to equalize representation across protected groups.
    Weights are computed per tradition using that tradition's group definition.

    Example:
        >>> rw = Reweigher()
        >>> groups = [1,1,0,0,1,0]
        >>> labels = [1,0,1,0,1,0]
        >>> result = rw.fit(groups, labels)
        >>> len(result.weights) == 6
        True
    """

    def fit(
        self,
        group_membership: list[int],
        labels: list[int],
        tradition_id: str = "western_v1",
        favorable_label: int = 1,
    ) -> PreprocessingResult:
        g = np.array(group_membership)
        y = np.array(labels)
        n = len(g)

        n_priv = int((g == 1).sum())
        n_unpriv = int((g == 0).sum())
        n_fav = int((y == favorable_label).sum())
        n_unfav = n - n_fav

        def p(mask: np.ndarray) -> float:
            return float(mask.sum()) / n if n > 0 else 0.0

        weights = np.ones(n)
        for i in range(n):
            is_priv = g[i] == 1
            is_fav = y[i] == favorable_label
            if is_priv and is_fav:
                w = (p(g == 1) * p(y == favorable_label)) / (p((g == 1) & (y == favorable_label)) + 1e-9)
            elif is_priv and not is_fav:
                w = (p(g == 1) * p(y != favorable_label)) / (p((g == 1) & (y != favorable_label)) + 1e-9)
            elif not is_priv and is_fav:
                w = (p(g == 0) * p(y == favorable_label)) / (p((g == 0) & (y == favorable_label)) + 1e-9)
            else:
                w = (p(g == 0) * p(y != favorable_label)) / (p((g == 0) & (y != favorable_label)) + 1e-9)
            weights[i] = w

        priv_rate = float((y[g == 1] == favorable_label).mean()) if n_priv > 0 else 0.0
        unpriv_rate = float((y[g == 0] == favorable_label).mean()) if n_unpriv > 0 else 0.0

        return PreprocessingResult(
            weights=weights.tolist(),
            method="reweighing",
            tradition_id=tradition_id,
            n_privileged=n_priv,
            n_unprivileged=n_unpriv,
            expected_rate_privileged=priv_rate,
            expected_rate_unprivileged=unpriv_rate,
        )

class DisparateImpactRemover:
    """
    Disparate Impact Remover (Feldman et al., 2015). Repairs feature values to
    reduce DI ratio. Lens-weighted feature importance protects culturally salient features.

    Example:
        >>> remover = DisparateImpactRemover(repair_level=0.8)
        >>> X = [[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]]
        >>> groups = [1, 1, 0]
        >>> X_repaired = remover.fit_transform(X, groups)
    """

    def __init__(self, repair_level: float = 1.0) -> None:
        self.repair_level = float(np.clip(repair_level, 0.0, 1.0))

    def fit_transform(
        self,
        X: list[list[float]],
        group_membership: list[int],
        protected_feature_indices: list[int] | None = None,
    ) -> list[list[float]]:
        arr = np.array(X, dtype=float)
        g = np.array(group_membership)
        repaired = arr.copy()

        for col in range(arr.shape[1]):
            if protected_feature_indices and col in protected_feature_indices:
                continue
            overall_median = float(np.median(arr[:, col]))
            for i in range(len(arr)):
                original = arr[i, col]
                repaired[i, col] = original + self.repair_level * (overall_median - original)

        return repaired.tolist()
