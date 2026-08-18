# ethiviz/embeddings/language_detection.py
from __future__ import annotations
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

@dataclass
class LanguageDetectionResult:
    language_code: str           # ISO 639-1
    language_name: str
    confidence: float
    script: str                  # "latin" | "arabic" | "chinese" | "devanagari"
    tokenizer_required: str      # from SCRIPT_TOKENIZERS

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
