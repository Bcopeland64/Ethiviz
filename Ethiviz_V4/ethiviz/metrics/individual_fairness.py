from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class IndividualFairnessResult:
    consistency_score: float
    sample_distortion_score: float
    k_neighbors: int
    cultural_proximity_used: bool
    interpretation: str

class IndividualFairnessCalculator:
    """
    Consistency and sample-distortion individual fairness metrics.
    'Similar individuals' are defined by cultural proximity (expressed values),
    not only by demographic similarity — an EthiViz extension beyond AIF360.

    Example:
        >>> calc = IndividualFairnessCalculator(k=3)
        >>> scores = [0.8, 0.75, 0.9, 0.2, 0.25, 0.15]
        >>> result = calc.compute(scores)
        >>> result.consistency_score > 0.5
        True
    """

    def __init__(self, k: int = 5) -> None:
        self.k = k

    def compute(
        self,
        scores: list[float],
        feature_matrix: list[list[float]] | None = None,
        perturbation_scale: float = 0.05,
        rng_seed: int = 42,
    ) -> IndividualFairnessResult:
        arr = np.array(scores, dtype=float)
        n = len(arr)
        if n < 2:
            return IndividualFairnessResult(1.0, 1.0, 0, False, "Insufficient samples for individual fairness.")

        consistency = self._consistency(arr, feature_matrix)
        distortion = self._sample_distortion(arr, perturbation_scale, rng_seed)
        cultural_proximity = feature_matrix is not None

        if consistency > 0.8 and distortion < 0.1:
            interp = "High individual fairness: similar individuals receive similar scores."
        elif consistency > 0.6:
            interp = "Moderate individual fairness: some inconsistency among similar individuals."
        else:
            interp = "Low individual fairness: similar individuals receive dissimilar scores — investigate feature interactions."

        return IndividualFairnessResult(
            consistency_score=consistency,
            sample_distortion_score=distortion,
            k_neighbors=min(self.k, n - 1),
            cultural_proximity_used=cultural_proximity,
            interpretation=interp,
        )

    def _consistency(self, arr: np.ndarray, features: list[list[float]] | None) -> float:
        n = len(arr)
        k = min(self.k, n - 1)
        if features is not None:
            X = np.array(features)
            diffs = []
            for i in range(n):
                dists = np.linalg.norm(X - X[i], axis=1)
                dists[i] = np.inf
                neighbors = np.argsort(dists)[:k]
                diffs.extend(abs(arr[i] - arr[j]) for j in neighbors)
        else:
            diffs = []
            for i in range(n):
                dists = abs(arr - arr[i])
                dists[i] = np.inf
                neighbors = np.argsort(dists)[:k]
                diffs.extend(abs(arr[i] - arr[j]) for j in neighbors)
        return float(1.0 - np.mean(diffs)) if diffs else 1.0

    def _sample_distortion(self, arr: np.ndarray, scale: float, seed: int) -> float:
        rng = np.random.default_rng(seed)
        perturbed = arr + rng.normal(0, scale, size=arr.shape)
        perturbed = np.clip(perturbed, 0.0, 1.0)
        return float(np.mean(np.abs(arr - perturbed)))
