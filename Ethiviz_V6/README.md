# EthiViz V6 — Cross-Cultural AI Bias Detection Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through **seven ethical traditions simultaneously** — Western, Ubuntu, Confucian, Islamic,
Buddhist, Hindu/Dharmic, and Indigenous/First Nations — instead of a single, typically
Western-centric fairness standard.

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias
> from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

This folder is the **current, working version** of EthiViz (v0.7.0): a real Flask API
backend running the actual 7-lens `ethiviz` engine, a React frontend, and start/stop
scripts that run the whole thing end-to-end. Earlier folders in this repo
(`Ethiviz_V2/`, `Ethiviz_V3/`, `Ethiviz_V4/`, `Ethiviz_V5/`) are preserved as historical
snapshots and are no longer maintained.

---

## What changed in V6

V5's contribution was architectural: it wired the running web app to the real 7-lens
engine, which V4 had built as a library but never actually called. V6 turns inward on
the engine itself. The headline finding is that several of the metrics carrying the most
cultural meaning were **structurally unable to measure what they documented** — not
inaccurate, but mathematically incapable of producing the result they claimed.

Full detail and migration notes are in [CHANGELOG.md](./CHANGELOG.md). In summary:

### Metrics that could not measure what they claimed

- **Intersectional analysis** computed `score_a * score_b`. A product of two values in
  `[0, 1]` is always less than or equal to either input, so the function could never
  represent compound disadvantage exceeding its parts — it structurally inverted the
  intersectionality claim it was documented as making. Rebuilt on a noisy-OR
  independence baseline with an amplification ratio that distinguishes superadditive,
  independent, and buffered interactions.
- **The iWEAT compound effect** computed `actual - (axis1_effect + axis2_effect)`. That
  sum expands algebraically to `actual` for every possible input, so the headline
  intersectionality metric was guaranteed to return exactly `0.0` regardless of the data.
  Replaced with the difference-in-differences interaction term.
- **The Cultural Inclusion Index** ignored its reference distribution's values entirely,
  checking only which categories were present. A balanced target and a 98/1/1 target both
  returned `1.0`. Rebuilt on Jensen-Shannon divergence over actual proportions.
- **`DualEthicsFramework.resolve_conflict()`** referenced bare names instead of `self.*`
  and raised `NameError` on every call. It had never worked.

### Multilingual analysis made real, and honest about its limits

The platform advertised six languages but was effectively English-only, and did not say so.

- **Translation coverage completed** across all six languages. Buddhist, Hindu and
  Indigenous prototype sets went from 0–70% coverage to full; missing translations
  previously fell back to English text compared against non-English input embeddings.
- **Per-language similarity calibration** added. The embedding model represents some
  languages coarsely enough that every sentence looks similar to every other, which
  inflated all dimensions uniformly — Hindi benign text scored 0.72–0.82 across *every*
  dimension. Similarities are now calibrated against each language's measured background.
- **Blend renormalisation.** Regex patterns exist only in English, and previously scored a
  structural `0.0` for other languages — a flat 30% deduction that read as "less biased"
  rather than "less measurable". The semantic channel now takes full weight when the
  lexical channel is unavailable.
- **Honest degradation.** `LensScore` carries `analysis_coverage` and `warnings`, and
  confidence scales with how much of the pipeline actually applied instead of a flat
  0.88/0.55. Previously the same claim scored 0.07 in English and 0.00 in Hindi while
  both reported identical confidence and no warning.
- **Per-text language detection** replaces detecting once from `dataset[0]`, which scored
  a mixed-language corpus entirely in the first text's language.

### Dimension-level cross-cultural reasoning

Conflict detection and synergy amplification compared one scalar per lens, which
collapses each tradition's internal structure: two lenses can reach the same score for
entirely different reasons, and a lens uniquely detecting a harm looks identical to one
that found nothing in particular.

`ethiviz/frameworks/dimension_map.py` reads ten shared moral constructs underneath those
scalars — Islamic `dignity_violation` and Hindu `dignity_harm` both express human
dignity; Buddhist and Hindu ethics both name `ahimsa_violation` outright — and reports:

- **Cross-tradition consensus**: independently-authored traditions agreeing is stronger
  evidence than any single lens scoring high.
- **Tradition-specific findings**: a harm visible through only one ethical frame while
  the others encoding the same construct see nothing. This is the signal a single
  consensus score averages into invisibility.

Available on results via `ScoredResult.tradition_specific_findings()` and
`.consensus_findings()`.

### Lens parity and detection quality

- Buddhist, Hindu and Indigenous lenses gained dedicated per-category patterns,
  tradition-weighted dimensions and specific recommendations, replacing a generic scorer
  that broadcast one undifferentiated match across every dimension at equal weight.
- Prototype `severity` (hand-graded 0.60–1.00) was loaded but never used; it now scales
  each prototype's contribution, so a mild example and an eliminationist one no longer
  count identically.
- A **negation guard** stops stereotypes quoted in order to refute them from scoring as
  assertions — "the myth that African cultures are primitive" previously scored as biased.
- Several patterns fired on bare topic-word co-occurrence rather than the harmful claim;
  "sustainably harvest timber from the forest" and "police vowed to prevent any attack on
  religious minorities" both scored as harms.
- WEAT word lists added for `buddhist_v1`, `hindu_v1` and `indigenous_v1`. All seven
  lenses now produce suites; previously four did and three were silently skipped.
- `_run_weat` no longer swallows every exception, which had made a malformed word list
  indistinguishable from "no bias found".
- Framework results carry `peak`/`p90` alongside the mean, so one severe document in a
  large corpus is not diluted toward zero.

### Test suite: 81 → 162

The embedding mock returned an all-ones vector for every input, making cosine similarity
exactly `1.0` for every pair. Lenses could not distinguish a matching prototype from an
unrelated one, and assertions of the form "biased text scores high" passed without
exercising the detector at all — one asserted `> 0.5` against a dimension weighted `0.05`,
which is unreachable legitimately. Replaced with deterministic bag-of-words embeddings,
and those tests rewritten to assert structural properties that hold independent of
embedding scale.

---

## Architecture

```
Ethiviz_V6/
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
- Python 3.10+ (the start script prefers `python3.13` if present)
- Node.js 16+ with npm

### Quick start

```bash
bash start_ethiviz.sh
```

This installs the `ethiviz` package (editable) and Flask/flask-cors if missing, starts
the backend on port 5001, waits for it to respond, then starts the React frontend on
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
- **Live in the engine, not yet surfaced through the web API**: the V6 additions —
  `construct_readings` (dimension-level cross-cultural findings), `analysis_coverage`,
  and per-lens `warnings` — are produced by `Analyzer.analyze()` and available to anyone
  using `ethiviz` as a library, but `Scripts/ethiviz_bridge.py` does not yet pass them
  into the API response, so the UI does not display them. Surfacing them is the natural
  next step.
- **Built, tested, but not yet wired into the live analyze path**: `ethiviz/metrics/`
  (AIF360-style group/individual fairness metrics), `ethiviz/mitigation/` (reweighing,
  disparate impact removal, calibrated equalized odds, reject-option classification), and
  `ethiviz/integration/sklearn_api.py` (scikit-learn-compatible pipeline). These are real,
  independently tested modules (see `tests/test_v5_tier4.py`) — a standalone
  AIF360-parity library — but `Analyzer.analyze()` doesn't call them yet.
- **`severity_thresholds`** blocks exist in every framework YAML but aren't parsed by the
  framework loader; the heatmap's severity buckets currently come from a documented
  rescaling of `ethiviz/metrics/group_fairness.py`'s threshold table instead (see
  `_severity_for` in `Scripts/ethiviz_bridge.py`).

## Known limitations

- **Prototype translations and non-English WEAT word lists are machine-generated and
  have not been reviewed by fluent speakers.** These are semantic anchors that directly
  determine scores in their language, so a mistranslation silently corrupts every result
  for that language. Each prototype file records this in a `translation_provenance`
  block. Have a fluent reviewer confirm each language set before treating non-English
  output as authoritative.
- **All six supported languages are colonial or majority languages** (English, Arabic,
  Mandarin, Spanish, Hindi, French). None is an Indigenous language, so the Indigenous
  lens cannot currently analyse text in the languages of the communities it exists to
  protect. Adding those requires community partnership and CARE-aligned data governance,
  not machine translation.
- Even with per-language calibration, non-English detection remains measurably weaker
  than English. This is now reported through `analysis_coverage` and `warnings` rather
  than hidden, but it is a real ceiling, not a solved problem.
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
  a previous version replaced.
- `compute_age_distribution` and `compute_gender_distribution` in
  `ethiviz/analysis/demographics.py` remain stubs returning empty results.

---

## Upgrading from V5

V6 contains breaking changes. See [CHANGELOG.md](./CHANGELOG.md) for the full list; the
ones most likely to affect existing code:

- `calculate_intersectional_analysis()` returns `Dict[str, IntersectionResult]` instead
  of `Dict[str, float]`.
- `cultural_inclusion_index()` returns a Jensen-Shannon similarity where it previously
  returned a key-overlap fraction. Existing thresholds are invalid.
- `BuddhistLens`, `HinduLens` and `IndigenousLens` no longer accept a `registry=` keyword
  (it was accepted and silently unused).
- Scores shift across all seven lenses. Identical input yields different output.

**Migration:** any Platt calibration fitted under 0.5.0 (`ethiviz/scoring/
calibration_data/`) and any drift baselines (`ethiviz/scoring/drift_snapshots/`) are
invalid against V6 scores and must be refit, not carried forward.

---

## Testing

```bash
cd Ethiviz_V6
python3.13 -m pytest tests/ -q
```

162 tests covering the engine, lenses, cultural metrics, multilingual coverage and
calibration, the dimension map, WEAT/iWEAT, mitigation modules, and the job store.

---

## Academic Context

EthiViz implements and extends the framework from Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

## License

Apache 2.0 — see [LICENSE](./LICENSE)
