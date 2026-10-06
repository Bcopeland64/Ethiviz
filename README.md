# EthiViz — Cultural Bias Analysis Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through multiple ethical traditions simultaneously. Unlike Western-centric fairness tools,
EthiViz treats cultural values as first-class analytical dimensions — not optional filters.

The platform is the computational implementation of Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

> **Project Governance Note:** To demonstrate end-to-end technical leadership and readiness as an **IT Project Manager**, this repository includes a dedicated directory containing full Project Management documentation (WBS, Risk Registers, Agile/Scrum artifacts, and Stakeholder Matrices). See the [Project Management Documentation](#project-management-documentation) section below.

---

## Table of Contents

- [What Makes EthiViz Different](#what-makes-ethiviz-different)
- [Current Version: V6](#current-version-v6)
- [What Changed in V6](#what-changed-in-v6)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Ethical Traditions](#ethical-traditions)
- [API Reference](#api-reference)
- [What's Real vs. What's Scaffolding](#whats-real-vs-whats-scaffolding)
- [Known Limitations](#known-limitations)
- [Upgrading from V5](#upgrading-from-v5)
- [Testing](#testing)
- [Project Management Documentation](#project-management-documentation)
- [Academic Context](#academic-context)
- [License](#license)

---

## What Makes EthiViz Different

Most bias detection tools (including IBM AI Fairness 360, Fairlearn, and Google's What-If
Tool) measure fairness using a single standard — typically a Western liberal framework
centred on individual rights and statistical parity. EthiViz rejects this monoculture:

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias
> from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

EthiViz analyses content through **seven ethical lenses simultaneously**: Western, Ubuntu,
Confucian, Islamic, Buddhist, Hindu/Dharmic, and Indigenous/First Nations.

---

## Current Version: V6

**[`Ethiviz_V6/`](Ethiviz_V6/) is the current, actively maintained version (v0.7.0)** — a
real Flask API backend running the actual 7-lens `ethiviz` engine, paired with a React
frontend, with working start/stop scripts that run the whole stack end-to-end. See
**[Ethiviz_V6/README.md](Ethiviz_V6/README.md)** for full architecture, API reference, and
setup details, and **[Ethiviz_V6/CHANGELOG.md](Ethiviz_V6/CHANGELOG.md)** for breaking
changes and migration notes.

`Ethiviz_V2/`, `Ethiviz_V3/`, `Ethiviz_V4/`, and `Ethiviz_V5/` are preserved in this repo
as historical snapshots of earlier iterations. They are not maintained and should not be
used for new work. Each version has a distinct contribution:

| Version | Contribution |
|---|---|
| V4 | Built the 7-lens engine as a library, but the web app never called it |
| V5 | Wired the running web app to the real 7-lens engine |
| **V6** | **Audited and repaired the engine itself: metrics, multilingual support, and cross-cultural reasoning** |

---

## What Changed in V6

V5's contribution was architectural. V6 turns inward on the engine. The headline finding
is that several of the metrics carrying the most cultural meaning were structurally unable
to measure what they documented — not inaccurate, but mathematically incapable of
producing the result they claimed. Full detail is in
[`Ethiviz_V6/CHANGELOG.md`](Ethiviz_V6/CHANGELOG.md).

### Metrics that could not measure what they claimed

- **Intersectional analysis** computed `score_a * score_b`. A product of two values in
  [0, 1] is never larger than either input, so it could never represent compound
  disadvantage — it inverted the intersectionality claim it documented. Rebuilt on a
  noisy-OR independence baseline with an amplification ratio that distinguishes
  superadditive, independent, and buffered interactions.
- **iWEAT compound effect** computed `actual - (axis1_effect + axis2_effect)`, which
  algebraically reduces to `actual` for every input, so the headline intersectionality
  metric always returned exactly `0.0`. Replaced with the difference-in-differences
  interaction term.
- **Cultural Inclusion Index** ignored its reference distribution's values, checking only
  which categories were present. A balanced target and a 98/1/1 target both returned 1.0.
  Rebuilt on Jensen-Shannon divergence over actual proportions.
- **`DualEthicsFramework.resolve_conflict()`** referenced bare names instead of `self.*`
  and raised `NameError` on every call. It had never worked.

### Multilingual analysis, made real and honest about its limits

The platform advertised six languages but was effectively English-only, and did not say so.

- **Translation coverage** completed across all six languages (Buddhist, Hindu, and
  Indigenous prototype sets went from 0–70% coverage to full).
- **Per-language similarity calibration** corrects for embedding models that represent
  some languages coarsely enough that every sentence looks similar to every other.
- **Blend renormalisation** gives the semantic channel full weight when the English-only
  regex channel is unavailable, instead of a flat 30% deduction that read as "less biased"
  rather than "less measurable."
- **Honest degradation:** `LensScore` now carries `analysis_coverage` and `warnings`, and
  confidence scales with how much of the pipeline actually applied.
- **Per-text language detection** replaces detecting once from the first text, which had
  scored mixed-language corpora entirely in that one language.

### Dimension-level cross-cultural reasoning

Conflict detection and synergy amplification used to compare one scalar per lens, which
hides each tradition's internal structure. The new `ethiviz/frameworks/dimension_map.py`
reads **ten shared moral constructs** beneath those scalars and reports:

- **Cross-tradition consensus** — independently authored traditions agreeing is stronger
  evidence than any single lens scoring high.
- **Tradition-specific findings** — a harm visible through only one ethical frame while
  the others that encode the same construct see nothing. This is the signal a single
  consensus score averages into invisibility.

Both are available on results via `ScoredResult.consensus_findings()` and
`ScoredResult.tradition_specific_findings()`.

### Lens parity and detection quality

- Buddhist, Hindu, and Indigenous lenses gained dedicated per-category patterns,
  tradition-weighted dimensions, and specific recommendations.
- Prototype severity (hand-graded 0.60–1.00) now scales each prototype's contribution.
- A negation guard stops stereotypes quoted in order to refute them from scoring as
  assertions.
- Patterns that fired on bare topic-word co-occurrence were fixed, removing false
  positives such as "sustainably harvest timber from the forest."
- WEAT word lists added for the Buddhist, Hindu, and Indigenous lenses; all seven lenses
  now produce WEAT suites, and `_run_weat` no longer swallows every exception.
- Framework results carry peak/p90 alongside the mean, so one severe document in a large
  corpus is not diluted toward zero.

### Test suite: 81 → 162

The old embedding mock returned an all-ones vector for every input, making cosine
similarity exactly 1.0 for every pair, so tests passed without exercising the detector.
It was replaced with deterministic bag-of-words embeddings, and affected tests were
rewritten to assert structural properties.

---

## Quick Start

```bash
bash start_ethiviz.sh
```

The root `start_ethiviz.sh` is a thin wrapper (as are `stop_ethiviz.sh` and
`start_services.sh`) that launches the copies in `Ethiviz_V6/`. It installs the `ethiviz`
package (editable) and Flask/flask-cors if missing, starts the backend on port **5001**,
waits for it to respond, then starts the React frontend on port **5173**. Once both are
up, open **http://localhost:5173**.

**Prerequisites:** Python 3.10+ (the start script prefers `python3.13` if present) and
Node.js 16+ with npm.

**Options:**

```bash
bash start_ethiviz.sh --backend-only     # backend only, tails the log
bash start_ethiviz.sh --frontend-only    # frontend only (backend already running)
bash start_ethiviz.sh --with-vision      # also installs mediapipe/torch/transformers
                                         # for real image face/skin-tone detection
                                         # (multi-GB download, not installed by default)
```

Without `--with-vision`, image analysis still works but degrades to a metadata-only proxy
(no real face/skin-tone detection) rather than failing.

**Manual setup (two terminals):**

```bash
# Terminal 1 — backend
cd Ethiviz_V6
python3.13 -m pip install --user -e .
python3.13 Scripts/api_server.py      # http://localhost:5001

# Terminal 2 — frontend
cd Ethiviz_V6/project
npm install
npm run dev                           # http://localhost:5173
```

**Stopping the app** — three equivalent ways:

1. Click the power-off icon in the app header (asks for confirmation, then shuts down both
   the backend and the frontend dev server).
2. Run `bash stop_ethiviz.sh` from the repo root.
3. Press `Ctrl-C` in the terminal running `start_ethiviz.sh` (only works while it is
   still attached in the foreground).

`POST /api/stop` only accepts requests from localhost; it is rejected from any other origin.

---

## Architecture

```
Ethiviz/
├── docs/pm/                            # ← IT Project Management & Governance Documentation
│   ├── Project_Charter.md              # Project Charter & Scope Statement
│   ├── WBS_and_Schedule.md             # Work Breakdown Structure & Timeline
│   ├── Risk_Management_Plan.md         # Risk Register & Mitigation Strategy
│   ├── Agile_Scrum_Artifacts.md        # Sprint Backlog, User Stories & Acceptance Criteria
│   └── Stakeholder_Matrix.md           # Stakeholder Analysis & Communication Plan
├── Ethiviz_V6/                         # ← current version, start here
│   ├── ethiviz/                        # Python package (pip install -e .)
│   │   ├── api.py                      # Analyzer — primary entry point
│   │   ├── lenses/                     # 7 cultural ethical lenses (+ shared base scoring)
│   │   ├── frameworks/
│   │   │   ├── conflict.py             # Scalar-level cross-tradition conflicts
│   │   │   └── dimension_map.py        # Dimension-level shared moral constructs
│   │   ├── embeddings/                 # Prototypes, per-language similarity calibration
│   │   ├── analysis/
│   │   │   ├── weat.py                 # WEAT + intersectional WEAT
│   │   │   └── weat_lists/             # Word lists — all 7 lenses
│   │   ├── metrics/                    # Group/individual fairness metrics (AIF360-style)
│   │   ├── mitigation/                 # Reweighing, DI Remover, Calibrated EO, etc.
│   │   ├── integration/                # sklearn-compatible pipeline wrapper
│   │   ├── storage/                    # SQLite job store
│   │   ├── sample_data/                # 140+ curated texts (7 traditions)
│   │   ├── vision/                     # Fitzpatrick skin tone, MediaPipe, CLIP
│   │   └── reporting/                  # HTML report generation
│   ├── Scripts/
│   │   ├── api_server.py               # Flask REST API (port 5001), async job processing
│   │   └── ethiviz_bridge.py           # Bridges the API to the real Analyzer engine
│   ├── project/                        # React 18 + Vite frontend (port 5173)
│   │   └── src/components/
│   │       ├── ConfigPanel.tsx, MainContent.tsx
│   │       ├── ExportButton.tsx, CompareMode.tsx
│   │       ├── CrossCulturalEquityDashboard.tsx
│   │       └── visualizations/CulturalFairnessHeatmap.tsx
│   ├── tests/                          # 162 tests
│   │   ├── test_v5_phase1_metrics.py        # Repaired cultural metrics
│   │   ├── test_v5_phase2_multilingual.py   # Coverage, calibration, translations
│   │   └── test_v5_phase3_crosscultural.py  # Dimension map, WEAT parity, iWEAT
│   ├── CHANGELOG.md                    # Breaking changes + migration notes
│   ├── start_ethiviz.sh / stop_ethiviz.sh
│   └── pyproject.toml
│
├── start_ethiviz.sh / stop_ethiviz.sh / start_services.sh  # root wrappers -> Ethiviz_V6/
├── Ethiviz_V5/                         # historical snapshot, not maintained
├── Ethiviz_V4/                         # historical snapshot, not maintained
├── Ethiviz_V3/                         # historical snapshot, not maintained
└── Ethiviz_V2/                         # historical snapshot, not maintained
```

---

## Ethical Traditions

EthiViz analyses content through seven ethical lenses simultaneously. The bias categories
below are the actual scoring dimensions each lens produces.

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

The dimension map groups these categories across traditions into ten constructs: human
dignity, essentialism, non-harm, cultural delegitimisation, group flattening, relational
obligation, gender subordination, truthfulness, intergenerational responsibility, and
knowledge sovereignty.

The last two are encoded by the Indigenous lens alone. That is reported as a finding
rather than smoothed over — a concern only one tradition measures is real information,
and its absence elsewhere is not consensus.

---

## API Reference

**Base URL:** `http://localhost:5001`

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Submit an analysis job; returns `job_id` + `status_url` |
| `/api/analyze/status/{job_id}` | GET | `pending` / `processing` / `completed` / `failed` |
| `/api/analyze/results/{job_id}` | GET | Retrieve results once completed |
| `/api/analyze/results/{job_id}/export` | GET | Download HTML or JSON report (`?format=html\|json`) |
| `/api/sample-data` | GET | List curated sample datasets |
| `/api/jobs` | GET | List recent jobs (persisted across restarts) |
| `/api/compare` | POST | Compare two completed jobs by id: `{job_id_a, job_id_b}` |
| `/api/stop` | POST | Gracefully shut down backend + frontend (localhost-only) |

### Request format (`POST /api/analyze`)

`Content-Type: multipart/form-data`

```
analysis_type        : "text" | "image" | "text_and_image"
data_source_type     : "upload" | "sample"
selected_traditions  : ["western", "ubuntu", "confucian", "islamic",
                        "buddhist", "hindu", "indigenous"]
advanced_options     : JSON string (currently accepted but not yet
                       wired to the real engine — see Known Limitations)
text_file            : file upload (CSV, XLSX, JSON, TXT)
image_files          : one or more file uploads (PNG, JPG, WEBP, GIF)
```

### Result shape

A completed job's results include:

- **`text_analysis`** — one item per input text, with a `{tradition}_ethics_score` per
  selected lens (e.g. `western_ethics_score`, `buddhist_ethics_score`), plus a
  `bias_score` (mean across selected lenses) and `diversity_index` (a cross-tradition
  agreement proxy). These are simple, documented heuristics, not validated composite
  metrics; see the comments in `Scripts/ethiviz_bridge.py`.
- **`image_analysis`** — the same, per image, keyed by filename.
- **`tradition_scores`** — `[{tradition, score, severity, confidence}, ...]`, keyed by the
  engine's internal framework id (e.g. `confucian_v2`, not `confucian`). This powers the
  fairness heatmap and cross-cultural dashboard in the UI.

> **Note on `confidence`:** its meaning changed in V6. It previously reported
> language-detection confidence; it now reflects each lens's own confidence scaled by how
> much of the detection pipeline actually applied to the input. Non-English analyses will
> report visibly lower values than before — that is the intended correction, not a
> regression.

Full request/response shapes are documented in
[`Ethiviz_V6/README.md`](Ethiviz_V6/README.md).

---

## What's Real vs. What's Scaffolding

Being direct about this matters for anyone building on top of EthiViz.

- **Live and verified end-to-end:** the 7-lens `Analyzer` engine, text and image analysis
  through the API, SQLite job persistence, the compare endpoint, the export endpoint, and
  the stop mechanism.
- **Live in the engine, not yet surfaced through the web API:** the V6 additions —
  `construct_readings` (dimension-level cross-cultural findings), `analysis_coverage`,
  and per-lens `warnings` — are produced by `Analyzer.analyze()` and available to anyone
  using `ethiviz` as a library, but `Scripts/ethiviz_bridge.py` does not yet pass them
  into the API response, so the UI does not display them. Surfacing them is the natural
  next step.
- **Built and tested, but not yet wired into the live analyze path:** `ethiviz/metrics/`
  (AIF360-style group/individual fairness metrics), `ethiviz/mitigation/` (reweighing,
  disparate impact removal, calibrated equalized odds, reject-option classification), and
  `ethiviz/integration/sklearn_api.py` (scikit-learn-compatible pipeline). These are real,
  independently tested modules — a standalone AIF360-parity library — but
  `Analyzer.analyze()` doesn't call them yet.
- **Not yet parsed:** `severity_thresholds` blocks exist in every framework YAML but the
  framework loader doesn't read them. The heatmap's severity buckets currently come from a
  documented rescaling of the threshold table in `ethiviz/metrics/group_fairness.py` (see
  `_severity_for` in `Scripts/ethiviz_bridge.py`).

---

## Known Limitations

- **Machine-generated translations.** Prototype translations and non-English WEAT word
  lists have not been reviewed by fluent speakers. They are semantic anchors that directly
  determine scores in their language, so a mistranslation silently corrupts every result
  for that language. Each prototype file records this in a `translation_provenance`
  block. Have a fluent reviewer confirm each language set before treating non-English
  output as authoritative.
- **No Indigenous languages.** All six supported languages (English, Arabic, Mandarin,
  Spanish, Hindi, French) are colonial or majority languages, so the Indigenous lens
  cannot yet analyse text in the languages of the communities it exists to protect.
  Adding those requires community partnership and CARE-aligned data governance, not
  machine translation.
- **Non-English detection is weaker than English,** even with per-language calibration.
  This is now reported through `analysis_coverage` and `warnings` rather than hidden, but
  it is a real ceiling, not a solved problem.
- **Shared singleton state.** The `Analyzer` instance is a lazily initialised singleton.
  Its calibrator and drift monitor hold mutable state shared across concurrent job
  threads, which can theoretically race under load. Flagged in code comments.
- **Partial job reconstruction.** SQLite persistence stores per-tradition aggregate
  scores, not full per-item detail. After a server restart, previously completed jobs
  return a `_partial: true` reconstruction (aggregate scores only).
- **Image analysis without `--with-vision`** produces a metadata-only proxy description
  rather than real face, skin-tone, or cultural-element detection.
- **`advanced_options` are inert.** Max tokens, NLP model, feature level, and batch size
  are accepted by the API but not used by the real engine; they were tailored to the
  legacy pipeline a previous version replaced.
- **Demographic stubs.** `compute_age_distribution` and `compute_gender_distribution` in
  `ethiviz/analysis/demographics.py` remain stubs returning empty results.

---

## Upgrading from V5

V6 contains breaking changes. See [`Ethiviz_V6/CHANGELOG.md`](Ethiviz_V6/CHANGELOG.md)
for the full list. The ones most likely to affect existing code:

- `calculate_intersectional_analysis()` returns `Dict[str, IntersectionResult]` instead of
  `Dict[str, float]`.
- `cultural_inclusion_index()` returns a Jensen-Shannon similarity where it previously
  returned a key-overlap fraction. Existing thresholds are invalid.
- `BuddhistLens`, `HinduLens`, and `IndigenousLens` no longer accept a `registry=` keyword
  (it was accepted and silently unused).
- Scores shift across all seven lenses. Identical input yields different output.

**Migration:** any Platt calibration fitted under 0.5.0
(`ethiviz/scoring/calibration_data/`) and any drift baselines
(`ethiviz/scoring/drift_snapshots/`) are invalid against V6 scores and must be refit, not
carried forward.

---

## Testing

```bash
cd Ethiviz_V6
python3.13 -m pytest tests/ -q
```

162 tests cover the engine, lenses, cultural metrics, multilingual coverage and
calibration, the dimension map, WEAT/iWEAT, mitigation modules, and the job store.

---

## Project Management Documentation

To complement the technical delivery, this project demonstrates end-to-end IT Project
Management lifecycle execution. The [`docs/pm/`](docs/pm/) folder showcases how full
software engineering initiatives are initiated, planned, executed, and governed:

| PM Artifact | Focus Area & Description |
|---|---|
| [Project Charter](docs/pm/Project_Charter.md) | High-level business case, objectives, milestones, constraints, and success metrics. |
| [WBS & Schedule](docs/pm/WBS_and_Schedule.md) | Detailed Work Breakdown Structure mapping architectural iterations (V2 through V6) to deliverable schedules. |
| [Risk Register](docs/pm/Risk_Management_Plan.md) | Identifies technical, ethical, and delivery risks alongside impact assessments and mitigation paths. |
| [Agile/Scrum Framework](docs/pm/Agile_Scrum_Artifacts.md) | User story mapping, acceptance criteria, epic definitions, and sprint velocity tracking. |
| [Stakeholder Matrix](docs/pm/Stakeholder_Matrix.md) | Communication strategy catering to academic advisors, open-source contributors, and end-users. |

This governance layer highlights my capability as an aspiring IT Project Manager to bridge
the gap between complex software engineering, cross-cultural domain ethics, and structured
project governance.

---

## Academic Context

EthiViz implements and extends the framework from:

> Brandon Scott Copeland. *"Cross-Cultural Bias Detection in AI Systems: A Computational
> Framework for Multi-Perspective Ethical Analysis."* Bachelor's Thesis, IU University of
> Applied Sciences, September 2025.

The thesis argues that existing AI bias detection tools are epistemologically
Western-centric and proposes a pluralistic alternative. EthiViz is that alternative.

---

## License

Apache 2.0 — see [`Ethiviz_V6/LICENSE`](Ethiviz_V6/LICENSE).
