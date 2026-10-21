import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import hashlib
import hmac
import html
import ipaddress
import json
import signal
import subprocess
import uuid
import threading
import time
import logging
import zipfile
from typing import Any
from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS # Import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
import filetype

# Pillow is only guaranteed to be installed with the `vision` extra (see
# README "What's real vs. what's scaffolding") — image analysis degrades to
# a metadata-only proxy without it. Guard this import the same way
# ethiviz_bridge.HAS_VISION does, rather than making Pillow a hard
# requirement just for the decompression-bomb guard below.
try:
    from PIL import Image as _PILImage
    _PILImage.MAX_IMAGE_PIXELS = 64_000_000  # ~8000x8000px cap
except ImportError:
    pass

# Ensure the parent directory is in sys.path to allow imports from Scripts
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# The ethiviz package is a direct sibling of Scripts/ inside Ethiviz_V5/ (not
# nested under an Ethiviz_V4/ subfolder, as in the original root copy).
ethiviz_root = parent_dir

# Structured JSON logging (Upgrade 50) — configured before anything below
# logs a single line, so the JobStore/queue startup messages come out
# structured too, not just requests handled after the app is fully up.
import Scripts.observability as observability
observability.configure_json_logging()

# Real 7-lens cultural bias engine bridge (ethiviz.Analyzer), replacing the
# legacy Scripts/text_analyzer.py + image_analyzer.py pipeline, which never
# invoked the V4 ethiviz package.
import Scripts.ethiviz_bridge as bridge
HAS_TEXT_ANALYZER = True
HAS_IMAGE_ANALYZER = bridge.HAS_VISION

# Bounded analysis queue (Upgrade 46) — RQ/Redis when ETHIVIZ_REDIS_URL is
# set, an in-process ThreadPoolExecutor otherwise, replacing the previous
# unbounded threading.Thread-per-request submission below.
from Scripts.analysis_queue import AnalysisQueue, QueueFullError
_analysis_queue = AnalysisQueue()
observability.register_queue_depth_provider(lambda: _analysis_queue.depth)

# Import SQLite-backed JobStore (Upgrade 31); Postgres opt-in via
# DATABASE_URL (Upgrade 48) — see ethiviz/storage/job_store.py.
try:
    from ethiviz.storage.job_store import JobStore, DEFAULT_DB_PATH
    _job_store = JobStore()
    HAS_JOB_STORE = True
    logging.info(f"JobStore initialized ({_job_store.backend_name}): "
                 f"{_job_store.db_path or _job_store.database_url}")
except ImportError as e:
    logging.warning(f"Could not import JobStore: {e}. Falling back to in-memory job storage.")
    _job_store = None
    HAS_JOB_STORE = False

app = Flask(__name__)
# CORS(app) with no origins= previously allowed any origin to call every
# route, including /api/analyze (accepts file uploads) and /api/jobs (lists
# all job history) — any site a user's browser visited could read their
# analysis results cross-origin. Per CLAUDE.md the frontend runs on
# http://localhost:5173; ETHIVIZ_ALLOWED_ORIGINS overrides for other
# deployments (comma-separated).
_allowed_origins = [
    o.strip() for o in os.environ.get(
        'ETHIVIZ_ALLOWED_ORIGINS', 'http://localhost:5173'
    ).split(',') if o.strip()
]
CORS(app, origins=_allowed_origins)

# request.remote_addr is used for /api/stop's loopback-only check, rate
# limiting, and upload-quota keys when auth is disabled. Behind the nginx
# reverse proxy in deploy/nginx.conf.sample, every request's actual TCP
# connection comes from nginx itself — without this, request.remote_addr
# would read as 127.0.0.1 for every caller, which would silently defeat
# /api/stop's loopback check for anyone going through the public proxy.
# ETHIVIZ_TRUST_PROXY must be explicitly set (Upgrade 42's deploy/ path only)
# — applying ProxyFix unconditionally would let any *direct*, unproxied
# caller spoof X-Forwarded-For to impersonate 127.0.0.1 themselves, which is
# worse than not having this at all.
if os.environ.get('ETHIVIZ_TRUST_PROXY', '').lower() in ('1', 'true'):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ── API-key authentication (Upgrade 40) ─────────────────────────────────────
# No route previously required any credential — anyone who could reach this
# port could read, list, and delete every job. ETHIVIZ_API_KEYS is
# comma-separated; auth is OFF by default (unset/empty) so the zero-config
# dev workflow in start_ethiviz.sh is unchanged. Only the sha256 hash of each
# configured key is ever kept in memory — plaintext keys are read once from
# the environment and discarded. Deliberately a full (untruncated) digest,
# unlike this codebase's usual hashlib.sha256(...).hexdigest()[:16]
# content-fingerprinting convention (see ethiviz/utils/reproducibility.py) —
# that truncation is fine for non-security fingerprints but would weaken a
# credential check.
_configured_api_keys = {
    k.strip() for k in os.environ.get('ETHIVIZ_API_KEYS', '').split(',') if k.strip()
}
_VALID_KEY_HASHES = {
    hashlib.sha256(k.encode('utf-8')).hexdigest() for k in _configured_api_keys
}
AUTH_ENABLED = bool(_VALID_KEY_HASHES)
# Routes that stay reachable without a key: '/' and sample-data are public
# discovery endpoints with no user data; /api/stop is already gated by its
# own loopback-only check.
_PUBLIC_ROUTES = {'/', '/api/sample-data', '/api/stop'}


def _validate_bind_configuration(host: str, is_dev: bool) -> None:
    """Refuse network exposure without API-key auth or with the debugger enabled."""
    normalized_host = host.strip("[]").lower()
    try:
        is_loopback = ipaddress.ip_address(normalized_host).is_loopback
    except ValueError:
        is_loopback = normalized_host == "localhost"

    if is_dev and not is_loopback:
        raise RuntimeError(
            "Refusing to bind the development server to a non-loopback interface. "
            "Use ETHIVIZ_ENV=production for network deployments."
        )
    if not is_loopback and not AUTH_ENABLED:
        raise RuntimeError(
            "Refusing to bind EthiViz to a non-loopback interface without API-key "
            "authentication. Configure ETHIVIZ_API_KEYS before setting ETHIVIZ_HOST."
        )


def _validate_api_key(auth_header: str | None, valid_hashes: set[str]) -> str | None:
    """Pure function, independent of Flask's request/g context, so it can be
    unit-tested directly: given an `Authorization` header value and the set
    of valid key hashes, returns the matching hash or None."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header[len('Bearer '):].strip()
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    for valid_hash in valid_hashes:
        if hmac.compare_digest(token_hash, valid_hash):  # timing-safe
            return valid_hash
    return None


@app.before_request
def _require_api_key():
    if not AUTH_ENABLED or request.method == 'OPTIONS' or request.path in _PUBLIC_ROUTES:
        return None
    matched_hash = _validate_api_key(request.headers.get('Authorization'), _VALID_KEY_HASHES)
    if matched_hash is None:
        return make_error_response("Unauthorized: missing or invalid API key.", 401)
    g.api_key_hash = matched_hash
    return None


def _current_key_hash() -> str | None:
    return getattr(g, 'api_key_hash', None)


def _job_owner_matches(job: dict | None) -> bool:
    """True if the current caller may access this job: auth is disabled, the
    job is unowned (created before Upgrade 40, or while auth was disabled),
    or the job's owner_key_hash matches the caller's key."""
    if not AUTH_ENABLED or job is None:
        return True
    owner = job.get("owner_key_hash")
    return owner is None or owner == _current_key_hash()


# ── Rate limiting (Upgrade 41) ──────────────────────────────────────────────
# In-memory storage — fine for the current single-process deployment;
# revisit with a shared (Redis) backend once Upgrade 46 introduces a real
# task queue and the API can run as multiple processes/instances.
limiter = Limiter(
    app=app,
    key_func=lambda: _current_key_hash() or get_remote_address(),
    default_limits=[os.environ.get('ETHIVIZ_RATE_LIMIT_DEFAULT', '120 per minute')],
    storage_uri="memory://",
)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Reject request bodies over 50MB outright (Werkzeug returns 413) rather than
# buffering an arbitrarily large upload into memory/disk per request — no
# cap previously existed, so a handful of large POSTs could exhaust disk or
# memory on the server.
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
ALLOWED_EXTENSIONS_TEXT = {'csv', 'xlsx', 'xls', 'json', 'txt'}
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGES_PER_JOB = 20
MAX_XLSX_ENTRIES = 10_000
MAX_XLSX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_XLSX_COMPRESSION_RATIO = 100

# Upgrade 43: per-key/per-IP daily upload quota, separate from the
# per-request MAX_CONTENT_LENGTH cap above — that cap alone doesn't stop
# many requests from accumulating unbounded total upload volume over a day.
UPLOAD_QUOTA_BYTES_PER_DAY = int(
    float(os.environ.get('ETHIVIZ_UPLOAD_QUOTA_MB_PER_DAY', '500')) * 1024 * 1024
)

# Upgrade 41: caps how many analysis jobs a single key/IP can have running
# at once, independent of the per-route rate limit below — that limits
# request *rate*, this limits concurrent *work in flight*, which is what
# actually matters for an unauthenticated caller trying to exhaust the
# server with expensive analysis jobs.
_MAX_CONCURRENT_JOBS_PER_KEY = int(os.environ.get('ETHIVIZ_MAX_CONCURRENT_JOBS_PER_KEY', '3'))
_concurrent_jobs_lock = threading.Lock()
_concurrent_jobs: dict = {}


def _try_acquire_job_slot(key: str) -> bool:
    with _concurrent_jobs_lock:
        if _concurrent_jobs.get(key, 0) >= _MAX_CONCURRENT_JOBS_PER_KEY:
            return False
        _concurrent_jobs[key] = _concurrent_jobs.get(key, 0) + 1
        return True


def _release_job_slot(key: str) -> None:
    with _concurrent_jobs_lock:
        if key in _concurrent_jobs:
            _concurrent_jobs[key] = max(0, _concurrent_jobs[key] - 1)


# In-memory fallback job store (used if SQLite import fails)
_jobs_fallback: dict = {}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.after_request
def _set_security_headers(response):
    """No security headers were previously set on any response. These are
    the low-risk, high-value defaults: block MIME-sniffing, block being
    framed by another site (clickjacking), and stop the exported HTML report
    from loading any external resource even if a future template regresses
    the escaping fixed above."""
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    if response.mimetype == 'text/html':
        response.headers.setdefault(
            'Content-Security-Policy',
            "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'",
        )
    # Upgrade 42: completes the header set for the production deployment
    # path (see deploy/). HSTS is harmless to send over plain HTTP too —
    # browsers only honor it once they've received it over a real HTTPS
    # connection, so setting it unconditionally here does not depend on
    # whether TLS is actually terminated in front of this process.
    response.headers.setdefault(
        'Strict-Transport-Security', 'max-age=63072000; includeSubDomains'
    )
    response.headers.setdefault(
        'Permissions-Policy',
        'geolocation=(), camera=(), microphone=(), payment=(), usb=()',
    )
    return response

# Logging setup — formatting/handlers are already installed by
# observability.configure_json_logging() above; this just sets the level
# app.logger filters at.
app.logger.setLevel(logging.INFO)

# Request correlation IDs, HTTP/job metrics, and GET /metrics (Upgrade 50).
observability.install(app)


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


# ── Upload retention (Upgrade 38) ───────────────────────────────────────────
# Uploaded source files (potentially containing demographic/bias-relevant
# content) previously lived in api_uploads/ forever — no TTL, no cleanup path
# besides the OS filling up. UPLOAD_RETENTION_HOURS is deliberately
# conservative (7 days) so a job someone wants to re-export or debug isn't
# yanked out from under them; DELETE /api/jobs/<job_id> covers immediate,
# explicit purges.
UPLOAD_RETENTION_HOURS = float(os.environ.get('ETHIVIZ_UPLOAD_RETENTION_HOURS', '168'))
_UPLOAD_SWEEP_INTERVAL_SECONDS = 3600


def _sweep_stale_uploads():
    """Background loop: once per hour, delete files in api_uploads/ older
    than UPLOAD_RETENTION_HOURS. Runs for the lifetime of the process."""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    while True:
        cutoff = time.time() - UPLOAD_RETENTION_HOURS * 3600
        try:
            for path in upload_dir.glob('*'):
                try:
                    if path.is_file() and path.stat().st_mtime < cutoff:
                        path.unlink()
                        app.logger.info(f"Retention sweep removed stale upload: {path.name}")
                except OSError:
                    continue
        except Exception:
            app.logger.exception("Upload retention sweep failed.")
        time.sleep(_UPLOAD_SWEEP_INTERVAL_SECONDS)


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
    """List recent jobs, scoped to the caller's own key (plus unowned/legacy
    jobs) when auth is enabled (Upgrade 40); unscoped otherwise, matching the
    original behavior exactly when auth is disabled."""
    owner = _current_key_hash() if AUTH_ENABLED else None
    if HAS_JOB_STORE:
        return _job_store.list_jobs(limit=limit, owner_key_hash=owner)
    jobs = list(_jobs_fallback.values())
    if AUTH_ENABLED:
        jobs = [j for j in jobs if _job_owner_matches(j)]
    return jobs[:limit]


def _purge_job_uploads(job_id: str) -> int:
    """Remove every uploaded source file for job_id from api_uploads/
    (Upgrade 38). Files are saved as '{job_id}_{filename}', so a glob scoped
    to that prefix is exact — job_id is a uuid4, not attacker-controlled path
    input, so this cannot escape UPLOAD_FOLDER."""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    removed = 0
    for path in upload_dir.glob(f"{job_id}_*"):
        try:
            path.unlink()
            removed += 1
        except OSError as e:
            app.logger.warning(f"Could not remove upload {path}: {e}")
    return removed


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


@app.errorhandler(429)
def _handle_rate_limit(e):
    """Wrap flask-limiter's default response in the same {"error", "details"}
    shape every other error on this API uses, instead of a differently-shaped
    body just for this one status code."""
    return make_error_response(
        "Rate limit exceeded. Please slow down and try again shortly.", 429,
        details=str(getattr(e, 'description', e)),
    )


# ── Upload content verification (Upgrade 43) ────────────────────────────────
# allowed_file() above only checks the filename's extension — a file with
# arbitrary content and a trusted-looking name passes it. These checks run
# after the file is saved to disk and look at the actual bytes.

_IMAGE_SIGNATURE_EXTENSIONS = {'png': 'png', 'jpg': 'jpg', 'jpeg': 'jpg', 'gif': 'gif', 'webp': 'webp'}


def _verify_image_content(filepath: str, declared_ext: str) -> bool:
    """Magic-byte check via `filetype` (pure Python, no libmagic system
    dependency) that the file's actual content matches its declared
    extension."""
    kind = filetype.guess(filepath)
    if kind is None:
        return False
    expected = _IMAGE_SIGNATURE_EXTENSIONS.get(declared_ext.lower())
    return expected is not None and kind.extension == expected


def _verify_text_content(filepath: str, declared_ext: str) -> bool:
    """csv/txt/json have no reliable magic number; xlsx is actually a ZIP
    (PK\\x03\\x04) and legacy xls is OLE2 (\\xD0\\xCF\\x11\\xE0) — check those
    specifically, and fall back to a NUL-byte sanity check for the rest (a
    genuine text file should not contain NUL bytes in its first few KB)."""
    ext = declared_ext.lower()
    with open(filepath, 'rb') as f:
        head = f.read(8192)
    if ext == 'xlsx':
        return head.startswith(b'PK\x03\x04') and _xlsx_archive_within_limits(filepath)
    if ext == 'xls':
        return head.startswith(b'\xd0\xcf\x11\xe0')
    return b'\x00' not in head


def _xlsx_archive_within_limits(filepath: str) -> bool:
    """Reject spreadsheet archives with excessive expansion or entry counts."""
    try:
        with zipfile.ZipFile(filepath) as archive:
            entries = archive.infolist()
    except (OSError, zipfile.BadZipFile):
        return False

    if len(entries) > MAX_XLSX_ENTRIES:
        return False
    total_uncompressed = sum(entry.file_size for entry in entries)
    if total_uncompressed > MAX_XLSX_UNCOMPRESSED_BYTES:
        return False
    return all(
        entry.file_size / max(entry.compress_size, 1) <= MAX_XLSX_COMPRESSION_RATIO
        for entry in entries
    )


def _upload_quota_key() -> str:
    return _current_key_hash() or request.remote_addr or 'unknown'


@app.route('/')
def home():
    # Was hardcoded to "0.6.0" — already stale before this pass (package was
    # at 0.7.0). Reading ethiviz.__version__ directly means this can't drift
    # from the package version again on the next bump.
    from ethiviz import __version__ as _ethiviz_version
    return jsonify({"message": "EthiViz API Server is running.", "version": _ethiviz_version})


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
def run_analysis_job(job_id, analysis_type, data_inputs, selected_traditions, advanced_options,
                      slot_key=None):
    """
    Runs the analysis in a separate thread.
    Updates the job status and results via the job store.

    slot_key: the concurrent-job-slot key (Upgrade 41) acquired by the caller
    before starting this thread — always released in `finally` regardless of
    how the job ends, so a failed/crashed job doesn't permanently occupy a
    concurrency slot.
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

    # Recorded in the finally block below for observability.record_job
    # (Upgrade 50) — default to "failed"/None since most except branches
    # below don't need to say so explicitly; only the success path updates
    # these.
    job_status = "failed"
    job_tradition_scores: list[dict] | None = None
    phase_timings: dict[str, Any] = {}
    analysis_started = time.perf_counter()

    try:
        text_results = None
        image_results = None
        text_scores: list[dict] = []
        image_scores: list[dict] = []
        text_performance: dict[str, Any] = {}

        selected_fids = bridge.resolve_framework_ids(selected_traditions)

        dimension_findings: dict | None = None
        if has_text:
            phase_started = time.perf_counter()
            text_input = data_inputs.get("text_input")
            app.logger.info(f"Job {job_id}: Running text analysis. Input type: {type(text_input)}")

            # Upgrade 52: opt-in since it's extra computation per lens on
            # top of the analysis itself — advanced_options already exists
            # as the documented place for this kind of flag (see
            # ConfigPanel.tsx's advanced-options JSON body).
            include_statistical_metrics = bool(
                advanced_options.get("include_statistical_metrics", False)
            )
            text_results, text_scores, dimension_findings = bridge.run_text_analysis(
                text_input=text_input,
                selected_fids=selected_fids,
                job_id=job_id,
                progress_callback=make_progress_cb(text_span, "Analyzing text"),
                include_statistical_metrics=include_statistical_metrics,
                performance_output=text_performance,
            )
            app.logger.info(f"Job {job_id}: Text analysis completed.")
            phase_timings["text_analysis_seconds"] = round(
                time.perf_counter() - phase_started, 4
            )
            phase_timings["text_engine"] = text_performance

        if has_image:
            phase_started = time.perf_counter()
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
            phase_timings["image_analysis_seconds"] = round(
                time.perf_counter() - phase_started, 4
            )

        _update_job(job_id, progress={"percent": 95, "message": "Finalizing results..."})
        final_results = {}
        if text_results:
            final_results["text_analysis"] = text_results
        if dimension_findings:
            final_results["dimension_findings"] = dimension_findings
        if image_results:
            final_results["image_analysis"] = image_results
            os.makedirs('ethiviz_results', exist_ok=True)
            with open('ethiviz_results/image_analysis_results.json', 'w') as f:
                json.dump(image_results, f, indent=2)

        if not final_results:
            raise ValueError("No analysis was performed or results were empty.")

        tradition_scores = bridge.merge_tradition_scores_across_modalities(text_scores, image_scores)
        final_results["tradition_scores"] = tradition_scores
        phase_timings["total_seconds"] = round(
            time.perf_counter() - analysis_started, 4
        )
        phase_timings["text_segments"] = len(text_results) if text_results else 0
        phase_timings["images"] = len(image_results) if image_results else 0
        final_results["performance"] = phase_timings

        _update_job(job_id, status="completed", result=final_results,
                    progress={"percent": 100, "message": "Analysis complete."})
        if HAS_JOB_STORE and tradition_scores:
            _job_store.store_results(job_id, bridge.to_sqlite_payload(tradition_scores))
        app.logger.info(f"Job {job_id} completed successfully.")
        job_status = "completed"
        job_tradition_scores = tradition_scores

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
        duration = end_time - start_time
        _update_job(job_id, end_time=end_time, duration_seconds=duration)
        observability.record_job(analysis_type, job_status, duration, job_tradition_scores)
        if slot_key is not None:
            _release_job_slot(slot_key)


# --- API Endpoints ---
@app.route('/api/analyze', methods=['POST'])
@limiter.limit(os.environ.get('ETHIVIZ_RATE_LIMIT_ANALYZE', '10 per minute'))
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

        owner_key_hash = _current_key_hash()

        # Upgrade 43: reject before doing any work if this caller is already
        # at/over their daily upload quota — checked against the incoming
        # request's declared size, separate from the per-request
        # MAX_CONTENT_LENGTH cap, which only bounds a single request.
        if HAS_JOB_STORE and data_source_type == 'upload':
            quota_key = _upload_quota_key()
            used_today = _job_store.get_upload_usage(quota_key)
            if used_today + (request.content_length or 0) > UPLOAD_QUOTA_BYTES_PER_DAY:
                return make_error_response(
                    "Daily upload quota exceeded for this caller.", 429,
                    details=f"Limit is {UPLOAD_QUOTA_BYTES_PER_DAY // (1024 * 1024)}MB/day.",
                )

        # Create the job via the persistent store
        if HAS_JOB_STORE:
            job_id = _job_store.create_job(analysis_type=analysis_type, owner_key_hash=owner_key_hash)
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
            "owner_key_hash": owner_key_hash,
        }

        data_inputs = {"source_type": data_source_type}
        _uploaded_paths_this_request: list = []

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
                declared_ext = text_filename.rsplit('.', 1)[1]
                if not _verify_text_content(text_filepath, declared_ext):
                    os.remove(text_filepath)
                    return make_error_response(
                        f"Uploaded text file does not match its declared type: {text_file.filename}.", 400,
                        details="File content failed validation for its extension.",
                    )
                data_inputs["text_input"] = text_filepath
                _uploaded_paths_this_request.append(text_filepath)
                app.logger.info(f"Saved text file for job {job_id} to {text_filepath}")

            if analysis_type in ['image', 'text_and_image']:
                image_files = request.files.getlist('image_files')
                if not image_files or all(f.filename == '' for f in image_files):
                    return make_error_response("Missing 'image_files' for image analysis upload.", 400)
                if len(image_files) > MAX_IMAGES_PER_JOB:
                    return make_error_response(
                        "Too many images in one analysis job.", 413,
                        details=f"Limit is {MAX_IMAGES_PER_JOB} images per job.",
                    )

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
                    declared_ext = img_filename.rsplit('.', 1)[1]
                    if not _verify_image_content(img_filepath, declared_ext):
                        os.remove(img_filepath)
                        for p in saved_image_paths:
                            os.remove(p)
                        if "text_input" in data_inputs and os.path.exists(data_inputs["text_input"]):
                            os.remove(data_inputs["text_input"])
                        return make_error_response(
                            f"Uploaded image file does not match its declared type: {img_file.filename}.", 400,
                            details="File content failed magic-byte validation for its extension.",
                        )
                    saved_image_paths.append(img_filepath)
                data_inputs["image_paths"] = saved_image_paths
                _uploaded_paths_this_request.extend(saved_image_paths)
                app.logger.info(f"Saved {len(saved_image_paths)} image files for job {job_id}.")

            if HAS_JOB_STORE and _uploaded_paths_this_request:
                actual_bytes = sum(
                    os.path.getsize(p) for p in _uploaded_paths_this_request if os.path.exists(p)
                )
                _job_store.record_upload(quota_key, actual_bytes)

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

        # Upgrade 41: cap concurrent analysis work per caller, acquired here
        # (not at the top of the request) so validation-only failures above
        # never consume a slot — only requests that actually reach the point
        # of starting real analysis work do.
        slot_key = owner_key_hash or request.remote_addr or 'unknown'
        if not _try_acquire_job_slot(slot_key):
            return make_error_response(
                "Too many concurrent analysis jobs in progress for this caller. "
                "Please wait for one to finish before submitting another.", 429,
            )

        app.logger.info(f"Job {job_id} created. Initial status: pending. Submitting to analysis queue "
                        f"({'distributed' if _analysis_queue.is_distributed else 'local'}).")
        try:
            _analysis_queue.enqueue(
                run_analysis_job,
                job_id,
                analysis_type,
                data_inputs,
                selected_traditions,
                advanced_options,
                slot_key,
            )
        except QueueFullError:
            # The job slot acquired above must be released — nothing will
            # ever run to release it in run_analysis_job's finally block,
            # since the job was never queued.
            _release_job_slot(slot_key)
            return make_error_response(
                "The analysis queue is at capacity. Please try again shortly.", 503,
            )

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
    if not _job_owner_matches(persistent_job or memory_job):
        # 404, not 403 — a mismatch shouldn't confirm that a job ID exists
        # and merely belongs to someone else.
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
    if not _job_owner_matches(persistent_job or memory_job):
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


def _generate_simple_pdf(job_id: str, result: dict) -> bytes:
    """Generate a minimal PDF payload without adding a heavy PDF dependency."""
    lines = ["EthiViz Analysis Report", f"Job ID: {job_id}", "", "Results:"]
    for key, value in result.items():
        if isinstance(value, (dict, list)):
            value_text = json.dumps(value, indent=2, default=str)
        else:
            value_text = str(value)
        lines.append(f"- {key}: {value_text[:180]}")
    text = "\n".join(lines)
    page_lines = text.splitlines() or ["EthiViz Analysis Report"]
    content = []
    y = 760
    for line in page_lines[:35]:
        escaped_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content.append(f"BT /F1 12 Tf 50 {y} Td ({escaped_line}) Tj ET")
        y -= 16
    stream = "\n".join(content).encode("latin-1", errors="replace")
    stream_obj = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        stream_obj,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


@app.route('/api/analyze/results/<job_id>/export', methods=['GET'])
def export_analysis_results(job_id):
    """
    Export analysis results as HTML report, raw JSON, or PDF.
    Query param: format=html|json|pdf
    """
    fmt = request.args.get('format', 'json').lower()
    persistent_job = _get_job(job_id)
    memory_job = _jobs_fallback.get(job_id)

    if not persistent_job and not memory_job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")
    if not _job_owner_matches(persistent_job or memory_job):
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    status = (persistent_job or {}).get("status") or (memory_job or {}).get("status", "unknown")
    if status != "completed":
        return make_error_response("Job not yet completed.", 422,
                                   details=f"Current job status: {status}")

    result = (memory_job or {}).get("result", {})

    if HAS_JOB_STORE:
        _job_store.log_event(job_id, "exported", {"format": fmt, "requester": request.remote_addr})

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
    elif fmt == 'pdf':
        pdf_bytes = _generate_simple_pdf(job_id, result)
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={"Content-Disposition": f"attachment; filename=ethiviz_report_{job_id}.pdf"},
        )
    else:
        return make_error_response(f"Unsupported export format: {fmt}", 400,
                                   details="Supported formats: html, json, pdf")


def _generate_fallback_html(job_id: str, result: dict) -> str:
    """Generate a simple HTML summary when the full BiasReport is unavailable.

    `result` embeds user-supplied analysis input verbatim (e.g. each text
    item's original_text), so it is untrusted content. Un-escaped f-string
    interpolation here previously let an uploaded text containing
    `</script><script>...` execute in the exported report — html.escape()
    both values before they reach the template.
    """
    result_json = html.escape(json.dumps(result, indent=2, default=str))
    safe_job_id = html.escape(job_id)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>EthiViz Report — {safe_job_id}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }}
    h1 {{ color: #6366f1; }}
    pre {{ background: #1e293b; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;
           font-size: 0.8rem; color: #94a3b8; }}
  </style>
</head>
<body>
  <h1>EthiViz Analysis Report</h1>
  <p>Job ID: <code>{safe_job_id}</code></p>
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


@app.route('/api/framework-coverage', methods=['GET'])
def framework_coverage():
    """Framework self-audit (Upgrade 36): how equitably EthiViz's own
    prototype corpus covers its 7 traditions, independent of any single
    analysis run. Answers the V5 plan's open question of whether CREI should
    also evaluate the tool itself."""
    try:
        from ethiviz.frameworks.coverage_audit import coverage_report
        return jsonify(coverage_report())
    except Exception as e:
        return make_error_response("Failed to compute framework coverage.", 500, details=str(e))


@app.route('/api/jobs/<job_id>/audit-log', methods=['GET'])
def job_audit_log(job_id):
    """Expose the audit trail JobStore has been recording since Upgrade 31
    but that no endpoint previously read back (Upgrade 39).
    ?verify=true recomputes the Upgrade 45 hash chain and reports whether any
    row has been altered or removed since it was written."""
    if not HAS_JOB_STORE:
        return make_error_response("Audit log requires the SQLite job store.", 501)
    job = _job_store.get_job(job_id)
    if not job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")
    if not _job_owner_matches(job):
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")
    entries = _job_store.get_audit_log(job_id)
    response = {"job_id": job_id, "events": entries, "count": len(entries)}
    if request.args.get('verify', '').lower() in ('true', '1'):
        response["chain_verification"] = _job_store.verify_audit_chain()
    return jsonify(response)


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Purge a job's persisted record, results, uploaded source files, and
    audit trail (Upgrade 38). Retention was previously indefinite: uploaded
    files in api_uploads/ and rows in jobs.db never expired, which is both a
    disk-exhaustion risk and a data-retention liability for a tool that
    ingests demographic/bias-relevant content."""
    job = _get_job(job_id) or _jobs_fallback.get(job_id)
    if not job:
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")
    if not _job_owner_matches(job):
        return make_error_response("Job not found.", 404, details=f"No job found with ID: {job_id}")

    removed_files = _purge_job_uploads(job_id)

    if HAS_JOB_STORE:
        _job_store.delete_job(job_id)
    _jobs_fallback.pop(job_id, None)

    return jsonify({
        "status": "deleted",
        "job_id": job_id,
        "files_removed": removed_files,
    })


@app.route('/api/compare', methods=['POST'])
@limiter.limit(os.environ.get('ETHIVIZ_RATE_LIMIT_ANALYZE', '10 per minute'))
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
        if not _job_owner_matches(job_a):
            return make_error_response(f"Job A not found: {job_id_a}", 404)
        if not _job_owner_matches(job_b):
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
    is_dev = os.environ.get('ETHIVIZ_ENV', 'production').lower() == 'development'
    host = os.environ.get('ETHIVIZ_HOST', '127.0.0.1')
    port = int(os.environ.get('ETHIVIZ_PORT', '5001'))
    _validate_bind_configuration(host, is_dev)

    app.logger.info(f"EthiViz API Server starting (V5)...")
    app.logger.info(f"ethiviz.Analyzer bridge active: {HAS_TEXT_ANALYZER}")
    app.logger.info(f"Vision detection available: {HAS_IMAGE_ANALYZER}")
    app.logger.info(f"SQLite JobStore available: {HAS_JOB_STORE}")
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    if AUTH_ENABLED:
        app.logger.info(f"API-key authentication ENABLED ({len(_VALID_KEY_HASHES)} key(s) configured).")
    else:
        app.logger.warning(
            "API-key authentication DISABLED (ETHIVIZ_API_KEYS not set) — every "
            "route is reachable without credentials. Set ETHIVIZ_API_KEYS before "
            "exposing this server beyond localhost."
        )
    # Warm the embedding model up in the background so it loads while the
    # server is starting (and while the user is still on the config page)
    # instead of during the first submitted job. Daemon thread: if it's still
    # running when a request arrives, get_analyzer()'s lock just makes that
    # request wait on the same load rather than duplicating it.
    threading.Thread(target=_warm_up_models, daemon=True).start()
    # Retention sweep for uploaded source files (Upgrade 38) — see
    # _sweep_stale_uploads for why this runs on an hourly loop rather than
    # purging immediately after each job.
    threading.Thread(target=_sweep_stale_uploads, daemon=True).start()

    # debug=True previously ran in every environment, including whatever the
    # user pointed `python Scripts/api_server.py` at. The Werkzeug debugger
    # exposes an interactive Python console over HTTP on every unhandled
    # exception — on host='0.0.0.0' that console was reachable from any
    # network the machine is on, which is remote code execution, not a
    # debugging convenience. ETHIVIZ_ENV must be explicitly set to
    # 'development' to get the debugger back; every other value (including
    # unset) runs the safe, production-appropriate defaults.
    if is_dev:
        app.logger.warning(
            "ETHIVIZ_ENV=development — Flask debug mode is ON. Never set this in production."
        )
    # use_reloader=False is required: with the Werkzeug debug reloader active,
    # a SIGTERM sent to the worker process by /api/stop can be silently
    # relaunched by the watcher parent instead of actually stopping the server.
    app.run(debug=is_dev, use_reloader=False, host=host, port=port)
