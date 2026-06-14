# ethiviz/scoring/multi_framework.py
from __future__ import annotations
import dataclasses
from typing import List, Tuple
from ethiviz.scoring.base import FrameworkScore

SYNERGY_PAIRS = [
    ("ubuntu_v1", "islamic_v1"),       # Both sensitive to essentialism
    ("ubuntu_v1", "confucian_v2"),     # Both emphasise communal harmony
    ("confucian_v2", "islamic_v1"),    # Both balance individual/collective
]
SYNERGY_AMPLIFICATION_FACTOR = 1.15   # 15% amplification when pair agrees

class MultiFrameworkScorer:
    """
    Aggregates scores across multiple ethical frameworks.
    Applies synergy amplification when synergistic lenses converge.
    """
    
    def aggregate(
        self,
        framework_scores: List[FrameworkScore],
        weights: dict[str, float] | None = None,
        threshold: float = 0.50
    ) -> Tuple[float, List[FrameworkScore], List[str]]:
        """
        Aggregates individual framework scores into a single consensus score.
        Applies synergy amplification if two synergistic lenses both exceed threshold.
        """
        amplified_scores, synergy_msgs = self._apply_synergy_amplification(
            framework_scores, threshold=threshold
        )
        
        if not weights:
            # Default to equal weighting if no weights provided
            weights = {fs.framework_id: 1.0 / len(amplified_scores) for fs in amplified_scores}
        
        consensus_score = sum(
            fs.overall_score * weights.get(fs.framework_id, 0.0)
            for fs in amplified_scores
        )
        
        return float(consensus_score), amplified_scores, synergy_msgs

    def _apply_synergy_amplification(
        self,
        framework_scores: list[FrameworkScore],
        threshold: float = 0.50,
    ) -> tuple[list[FrameworkScore], list[str]]:
        """
        When two lenses with a synergy relationship both flag bias above threshold,
        amplify both scores by SYNERGY_AMPLIFICATION_FACTOR (capped at 1.0).
        """
        score_map = {fs.framework_id: fs for fs in framework_scores}
        amplified_pairs = []

        for lens_a, lens_b in SYNERGY_PAIRS:
            if lens_a not in score_map or lens_b not in score_map:
                continue
            sa = score_map[lens_a].overall_score
            sb = score_map[lens_b].overall_score
            if sa >= threshold and sb >= threshold:
                score_map[lens_a] = self._amplify(score_map[lens_a])
                score_map[lens_b] = self._amplify(score_map[lens_b])
                amplified_pairs.append(
                    f"{lens_a} + {lens_b} (both ≥ {threshold:.2f}; "
                    f"convergent essentialism/communal-harm signal amplified)"
                )

        return list(score_map.values()), amplified_pairs

    def _amplify(self, fs: FrameworkScore) -> FrameworkScore:
        new_score = min(1.0, fs.overall_score * SYNERGY_AMPLIFICATION_FACTOR)
        return dataclasses.replace(fs, overall_score=new_score)
