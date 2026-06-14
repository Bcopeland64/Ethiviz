from __future__ import annotations
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.lenses.western import WesternLens


class IndigenousLens(EthicalLens):
    """
    Indigenous / First Nations ethical lens.
    Centres land-relational ethics, the seven-generations principle, CARE Principles,
    and FNIGC protocols for collective data stewardship.
    """

    LENS_ID = "indigenous_v1"
    REGEX_PATTERNS = [
        r"\b(exploit|extract|mine|harvest)\b.*\b(land|resource|territory|forest)\b",
        r"\b(primitive|savage|uncivilized|backward)\b.*\b(indigenous|native|tribal|aboriginal)\b",
        r"\btraditional knowledge\b.*\b(patent|own|commerciali[sz]e)\b",
        r"\b(dying out|disappearing|extinct)\b.*\b(language|culture|tradition|people)\b",
        r"\bprofit\b.*\b(future generations?|environment|ecosystem)\b",
    ]

    def __init__(self, registry=None, use_semantic: bool = True) -> None:
        super().__init__("indigenous_v1", use_semantic=use_semantic)
        self._western_lens = WesternLens(registry=registry, use_semantic=use_semantic)

    def score(self, text: str, language: str = "en") -> LensScore:
        return self._western_lens._score_with_patterns(
            text=text,
            lens_id=self.LENS_ID,
            regex_patterns=self.REGEX_PATTERNS,
            language=language,
            dimension_keys=["land_relational_harm", "knowledge_extraction",
                           "cultural_erasure", "seven_generations_violation", "stereotyping"],
        )
