from __future__ import annotations
import numpy as np
from typing import Any, List

MODEL_ID = "sentence-transformers/all-MiniLM-L12-v2"

class EmbeddingModel:
    """Wrapper for the sentence-transformers embedding model."""
    _instance: EmbeddingModel | None = None

    def __init__(self, model_id: str = MODEL_ID) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_id)
        except ImportError:
            # Fallback for mock/testing
            self.model = None
            print(f"Warning: sentence-transformers not installed. Using mock model for {model_id}.")

    @classmethod
    def instance(cls) -> EmbeddingModel:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def encode(self, texts: List[str] | str) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model:
            return self.model.encode(texts)
        
        # Mock implementation: random embeddings
        return np.random.rand(len(texts), 384).astype(np.float32)
