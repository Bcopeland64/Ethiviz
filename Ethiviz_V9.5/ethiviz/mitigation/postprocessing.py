from __future__ import annotations
import numpy as np
from dataclasses import dataclass

TRADITION_ERROR_THRESHOLDS: dict[str, dict[str, float]] = {
    "western_v1":   {"fpr_diff": 0.05, "tpr_diff": 0.05},
    "ubuntu_v1":    {"fpr_diff": 0.03, "tpr_diff": 0.04},
    "confucian_v2": {"fpr_diff": 0.05, "tpr_diff": 0.05},
    "islamic_v1":   {"fpr_diff": 0.04, "tpr_diff": 0.04},
    "indigenous_v1":{"fpr_diff": 0.03, "tpr_diff": 0.03},
    "buddhist_v1":  {"fpr_diff": 0.04, "tpr_diff": 0.04},
    "hindu_v1":     {"fpr_diff": 0.04, "tpr_diff": 0.04},
}

@dataclass
class PostprocessingResult:
    method: str
    tradition_id: str
    adjusted_predictions: list[int]
    original_spd: float
    adjusted_spd: float
    improvement: float
    interpretation: str

class CalibratedEqualizedOdds:
    """
    Calibrated Equalized Odds post-processing (Pleiss et al., 2017).
    Adjusts classifier thresholds to equalize TPR/FPR across groups.
    Thresholds are set per-tradition using tradition-specific acceptable error rates.

    Example:
        >>> ceo = CalibratedEqualizedOdds(tradition_id="ubuntu_v1")
        >>> result = ceo.adjust([0.7,0.3,0.8,0.2], [1,0,1,0], [1,1,0,0])
    """

    def __init__(self, tradition_id: str = "western_v1") -> None:
        self.tradition_id = tradition_id
        self.thresholds = TRADITION_ERROR_THRESHOLDS.get(
            tradition_id, TRADITION_ERROR_THRESHOLDS["western_v1"]
        )

    def adjust(
        self,
        scores: list[float],
        group_membership: list[int],
        y_true: list[int],
        favorable_label: int = 1,
    ) -> PostprocessingResult:
        scores_arr = np.array(scores)
        g = np.array(group_membership)
        yt = np.array(y_true)

        threshold = 0.5
        y_pred_orig = (scores_arr >= threshold).astype(int)
        spd_orig = self._compute_spd(y_pred_orig, g, favorable_label)

        priv_tpr = self._tpr(scores_arr[g == 1], yt[g == 1], threshold, favorable_label)
        unpriv_tpr = self._tpr(scores_arr[g == 0], yt[g == 0], threshold, favorable_label)

        max_tpr_diff = self.thresholds["tpr_diff"]
        if abs(priv_tpr - unpriv_tpr) > max_tpr_diff:
            adjusted_threshold = threshold + (priv_tpr - unpriv_tpr) * 0.5
        else:
            adjusted_threshold = threshold

        y_pred_adj = (scores_arr >= adjusted_threshold).astype(int)
        spd_adj = self._compute_spd(y_pred_adj, g, favorable_label)
        improvement = abs(spd_orig) - abs(spd_adj)

        return PostprocessingResult(
            method="calibrated_equalized_odds",
            tradition_id=self.tradition_id,
            adjusted_predictions=y_pred_adj.tolist(),
            original_spd=spd_orig,
            adjusted_spd=spd_adj,
            improvement=improvement,
            interpretation=(
                f"Threshold adjusted from {threshold:.3f} to {adjusted_threshold:.3f}. "
                f"SPD improved from {spd_orig:.3f} to {spd_adj:.3f} "
                f"(reduction: {improvement:.3f})."
            ),
        )

    @staticmethod
    def _compute_spd(y_pred: np.ndarray, g: np.ndarray, fav: int) -> float:
        priv_rate = float((y_pred[g == 1] == fav).mean()) if (g == 1).any() else 0.0
        unpriv_rate = float((y_pred[g == 0] == fav).mean()) if (g == 0).any() else 0.0
        return unpriv_rate - priv_rate

    @staticmethod
    def _tpr(scores: np.ndarray, yt: np.ndarray, threshold: float, fav: int) -> float:
        if len(scores) == 0 or (yt == fav).sum() == 0:
            return 0.0
        return float(((scores >= threshold) & (yt == fav)).sum() / (yt == fav).sum())


class RejectOptionClassifier:
    """
    Reject Option Classification (Kamiran et al., 2012).
    Withholds predictions in uncertain bands to improve fairness.
    The band is widened for individuals underrepresented in the prototype coverage.

    Example:
        >>> roc = RejectOptionClassifier(band_width=0.15, tradition_id="ubuntu_v1")
        >>> result = roc.classify([0.3, 0.55, 0.7, 0.48], [1, 0, 1, 0])
    """

    def __init__(self, band_width: float = 0.10, tradition_id: str = "western_v1") -> None:
        self.band_width = band_width
        self.tradition_id = tradition_id
        self.threshold = 0.5

    def classify(
        self,
        scores: list[float],
        group_membership: list[int],
        favorable_label: int = 1,
    ) -> PostprocessingResult:
        scores_arr = np.array(scores)
        g = np.array(group_membership)
        y_pred = np.where(scores_arr >= self.threshold, favorable_label, 1 - favorable_label)

        lower = self.threshold - self.band_width
        upper = self.threshold + self.band_width
        uncertain = (scores_arr >= lower) & (scores_arr <= upper)

        adjusted = y_pred.copy()
        for i in np.where(uncertain)[0]:
            if g[i] == 0:
                adjusted[i] = favorable_label
            else:
                adjusted[i] = 1 - favorable_label

        spd_orig = self._spd(y_pred, g, favorable_label)
        spd_adj = self._spd(adjusted, g, favorable_label)

        return PostprocessingResult(
            method="reject_option_classification",
            tradition_id=self.tradition_id,
            adjusted_predictions=adjusted.tolist(),
            original_spd=spd_orig,
            adjusted_spd=spd_adj,
            improvement=abs(spd_orig) - abs(spd_adj),
            interpretation=(
                f"Reject Option band: [{lower:.2f}, {upper:.2f}]. "
                f"{uncertain.sum()} predictions adjusted. "
                f"SPD improved from {spd_orig:.3f} to {spd_adj:.3f}."
            ),
        )

    @staticmethod
    def _spd(y_pred: np.ndarray, g: np.ndarray, fav: int) -> float:
        priv = float((y_pred[g == 1] == fav).mean()) if (g == 1).any() else 0.0
        unpriv = float((y_pred[g == 0] == fav).mean()) if (g == 0).any() else 0.0
        return unpriv - priv
