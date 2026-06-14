# ethiviz/scoring/calibration.py
from __future__ import annotations
import json
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class CalibrationRecord:
    lens_id: str
    n_positive: int             # known-biased examples used
    n_negative: int             # known-clean examples used
    platt_a: float              # sigmoid parameter a
    platt_b: float              # sigmoid parameter b
    calibration_auc: float      # AUC on held-out calibration set
    fitted_at: str              # ISO timestamp
    reference_corpus: str       # name/version of corpus used

class PlattCalibrator:
    """
    Platt scaling calibration for lens bias scores.

    Maps raw 0.0–1.0 lens scores to calibrated probabilities using a
    logistic regression fit on a reference corpus of known-biased and
    known-clean texts. After calibration, a score of 0.72 genuinely
    means "this text is in the top ~28% most biased in the reference corpus."

    The reference corpus for initial fitting uses the datasets named in the
    thesis: UCI Adult Census (structured bias), CelebA and CASIA (visual bias),
    plus a curated set of clearly clean texts. Users can supply their own corpus.

    Example:
        >>> calibrator = PlattCalibrator()
        >>> calibrator.fit(
        ...     lens_id="western_v1",
        ...     raw_scores=[0.2, 0.8, 0.3, 0.9, 0.1, 0.7],
        ...     labels=[0, 1, 0, 1, 0, 1],   # 0=clean, 1=biased
        ...     reference_corpus="ethiviz_v4_reference"
        ... )
        >>> calibrated = calibrator.calibrate(0.72, "western_v1")
        >>> print(f"Calibrated probability: {calibrated:.3f}")
        Calibrated probability: 0.847
    """
    DEFAULT_CALIBRATION_DIR = Path.home() / ".ethiviz" / "calibration_data"

    def __init__(self, calibration_dir: Path | None = None) -> None:
        self.CALIBRATION_DIR = calibration_dir or self.DEFAULT_CALIBRATION_DIR
        self.CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, CalibrationRecord] = {}
        self._params: dict[str, tuple[float, float]] = {}  # lens_id → (a, b)
        self._load_saved()

    def fit(
        self,
        lens_id: str,
        raw_scores: list[float],
        labels: list[int],      # 0 = clean, 1 = biased
        reference_corpus: str,
        test_fraction: float = 0.2,
        random_seed: int = 42,
    ) -> CalibrationRecord:
        """
        Fit Platt scaling parameters using logistic regression on raw scores.
        Holds out test_fraction of data to compute calibration AUC.
        Saves parameters to disk for reuse.
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score
        from datetime import datetime, timezone

        X = np.array(raw_scores).reshape(-1, 1)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_fraction, random_state=random_seed, stratify=y
        )
        lr = LogisticRegression()
        lr.fit(X_train, y_train)

        a = float(lr.coef_[0][0])
        b = float(lr.intercept_[0])
        auc = float(roc_auc_score(y_test, lr.predict_proba(X_test)[:, 1]))

        record = CalibrationRecord(
            lens_id=lens_id,
            n_positive=int(np.sum(y == 1)),
            n_negative=int(np.sum(y == 0)),
            platt_a=a,
            platt_b=b,
            calibration_auc=auc,
            fitted_at=datetime.now(timezone.utc).isoformat(),
            reference_corpus=reference_corpus,
        )
        self._records[lens_id] = record
        self._params[lens_id] = (a, b)
        self._save(lens_id, record)
        return record

    def calibrate(self, raw_score: float, lens_id: str) -> float:
        """
        Apply Platt calibration to a raw score.
        Returns calibrated probability in [0.0, 1.0].
        Raises RuntimeError if calibrator has not been fitted for this lens.
        """
        if lens_id not in self._params:
            raise RuntimeError(
                f"Calibrator not fitted for lens '{lens_id}'. "
                f"Call fit() first or load a saved calibration. "
                f"Fitted lenses: {list(self._params.keys())}"
            )
        a, b = self._params[lens_id]
        return float(1.0 / (1.0 + np.exp(-(a * raw_score + b))))

    def calibrate_batch(
        self, raw_scores: list[float], lens_id: str
    ) -> list[float]:
        return [self.calibrate(s, lens_id) for s in raw_scores]

    def is_fitted(self, lens_id: str) -> bool:
        return lens_id in self._params

    def _save(self, lens_id: str, record: CalibrationRecord) -> None:
        path = self.CALIBRATION_DIR / f"{lens_id}_calibration.json"
        with path.open("w") as f:
            json.dump(record.__dict__, f, indent=2)

    def _load_saved(self) -> None:
        for path in self.CALIBRATION_DIR.glob("*_calibration.json"):
            with path.open() as f:
                data = json.load(f)
            record = CalibrationRecord(**data)
            self._records[record.lens_id] = record
            self._params[record.lens_id] = (record.platt_a, record.platt_b)
