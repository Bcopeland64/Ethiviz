"""
ethiviz/server.py — Minimal Flask server for the EthiViz interactive report.

Endpoints:
    GET  /                    → serve the live-analysis landing report
    POST /analyze/text        → upload text file, return updated HTML report
    POST /analyze/image       → upload image file, return updated HTML report
    POST /stop                → shut down the server gracefully
"""
from __future__ import annotations
import io
import os
import sys
import threading
from pathlib import Path
from typing import Any

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from ethiviz.api import Analyzer
from ethiviz.context.deployment import DeploymentContext
from ethiviz.reporting.base import BiasReport
from ethiviz.reporting.html_report import generate_html_report
from ethiviz.scoring.base import ScoredResult
from ethiviz.utils.reproducibility import ReproducibilityRecord

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5000"])

# Default deployment context — overridable via env vars or startup argument
_DEFAULT_CTX = DeploymentContext(
    region=os.environ.get("ETHIVIZ_REGION", "US"),
    domain=os.environ.get("ETHIVIZ_DOMAIN", "general"),
    primary_community=os.environ.get("ETHIVIZ_COMMUNITY", "global"),
    regulatory_framework=os.environ.get("ETHIVIZ_REGULATION", "gdpr"),
)

_analyzer: Analyzer | None = None


def _get_analyzer(ctx: DeploymentContext | None = None) -> Analyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = Analyzer(
            deployment_context=ctx or _DEFAULT_CTX,
            use_semantic=True,
        )
    return _analyzer


def _empty_report(message: str) -> str:
    """Return a minimal HTML report shell when no analysis has run yet."""
    sr = ScoredResult(
        candidates=[],
        framework_scores=[],
        consensus_score=0.0,
        conflicts=[],
        synergy_amplifications=[],
        weat_results=None,
        iweat_results=None,
        deployment_context=_DEFAULT_CTX,
        reproducibility=ReproducibilityRecord.capture([]),
        metadata={
            "language_detected": "en",
            "n_texts": 0,
            "per_text_scores": {},
            "texts": [],
            "source_type": "text",
            "message": message,
        },
    )
    sr.generate_report = lambda: BiasReport(scored_result=sr)
    report = BiasReport(scored_result=sr, summary_text=message)
    return generate_html_report(report)


@app.route("/", methods=["GET"])
def index() -> Response:
    """Landing page — show an empty report template ready for file upload."""
    html = _empty_report("Upload a text or image file to begin analysis.")
    return Response(html, mimetype="text/html")


@app.route("/analyze/text", methods=["POST"])
def analyze_text() -> Response:
    """Accept a text/CSV/JSON upload and return a rendered HTML bias report."""
    if "file" not in request.files:
        return Response("No file provided", status=400)

    file = request.files["file"]
    raw_bytes = file.read()

    # Decode content
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            content = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return Response("Could not decode file as text", status=422)

    # Parse lines / CSV rows
    filename = file.filename or "upload.txt"
    if filename.endswith(".csv"):
        import csv
        reader = csv.reader(io.StringIO(content))
        texts = [" ".join(row) for row in reader if any(row)]
    elif filename.endswith(".json"):
        import json as _json
        try:
            data = _json.loads(content)
            if isinstance(data, list):
                texts = [str(item) for item in data if item]
            elif isinstance(data, dict):
                texts = [str(v) for v in data.values() if v]
            else:
                texts = [content]
        except Exception:
            texts = [content]
    else:
        texts = [ln.strip() for ln in content.splitlines() if ln.strip()]

    if not texts:
        return Response(
            _empty_report("File was empty or contained no usable text rows."),
            mimetype="text/html",
        )

    analyzer = _get_analyzer()
    run_weat = len(texts) >= 5   # only run WEAT when we have enough text
    result = analyzer.analyze(
        dataset=texts,
        run_weat=run_weat,
        dataset_source=filename,
    )
    # Enrich metadata for the template
    result.metadata["source_type"] = "text"
    result.metadata["filename"] = filename
    result.metadata["file_size"] = f"{len(raw_bytes):,} bytes"

    report = result.generate_report()
    html = generate_html_report(report)
    return Response(html, mimetype="text/html")


@app.route("/analyze/image", methods=["POST"])
def analyze_image() -> Response:
    """Accept an image upload and run ITA skin-tone + text-proxy analysis."""
    if "file" not in request.files:
        return Response("No file provided", status=400)

    file = request.files["file"]
    raw_bytes = file.read()
    filename = file.filename or "upload.png"
    import base64
    mime = file.content_type or "image/png"
    data_uri = f"data:{mime};base64,{base64.b64encode(raw_bytes).decode()}"

    # ── ITA skin-tone analysis (OpenCV + PIL available) ──────────────
    vision_summary: str
    vision_detail: dict = {}
    try:
        import numpy as np
        from PIL import Image as PILImage
        from ethiviz.vision.skin_tone import ITASkinToneEstimator

        img = PILImage.open(io.BytesIO(raw_bytes)).convert("RGB")
        arr = np.array(img)
        estimator = ITASkinToneEstimator()
        result_ita = estimator.estimate(arr)

        vision_detail = {
            "fitzpatrick_type": result_ita.fitzpatrick_type,
            "ita_angle": round(result_ita.ita_angle, 2),
            "mean_l": round(result_ita.mean_l, 2),
            "mean_b": round(result_ita.mean_b, 2),
            "pixel_coverage": f"{result_ita.pixel_coverage * 100:.1f}%",
            "image_size": f"{img.width}×{img.height}",
        }
        vision_summary = (
            f"Skin tone: {result_ita.fitzpatrick_type} "
            f"(ITA={result_ita.ita_angle:.1f}°) — "
            f"{result_ita.pixel_coverage*100:.1f}% skin pixels sampled"
        )
    except Exception as exc:
        vision_summary = f"Vision analysis unavailable: {exc}"

    # ── Run text lenses on a descriptive proxy sentence ──────────────
    proxy = f"Image uploaded for skin-tone and diversity analysis. {vision_summary}"
    analyzer = _get_analyzer()
    result = analyzer.analyze(dataset=[proxy], dataset_source=filename)

    result.metadata.update({
        "source_type": "image",
        "source_content": data_uri,
        "filename": filename,
        "file_size": f"{len(raw_bytes):,} bytes",
        "vision_findings": vision_summary,
        "vision_detail": vision_detail,
        "n_texts": 1,
    })

    report = result.generate_report()
    html = generate_html_report(report)
    return Response(html, mimetype="text/html")


@app.route("/stop", methods=["POST"])
def stop() -> Response:
    """Shut down the Flask server and the frontend dev server."""
    def _shutdown():
        import subprocess, time
        time.sleep(0.3)
        # Kill the Vite frontend (port 5173) if running
        try:
            subprocess.run(
                ["sh", "-c", "lsof -ti :5173 | xargs -r kill -9"],
                capture_output=True,
            )
        except Exception:
            pass
        os._exit(0)

    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({"status": "stopping"})


@app.route("/health", methods=["GET"])
def health() -> Response:
    return jsonify({"status": "ok", "version": "4.0.0"})


def _warmup() -> None:
    """Load the embedding model and initialise the analyzer in a background thread."""
    try:
        from ethiviz.embeddings.model import EmbeddingModel
        EmbeddingModel.instance().encode(["warmup"])
        _get_analyzer()
        print("EthiViz: model warm-up complete — ready to analyse.")
    except Exception as exc:
        print(f"EthiViz: warm-up warning ({exc}); analysis will load on first request.")


def run(host: str = "0.0.0.0", port: int = 5001, debug: bool = False) -> None:
    """Start the EthiViz server."""
    print(f"EthiViz server starting on http://{host}:{port}")
    threading.Thread(target=_warmup, daemon=True).start()
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EthiViz V4 server")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    run(host=args.host, port=args.port, debug=args.debug)
