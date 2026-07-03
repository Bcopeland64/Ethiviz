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
        self._prototype_cache: Dict[str, np.ndarray] = {}

    def detect(self, text: str, lens_id: str, language: str = "en") -> Dict[str, float]:
        """
        Returns similarity scores for all prototypes in the given lens.
        Returns {prototype_id: similarity_score}.
        """
        prototypes = self.store.load(lens_id, language=language)
        if not prototypes:
            return {}

        input_emb = self.model.encode(text)
        
        # Prototype embeddings (could be cached)
        proto_texts = [p["text"] for p in prototypes]
        proto_embs = self.model.encode(proto_texts)
        
        # Cosine similarity
        # (input_emb: 1x384, proto_embs: Nx384)
        input_norm = input_emb / (np.linalg.norm(input_emb) + 1e-8)
        proto_norms = proto_embs / (np.linalg.norm(proto_embs, axis=1, keepdims=True) + 1e-8)
        
        similarities = np.dot(proto_norms, input_norm.T).flatten()
        
        return {
            prototypes[i]["id"]: float(similarities[i])
            for i in range(len(prototypes))
        }
