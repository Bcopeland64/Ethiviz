from __future__ import annotations
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.lenses.western import WesternLens


class HinduLens(EthicalLens):
    """
    Hindu / Dharmic ethical lens.
    Applies dharmic duty, ahimsa, satya (truthfulness), and manava mahatma (human dignity).
    Draws from dharmashastra tradition and contemporary Hindu ethics scholarship.
    """

    LENS_ID = "hindu_v1"
    REGEX_PATTERNS = [
        r"\b(violence|harm|attack)\b.*\b(minority|community|religious|dalit)\b",
        r"\b(inferior|polluted|impure)\b.*\b(caste|jati|dalit|untouchable)\b",
        r"\b(all|every)\b.*\b(muslim|hindu|christian|sikh)\b.*\b(terrorist|criminal|corrupt)\b",
        r"\bcaste\b.*\b(determines|decides|fixes)\b.*\b(intelligence|ability|destiny)\b",
        r"\b(superstition|nonsense|primitive)\b.*\b(ritual|prayer|worship|dharma)\b",
    ]

    def __init__(self, registry=None, use_semantic: bool = True) -> None:
        super().__init__("hindu_v1", use_semantic=use_semantic)
        self._western_lens = WesternLens(registry=registry, use_semantic=use_semantic)

    def score(self, text: str, language: str = "en") -> LensScore:
        return self._western_lens._score_with_patterns(
            text=text,
            lens_id=self.LENS_ID,
            regex_patterns=self.REGEX_PATTERNS,
            language=language,
            dimension_keys=["ahimsa_violation", "satya_violation",
                           "dharmic_disrespect", "dignity_harm", "caste_essentialism"],
        )
