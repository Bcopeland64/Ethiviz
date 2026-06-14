from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class DetectionBackend(ABC):
    """Base class for all bias detection backends."""
    @abstractmethod
    def detect(self, input_data: Any, **kwargs: Any) -> Any:
        pass
