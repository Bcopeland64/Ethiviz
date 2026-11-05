# ethiviz/vision/cultural_element_detector.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

CULTURAL_ELEMENT_QUERIES = {
    "religious_symbols": [
        "hijab", "niqab", "turban", "kippah", "cross", "crucifix",
        "prayer beads", "rosary", "bindi", "tilak", "Buddhist robes",
    ],
    "cultural_clothing": [
        "sari", "kimono", "hanbok", "dashiki", "kente cloth",
        "cheongsam", "thobe", "dirndl", "kufi",
    ],
    "cultural_landmarks": [
        "mosque", "temple", "cathedral", "synagogue", "pagoda",
        "shrine", "stupa",
    ],
}

@dataclass
class CulturalElementResult:
    found_elements: dict[str, list[str]]     # category → list of detected items
    essentialism_risk: dict[str, float]      # risk scores per category
    cultural_landmarks: list[str]            # subset of found landmarks
    diversity_count: int                     # total distinct elements found

class CLIPCulturalDetector:
    """
    Zero-shot cultural element detection using OpenAI CLIP.
    Avoids training a custom classifier by using CLIP's zero-shot capability
    to match image regions against text descriptions of cultural elements.

    No training data required, no API key, CPU-capable (slow but functional).

    Requires: pip install ethiviz[vision]

    Example:
        >>> detector = CLIPCulturalDetector()
        >>> result = detector.detect(image_array)
        >>> "religious_symbols" in result.found_elements
        True
    """
    def __init__(self, confidence_threshold: float = 0.25) -> None:
        self.threshold = confidence_threshold
        self._model = None
        self._processor = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        except ImportError:
            # Mock or warning
            print("Warning: transformers/torch not installed. Using mock cultural detector.")

    def detect(self, image: np.ndarray) -> CulturalElementResult:
        if self._model is None:
            # Lazy load or mock
            try:
                import torch
                from PIL import Image as PILImage
                self._load_model()
            except ImportError:
                return CulturalElementResult({}, {}, [], 0)

        import torch
        from PIL import Image as PILImage
        
        pil_image = PILImage.fromarray(image)
        found: dict[str, list[str]] = {cat: [] for cat in CULTURAL_ELEMENT_QUERIES}

        for category, queries in CULTURAL_ELEMENT_QUERIES.items():
            if not queries:
                continue
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
            for item, prob in zip(queries, probs):
                if prob >= self.threshold:
                    found[category].append(item)

        # Essentialism risk: single element dominating one category
        essentialism_risk = {}
        for cat, items in found.items():
            if len(items) == 1:
                essentialism_risk[cat] = 0.7   # single item = higher essentialist risk
            elif len(items) == 0:
                essentialism_risk[cat] = 0.0
            else:
                essentialism_risk[cat] = max(0.0, 0.7 - (len(items) - 1) * 0.15)

        landmarks = found.get("cultural_landmarks", [])
        diversity = sum(len(v) for v in found.values())

        return CulturalElementResult(
            found_elements=found,
            essentialism_risk=essentialism_risk,
            cultural_landmarks=landmarks,
            diversity_count=diversity,
        )
