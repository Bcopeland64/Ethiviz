# EthiViz V5 — Cross-Cultural AI Bias Detection Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through **seven ethical traditions simultaneously** — Western, Ubuntu, Confucian, Islamic,
Buddhist, Hindu/Dharmic, and Indigenous/First Nations — instead of a single, typically
Western-centric fairness standard.

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias
> from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

This folder is the **current, working version** of EthiViz: a real Flask API backend
running the actual 7-lens `ethiviz` engine, a React frontend, and start/stop scripts that
run the whole thing end-to-end. Earlier folders in this repo (`Ethiviz_V2/`, `Ethiviz_V3/`,
`Ethiviz_V4/`) are preserved as historical snapshots and are no longer maintained.

---

## What changed in V5

V4 built a real 7-lens cultural bias engine (`ethiviz/`) as a Python library, but the
running web app never actually called it — the Flask server was wired to a separate,
older analysis pipeline instead. V5's core fix is architectural, not a new feature:
**the web app now actually runs the real engine.**

- `Scripts/api_server.py` (Flask, job-queue API) now calls `ethiviz.Analyzer` through
  `Scripts/ethiviz_bridge.py`, instead of the legacy pipeline that predated it.
- Completed jobs' per-tradition scores are persisted to SQLite (`~/.ethiviz/jobs.db`),
  with a best-effort reconstruction if the server restarts mid-history.
- The dataset-comparison endpoint (`/api/compare`) was fixed — it previously read a
  response shape nothing ever produced.
- A safe shutdown path was added: a **Stop** button in the UI and a `POST /api/stop`
  endpoint (loopback-only, graceful) that shuts down both the backend and the frontend
  dev server — see [Stopping the app](#stopping-the-app).
- The frontend gained a fairness heatmap, a cross-cultural equity dashboard, an export
  button, and a dataset-compare panel, all wired to real backend data.
- All 7 traditions (not just 4) are now selectable from the UI.

---

## Architecture

```
Ethiviz_V5/
├── ethiviz/                    # The core Python engine (installable package)
│   ├── api.py                  # Analyzer — the primary entry point
│   ├── lenses/                 # 7 cultural ethical lenses
│   ├── metrics/                # Group/individual fairness metrics (AIF360-style)
│   ├── mitigation/              # Reweighing, DI Remover, Calibrated EO, etc.
│   ├── integration/             # sklearn-compatible pipeline wrapper
│   ├── storage/                 # SQLite job store
│   ├── sample_data/              # 140+ curated example texts (7 traditions)
│   ├── vision/                   # Fitzpatrick skin tone, MediaPipe, CLIP detection
│   └── reporting/                 # HTML report generation
├── Scripts/
│   ├── api_server.py            # Flask REST API (port 5001), async job processing
│   └── ethiviz_bridge.py        # Bridges api_server.py to the real Analyzer engine
├── project/                     # React 18 + Vite frontend (port 5173)
│   └── src/components/
│       ├── ConfigPanel.tsx, MainContent.tsx
│       ├── ExportButton.tsx, CompareMode.tsx
│       ├── CrossCulturalEquityDashboard.tsx
│       └── visualizations/CulturalFairnessHeatmap.tsx
├── tests/                       # 81 tests covering the engine, metrics, mitigation
├── start_ethiviz.sh              # Start backend + frontend together
├── stop_ethiviz.sh                # Stop both (also see the in-app Stop button)
└── pyproject.toml
```

Root-level `start_ethiviz.sh` / `stop_ethiviz.sh` / `start_services.sh` are thin
wrappers that just launch the copies in this folder — you can run either.

---

## Ethical Traditions

| Tradition | Core Values | Bias Categories Detected |
|---|---|---|
| **Western** | Individual rights, equal opportunity, statistical parity | Racial bias, gender bias, stereotyping, rights violations |
| **Ubuntu** | Community harmony, relational impact, collective benefit | Cultural erasure, community devaluation, African essentialism |
| **Confucian** | Social harmony, role appropriateness, hierarchical respect | Hierarchical disrespect, face violations, relational bias |
| **Islamic** | Dignity preservation, equitable treatment, harm prevention | Orientalism, Islamic essentialism, violent stereotyping |
| **Buddhist** | Ahimsa, right speech, interdependence | Essentialist categorisation, attachment to identity labels |
| **Hindu / Dharmic** | Dharma, satya, ahimsa | Caste stereotyping, colonial framing, dharmic misrepresentation |
| **Indigenous / First Nations** | CARE Principles, seven-generations stewardship | Erasure of oral tradition, land commodification framing |

---

## Setup

### Prerequisites
- Python 3.10+ (the start script prefers `python3.13` if present)
- Node.js 16+ with npm

### Quick start

```bash
bash start_ethiviz.sh
```

This installs the `ethiviz` package (editable) and Flask/flask-cors if missing, starts
the backend on port 5001, waits for it to respond, then starts the React frontend on
port 5173 and opens it in your default flow (visit `http://localhost:5173`).

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
python3.13 -m pip install --user -e .
python3.13 Scripts/api_server.py      # http://localhost:5001

# Terminal 2 — frontend
cd project
npm install
npm run dev                            # http://localhost:5173
```

---

## Stopping the app

Three equivalent ways:
1. Click the **power-off icon** in the app header (asks for confirmation, then shuts
   down both the backend and the frontend dev server).
2. `bash stop_ethiviz.sh` from a terminal.
3. `Ctrl-C` in the terminal running `start_ethiviz.sh` (only works if it's still
   attached in the foreground).

`POST /api/stop` only accepts requests from `localhost` — it's rejected from any other
origin, unlike the unauthenticated shutdown pattern in earlier prototype servers.

---

## API Reference

Base URL: `http://localhost:5001`

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Submit an analysis job; returns `job_id` + `status_url` |
| `/api/analyze/status/{job_id}` | GET | `pending` / `processing` / `completed` / `failed` |
| `/api/analyze/results/{job_id}` | GET | Retrieve results once completed |
| `/api/analyze/results/{job_id}/export` | GET | Download HTML or JSON report (`?format=html\|json`) |
| `/api/sample-data` | GET | List curated sample datasets |
| `/api/jobs` | GET | List recent jobs (persisted across restarts) |
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

### Request format (`POST /api/analyze`)

```
Content-Type: multipart/form-data

analysis_type        : "text" | "image" | "text_and_image"
data_source_type      : "upload" | "sample"
selected_traditions   : ["western", "ubuntu", "confucian", "islamic",
                          "buddhist", "hindu", "indigenous"]
advanced_options      : JSON string (currently accepted but not yet
                         wired to the real engine — see Known limitations)
text_file             : file upload (CSV, XLSX, JSON, TXT)
image_files           : one or more file uploads (PNG, JPG, WEBP, GIF)
```

---

## What's real vs. what's scaffolding

Being direct about this because it matters for anyone building on top of it:

- **Live and verified end-to-end**: the 7-lens `Analyzer` engine, text and image analysis
  through the API, SQLite job persistence, the compare endpoint, the export endpoint, and
  the stop mechanism.
- **Built, tested, but not yet wired into the live analyze path**: `ethiviz/metrics/`
  (AIF360-style group/individual fairness metrics), `ethiviz/mitigation/` (reweighing,
  disparate impact removal, calibrated equalized odds, reject-option classification), and
  `ethiviz/integration/sklearn_api.py` (scikit-learn-compatible pipeline). These are real,
  independently tested modules (see `tests/test_v5_tier4.py`) — a standalone
  AIF360-parity library — but `Analyzer.analyze()` doesn't call them yet. Wiring them into
  the live API is a separate, larger follow-up.
- **`severity_thresholds`** blocks exist in every framework YAML but aren't parsed by the
  framework loader; the heatmap's severity buckets currently come from a documented
  rescaling of `ethiviz/metrics/group_fairness.py`'s threshold table instead (see
  `_severity_for` in `Scripts/ethiviz_bridge.py`).

## Known limitations

- The `Analyzer` instance is a shared, lazily-initialized singleton for performance
  (avoids reloading embedding models per request). Its calibrator and drift monitor hold
  mutable state shared across concurrent job threads — under concurrent load, this can
  theoretically race. Not fixed in this pass; flagged in code comments where it matters.
- SQLite persistence stores per-tradition **aggregate** scores, not full per-item detail —
  if the server restarts mid-session, previously completed jobs return a `_partial: true`
  reconstruction (aggregate scores only), not the original per-item breakdown.
- Image analysis without `--with-vision` installed produces a metadata-only proxy
  description rather than real face/skin-tone/cultural-element detection.
- `advanced_options` (max tokens, NLP model, feature level, batch size) are accepted by
  the API but not yet used by the real engine — they were tailored to the legacy pipeline
  this version replaced.

---

## Testing

```bash
cd Ethiviz_V5
python3.13 -m pytest tests/ -q
```

81 tests covering the engine, lenses, metrics, mitigation modules, and job store.

---

## Academic Context

EthiViz implements and extends the framework from Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

## License

Apache 2.0 — see [LICENSE](./LICENSE)
