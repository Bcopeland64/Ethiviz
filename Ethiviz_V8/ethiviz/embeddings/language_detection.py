# ethiviz/embeddings/language_detection.py
from __future__ import annotations
import hashlib
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ar": "Arabic",
    "zh": "Mandarin",
    "es": "Spanish",
    "hi": "Hindi",
    "fr": "French",
}

SCRIPT_TOKENIZERS = {
    "zh": "jieba",        # character-level segmentation for Mandarin
    "ar": "stanza",       # morphological tokenisation for Arabic
    "hi": "stanza",       # Devanagari tokenisation for Hindi
    "en": "whitespace",
    "es": "whitespace",
    "fr": "whitespace",
}

@dataclass(frozen=True)
class LanguageDetectionResult:
    language_code: str           # ISO 639-1
    language_name: str
    confidence: float
    script: str                  # "latin" | "arabic" | "chinese" | "devanagari"
    tokenizer_required: str      # from SCRIPT_TOKENIZERS


_LANGUAGE_CACHE_MAX_ENTRIES = max(0, int(os.environ.get("ETHIVIZ_LANGUAGE_CACHE_SIZE", "2048")))
_LANGUAGE_CACHE_TTL_SECONDS = max(0, float(os.environ.get("ETHIVIZ_LANGUAGE_CACHE_TTL_SECONDS", "300")))
_LANGUAGE_CACHE: OrderedDict[str, tuple[float, LanguageDetectionResult]] = OrderedDict()
_LANGUAGE_CACHE_LOCK = threading.Lock()
_LANGUAGE_DETECTOR_VERSION = "langdetect-v1"


def clear_language_cache() -> None:
    """Clear cached language labels without retaining or exposing input text."""
    with _LANGUAGE_CACHE_LOCK:
        _LANGUAGE_CACHE.clear()


class LanguageDetector:
    """
    Language detection preprocessing step for all lens scoring.
    Uses langdetect (fasttext fallback) to identify input language.
    When detected language has prototype variants, loads them.
    When language is unsupported, warns and falls back to English
    with a reduced confidence score on the LensScore output.

    Example:
        >>> detector = LanguageDetector()
        >>> result = detector.detect("جميع المسلمين يدعمون العنف")
        >>> result.language_code
        'ar'
        >>> result.tokenizer_required
        'stanza'
        >>> result.script
        'arabic'
    """
    def detect(self, text: str) -> LanguageDetectionResult:
        normalized_text = " ".join(text.split())
        cache_enabled = (
            _LANGUAGE_CACHE_MAX_ENTRIES > 0
            and _LANGUAGE_CACHE_TTL_SECONDS > 0
            and os.environ.get("ETHIVIZ_DISABLE_LANGUAGE_CACHE", "").lower()
            not in {"1", "true", "yes"}
        )
        cache_key = hashlib.sha256(
            f"{_LANGUAGE_DETECTOR_VERSION}\0{normalized_text}".encode("utf-8")
        ).hexdigest()

        if cache_enabled:
            now = time.monotonic()
            with _LANGUAGE_CACHE_LOCK:
                cached = _LANGUAGE_CACHE.get(cache_key)
                if cached is not None:
                    expires_at, result = cached
                    if expires_at > now:
                        _LANGUAGE_CACHE.move_to_end(cache_key)
                        return result
                    del _LANGUAGE_CACHE[cache_key]

        result = self._detect_uncached(text)
        if cache_enabled:
            with _LANGUAGE_CACHE_LOCK:
                _LANGUAGE_CACHE[cache_key] = (
                    time.monotonic() + _LANGUAGE_CACHE_TTL_SECONDS,
                    result,
                )
                _LANGUAGE_CACHE.move_to_end(cache_key)
                while len(_LANGUAGE_CACHE) > _LANGUAGE_CACHE_MAX_ENTRIES:
                    _LANGUAGE_CACHE.popitem(last=False)
        return result

    def _detect_uncached(self, text: str) -> LanguageDetectionResult:
        try:
            from langdetect import detect as _detect, DetectorFactory
            DetectorFactory.seed = 42    # reproducibility
            code = _detect(text)
        except Exception:
            code = "en"  # fallback

        # langdetect returns regional variants for some languages (e.g.
        # "zh-cn"/"zh-tw" for Mandarin) that never match a bare key in
        # SUPPORTED_LANGUAGES. Every Chinese input was previously falling
        # through to the `code not in SUPPORTED_LANGUAGES` branch below and
        # silently scoring as English — a complete, silent loss of one of
        # the six supported languages. Normalizing to the primary subtag
        # fixes this without affecting codes that were already bare (en, ar,
        # es, hi, fr all come back unsuffixed from langdetect).
        code = code.split("-")[0]

        if code not in SUPPORTED_LANGUAGES:
            code = "en"

        script = self._detect_script(code)
        return LanguageDetectionResult(
            language_code=code,
            language_name=SUPPORTED_LANGUAGES.get(code, "Unknown"),
            confidence=0.90 if code in SUPPORTED_LANGUAGES else 0.50,
            script=script,
            tokenizer_required=SCRIPT_TOKENIZERS.get(code, "whitespace"),
        )

    def _detect_script(self, code: str) -> str:
        return {
            "ar": "arabic",
            "zh": "chinese",
            "hi": "devanagari",
        }.get(code, "latin")
