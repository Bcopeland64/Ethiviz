# ethiviz/analysis/intersectional.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any

# Amplification ratio above which an intersection is treated as superadditive
# (compound disadvantage exceeding what the independent axes predict).
SUPERADDITIVE_THRESHOLD = 1.05
# Ratio below which the intersection is *less* than the independent baseline
# predicts — a buffering interaction rather than a compound harm.
SUBADDITIVE_THRESHOLD = 0.95


@dataclass
class IntersectionResult:
    """
    Bias measured at a single identity intersection, expressed relative to
    what the two constituent axes would predict on their own.

    `observed` is the measured bias at the intersection. `expected_independent`
    is the noisy-OR baseline — the bias level you would see if the two axes
    combined independently, with no interaction. `amplification` is their
    ratio, and it carries the intersectional claim:

      > 1.0  compound disadvantage — the intersection is worse than its parts
             predict (the Crenshaw case)
      ~ 1.0  the axes are behaving independently
      < 1.0  the intersection is buffered relative to the independent baseline
    """
    identity_a: str
    identity_b: str
    score_a: float
    score_b: float
    observed: float
    expected_independent: float
    amplification: float
    is_superadditive: bool
    interpretation: str


def _noisy_or(a: float, b: float) -> float:
    """
    Independent-combination baseline: the harm level expected from A or B when
    the two axes do not interact. Chosen over a plain sum because bias scores
    are bounded in [0, 1] and a sum can exceed the scale (0.8 + 0.7 = 1.5),
    which would make superadditivity inexpressible at the top of the range.
    """
    return a + b - (a * b)


def calculate_intersectional_analysis(
    dimension_a_scores: Dict[str, float],
    dimension_b_scores: Dict[str, float],
    observed_scores: Dict[str, float] | None = None,
) -> Dict[str, IntersectionResult]:
    """
    Calculate compound bias at identity intersections (Figure A3).
    Example: Intersection of Race (A) and Gender (B).

    For each (identity_a, identity_b) pair this compares the observed bias at
    that intersection against the noisy-OR independent baseline, and reports
    the amplification ratio between them.

    `observed_scores` maps "{identity_a}_{identity_b}" to the measured bias at
    that intersection. When it is not supplied (no directly measured
    intersection data available), observed falls back to the independent
    baseline, yielding amplification 1.0 — i.e. "no evidence of an interaction"
    rather than a fabricated one.

    This replaces an earlier implementation that returned `score_a * score_b`.
    A product of two values in [0, 1] is always <= either input, so that
    formulation could never represent compound disadvantage exceeding its
    parts — it structurally inverted the claim it was documented as making.

    Example:
        >>> res = calculate_intersectional_analysis(
        ...     {"black": 0.5}, {"woman": 0.5}, {"black_woman": 0.9}
        ... )
        >>> round(res["black_woman"].expected_independent, 2)
        0.75
        >>> round(res["black_woman"].amplification, 2)
        1.2
        >>> res["black_woman"].is_superadditive
        True
    """
    observed_scores = observed_scores or {}
    intersections: Dict[str, IntersectionResult] = {}

    for identity_a, score_a in dimension_a_scores.items():
        for identity_b, score_b in dimension_b_scores.items():
            key = f"{identity_a}_{identity_b}"
            expected = _noisy_or(score_a, score_b)
            observed = observed_scores.get(key, expected)

            # Degenerate case: neither axis shows bias, so there is no baseline
            # to amplify. Report exact independence rather than dividing by ~0.
            amplification = 1.0 if expected <= 0.0 else observed / expected

            if amplification >= SUPERADDITIVE_THRESHOLD:
                interpretation = (
                    f"Compound disadvantage: bias at the {identity_a}/{identity_b} "
                    f"intersection is {amplification:.2f}x what the individual axes "
                    f"predict independently."
                )
            elif amplification <= SUBADDITIVE_THRESHOLD:
                interpretation = (
                    f"Buffered: bias at the {identity_a}/{identity_b} intersection "
                    f"is {amplification:.2f}x the independent prediction — lower "
                    f"than the constituent axes alone would suggest."
                )
            else:
                interpretation = (
                    f"Approximately independent: the {identity_a}/{identity_b} "
                    f"intersection shows no material interaction effect."
                )

            intersections[key] = IntersectionResult(
                identity_a=identity_a,
                identity_b=identity_b,
                score_a=score_a,
                score_b=score_b,
                observed=observed,
                expected_independent=expected,
                amplification=amplification,
                is_superadditive=amplification >= SUPERADDITIVE_THRESHOLD,
                interpretation=interpretation,
            )

    return intersections
