from __future__ import annotations
import numpy as np
from ethiviz.vision.cultural_element_detector import CLIPCulturalDetector

class CLIPObjectDetector(CLIPCulturalDetector):
    """
    General object detector using CLIP zero-shot matching.
    Extends CLIPCulturalDetector to handle arbitrary object queries.
    """
    def detect_objects(self, image: np.ndarray, queries: list[str]) -> dict[str, float]:
        self._load_model()
        if self._model is None:
            return {}

        import torch
        from PIL import Image as PILImage
        
        pil_image = PILImage.fromarray(image)
        inputs = self._processor(
            text=queries,
            images=pil_image,
            return_tensors="pt",
            padding=True,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
        
        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=0).tolist()
        
        return {query: prob for query, prob in zip(queries, probs)}
