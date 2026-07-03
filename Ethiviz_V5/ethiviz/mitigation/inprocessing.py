from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class PrejudiceRemoverResult:
    weights_adjustment: list[float]
    regularization_weight: float
    tradition_id: str
    domain: str
    interpretation: str

def run_prejudice_remover(
    scores: list[float],
    group_membership: list[int],
    tradition_id: str = "western_v1",
    domain: str = "general",
    eta: float = 1.0,
) -> PrejudiceRemoverResult:
    """
    Prejudice Remover regularization suggestion.
    Computes the per-sample weight adjustment that would reduce group-based
    score differences. The regularization weight (eta) is context-weighted
    by DeploymentContext domain.

    This is presented as a suggestion (showing what the data would look like if
    debiased) rather than automatically transforming data, preserving user agency.

    Example:
        >>> result = run_prejudice_remover([0.8, 0.3, 0.7, 0.2], [1, 0, 1, 0])
        >>> len(result.weights_adjustment) == 4
        True
    """
    scores_arr = np.array(scores, dtype=float)
    groups_arr = np.array(group_membership)

    domain_eta_multiplier = {
        "hiring": 1.5, "healthcare": 1.3, "content_moderation": 1.2,
        "education": 1.1, "finance": 1.2, "general": 1.0,
    }
    effective_eta = eta * domain_eta_multiplier.get(domain, 1.0)

    priv_mask = groups_arr == 1
    unpriv_mask = groups_arr == 0
    priv_mean = float(scores_arr[priv_mask].mean()) if priv_mask.any() else 0.0
    unpriv_mean = float(scores_arr[unpriv_mask].mean()) if unpriv_mask.any() else 0.0
    overall_mean = float(scores_arr.mean())

    adjustments = np.zeros(len(scores_arr))
    for i in range(len(scores_arr)):
        group_mean = priv_mean if groups_arr[i] == 1 else unpriv_mean
        adjustments[i] = -effective_eta * (group_mean - overall_mean) * 0.1

    interp = (
        f"Prejudice Remover suggests adjustments of up to "
        f"{float(np.abs(adjustments).max()):.3f} for '{tradition_id}' lens. "
        f"Privileged group mean: {priv_mean:.3f}, unprivileged: {unpriv_mean:.3f}. "
        f"Applying these adjustments reduces SPD by approximately "
        f"{abs(priv_mean - unpriv_mean) * effective_eta * 0.1:.3f}."
    )

    return PrejudiceRemoverResult(
        weights_adjustment=adjustments.tolist(),
        regularization_weight=effective_eta,
        tradition_id=tradition_id,
        domain=domain,
        interpretation=interp,
    )
