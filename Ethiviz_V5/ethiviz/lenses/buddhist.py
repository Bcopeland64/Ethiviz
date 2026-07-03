from __future__ import annotations
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.lenses.western import WesternLens


class BuddhistLens(EthicalLens):
    """
    Buddhist ethical lens.
    Applies ahimsa (non-harm), right speech, interdependence (pratītyasamutpāda),
    and non-attachment to fixed identity categories.
    """

    LENS_ID = "buddhist_v1"
    REGEX_PATTERNS = [
        r"\b(eliminate|destroy|exterminate)\b.*\b(people|group|community|culture)\b",
        r"\b(inferior|worthless|subhuman)\b.*\b(race|ethnicity|religion|group)\b",
        r"\b(inherently|naturally|genetically)\b.*\b(violent|criminal|lazy|inferior)\b",
        r"\bnot our concern\b|\btheir own fault\b|\bdeserve(s)? to suffer\b",
        r"\bblood\b.*\b(criminal|violent|inferior|corrupt)\b",
    ]

    def __init__(self, registry=None, use_semantic: bool = True) -> None:
        super().__init__("buddhist_v1", use_semantic=use_semantic)
        self._western_lens = WesternLens(registry=registry, use_semantic=use_semantic)

    def score(self, text: str, language: str = "en") -> LensScore:
        return self._western_lens._score_with_patterns(
            text=text,
            lens_id=self.LENS_ID,
            regex_patterns=self.REGEX_PATTERNS,
            language=language,
            dimension_keys=["ahimsa_violation", "right_speech_violation",
                           "interdependence_denial", "identity_reification", "compassion_deficit"],
        )
