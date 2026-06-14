from __future__ import annotations
import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

def memoize(func: F) -> F:
    """Simple in-memory cache for functions."""
    cache: dict[tuple[Any, ...], Any] = {}
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper  # type: ignore
