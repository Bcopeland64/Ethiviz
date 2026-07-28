import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import signal
import subprocess
import uuid
import threading
import time
import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS # Import CORS
from werkzeug.utils import secure_filename
from pathlib import Path

# Ensure the parent directory is in sys.path to allow imports from Scripts
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# The ethiviz package is a direct sibling of Scripts/ inside Ethiviz_V5/ (not
# nested under an Ethiviz_V4/ subfolder, as in the original root copy).
ethiviz_root = parent_dir

# Real 7-lens cultural bias engine bridge (ethiviz.Analyzer), replacing the
# legacy Scripts/text_analyzer.py + image_analyzer.py pipeline, which never
# invoked the V4 ethiviz package.
import Scripts.ethiviz_bridge as bridge
HAS_TEXT_ANALYZER = True
HAS_IMAGE_ANALYZER = bridge.HAS_VISION

# Import SQLite-backed JobStore (Upgrade 31)
try:
    from ethiviz.storage.job_store import JobStore, DEFAULT_DB_PATH
    _job_store = JobStore()
    HAS_JOB_STORE = True
    logging.info(f"SQLite JobStore initialized at {_job_store.db_path}")
except ImportError as e:
    logging.warning(f"Could not import JobStore: {e}. Falling back to in-memory job storage.")
    _job_store = None
    HAS_JOB_STORE = False

app = Flask(__name__)
CORS(app) # Enable CORS for all routes and origins.

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS_TEXT = {'csv', 'xlsx', 'xls', 'json', 'txt'}
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# In-memory fallback job store (used if SQLite import fails)
_jobs_fallback: dict = {}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.INFO)


# ── Model warm-up ─────────────────────────────────────────────────────────────

def _warm_up_models():
    """Eagerly load the sentence-transformer embedding model and every lens's
    prototype-embedding cache at server startup, instead of paying that cost
    inside the first real analysis job.

    bridge.get_analyzer() and each lens's SemanticBiasDetector both build
    their expensive state lazily on first use: the ~120MB sentence-transformer
    model (ethiviz/embeddings/model.py), then one encode() pass per lens's
    prototype set. Left alone, the first job submitted after server start pays
    for all of that on top of the actual scoring work, which is what made the
    initial analysis look slow — every job after it is fast because the
    singleton is already warm. Calling lens.score() directly here (not
    analyzer.analyze()) warms the prototype cache without touching the shared
    PlattCalibrator/DriftMonitor state that analyze() updates.
    """
    start = time.time()
    try:
        analyzer = bridge.get_analyzer()
        for lens in analyzer.lenses.values():
            lens.score("warm up", language="en")
        if HAS_IMAGE_ANALYZER:
            bridge.get_image_backend()
        app.logger.info(f"Model warm-up completed in {time.time() - start:.1f}s")
    except Exception:
        app.logger.exception(
            "Model warm-up failed — models will load lazily on first request instead."
        )


# ── Job store helpers ────────────────────────────────────────────────────────

def _get_job(job_id: str) -> dict | None:
    """Retrieve a job by ID from SQLite or in-memory fallback."""
    if HAS_JOB_STORE:
        return _job_store.get_job(job_id)
    return _jobs_fallback.get(job_id)

def _create_job_record(job_id: str, analysis_type: str) -> None:
    """Persist a new job record."""
    if HAS_JOB_STORE:
        # Already created via _job_store.create_job() — update with job_id if needed
        pass  # handled in submit_analysis
    else:
        _jobs_fallback[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "analysis_type": analysis_type,
            "submission_time": time.time(),
        }

def _update_job(job_id: str, **kwargs) -> None:
    """Update job fields in the appropriate store."""
    if HAS_JOB_STORE:
        status = kwargs.get("status")
        error = kwargs.get("error")
        if status:
            _job_store.update_status(job_id, status, error)
        # Store any result data
        result = kwargs.get("result")
        if result and isinstance(result, dict):
            _job_store.store_results(job_id, result)
        # Also store extra data in fallback dict (for result retrieval)
        if job_id not in _jobs_fallback:
            _jobs_fallback[job_id] = {}
        _jobs_fallback[job_id].update(kwargs)
    else:
        if job_id in _jobs_fallback:
            _jobs_fallback[job_id].update(kwargs)

def _list_jobs(limit: int = 50) -> list[dict]:
    """List recent jobs."""
    if HAS_JOB_STORE:
        return _job_store.list_jobs(limit=limit)
    return list(_jobs_fallback.values())[:limit]


# --- Helper for Standardized Error Responses ---
def make_error_response(message, status_code, details=None):
    response = {"error": message}
    if details:
        response["details"] = details
    app.logger.error(f"Error {status_code}: {message} - Details: {details}")
    return jsonify(response), status_code

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/')
def home():
    return jsonify({"message": "EthiViz API Server is running.", "version": "0.6.0"})


# ── Sample Data (Upgrade 32) ─────────────────────────────────────────────────

def _get_sample_data_store() -> dict:
    """Build sample data store from actual sample CSV files."""
    sample_dir = Path(ethiviz_root) / "ethiviz" / "sample_data"
    tradition_files = [
        ("western", "sample_texts_western.csv"),
        ("ubuntu", "sample_texts_ubuntu.csv"),
        ("confucian", "sample_texts_confucian.csv"),
        ("islamic", "sample_texts_islamic.csv"),
        ("indigenous", "sample_texts_indigenous.csv"),
        ("buddhist", "sample_texts_buddhist.csv"),
        ("hindu", "sample_texts_hindu.csv"),
    ]
    texts = []
    for tradition, fname in tradition_files:
        fpath = sample_dir / fname
        if fpath.exists():
            texts.append({
                "id": f"sample_{tradition}",
                "name": f"{tradition.title()} Ethical Framework Sample",
                "description": f"Curated sample texts for {tradition.title()} lens evaluation.",
                "path": str(fpath),
                "tradition": tradition,
                "format": "csv",
            })
        else:
            texts.append({
                "id": f"sample_{tradition}",
                "name": f"{tradition.title()} Ethical Framework Sample",
                "description": f"Sample texts for {tradition.title()} lens (file not found).",
                "tradition": tradition,
                "format": "csv",
                "available": False,
            })

    return {
        "texts": texts,
        "images": [
            {
                "id": "sample_image_set_1",
                "name": "General Iconography",
                "description": "A diverse set of icons and symbols.",
            }
        ],
    }


@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """Returns available sample datasets with actual file metadata."""
    return jsonify(_get_sample_data_store())


# --- Analysis Job Function ---
def run_analysis_job(job_id, analysis_type, data_inputs, selected_traditions, advanced_options):
    """
    Runs the analysis in a separate thread.
    Updates the job status and results via the job store.
    """
    app.logger.info(f"Starting analysis for job_id: {job_id}")
    _update_job(job_id, status="processing", start_time=time.time(),
                progress={"percent": 0, "message": "Starting analysis..."})

    # Text and image phases each get a slice of the 0-100 progress range when
    # both run (text_and_image); a single-modality job gets the full range.
    has_text = "text" in analysis_type.lower()
    has_image = "image" in analysis_type.lower()
    text_span = (0, 47) if (has_text and has_image) else (0, 95)
    image_span = (47, 95) if (has_text and has_image) else (0, 95)

    def make_progress_cb(span, label):
        start, end = span
        def cb(done, total):
            percent = start + (end - start) * (done / total if total else 1)
            _update_job(job_id, progress={
                "percent": round(percent, 1),
                "message": f"{label}: {done}/{total}",
            })
        return cb

    try:
        text_results = None
        image_results = None
        text_scores: list[dict] = []
        image_scores: list[dict] = []

        selected_fids = bridge.resolve_framework_ids(selected_traditions)

        if has_text:
            text_input = data_inputs.get("text_input")
            app.logger.info(f"Job {job_id}: Running text analysis. Input type: {type(text_input)}")

            text_results, text_scores = bridge.run_text_analysis(
                text_input=text_input,
                selected_fids=selected_fids,
                job_id=job_id,
                progress_callback=make_progress_cb(text_span, "Analyzing text"),
            )
            app.logger.info(f"Job {job_id}: Text analysis completed.")

        if has_image:
            if not HAS_IMAGE_ANALYZER:
                app.logger.warning(
                    f"Job {job_id}: vision dependencies not installed — image analysis "
                    "will degrade to metadata-only proxies (see ethiviz_bridge.HAS_VISION)."
                )

            image_paths = data_inputs.get("image_paths")
            if not image_paths:
                raise ValueError("Image analysis requested but no image paths provided.")
            app.logger.info(f"Job {job_id}: Running image analysis for {len(image_paths)} images.")

            image_results, image_scores = bridge.run_image_analysis(
                image_paths=image_paths,
                selected_fids=selected_fids,
                progress_callback=make_progress_cb(image_span, "Analyzing images"),
            )
            app.logger.info(f"Job {job_id}: Image analysis completed.")

        _update_job(job_id, progress={"percent": 95, "message": "Finalizing results..."})
        final_results = {}
        if text_results:
            final_results["text_analysis"] = text_results
        if image_results:
            final_results["image_analysis"] = image_results
            os.makedirs('ethiviz_results', exist_ok=True)
            with open('ethiviz_results/image_analysis_results.json', 'w') as f:
                json.dump(image_results, f, indent=2)

        if not final_results:
            raise ValueError("No analysis was performed or results were empty.")

        tradition_scores = bridge.merge_tradition_scores_across_modalities(text_scores, image_scores)
        final_results["tradition_scores"] = tradition_scores

        _update_job(job_id, status="completed", result=final_results,
                    progress={"percent": 100, "message": "Analysis complete."})
        if HAS_JOB_STORE and tradition_scores:
            _job_store.store_results(job_id, bridge.to_sqlite_payload(tradition_scores))
        app.logger.info(f"Job {job_id} completed successfully.")

    except FileNotFoundError as fnf_error:
        _update_job(job_id, status="failed", error=f"File not found: {str(fnf_error)}")
        app.logger.error(f"Job {job_id} failed: File not found - {fnf_error}", exc_info=True)
    except ValueError as val_error:
        _update_job(job_id, status="failed", error=f"Invalid input or configuration: {str(val_error)}")
        app.logger.error(f"Job {job_id} failed: Value error - {val_error}", exc_info=True)
    except RuntimeError as rt_error:
        _update_job(job_id, status="failed", error=f"Analysis runtime error: {str(rt_error)}")
        app.logger.error(f"Job {job_id} failed: Runtime error - {rt_error}", exc_info=True)
    except Exception as e:
        _update_job(job_id, status="failed", error=f"An unexpected error occurred during analysis: {str(e)}")
        app.logger.exception(f"Job {job_id} failed with unexpected error: {e}")
    finally:
        end_time = time.time()
        start_time = _jobs_fallback.get(job_id, {}).get("start_time", end_time)
        _update_job(job_id, end_time=end_time, duration_seconds=end_time - start_time)


# --- API Endpoints ---
@app.route('/api/analyze', methods=['POST'])
def submit_analysis():
    """
    Submits a new analysis job.
    Expects multipart/form-data with analysis parameters and optional files.
    """
    app.logger.info(f"Received /api/analyze POST request from {request.remote_addr}")
    try:
        if 'analysis_type' not in request.form:
            return make_error_response("Missing 'analysis_type' parameter.", 400,
                                       details="Provide 'text', 'image', or 'text_and_image'.")

        analysis_type = request.form['analysis_type'].lower()
        valid_analysis_types = ['text', 'image', 'text_and_image']
        if analysis_type not in valid_analysis_types:
            return make_error_response(f"Invalid 'analysis_type': {analysis_type}.", 400,
                                       details=f"Valid types are: {', '.join(valid_analysis_types)}.")

        data_source_type = request.form.get('data_source_type', 'upload').lower()
        valid_data_source_types = ['upload', 'sample']
        if data_source_type not in valid_data_source_types:
            return make_error_response(f"Invalid 'data_source_type': {data_source_type}.", 400,
                                       details=f"Valid types are: {', '.join(valid_data_source_types)}.")

        selected_traditions = request.form.getlist('selected_traditions')
        if not selected_traditions:
            selected_traditions = ['western', 'ubuntu', 'confucian', 'islamic']
            app.logger.info("No traditions selected, using default list.")
        elif not isinstance(selected_traditions, list) or not all(isinstance(t, str) for t in selected_traditions):
            return make_error_response("'selected_traditions' must be a list of strings.", 400)

        advanced_options_json = request.form.get('advanced_options', '{}')
        try:
            advanced_options = json.loads(advanced_options_json)
            if not isinstance(advanced_options, dict):
                raise ValueError("Advanced options should be a JSON object.")
        except (json.JSONDecodeError, ValueError) as e:
            return make_error_response("Invalid JSON format for 'advanced_options'.", 400, details=str(e))

        # Create the job via the persistent store
        if HAS_JOB_STORE:
            job_id = _job_store.create_job(analysis_type=analysis_type)
        else:
            job_id = str(uuid.uuid4())

        # Initialize fallback entry for runtime state
        _jobs_fallback[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "analysis_type": analysis_type,
            "data_inputs_summary": {},
            "selected_traditions": selected_traditions,
            "advanced_options": advanced_options,
            "submission_time": time.time(),
            "progress": {"percent": 0, "message": "Queued"},
        }

        data_inputs = {"source_type": data_source_type}

        if data_source_type == 'upload':
            if analysis_type in ['text', 'text_and_image']:
                if 'text_file' not in request.files:
                    return make_error_response("Missing 'text_file' for text analysis upload.", 400)
                text_file = request.files['text_file']
                if text_file.filename == '':
                    return make_error_response("No text file selected for upload.", 400)
                if not allowed_file(text_file.filename, ALLOWED_EXTENSIONS_TEXT):
                    return make_error_response(f"Invalid text file type: {text_file.filename}.", 400,
                                               details=f"Allowed text types: {', '.join(ALLOWED_EXTENSIONS_TEXT)}")
                text_filename = secure_filename(text_file.filename)
                text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{text_filename}")
                text_file.save(text_filepath)
                data_inputs["text_input"] = text_filepath
                app.logger.info(f"Saved text file for job {job_id} to {text_filepath}")

            if analysis_type in ['image', 'text_and_image']:
                image_files = request.files.getlist('image_files')
                if not image_files or all(f.filename == '' for f in image_files):
                    return make_error_response("Missing 'image_files' for image analysis upload.", 400)

                saved_image_paths = []
                for img_file in image_files:
                    if not allowed_file(img_file.filename, ALLOWED_EXTENSIONS_IMAGE):
                        for p in saved_image_paths:
                            os.remove(p)
                        if "text_input" in data_inputs and os.path.exists(data_inputs["text_input"]):
                            os.remove(data_inputs["text_input"])
                        return make_error_response(f"Invalid image file type: {img_file.filename}.", 400,
                                                   details=f"Allowed image types: {', '.join(ALLOWED_EXTENSIONS_IMAGE)}")
                    img_filename = secure_filename(img_file.filename)
                    img_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{img_filename}")
                    img_file.save(img_filepath)
                    saved_image_paths.append(img_filepath)
                data_inputs["image_paths"] = saved_image_paths
                app.logger.info(f"Saved {len(saved_image_paths)} image files for job {job_id}.")

        elif data_source_type == 'sample':
            if analysis_type in ['text', 'text_and_image']:
                sample_text_id = request.form.get('sample_text_id')
                if not sample_text_id:
                    return make_error_response("Missing 'sample_text_id' for sample text analysis.", 400)
                # Try to load from actual sample CSV
                sample_dir = Path(ethiviz_root) / "ethiviz" / "sample_data"
                sample_map = {
                    "sample_western": sample_dir / "sample_texts_western.csv",
                    "sample_ubuntu": sample_dir / "sample_texts_ubuntu.csv",
                    "sample_confucian": sample_dir / "sample_texts_confucian.csv",
                    "sample_islamic": sample_dir / "sample_texts_islamic.csv",
                    "sample_indigenous": sample_dir / "sample_texts_indigenous.csv",
                    "sample_buddhist": sample_dir / "sample_texts_buddhist.csv",
                    "sample_hindu": sample_dir / "sample_texts_hindu.csv",
                    "sample_text_1": None,  # legacy
                }
                if sample_text_id == "sample_text_1":
                    data_inputs["text_input"] = (
                        "This is sample text about individual rights and community harmony. "
                        "Ubuntu teaches us compassion. Confucianism values order. "
                        "Islamic ethics stress justice."
                    )
                elif sample_text_id in sample_map and sample_map[sample_text_id] and sample_map[sample_text_id].exists():
                    data_inputs["text_input"] = str(sample_map[sample_text_id])
                else:
                    return make_error_response(f"Sample text ID '{sample_text_id}' not recognized.", 404)
                app.logger.info(f"Using sample text ID: {sample_text_id} for job {job_id}")

            if analysis_type in ['image', 'text_and_image']:
                sample_image_id = request.form.get('sample_image_id')
                if not sample_image_id:
                    return make_error_response("Missing 'sample_image_id' for sample image analysis.", 400)
                app.logger.warning(f"Sample image data handling for ID '{sample_image_id}' not fully implemented.")
                data_inputs["image_paths"] = []
                if not data_inputs["image_paths"]:
                    return make_error_response("Sample image data handling not implemented or ID not found.", 501,
                                               details=f"Sample image ID '{sample_image_id}' could not be processed.")

        _jobs_fallback[job_id]["data_inputs_summary"] = {
            k: (v if k != "image_paths" else f"{len(v)} images") for k, v in data_inputs.items()
        }

        app.logger.info(f"Job {job_id} created. Initial status: pending. Starting analysis thread.")
        thread = threading.Thread(target=run_analysis_job, args=(
            job_id,
            analysis_type,
            data_inputs,
            selected_traditions,
            advanced_options
        ))
        thread.daemon = True
        thread.start()

        status_url = request.url_root + f"api/analyze/status/{job_id}"
        return jsonify({
            "message": "Analysis job submitted successfully.",
            "job_id": job_id,
            "status": "pending",
            "status_url": status_url,
            "persistent_storage": HAS_JOB_STORE,
        }), 202

    except Exception as e:
        app.logger.exception(f"Unexpected error in /api/analyze: {e}")
        return make_error_response("An unexpected server error occurred while submitting the job.", 500, details=str(e))


@app.route('/api/analyze/status/<job_id>', methods=['GET'])
def get_analysis_status(job_id):
    """Returns the status of an analysis job."""
    # Try SQLite first, fall back to in-memory
    persistent_job = _get_job(job_id)
    memory_job = _jobs_fallback.get(job_id)

    if not persistent_job and not memory_job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    # Merge: persistent status takes precedence
    status = (persistent_job or {}).get("status") or (memory_job or {}).get("status", "unknown")
    submission_time = (memory_job or {}).get("submission_time")
    start_time = (memory_job or {}).get("start_time")
    end_time = (memory_job or {}).get("end_time")
    duration_seconds = (memory_job or {}).get("duration_seconds")
    progress = (memory_job or {}).get("progress") or {"percent": 0, "message": ""}

    response = {
        "job_id": job_id,
        "status": status,
        "submission_time": submission_time,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds,
        "progress": progress,
    }
    if status == "completed":
        response["message"] = "Analysis completed successfully."
        response["results_url"] = request.url_root + f"api/analyze/results/{job_id}"
    elif status == "failed":
        error_msg = (persistent_job or {}).get("error_message") or (memory_job or {}).get("error", "An unknown error occurred.")
        response["error_message"] = error_msg
    elif status == "processing":
        response["message"] = "Analysis is currently in progress."
    elif status == "pending":
        response["message"] = "Analysis job is pending execution."

    return jsonify(response)


@app.route('/api/analyze/results/<job_id>', methods=['GET'])
def get_analysis_results(job_id):
    """Returns the results of a completed analysis job."""
    persistent_job = _get_job(job_id)
    memory_job = _jobs_fallback.get(job_id)

    if not persistent_job and not memory_job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    status = (persistent_job or {}).get("status") or (memory_job or {}).get("status", "unknown")
    if status != "completed":
        error_msg = (persistent_job or {}).get("error_message") or (memory_job or {}).get("error")
        return make_error_response("Job not yet completed or has failed.", 422,
                                   details=f"Current job status: {status}. Error: {error_msg}")

    result = (memory_job or {}).get("result")
    analysis_type = (persistent_job or memory_job or {}).get("analysis_type")

    if result is None and HAS_JOB_STORE and status == "completed":
        # Server restarted since this job completed — _jobs_fallback (the
        # full-fidelity read path) lost the per-item results, but the
        # aggregate tradition_scores were persisted to SQLite. Reconstruct a
        # best-effort partial result rather than a 404.
        rows = _job_store.get_results(job_id)
        result = {
            "text_analysis": [],
            "image_analysis": {},
            "tradition_scores": bridge.reconstruct_tradition_scores(rows),
            "_partial": True,
            "_note": ("Full per-item results were lost on server restart; only "
                      "aggregate per-tradition scores were recoverable from "
                      "persistent storage."),
        }

    return jsonify({
        "job_id": job_id,
        "status": status,
        "analysis_type": analysis_type,
        "results": result,
    })


@app.route('/api/analyze/results/<job_id>/export', methods=['GET'])
def export_analysis_results(job_id):
    """
    Export analysis results as HTML report or raw JSON (Upgrade 33).
    Query param: format=html|json
    """
    fmt = request.args.get('format', 'json').lower()
    persistent_job = _get_job(job_id)
    memory_job = _jobs_fallback.get(job_id)

    if not persistent_job and not memory_job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    status = (persistent_job or {}).get("status") or (memory_job or {}).get("status", "unknown")
    if status != "completed":
        return make_error_response("Job not yet completed.", 422,
                                   details=f"Current job status: {status}")

    result = (memory_job or {}).get("result", {})

    if fmt == 'json':
        payload = json.dumps({"job_id": job_id, "results": result}, indent=2, default=str)
        return Response(
            payload,
            mimetype='application/json',
            headers={"Content-Disposition": f"attachment; filename=ethiviz_report_{job_id}.json"},
        )
    elif fmt == 'html':
        try:
            from ethiviz.reporting.html_report import generate_html_report
            from ethiviz.reporting.base import BiasReport
            # If we have a proper BiasReport, use it; otherwise build a minimal HTML summary
            html_content = _generate_fallback_html(job_id, result)
            return Response(
                html_content,
                mimetype='text/html',
                headers={"Content-Disposition": f"attachment; filename=ethiviz_report_{job_id}.html"},
            )
        except Exception as e:
            app.logger.warning(f"HTML report generation failed: {e}")
            html_content = _generate_fallback_html(job_id, result)
            return Response(
                html_content,
                mimetype='text/html',
                headers={"Content-Disposition": f"attachment; filename=ethiviz_report_{job_id}.html"},
            )
    else:
        return make_error_response(f"Unsupported export format: {fmt}", 400,
                                   details="Supported formats: html, json")


def _generate_fallback_html(job_id: str, result: dict) -> str:
    """Generate a simple HTML summary when the full BiasReport is unavailable."""
    result_json = json.dumps(result, indent=2, default=str)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>EthiViz Report — {job_id}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }}
    h1 {{ color: #6366f1; }}
    pre {{ background: #1e293b; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;
           font-size: 0.8rem; color: #94a3b8; }}
  </style>
</head>
<body>
  <h1>EthiViz Analysis Report</h1>
  <p>Job ID: <code>{job_id}</code></p>
  <h2>Results</h2>
  <pre>{result_json}</pre>
</body>
</html>"""


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List recent analysis jobs (Upgrade 31)."""
    limit = request.args.get('limit', 50, type=int)
    try:
        jobs = _list_jobs(limit=limit)
        return jsonify({"jobs": jobs, "count": len(jobs)})
    except Exception as e:
        return make_error_response("Failed to list jobs.", 500, details=str(e))


@app.route('/api/compare', methods=['POST'])
def compare_datasets():
    """
    Compare bias metrics between two completed analysis jobs (Upgrade 34).
    Body: {"job_id_a": "...", "job_id_b": "..."}
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        job_id_a = body.get("job_id_a", "").strip()
        job_id_b = body.get("job_id_b", "").strip()

        if not job_id_a or not job_id_b:
            return make_error_response("Both 'job_id_a' and 'job_id_b' are required.", 400)

        job_a = _get_job(job_id_a) or _jobs_fallback.get(job_id_a)
        job_b = _get_job(job_id_b) or _jobs_fallback.get(job_id_b)

        if not job_a:
            return make_error_response(f"Job A not found: {job_id_a}", 404)
        if not job_b:
            return make_error_response(f"Job B not found: {job_id_b}", 404)

        status_a = job_a.get("status", "unknown")
        status_b = job_b.get("status", "unknown")

        if status_a != "completed":
            return make_error_response(f"Job A is not completed (status: {status_a}).", 422)
        if status_b != "completed":
            return make_error_response(f"Job B is not completed (status: {status_b}).", 422)

        result_a = _jobs_fallback.get(job_id_a, {}).get("result", {})
        result_b = _jobs_fallback.get(job_id_b, {}).get("result", {})

        # Build per-tradition comparison from stored results
        comparison = _compare_job_results(job_id_a, result_a, job_id_b, result_b)

        return jsonify(comparison)

    except Exception as e:
        app.logger.exception(f"Error in /api/compare: {e}")
        return make_error_response("Comparison failed.", 500, details=str(e))


def _compare_job_results(job_id_a: str, result_a: dict, job_id_b: str, result_b: dict) -> dict:
    """Build a per-tradition comparison between two job results."""
    # Real per-tradition aggregate scores now live in the top-level
    # `tradition_scores` field (bridge.compute_tradition_scores), not nested
    # under text_analysis.framework_scores — nothing ever produced that shape.
    def extract_framework_scores(result: dict) -> dict[str, dict]:
        return {
            entry["tradition"]: {
                "overall_score": entry.get("score", 0.0),
                "severity": entry.get("severity", "unknown"),
            }
            for entry in (result or {}).get("tradition_scores", [])
        }

    scores_a = extract_framework_scores(result_a)
    scores_b = extract_framework_scores(result_b)

    all_traditions = set(scores_a) | set(scores_b)
    per_tradition: dict[str, dict] = {}

    for tid in sorted(all_traditions):
        sa = scores_a.get(tid, {})
        sb = scores_b.get(tid, {})
        score_a = sa.get("overall_score")
        score_b = sb.get("overall_score")
        improvement = (abs(score_a) - abs(score_b)) if (score_a is not None and score_b is not None) else None

        per_tradition[tid] = {
            "spd_before": score_a,
            "spd_after": score_b,
            "improvement": improvement,
            "severity_before": sa.get("severity"),
            "severity_after": sb.get("severity"),
        }

    # If no framework scores extracted, provide a basic summary
    if not per_tradition:
        per_tradition["_summary"] = {
            "spd_before": None,
            "spd_after": None,
            "improvement": None,
            "severity_before": None,
            "severity_after": None,
            "note": "No per-tradition framework scores available in results. Re-run analysis with EthiViz V5 API.",
        }

    return {
        "job_id_a": job_id_a,
        "job_id_b": job_id_b,
        "per_tradition_comparison": per_tradition,
        "summary": (
            f"Comparison of {len(all_traditions)} tradition(s) between "
            f"job {job_id_a[:8]}... and job {job_id_b[:8]}..."
        ),
    }


@app.route('/api/stop', methods=['POST'])
def stop_server():
    """
    Gracefully shut down the backend and the frontend dev server.

    Loopback-only: this process controls both halves of a local dev app, so a
    request from any other origin is rejected rather than trusted. Improves on
    the unauthenticated, os._exit(0)-based precedent in the (dead-code)
    ethiviz/server.py:210-227 by checking the caller's address and using a
    graceful SIGTERM instead of an abrupt exit.
    """
    if request.remote_addr not in ('127.0.0.1', '::1', 'localhost'):
        return make_error_response(
            "Forbidden: /api/stop is only callable from localhost.", 403
        )
    app.logger.warning(f"Received /api/stop from {request.remote_addr} — shutting down.")

    def _shutdown():
        time.sleep(0.3)  # let the response flush before tearing anything down
        try:
            subprocess.run(
                ["sh", "-c", "lsof -ti :5173 | xargs -r kill"],
                capture_output=True, timeout=5,
            )
        except Exception:
            app.logger.warning("Could not stop frontend process on port 5173.")
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({
        "status": "stopping",
        "message": "EthiViz backend and frontend are shutting down.",
    }), 200


if __name__ == '__main__':
    app.logger.info(f"EthiViz API Server starting (V5)...")
    app.logger.info(f"ethiviz.Analyzer bridge active: {HAS_TEXT_ANALYZER}")
    app.logger.info(f"Vision detection available: {HAS_IMAGE_ANALYZER}")
    app.logger.info(f"SQLite JobStore available: {HAS_JOB_STORE}")
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    # Warm the embedding model up in the background so it loads while the
    # server is starting (and while the user is still on the config page)
    # instead of during the first submitted job. Daemon thread: if it's still
    # running when a request arrives, get_analyzer()'s lock just makes that
    # request wait on the same load rather than duplicating it.
    threading.Thread(target=_warm_up_models, daemon=True).start()
    # use_reloader=False is required: with the Werkzeug debug reloader active,
    # a SIGTERM sent to the worker process by /api/stop can be silently
    # relaunched by the watcher parent instead of actually stopping the server.
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
