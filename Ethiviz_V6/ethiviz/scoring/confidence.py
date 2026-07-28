# ethiviz/scoring/confidence.py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Any

@dataclass
class BootstrapCI:
    mean: float
    lower: float
    upper: float
    n_samples: int

def bootstrap_text_ci(
    scores: List[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> BootstrapCI:
    """Computes bootstrap confidence intervals for text bias scores."""
    if not scores:
        return BootstrapCI(0.0, 0.0, 0.0, 0)
    
    arr = np.array(scores)
    boot_means = []
    rng = np.random.default_rng(seed=42)
    
    for _ in range(n_bootstrap):
        resample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(np.mean(resample))
    
    boot_means = np.sort(boot_means)
    alpha = 1.0 - confidence_level
    lower = np.percentile(boot_means, alpha / 2 * 100)
    upper = np.percentile(boot_means, (1 - alpha / 2) * 100)
    
    return BootstrapCI(
        mean=float(np.mean(arr)),
        lower=float(lower),
        upper=float(upper),
        n_samples=n_bootstrap
    )

def bootstrap_image_ci(
    scores: List[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> BootstrapCI:
    """Computes bootstrap confidence intervals for image bias scores."""
    return bootstrap_text_ci(scores, n_bootstrap, confidence_level)
