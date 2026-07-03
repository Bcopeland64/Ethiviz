# EthiViz — Cultural Bias Analysis Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through multiple ethical traditions simultaneously. Unlike Western-centric fairness tools,
EthiViz treats cultural values as first-class analytical dimensions — not optional filters.

The platform is the computational implementation of Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

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

## Current Version: V5

**[`Ethiviz_V5/`](Ethiviz_V5/) is the current, actively maintained version** — a real
Flask API backend running the actual 7-lens `ethiviz` engine, paired with a React
frontend, with working start/stop scripts. See **[Ethiviz_V5/README.md](Ethiviz_V5/README.md)**
for full architecture, API reference, and setup details.

`Ethiviz_V2/`, `Ethiviz_V3/`, and `Ethiviz_V4/` are preserved in this repo as historical
snapshots of earlier iterations. They are not maintained and should not be used for new
work — the engine and web app inside `Ethiviz_V4/` were the basis V5 was built from, but
V5 is where active development now happens.

### Quick start

```bash
bash start_ethiviz.sh
```

This is a thin wrapper that launches `Ethiviz_V5/start_ethiviz.sh` — it installs
dependencies if missing, starts the Flask backend on port 5001, and the React frontend
on port 5173. Open `http://localhost:5173` once both are up.

To stop everything: click the **Stop** button in the app header, or run
`bash stop_ethiviz.sh` from the repo root.

Full details, including the `--with-vision` flag for real image analysis and the
`--backend-only`/`--frontend-only` modes, are documented in
[Ethiviz_V5/README.md](Ethiviz_V5/README.md#setup).

---

## Architecture (V5)

```
Ethiviz/
├── Ethiviz_V5/                        # ← current version, start here
│   ├── ethiviz/                       # Python package (pip install -e .)
│   │   ├── api.py                     # Analyzer — primary entry point
│   │   ├── lenses/                    # 7 cultural ethical lenses
│   │   ├── metrics/                   # SPD, DI, EOD, AOD, Theil, consistency
│   │   ├── mitigation/                # Reweighing, DI Remover, Calibrated EO, etc.
│   │   ├── integration/               # EthiVizPipeline (sklearn-compatible)
│   │   ├── storage/                   # SQLite persistent job store
│   │   ├── sample_data/               # 140+ curated texts (7 traditions)
│   │   ├── vision/                    # Fitzpatrick skin tone, MediaPipe, CLIP
│   │   └── reporting/                 # HTML/JSON export
│   ├── Scripts/
│   │   ├── api_server.py              # Flask REST API (port 5001), async job processing
│   │   └── ethiviz_bridge.py          # Bridges the API to the real Analyzer engine
│   ├── project/                       # React 18 + Vite frontend (port 5173)
│   │   └── src/components/
│   │       ├── ConfigPanel.tsx, MainContent.tsx
│   │       ├── ExportButton.tsx, CompareMode.tsx
│   │       ├── CrossCulturalEquityDashboard.tsx
│   │       └── visualizations/CulturalFairnessHeatmap.tsx
│   ├── tests/                         # 81 tests
│   ├── start_ethiviz.sh / stop_ethiviz.sh
│   └── pyproject.toml
│
├── start_ethiviz.sh / stop_ethiviz.sh  # root wrappers -> Ethiviz_V5/
├── Ethiviz_V4/                          # historical snapshot, not maintained
├── Ethiviz_V3/                          # historical snapshot, not maintained
└── Ethiviz_V2/                          # historical snapshot, not maintained
```

---

## Ethical Traditions

EthiViz analyses content through seven ethical lenses simultaneously.

| Tradition | Core Values | Bias Categories Detected |
|---|---|---|
| **Western** | Individual rights, equal opportunity, statistical parity | Racial bias, gender bias, stereotyping, individual rights violations |
| **Ubuntu** | Community harmony, relational impact, collective benefit | Cultural erasure, community devaluation, African essentialism |
| **Confucian** | Social harmony, role appropriateness, hierarchical respect | Hierarchical disrespect, face violations, relational bias |
| **Islamic** | Dignity preservation, equitable treatment, harm prevention | Orientalism, Islamic essentialism, violent stereotyping |
| **Buddhist** | Ahimsa, right speech, interdependence | Essentialist categorisation, attachment to identity labels |
| **Hindu / Dharmic** | Dharma, satya, ahimsa | Caste stereotyping, colonial framing, dharmic misrepresentation |
| **Indigenous / First Nations** | CARE Principles, seven-generations stewardship | Erasure of oral tradition, land commodification framing |

---

## API Reference

Base URL: `http://localhost:5001`

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Submit analysis job; returns `job_id` |
| `/api/analyze/status/{job_id}` | GET | Check job status: `pending` / `processing` / `completed` / `failed` |
| `/api/analyze/results/{job_id}` | GET | Retrieve completed analysis results |
| `/api/analyze/results/{job_id}/export` | GET | Download HTML or JSON report |
| `/api/sample-data` | GET | List available curated sample datasets |
| `/api/jobs` | GET | List recent jobs (persisted across restarts) |
| `/api/compare` | POST | Side-by-side comparison of two completed jobs |
| `/api/stop` | POST | Gracefully shut down backend + frontend (localhost-only) |

Full request/response shapes are documented in
[Ethiviz_V5/README.md](Ethiviz_V5/README.md#api-reference).

---

## What's Real vs. What's Scaffolding

The 7-lens engine, text/image analysis, job persistence, compare, export, and stop are
live and verified end-to-end. The AIF360-parity fairness metrics, mitigation algorithms,
and scikit-learn integration (`ethiviz/metrics/`, `ethiviz/mitigation/`,
`ethiviz/integration/`) are real, independently tested modules, but are **not yet wired
into the live `Analyzer.analyze()` path** — they exist as a standalone, tested library
today. See [Ethiviz_V5/README.md](Ethiviz_V5/README.md#whats-real-vs-whats-scaffolding)
for the full, honest breakdown.

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

Apache 2.0 — see [Ethiviz_V5/LICENSE](Ethiviz_V5/LICENSE)
