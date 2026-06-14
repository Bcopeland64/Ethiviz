# ethiviz/scoring/drift.py
from __future__ import annotations
import json
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from scipy.special import rel_entr

@dataclass
class ScoreSnapshot:
    """Historical score distribution for one lens at one point in time."""
    lens_id: str
    snapshot_id: str
    dataset_source: str
    scores: list[float]
    mean: float
    std: float
    histogram: list[float]          # 10-bin normalised histogram
    histogram_bin_edges: list[float]
    n_samples: int
    recorded_at: str

@dataclass
class DriftAlert:
    lens_id: str
    baseline_snapshot_id: str
    current_snapshot_id: str
    kl_divergence: float
    threshold: float
    drift_detected: bool
    interpretation: str
    recommended_action: str

class DriftMonitor:
    """
    Temporal drift detection for bias score distributions.

    Stores score distribution snapshots and computes KL divergence between
    the current distribution and a stored baseline. When divergence exceeds
    the threshold, a DriftAlert is raised recommending re-calibration or
    expert review of the prototype store.
    """
    DEFAULT_SNAPSHOT_DIR = Path.home() / ".ethiviz" / "drift_snapshots"
    DEFAULT_THRESHOLD = 0.10
    N_BINS = 10

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        snapshot_dir: Path | None = None,
    ) -> None:
        self.threshold = threshold
        self.SNAPSHOT_DIR = snapshot_dir or self.DEFAULT_SNAPSHOT_DIR
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def record_snapshot(
        self,
        lens_id: str,
        scores: list[float],
        dataset_source: str,
        set_as_baseline: bool = False,
    ) -> ScoreSnapshot:
        """Record a score distribution snapshot. If set_as_baseline=True,
        this snapshot becomes the reference for future drift comparisons."""
        arr = np.array(scores, dtype=float)
        hist, edges = np.histogram(arr, bins=self.N_BINS, range=(0.0, 1.0))
        hist_norm = hist / (hist.sum() + 1e-8)

        snapshot = ScoreSnapshot(
            lens_id=lens_id,
            snapshot_id=f"{lens_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
            dataset_source=dataset_source,
            scores=scores,
            mean=float(arr.mean()),
            std=float(arr.std()),
            histogram=hist_norm.tolist(),
            histogram_bin_edges=edges.tolist(),
            n_samples=len(scores),
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save_snapshot(snapshot, is_baseline=set_as_baseline)
        return snapshot

    def check_drift(
        self,
        lens_id: str,
        current_scores: list[float],
        dataset_source: str,
    ) -> DriftAlert:
        """
        Compare current scores against the stored baseline for lens_id.
        Returns DriftAlert with KL divergence and recommended action.
        Raises RuntimeError if no baseline snapshot exists for this lens.
        """
        baseline = self._load_baseline(lens_id)
        if baseline is None:
            raise RuntimeError(
                f"No baseline snapshot for lens '{lens_id}'. "
                f"Call record_snapshot(..., set_as_baseline=True) first."
            )
        current = self.record_snapshot(lens_id, current_scores, dataset_source)

        # KL divergence between baseline and current histograms
        p = np.array(baseline.histogram) + 1e-8    # smoothing
        q = np.array(current.histogram) + 1e-8
        p /= p.sum()
        q /= q.sum()
        kl = float(np.sum(rel_entr(p, q)))

        drift_detected = kl > self.threshold
        mean_delta = current.mean - baseline.mean

        if not drift_detected:
            interpretation = (
                f"No significant drift detected (KL={kl:.3f} ≤ threshold={self.threshold}). "
                f"Score distribution is stable relative to baseline."
            )
            action = "Continue monitoring. No action required."
        elif mean_delta > 0:
            interpretation = (
                f"Significant distribution shift detected (KL={kl:.3f} > threshold={self.threshold}). "
                f"Current mean score ({current.mean:.3f}) is higher than baseline "
                f"({baseline.mean:.3f}), suggesting increased bias in the monitored "
                f"dataset or that new bias patterns are not covered by current prototypes."
            )
            action = (
                f"Review prototype store for the '{lens_id}' lens. "
                "Consider running PrototypeLearner.collect_uncertain() on the current "
                "dataset to identify uncovered patterns. Re-calibrate PlattCalibrator "
                "if calibration was previously fitted."
            )
        else:
            interpretation = (
                f"Significant distribution shift detected (KL={kl:.3f} > threshold={self.threshold}). "
                f"Current scores are lower than baseline, possibly indicating improvement "
                f"in the monitored dataset or model changes affecting detection."
            )
            action = (
                "Investigate whether dataset composition has changed or whether upstream "
                "model changes have affected bias detection sensitivity."
            )

        return DriftAlert(
            lens_id=lens_id,
            baseline_snapshot_id=baseline.snapshot_id,
            current_snapshot_id=current.snapshot_id,
            kl_divergence=kl,
            threshold=self.threshold,
            drift_detected=drift_detected,
            interpretation=interpretation,
            recommended_action=action,
        )

    def _save_snapshot(self, snapshot: ScoreSnapshot, is_baseline: bool) -> None:
        path = self.SNAPSHOT_DIR / f"{snapshot.snapshot_id}.json"
        with path.open("w") as f:
            json.dump(snapshot.__dict__, f, indent=2)
        if is_baseline:
            baseline_path = self.SNAPSHOT_DIR / f"{snapshot.lens_id}_baseline.json"
            with baseline_path.open("w") as f:
                json.dump(snapshot.__dict__, f, indent=2)

    def _load_baseline(self, lens_id: str) -> ScoreSnapshot | None:
        path = self.SNAPSHOT_DIR / f"{lens_id}_baseline.json"
        if not path.exists():
            return None
        with path.open() as f:
            data = json.load(f)
        return ScoreSnapshot(**data)
