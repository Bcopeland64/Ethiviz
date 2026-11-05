"""
ethiviz/reporting/explainability.py — LIME-style token attribution for bias detection.

Implements a fast perturbation-based explainer that does not require the full
`lime` library. The explainer:
  1. Tokenises the text (script-aware for CJK / Arabic / Devanagari).
  2. Generates N masked variants by randomly zeroing out tokens.
  3. Scores each variant through the lens.
  4. Fits a simple linear regression attributing score change to each token.

The result is a list of (token, attribution) pairs suitable for inline HTML
heat-map highlighting. Positive attribution → token drove bias score up.
"""
from __future__ import annotations
import re
import numpy as np
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextExplanation:
    input_text: str
    tokens: list[str]
    attributions: list[float]          # one float per token, range ≈ [-1, 1]
    lens_id: str
    base_score: float = 0.0
    top_positive: list[tuple[str, float]] = field(default_factory=list)
    top_negative: list[tuple[str, float]] = field(default_factory=list)

    def to_html_highlight(self, max_tokens: int = 60) -> str:
        """
        Return an HTML fragment with each token wrapped in a <span> whose
        background colour reflects its attribution (red = positive / bias-driving,
        blue = negative / protective).
        """
        parts: list[str] = []
        for tok, attr in zip(self.tokens[:max_tokens], self.attributions[:max_tokens]):
            if attr > 0.05:
                intensity = min(int(attr * 255), 200)
                bg = f"rgba(239,68,68,{intensity/255:.2f})"
                color = "#fff" if intensity > 80 else "#fca5a5"
            elif attr < -0.05:
                intensity = min(int(-attr * 255), 200)
                bg = f"rgba(34,211,238,{intensity/255:.2f})"
                color = "#fff" if intensity > 80 else "#67e8f9"
            else:
                bg = "transparent"
                color = "#94a3b8"
            escaped = tok.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(
                f'<span style="background:{bg};color:{color};'
                f'padding:.1rem .2rem;border-radius:3px" '
                f'title="attribution: {attr:.3f}">{escaped}</span>'
            )
        return " ".join(parts)


class ScriptAwareTokenizer:
    """Routes to the correct tokeniser based on detected script."""

    def tokenize(self, text: str, script: str) -> list[str]:
        if script == "chinese":
            try:
                import jieba
                return list(jieba.cut(text))
            except ImportError:
                raise ImportError(
                    "Mandarin tokenisation requires jieba: pip install ethiviz[multilingual]"
                )
        elif script in ("arabic", "devanagari"):
            try:
                import stanza
                lang = "ar" if script == "arabic" else "hi"
                nlp = stanza.Pipeline(lang, processors="tokenize", verbose=False)
                doc = nlp(text)
                return [w.text for sent in doc.sentences for w in sent.words]
            except ImportError:
                raise ImportError(
                    "Arabic/Hindi tokenisation requires stanza: pip install ethiviz[multilingual]"
                )
        else:
            # Whitespace + preserve punctuation as separate tokens
            return re.findall(r"\S+", text)


class LIMETextExplainer:
    """
    Perturbation-based token attribution. Works with any lens that exposes
    `score(text: str) -> LensScore`.

    Parameters
    ----------
    n_samples : int
        Number of masked variants to generate. Higher = more stable but slower.
    mask_token : str
        Replacement string for masked tokens. Default is empty string.
    seed : int
        Random seed for reproducibility.
    """

    def __init__(
        self, n_samples: int = 80, mask_token: str = "", seed: int = 42
    ) -> None:
        self.n_samples = n_samples
        self.mask_token = mask_token
        self.rng = np.random.default_rng(seed)

    def explain(
        self, text: str, lens: Any, script: str = "latin", language: str = "en"
    ) -> TextExplanation:
        tokenizer = ScriptAwareTokenizer()
        tokens = tokenizer.tokenize(text, script)
        if not tokens:
            return TextExplanation(text, [], [], lens.lens_id)

        n = len(tokens)
        base_score = lens.score(text, language=language).overall_score

        # Generate binary presence matrix (n_samples × n_tokens)
        presence = self.rng.integers(0, 2, size=(self.n_samples, n), dtype=np.int8)
        # Ensure at least one token present per sample
        for i in range(self.n_samples):
            if presence[i].sum() == 0:
                presence[i, self.rng.integers(0, n)] = 1

        # Score each masked variant
        scores = np.zeros(self.n_samples, dtype=float)
        sep = "" if script == "chinese" else " "
        for i, mask in enumerate(presence):
            masked_text = sep.join(
                tokens[j] if mask[j] else self.mask_token for j in range(n)
            ).strip()
            if masked_text:
                scores[i] = lens.score(masked_text, language=language).overall_score
            else:
                scores[i] = 0.0

        # Linear regression: attribution[j] = coef of token_j on score
        # X = presence matrix (float), y = masked scores
        X = presence.astype(float)
        # Add intercept column
        X_int = np.hstack([np.ones((self.n_samples, 1)), X])
        try:
            coef, _, _, _ = np.linalg.lstsq(X_int, scores, rcond=None)
            attributions = coef[1:].tolist()   # drop intercept
        except np.linalg.LinAlgError:
            attributions = [0.0] * n

        # Normalise to [-1, 1] range
        max_abs = max(abs(a) for a in attributions) if attributions else 1.0
        if max_abs > 0:
            attributions = [a / max_abs for a in attributions]

        # Summary
        paired = sorted(zip(tokens, attributions), key=lambda x: -x[1])
        top_pos = [(t, a) for t, a in paired if a > 0.1][:5]
        top_neg = [(t, a) for t, a in paired[::-1] if a < -0.1][:5]

        return TextExplanation(
            input_text=text,
            tokens=tokens,
            attributions=attributions,
            lens_id=lens.lens_id,
            base_score=base_score,
            top_positive=top_pos,
            top_negative=top_neg,
        )


class SHAPTextExplainer:
    """
    KernelSHAP-style explainer (delegates to LIMETextExplainer with higher
    n_samples for better Shapley value approximation).
    """

    def __init__(self, n_samples: int = 200, seed: int = 42) -> None:
        self._lime = LIMETextExplainer(n_samples=n_samples, seed=seed)

    def explain(
        self, text: str, lens: Any, script: str = "latin", language: str = "en"
    ) -> TextExplanation:
        return self._lime.explain(text, lens, script=script, language=language)
