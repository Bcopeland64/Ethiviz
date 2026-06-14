from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Any

TRADITION_THRESHOLDS: dict[str, dict[str, float]] = {
    "western_v1":   {"low": 0.05, "moderate": 0.10, "high": 0.20, "critical": 0.30},
    "ubuntu_v1":    {"low": 0.03, "moderate": 0.08, "high": 0.15, "critical": 0.25},
    "confucian_v2": {"low": 0.05, "moderate": 0.10, "high": 0.20, "critical": 0.30},
    "islamic_v1":   {"low": 0.04, "moderate": 0.09, "high": 0.18, "critical": 0.28},
    "indigenous_v1":{"low": 0.03, "moderate": 0.07, "high": 0.14, "critical": 0.22},
    "buddhist_v1":  {"low": 0.04, "moderate": 0.08, "high": 0.16, "critical": 0.24},
    "hindu_v1":     {"low": 0.04, "moderate": 0.09, "high": 0.18, "critical": 0.28},
}

@dataclass
class TraditionFairnessScore:
    tradition_id: str
    spd: float
    disparate_impact: float
    equal_opportunity_diff: float
    average_odds_diff: float
    theil_index: float
    mean_difference: float
    severity: str
    threshold_source: str

@dataclass
class GroupFairnessResult:
    per_tradition: dict[str, TraditionFairnessScore]
    overall_consensus: float | None
    conflicts: list[str]
    mitigation_recommended: list[str]

class GroupFairnessCalculator:
    """
    AIF360-equivalent group fairness metrics with per-tradition cultural extensions.
    Each metric is computed for all available traditions.

    Example:
        >>> calc = GroupFairnessCalculator()
        >>> y_true = [1,1,0,0,1,0]
        >>> y_pred = [1,0,0,0,1,0]
        >>> groups = {"western_v1": [1,1,0,0,1,0]}  # 1=privileged, 0=unprivileged
        >>> result = calc.compute(y_true, y_pred, groups)
    """

    def compute(
        self,
        y_true: list[int],
        y_pred: list[int],
        group_memberships: dict[str, list[int]],
        favorable_label: int = 1,
    ) -> GroupFairnessResult:
        per_tradition: dict[str, TraditionFairnessScore] = {}
        for tradition_id, groups in group_memberships.items():
            score = self._compute_tradition(
                y_true, y_pred, groups, favorable_label, tradition_id
            )
            per_tradition[tradition_id] = score

        all_spds = [s.spd for s in per_tradition.values()]
        conflicts = []
        traditions = list(per_tradition.keys())
        for i in range(len(traditions)):
            for j in range(i + 1, len(traditions)):
                a, b = traditions[i], traditions[j]
                if abs(per_tradition[a].spd - per_tradition[b].spd) > 0.10:
                    conflicts.append(f"{a} vs {b}")

        consensus = float(np.mean(all_spds)) if all_spds else None
        mitigation_needed = [
            tid for tid, s in per_tradition.items()
            if s.severity in ("high", "critical")
        ]

        return GroupFairnessResult(
            per_tradition=per_tradition,
            overall_consensus=consensus,
            conflicts=conflicts,
            mitigation_recommended=mitigation_needed,
        )

    def _compute_tradition(
        self,
        y_true: list[int],
        y_pred: list[int],
        groups: list[int],
        favorable: int,
        tradition_id: str,
    ) -> TraditionFairnessScore:
        yt = np.array(y_true)
        yp = np.array(y_pred)
        g = np.array(groups)

        priv = g == 1
        unpriv = g == 0

        def rate(mask: np.ndarray, arr: np.ndarray) -> float:
            sub = arr[mask]
            return float(sub.mean()) if len(sub) > 0 else 0.0

        priv_rate = rate(priv, yp == favorable)
        unpriv_rate = rate(unpriv, yp == favorable)

        spd = unpriv_rate - priv_rate
        di = (unpriv_rate / priv_rate) if priv_rate > 0 else 0.0
        mean_diff = abs(unpriv_rate - priv_rate)

        priv_tp = rate(priv & (yt == favorable), yp == favorable)
        unpriv_tp = rate(unpriv & (yt == favorable), yp == favorable)
        priv_fp = rate(priv & (yt != favorable), yp == favorable)
        unpriv_fp = rate(unpriv & (yt != favorable), yp == favorable)

        eod = unpriv_tp - priv_tp
        aod = ((unpriv_tp - priv_tp) + (unpriv_fp - priv_fp)) / 2.0

        rates = np.array([priv_rate, unpriv_rate])
        theil = float(np.mean(rates * np.log(rates / rates.mean() + 1e-10))) if rates.mean() > 0 else 0.0

        thresholds = TRADITION_THRESHOLDS.get(tradition_id, TRADITION_THRESHOLDS["western_v1"])
        severity = self._classify_severity(abs(spd), thresholds)

        return TraditionFairnessScore(
            tradition_id=tradition_id,
            spd=spd,
            disparate_impact=di,
            equal_opportunity_diff=eod,
            average_odds_diff=aod,
            theil_index=theil,
            mean_difference=mean_diff,
            severity=severity,
            threshold_source="WVS_wave_7" if "ubuntu" in tradition_id or "western" in tradition_id else "tradition_literature",
        )

    @staticmethod
    def _classify_severity(abs_spd: float, thresholds: dict[str, float]) -> str:
        if abs_spd >= thresholds["critical"]:
            return "critical"
        elif abs_spd >= thresholds["high"]:
            return "high"
        elif abs_spd >= thresholds["moderate"]:
            return "moderate"
        return "low"
