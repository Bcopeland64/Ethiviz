# ethiviz/analysis/cultural_inclusion.py
from __future__ import annotations
import math
from collections import Counter
from typing import List, Dict


def _jensen_shannon_divergence(p: List[float], q: List[float]) -> float:
    """
    Jensen-Shannon divergence between two probability distributions, in bits.
    Symmetric, always finite, and bounded in [0, 1] with log base 2 — which is
    what makes it usable directly as a normalised distance. (KL divergence is
    unbounded and asymmetric, so it can't be turned into a 0-1 index without
    arbitrary clipping.)
    """
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]

    def _kl(a: List[float], b: List[float]) -> float:
        total = 0.0
        for ai, bi in zip(a, b):
            if ai > 0.0 and bi > 0.0:
                total += ai * math.log2(ai / bi)
        return total

    return 0.5 * _kl(p, m) + 0.5 * _kl(q, m)


def cultural_inclusion_index(
    detected_elements: List[str],
    reference_distribution: Dict[str, float],
) -> float:
    """
    Calculate the Cultural Inclusion Index (Figure A4).
    Measures how well the detected cultural elements match a target distribution.

    Returns a score in [0, 1]: 1.0 when the observed frequency of detected
    elements matches the reference distribution exactly, approaching 0.0 as
    the observed distribution diverges from the target.

    This compares actual *proportions*, not merely which categories are
    present. An earlier implementation returned the fraction of reference keys
    appearing at least once, which meant one token instance of each category
    scored identically to a perfectly balanced sample, and the reference
    distribution's values were never read at all.

    Elements detected but absent from the reference are counted in the
    observed total (they are real representation, and dropping them would let
    off-target content inflate the score) while contributing no matching mass.

    Example:
        >>> ref = {"hijab": 0.5, "sari": 0.5}
        >>> round(cultural_inclusion_index(["hijab", "sari"], ref), 3)
        1.0
        >>> round(cultural_inclusion_index(["hijab"] * 99 + ["sari"], ref), 2)
        0.72
        >>> cultural_inclusion_index(["kimono", "kimono"], ref)
        0.0
    """
    if not detected_elements or not reference_distribution:
        return 0.0

    ref_total = sum(reference_distribution.values())
    if ref_total <= 0:
        return 0.0

    counts = Counter(detected_elements)
    observed_total = sum(counts.values())

    # Compare over the union so off-target detections register as divergence
    # rather than being silently dropped.
    categories = list(dict.fromkeys(list(reference_distribution) + list(counts)))

    observed = [counts.get(c, 0) / observed_total for c in categories]
    expected = [reference_distribution.get(c, 0.0) / ref_total for c in categories]

    return 1.0 - _jensen_shannon_divergence(observed, expected)
