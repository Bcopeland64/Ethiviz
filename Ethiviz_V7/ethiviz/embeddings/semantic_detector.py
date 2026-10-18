from __future__ import annotations
import numpy as np
from typing import Any, Dict, List
from ethiviz.embeddings.model import EmbeddingModel
from ethiviz.embeddings.prototype_store import PrototypeStore

# Floor for the calibration denominator, so a degenerate prototype set whose
# background similarity approaches 1.0 cannot blow the rescaling up.
_MIN_CALIBRATION_RANGE = 0.05


class SemanticBiasDetector:
    """Detects bias using semantic similarity to known biased prototypes."""

    def __init__(
        self,
        model: EmbeddingModel | None = None,
        store: PrototypeStore | None = None,
        calibrate_by_language: bool = True,
    ) -> None:
        self.model = model or EmbeddingModel.instance()
        self.store = store or PrototypeStore()
        self.calibrate_by_language = calibrate_by_language
        # Keyed by (lens_id, language) -> (prototypes, normalized prototype
        # embeddings, background_similarity). Each lens's prototype set is
        # static, so encoding it through the sentence-transformer model on
        # every detect() call (as this used to do) redid the same forward pass
        # for every text scored by every lens — the dominant cost of analysis
        # regardless of input size. Computed once per lens/language and reused
        # for the life of this detector instance.
        self._prototype_cache: Dict[tuple, tuple] = {}

    @staticmethod
    def _background_similarity(proto_norms: np.ndarray) -> float:
        """
        Mean off-diagonal similarity among a lens's own prototypes: how alike
        any two unrelated sentences look in this language.

        The embedding model represents some languages more coarsely than
        English. In those languages every sentence sits closer to every other
        sentence, so raw cosine similarity is inflated across the board and a
        threshold tuned on English (or the raw value used directly as a
        dimension score) reports bias that isn't there. Measuring the model's
        own background level for this prototype set gives a per-language
        reference point without hand-tuned constants.
        """
        n = proto_norms.shape[0]
        if n < 2:
            return 0.0
        sim_matrix = proto_norms @ proto_norms.T
        off_diagonal = sim_matrix[~np.eye(n, dtype=bool)]
        return float(np.mean(off_diagonal))

    def detect(self, text: str, lens_id: str, language: str = "en") -> Dict[str, float]:
        """
        Returns similarity scores for all prototypes in the given lens.
        Returns {prototype_id: similarity_score}.

        Scores are calibrated against the language's background similarity so
        they are comparable across languages; see _background_similarity.
        """
        cache_key = (lens_id, language)
        cached = self._prototype_cache.get(cache_key)
        if cached is None:
            prototypes = self.store.load(lens_id, language=language)
            if not prototypes:
                self._prototype_cache[cache_key] = ([], None, 0.0)
                return {}
            proto_texts = [p["text"] for p in prototypes]
            proto_embs = self.model.encode(proto_texts)
            proto_norms = proto_embs / (np.linalg.norm(proto_embs, axis=1, keepdims=True) + 1e-8)
            background = self._background_similarity(proto_norms)
            cached = (prototypes, proto_norms, background)
            self._prototype_cache[cache_key] = cached

        prototypes, proto_norms, background = cached
        if not prototypes:
            return {}

        input_emb = self.model.encode(text)

        # Cosine similarity
        # (input_emb: 1x384, proto_norms: Nx384)
        input_norm = input_emb / (np.linalg.norm(input_emb) + 1e-8)
        similarities = np.dot(proto_norms, input_norm.T).flatten()

        if self.calibrate_by_language:
            # Rescale so that "as similar as two unrelated prototypes" maps to
            # 0.0 and a perfect match still maps to 1.0. In English, where
            # prototypes are already well separated, background is low and this
            # barely moves the scores; in a coarsely-represented language it
            # removes the uniform inflation instead of letting every dimension
            # read as a hit.
            denom = max(1.0 - background, _MIN_CALIBRATION_RANGE)
            similarities = (similarities - background) / denom
            similarities = np.clip(similarities, 0.0, 1.0)

        return {
            prototypes[i]["id"]: float(similarities[i])
            for i in range(len(prototypes))
        }
