from __future__ import annotations
from typing import Any, TypeVar, Protocol, runtime_checkable
import numpy as np

T = TypeVar("T")

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...

@runtime_checkable
class ImageArray(Protocol):
    """Protocol for image arrays (H, W, 3) np.ndarray."""
    def __getitem__(self, key: Any) -> Any: ...
    @property
    def shape(self) -> tuple[int, ...]: ...
    @property
    def dtype(self) -> np.dtype: ...
