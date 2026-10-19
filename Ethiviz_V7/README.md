# EthiViz V7 — Cross-Cultural AI Bias Detection Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through **seven ethical traditions simultaneously** — Western, Ubuntu, Confucian, Islamic,
Buddhist, Hindu/Dharmic, and Indigenous/First Nations — instead of a single, typically
Western-centric fairness standard.

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias
> from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

This folder is the **current V7 project snapshot**: a Flask API backend running the
7-lens `ethiviz` engine, a React frontend, and local and containerized deployment paths.
Earlier version folders in the repository are historical snapshots; this folder is the
recommended starting point for V7 work.

---

## V7 at a glance

V7 builds on V6's engine and addresses the API, operations, and user experience around
it. The project includes API-key authentication and job ownership, rate limits and upload
verification, an optional bounded Redis/RQ worker queue and PostgreSQL store, structured
logging and metrics, and frontend support for cross-cultural findings and recent jobs.
See [CHANGELOG.md](./CHANGELOG.md) for implementation details and deferred work.

### Cross-cultural analysis

Results can include dimension-level consensus and tradition-specific findings across
seven ethical traditions. Individual-fairness metrics can be enabled as an optional
analysis setting. These are decision-support signals, not determinations of legal
compliance or substitutes for community and domain expertise.

### Product and operations

- The frontend accepts an API key and uses it for analysis, polling, results, comparison,
  exports, and recent-job history.
- HTML, JSON, and PDF exports are available. PDF output is a simple text-based report;
  it is not rendered from the HTML template.
- Translation-review metadata, community-consent intake guidance, and calibration
  evaluation utilities are included. A human-annotated benchmark and established
  community partnerships are not included.
- GitHub Actions runs backend tests and builds the frontend. The load-test directory
  currently contains a queue smoke test, not a full load or penetration-testing suite.
- Text embeddings are encoded in bounded, per-language batches and reused by all selected
  lenses for each input segment. Completed results include phase timings and throughput
  so operators can benchmark actual workloads before tuning concurrency or hardware.
- Image results expose detector availability/status, labels, and the count of detected
  cultural elements (not the number of detector categories). These image signals remain
  exploratory because the lens scores are based on a detector-generated text proxy.

## Architecture

```
Ethiviz_V7/
├── ethiviz/                    # The core Python engine (installable package)
│   ├── api.py                  # Analyzer — the primary entry point
│   ├── lenses/                 # 7 cultural ethical lenses (+ shared base scoring)
│   ├── frameworks/
│   │   ├── conflict.py         # Scalar-level cross-tradition conflicts
│   │   └── dimension_map.py    # Dimension-level shared moral constructs
│   ├── embeddings/             # Prototypes, per-language similarity calibration
│   ├── analysis/
│   │   ├── weat.py             # WEAT + intersectional WEAT
│   │   └── weat_lists/         # Word lists — all 7 lenses
│   ├── metrics/                # Group/individual fairness metrics (AIF360-style)
│   ├── mitigation/             # Reweighing, DI Remover, Calibrated EO, etc.
│   ├── integration/            # sklearn-compatible pipeline wrapper
│   ├── storage/                # SQLite job store
│   ├── sample_data/            # 140+ curated example texts (7 traditions)
│   ├── vision/                 # Fitzpatrick skin tone, MediaPipe, CLIP detection
│   └── reporting/              # HTML report generation
├── Scripts/
│   ├── api_server.py           # Flask REST API (port 5001), async job processing
│   └── ethiviz_bridge.py       # Bridges api_server.py to the real Analyzer engine
├── project/                    # React 18 + Vite frontend (port 5173)
│   └── src/components/
│       ├── ConfigPanel.tsx, MainContent.tsx
│       ├── ExportButton.tsx, CompareMode.tsx
│       ├── CrossCulturalEquityDashboard.tsx
│       └── visualizations/CulturalFairnessHeatmap.tsx
├── tests/                      # 162 tests
│   ├── test_v5_phase1_metrics.py        # Repaired cultural metrics
│   ├── test_v5_phase2_multilingual.py   # Coverage, calibration, translations
│   └── test_v5_phase3_crosscultural.py  # Dimension map, WEAT parity, iWEAT
├── CHANGELOG.md                # Breaking changes + migration notes
├── start_ethiviz.sh            # Start backend + frontend together
├── stop_ethiviz.sh             # Stop both (also see the in-app Stop button)
└── pyproject.toml
```

Root-level `start_ethiviz.sh` / `stop_ethiviz.sh` / `start_services.sh` are thin
wrappers that just launch the copies in this folder — you can run either.

---

## Ethical Traditions

Bias categories below are the actual scoring dimensions each lens produces.

| Tradition | Core Values | Bias Categories Detected |
|---|---|---|
| **Western** | Individual rights, equal opportunity, statistical parity | Racial bias, gender bias, stereotyping, individual rights violation, cultural superiority, procedural bias |
| **Ubuntu** | Community harmony, relational impact, collective benefit | Cultural erasure, community devaluation, Ubuntu violation, African essentialism |
| **Confucian** | Social harmony, role appropriateness, hierarchical respect | Hierarchical disrespect, collectivist harm, face violation, relational bias |
| **Islamic** | Maqasid al-shari'ah, karamah (dignity), harm prevention | Violent stereotyping, Islamic essentialism, gender essentialism, orientalism, dignity violation |
| **Buddhist** | Ahimsa, right speech, interdependence, non-attachment to identity | Ahimsa violation, identity reification, right speech violation, compassion deficit, interdependence denial |
| **Hindu / Dharmic** | Dharma, satya, ahimsa, manava mahatma (human dignity) | Caste essentialism, dignity harm, ahimsa violation, satya violation, dharmic disrespect |
| **Indigenous / First Nations** | CARE Principles, seven-generations stewardship, land relationality | Knowledge extraction, land relational harm, cultural erasure, seven-generations violation, stereotyping |

### Shared moral constructs

The dimension map groups these across traditions into ten constructs: human dignity,
essentialism, non-harm, cultural delegitimisation, group flattening, relational
obligation, gender subordination, truthfulness, intergenerational responsibility, and
knowledge sovereignty.

The last two are encoded by the Indigenous lens alone. That is reported as a finding
rather than smoothed over — a concern only one tradition measures is real information,
and its absence elsewhere is not consensus.

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 16+ with npm

### Quick start

```bash
bash start_ethiviz.sh
```

This installs the `ethiviz` package and API dependencies if needed, starts the backend
on port 5001, waits for it to respond, then starts the React frontend on
port 5173 (visit `http://localhost:5173`).

Options:
```bash
bash start_ethiviz.sh --backend-only     # backend only, tails the log
bash start_ethiviz.sh --frontend-only    # frontend only (backend already running)
bash start_ethiviz.sh --with-vision      # also installs mediapipe/torch/transformers
                                          # for real image face/skin-tone detection
                                          # (multi-GB download, not installed by default)
```

Without `--with-vision`, image analysis still works but degrades to a metadata-only
proxy (no real face/skin-tone detection) rather than failing.

### Manual setup (two terminals)

```bash
# Terminal 1 — backend
python3 -m pip install -e '.[api]'
python3 Scripts/api_server.py         # http://localhost:5001

# Terminal 2 — frontend
cd project
npm install
npm run dev                            # http://localhost:5173
```

### Production deployment

The above runs Werkzeug's development server — fine for local use, not for anywhere
reachable beyond localhost. `deploy/` has a gunicorn + nginx (TLS-terminating reverse
proxy) setup instead; see [deploy/README.md](./deploy/README.md).

At minimum, set `ETHIVIZ_API_KEYS` before running this anywhere beyond localhost — every
route is open with no credential until you do (see **Security** below).

---

## Security

- **API keys**: set `ETHIVIZ_API_KEYS` to a comma-separated list. Protected endpoints
  require `Authorization: Bearer <key>`. Authentication is disabled when the variable is
  empty, so configure it before exposing the service beyond localhost. Jobs are scoped to
  the key that created them; legacy or unowned jobs remain visible to authenticated
  callers. The frontend stores the entered key in browser local storage; do not use it on
  a shared browser.
- **Rate and workload limits**: `ETHIVIZ_RATE_LIMIT_DEFAULT` defaults to `120 per minute`,
  `ETHIVIZ_RATE_LIMIT_ANALYZE` to `10 per minute`, and
  `ETHIVIZ_MAX_CONCURRENT_JOBS_PER_KEY` to `3` concurrent jobs per key/IP.
- **Uploads**: files are checked against their declared type, requests are capped at 50 MB,
  and `ETHIVIZ_UPLOAD_QUOTA_MB_PER_DAY` defaults to 500 MB per key/IP.
- **Audit trail**: job audit records are hash-chained. Use
  `GET /api/jobs/<id>/audit-log?verify=true` to verify the chain.
- **Proxy trust**: set `ETHIVIZ_TRUST_PROXY` only when requests reach the app through a
  trusted reverse proxy. See [deploy/README.md](./deploy/README.md).

---

## Scaling & Observability

V7 Phase 2 (Upgrades 46-50) replaced the pieces that only worked for one developer on
one laptop with ones that hold up under real, concurrent, multi-process traffic. Every
piece below is opt-in — the zero-config dev workflow above (`start_ethiviz.sh`, SQLite,
no Redis) is unchanged if you set none of these.

- **Task queue** (`ETHIVIZ_REDIS_URL`): without it, `/api/analyze` runs jobs on a bounded
  in-process thread pool (`ETHIVIZ_LOCAL_WORKERS`, default 2; `ETHIVIZ_QUEUE_MAX_DEPTH`,
  default 100 — a full queue returns 503, not an unbounded pile of threads). Set it to a
  Redis URL and run one or more `python Scripts/worker.py` processes to move analysis
  work off the API process entirely, with one automatic retry on a crashed job
  (`ETHIVIZ_JOB_TIMEOUT`, default 3600s).
- **Postgres** (`DATABASE_URL`): `ethiviz/storage/job_store.py`'s `JobStore` defaults to
  SQLite (one file, one process). Setting `DATABASE_URL` to a `postgresql+psycopg://` URL
  switches to a SQLAlchemy-Core-backed implementation instead, so the API and every
  `Scripts/worker.py` process can share one database — required once you're running more
  than one of either. The tamper-evident audit chain (above) stays correct across
  multiple writers via a Postgres advisory lock, not just the in-process
  `threading.Lock` the SQLite path uses.
- **Containers**: `Dockerfile` + `docker-compose.yml` at the repo root run the API,
  a worker, Redis, Postgres, and the built React frontend behind nginx together —
  `cp .env.example .env`, set `POSTGRES_PASSWORD`, then `docker compose up --build`.
  The runtime image runs as a non-root user. See `deploy/README.md` for running the
  pieces individually instead (bare metal/VM).
- **Metrics**: `GET /metrics` (Prometheus text format) — HTTP request counts/latency,
  analysis job counts/duration by type and outcome, and `ethiviz_lens_warning_rate`
  (how often each lens attaches a `warnings` entry, across all scored jobs). Subject to
  `ETHIVIZ_API_KEYS` like every other route when auth is enabled — configure your scraper
  with a bearer token rather than exempting this endpoint from auth.
- **Structured logs**: every log line is now JSON (timestamp, level, logger, message,
  `request_id`) via `Scripts/observability.py`; a correlation ID is generated per request
  (or read from an incoming `X-Request-ID` header) and echoed back in the response.
- **Regression coverage**: `tests/test_concurrency.py` (Upgrade 47) and
  `tests/test_v7_phase2.py` (Upgrades 46/48/50) — the Postgres tests in the latter are
  skipped unless `ETHIVIZ_TEST_DATABASE_URL` points at a reachable database (CI's
  workflow brings one up as a service container; there usually isn't one in a local dev
  environment, and the SQLite path already has full coverage without it).

---

## Cross-Cultural Findings & Statistical Fairness

V7 Phase 3 activated engine output that existed since V6 but never reached a caller —
`Scripts/ethiviz_bridge.py` computed it and then discarded it before the API response
was built.

- **Dimension-level findings** (`dimension_findings` on a completed text job's
  `results`): `ethiviz/frameworks/dimension_map.py` reads 10 shared moral constructs
  (human dignity, essentialism, non-harm, and others) across all 7 lenses' dimension
  scores, not just each tradition's single overall score. `consensus_findings` are
  constructs multiple traditions independently flag; `tradition_specific_findings` are
  ones only a single lens (`distinctive_lens`) encodes — EthiViz's most distinctive
  output, now visible in `DimensionFindingsPanel.tsx` instead of Python-object-only.
  `conflicts` (two lenses reading the same content in opposite directions, with a
  documented resolution strategy) and `synergy_amplifications` are included too.
- **Individual fairness** (opt-in): check the "Include statistical fairness metrics" box
  under Advanced Options, or set `advanced_options.include_statistical_metrics = true`
  directly, to add `ethiviz/metrics/individual_fairness.py`'s consistency/
  sample-distortion check to each `tradition_scores` entry — "do similar inputs get
  similar scores from this lens?" Off by default since it's extra per-lens computation.
  Rendered in `StatisticalFairnessPanel.tsx` when present.
- **Not included**: Group fairness (SPD/DI/EOD/AOD) and any mitigation preview — see
  "Known limitations" below for why.

---

## Stopping the app

Three equivalent ways:

1. Click the **power-off icon** in the app header (asks for confirmation, then shuts
   down both the backend and the frontend dev server).
2. `bash stop_ethiviz.sh` from a terminal.
3. `Ctrl-C` in the terminal running `start_ethiviz.sh` (only works if it's still
   attached in the foreground).

`POST /api/stop` is loopback-only.

---

## API Reference

Base URL: `http://localhost:5001`

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Submit an analysis job; returns `job_id` + `status_url` |
| `/api/analyze/status/{job_id}` | GET | `pending` / `processing` / `completed` / `failed` |
| `/api/analyze/results/{job_id}` | GET | Retrieve results once completed |
| `/api/analyze/results/{job_id}/export` | GET | Download HTML, JSON, or PDF (`?format=html\|json\|pdf`) |
| `/api/sample-data` | GET | List curated sample datasets |
| `/api/jobs` | GET | List recent jobs (persisted across restarts) |
| `/api/jobs/{job_id}` | DELETE | Delete an owned job and associated uploaded files |
| `/api/jobs/{job_id}/audit-log` | GET | Read the job audit log; `?verify=true` checks its hash chain |
| `/api/compare` | POST | Compare two completed jobs by id: `{job_id_a, job_id_b}` |
| `/api/stop` | POST | Gracefully shut down the backend + frontend (localhost-only) |

### Result shape

A completed job's `results` includes:

- `text_analysis`: one item per input text, with a `{tradition}_ethics_score` per
  selected lens (e.g. `western_ethics_score`, `buddhist_ethics_score`), plus a `bias_score`
  (mean across selected lenses) and `diversity_index` (a cross-tradition-agreement proxy —
  see the code comments in `Scripts/ethiviz_bridge.py` for exactly what these mean; they
  are simple, documented heuristics, not validated composite metrics).
- `image_analysis`: same per-image, keyed by filename.
- `tradition_scores`: `[{tradition, score, severity, confidence}, ...]`, keyed by the
  engine's internal framework id (e.g. `confucian_v2`, not `confucian`) — this is what
  powers the fairness heatmap and cross-cultural dashboard in the UI.

> **Note on `confidence`:** the meaning of this field changed in V6. It previously
> reported language-detection confidence; it now reflects each lens's own confidence
> scaled by how much of the detection pipeline actually applied to the input. Non-English
> analyses will report visibly lower values than before — that is the intended correction,
> not a regression.

### Request format (`POST /api/analyze`)

```
Content-Type: multipart/form-data

analysis_type        : "text" | "image" | "text_and_image"
data_source_type      : "upload" | "sample"
selected_traditions   : ["western", "ubuntu", "confucian", "islamic",
                          "buddhist", "hindu", "indigenous"]
advanced_options      : JSON string (includes optional
                         `include_statistical_metrics: true`)
text_file             : file upload (CSV, XLSX, JSON, TXT)
image_files           : one or more file uploads (PNG, JPG, WEBP, GIF)
```

---

## Implemented features and current scope

- The API runs the seven-lens engine and exposes text/image results, per-lens coverage
  and warnings, dimension-level cross-cultural findings, job comparison, and HTML/JSON/
  PDF export.
- API-key authentication and job ownership are implemented. Authentication is disabled
  unless `ETHIVIZ_API_KEYS` is configured; see **Security** before deployment.
- Individual-fairness metrics are available as an opt-in. Group-fairness metrics and
  mitigation algorithms are not exposed in the live analysis workflow because the app
  does not collect the protected-group labels these methods require.
- The framework loader reads each framework's configured `severity_thresholds`.
- Translation review and community-consent metadata, calibration-evaluation utilities,
  and operator documentation are present. They are infrastructure, not evidence that
  translations have been reviewed, community partnerships have been established, or
  confidence has been validated against human judgments.
- The dimension-map panel and recent-job history are present in the frontend. PDF export
  is a basic text-based PDF; it is not rendered from the HTML report template.
- CI runs backend tests and a frontend production build. The checked-in load smoke test
  does not constitute a comprehensive load test or external security assessment.

## Known limitations

- **Prototype translation review is not complete.** Review-state metadata and governance
  guidance are available, but do not mean translations have been approved by fluent
  speakers. Treat non-English results cautiously until a qualified review is recorded.
- **All six supported languages are colonial or majority languages** (English, Arabic,
  Mandarin, Spanish, Hindi, French). None is an Indigenous language, so the Indigenous
  lens cannot currently analyse text in the languages of the communities it exists to
  protect. Adding those requires community partnership and CARE-aligned data governance,
  not machine translation.
- Even with per-language calibration, non-English detection remains measurably weaker
  than English. This is now reported through `analysis_coverage` and `warnings` rather
  than hidden, but it is a real ceiling, not a solved problem.
- The `Analyzer` instance is a shared, lazily-initialized singleton for performance
  (avoids reloading embedding models per request). Its calibrator and drift monitor used
  to hold mutable state shared across concurrent job threads with no lock; V7 Upgrade 47
  added one (plus atomic writes) around both, and `tests/test_concurrency.py` exercises
  concurrent `fit()`/`calibrate()`/`record_snapshot()` calls to prove it holds. Each RQ
  worker process (Upgrade 46) also gets its own independent `Analyzer` singleton, so this
  is no longer a race either within one process or across worker processes.
- Job persistence stores per-tradition **aggregate** scores, not full per-item detail —
  if the server restarts mid-session, previously completed jobs return a `_partial: true`
  reconstruction (aggregate scores only), not the original per-item breakdown. True for
  both backends (SQLite, the default, and the Postgres option from Upgrade 48).
- Image analysis without `--with-vision` installed produces a metadata-only proxy
  description rather than real face/skin-tone/cultural-element detection.
- `advanced_options` currently controls the opt-in individual-fairness computation;
  legacy options for token counts, NLP models, and image feature levels are not all
  implemented by the active engine.
- Group-fairness metrics (SPD/DI/EOD/AOD in `ethiviz/metrics/group_fairness.py`) and every
  `ethiviz/mitigation/` algorithm require protected-attribute group labels — which row
  belongs to a protected group — that nothing in the app collects; it produces bias
  *scores* on content, not group-labeled predictions. Only Individual Fairness (Upgrade
  52) is wired in, since it needs just the scores the engine already produces. Wiring the
  rest for real would mean adding a way to collect those labels first (e.g. letting a
  caller tag a column in an uploaded dataset), not just calling the existing code.

## Performance benchmarking and analysis validation

Run `python Scripts/benchmark_analysis.py --input path/to/data.txt` from this directory to
measure cold and warm analysis time, phase timings, throughput, and dataset size. Use the
same hardware, model revision, input corpus, and lens selection when comparing changes;
latency numbers are not accuracy metrics.

Accuracy claims require a separate human-reviewed evaluation set. Do not treat the
existing curated examples as ground truth unless they have been independently reviewed.
For each evaluation item, record the text/image context, language, lens, construct,
adjudicated label, evidence span, annotator decisions, disagreement, and adjudication.
Report precision/recall and calibration by lens and language, include satire, quotation,
refutation, and neutral identity mentions, and obtain appropriate community review and
consent before collecting culturally sensitive examples.

---

## Version and migration notes

V7 builds on V6 and retains its breaking API and scoring changes. See
[CHANGELOG.md](./CHANGELOG.md) for version-by-version details. Changes introduced in V6
include:

- `calculate_intersectional_analysis()` returns `Dict[str, IntersectionResult]` instead
  of `Dict[str, float]`.
- `cultural_inclusion_index()` returns a Jensen-Shannon similarity where it previously
  returned a key-overlap fraction. Existing thresholds are invalid.
- `BuddhistLens`, `HinduLens` and `IndigenousLens` no longer accept a `registry=` keyword
  (it was accepted and silently unused).
- Scores shift across all seven lenses. Identical input yields different output.

**Migration:** recalibrate Platt calibration data and drift baselines created against
older scores before reusing them with V7.

---

## Testing

```bash
python3 -m pytest tests/ -q
```

The GitHub Actions workflow runs the backend test suite and frontend production build.
PostgreSQL-specific coverage requires a reachable database configured with
`ETHIVIZ_TEST_DATABASE_URL`. To build the frontend locally:

```bash
cd project
npm ci
npm run build
```

---

## Academic Context

EthiViz implements and extends the framework from Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

## License

Apache 2.0 — see [LICENSE](./LICENSE)
