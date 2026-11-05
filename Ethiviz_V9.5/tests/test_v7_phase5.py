from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "Scripts"
sys.path.insert(0, str(SCRIPTS))


def _reload_api_server(monkeypatch, api_keys: str = ""):
    monkeypatch.setenv("ETHIVIZ_API_KEYS", api_keys)
    monkeypatch.delenv("ETHIVIZ_REDIS_URL", raising=False)
    import api_server
    return importlib.reload(api_server)


def test_validate_api_key_accepts_bearer_token(monkeypatch):
    api_server = _reload_api_server(monkeypatch, "alpha, beta")
    valid_hashes = api_server._VALID_KEY_HASHES
    assert api_server._validate_api_key("Bearer beta", valid_hashes) is not None
    assert api_server._validate_api_key("Bearer wrong", valid_hashes) is None


def test_pdf_export_returns_valid_pdf(monkeypatch):
    api_server = _reload_api_server(monkeypatch, "")
    job_id = "job-pdf-123"
    api_server._jobs_fallback[job_id] = {
        "status": "completed",
        "result": {"tradition_scores": [{"tradition": "western", "score": 0.8}]},
        "owner_key_hash": None,
    }

    client = api_server.app.test_client()
    response = client.get(f"/api/analyze/results/{job_id}/export?format=pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
