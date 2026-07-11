from __future__ import annotations
import numpy as np
from typing import Any, Dict, List
from ethiviz.embeddings.model import EmbeddingModel
from ethiviz.embeddings.prototype_store import PrototypeStore

class SemanticBiasDetector:
    """Detects bias using semantic similarity to known biased prototypes."""
    def __init__(
        self,
        model: EmbeddingModel | None = None,
        store: PrototypeStore | None = None
    ) -> None:
        self.model = model or EmbeddingModel.instance()
        self.store = store or PrototypeStore()
        # Keyed by (lens_id, language) -> (prototypes, normalized prototype
        # embeddings). Each lens's prototype set is static, so encoding it
        # through the sentence-transformer model on every detect() call (as
        # this used to do) redid the same forward pass for every text scored
        # by every lens — the dominant cost of analysis regardless of input
        # size. Computed once per lens/language and reused for the life of
        # this detector instance (one per lens, held for the process).
        self._prototype_cache: Dict[tuple, tuple] = {}

    def detect(self, text: str, lens_id: str, language: str = "en") -> Dict[str, float]:
        """
        Returns similarity scores for all prototypes in the given lens.
        Returns {prototype_id: similarity_score}.
        """
        cache_key = (lens_id, language)
        cached = self._prototype_cache.get(cache_key)
        if cached is None:
            prototypes = self.store.load(lens_id, language=language)
            if not prototypes:
                self._prototype_cache[cache_key] = ([], None)
                return {}
            proto_texts = [p["text"] for p in prototypes]
            proto_embs = self.model.encode(proto_texts)
            proto_norms = proto_embs / (np.linalg.norm(proto_embs, axis=1, keepdims=True) + 1e-8)
            cached = (prototypes, proto_norms)
            self._prototype_cache[cache_key] = cached

        prototypes, proto_norms = cached
        if not prototypes:
            return {}

        input_emb = self.model.encode(text)

        # Cosine similarity
        # (input_emb: 1x384, proto_norms: Nx384)
        input_norm = input_emb / (np.linalg.norm(input_emb) + 1e-8)
        similarities = np.dot(proto_norms, input_norm.T).flatten()

        return {
            prototypes[i]["id"]: float(similarities[i])
            for i in range(len(prototypes))
        }
