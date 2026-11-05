from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Scripts"))

from ethiviz.embeddings import language_detection as language_module  # noqa: E402
from ethiviz.embeddings.language_detection import (  # noqa: E402
    LanguageDetectionResult,
    LanguageDetector,
    clear_language_cache,
)


def test_language_cache_is_bounded_and_does_not_retain_raw_text(monkeypatch):
    clear_language_cache()
    monkeypatch.setattr(language_module, "_LANGUAGE_CACHE_MAX_ENTRIES", 1)
    monkeypatch.setattr(language_module, "_LANGUAGE_CACHE_TTL_SECONDS", 60)
    calls = []

    def detect(text):
        calls.append(text)
        return LanguageDetectionResult("en", "English", 0.9, "latin", "whitespace")

    monkeypatch.setattr(LanguageDetector, "_detect_uncached", staticmethod(detect))
    detector = LanguageDetector()
    detector.detect("Sensitive user content")
    detector.detect("Sensitive   user content")

    assert calls == ["Sensitive user content"]
    assert len(language_module._LANGUAGE_CACHE) == 1
    assert "Sensitive user content" not in language_module._LANGUAGE_CACHE
    clear_language_cache()


def test_language_cache_can_be_disabled(monkeypatch):
    clear_language_cache()
    monkeypatch.setattr(language_module, "_LANGUAGE_CACHE_MAX_ENTRIES", 2)
    monkeypatch.setattr(language_module, "_LANGUAGE_CACHE_TTL_SECONDS", 60)
    monkeypatch.setenv("ETHIVIZ_DISABLE_LANGUAGE_CACHE", "true")
    calls = []
    result = LanguageDetectionResult("en", "English", 0.9, "latin", "whitespace")
    monkeypatch.setattr(
        LanguageDetector,
        "_detect_uncached",
        staticmethod(lambda text: calls.append(text) or result),
    )

    detector = LanguageDetector()
    detector.detect("same text")
    detector.detect("same text")

    assert calls == ["same text", "same text"]
    assert not language_module._LANGUAGE_CACHE


def test_api_security_headers_cover_api_and_html_responses():
    import api_server

    api_response = api_server.app.test_client().get("/")
    assert api_response.headers["X-Content-Type-Options"] == "nosniff"
    assert api_response.headers["X-Frame-Options"] == "DENY"
    assert api_response.headers["Referrer-Policy"] == "same-origin"
    assert "Permissions-Policy" in api_response.headers

    html_response = api_server.app.response_class("<h1>Report</h1>", mimetype="text/html")
    secured_response = api_server._set_security_headers(html_response)
    assert "default-src 'none'" in secured_response.headers["Content-Security-Policy"]


def test_bind_configuration_fails_closed_for_exposed_services(monkeypatch):
    import api_server

    monkeypatch.setattr(api_server, "AUTH_ENABLED", False)
    api_server._validate_bind_configuration("127.0.0.1", False)
    api_server._validate_bind_configuration("::1", False)
    api_server._validate_bind_configuration("localhost", True)
    with pytest.raises(RuntimeError, match="without API-key authentication"):
        api_server._validate_bind_configuration("0.0.0.0", False)

    monkeypatch.setattr(api_server, "AUTH_ENABLED", True)
    api_server._validate_bind_configuration("0.0.0.0", False)
    with pytest.raises(RuntimeError, match="development server"):
        api_server._validate_bind_configuration("0.0.0.0", True)


def test_xlsx_archives_are_limited_by_expansion_ratio(tmp_path):
    import api_server

    allowed = tmp_path / "allowed.xlsx"
    with zipfile.ZipFile(allowed, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("small.txt", "spreadsheet content")
    assert api_server._verify_text_content(str(allowed), "xlsx")

    oversized = tmp_path / "oversized.xlsx"
    with zipfile.ZipFile(oversized, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("large.txt", "0" * 100_000)
    assert not api_server._verify_text_content(str(oversized), "xlsx")
