# EthiViz V4 — Cross-Cultural AI Bias Detection

EthiViz is a computational framework for multi-perspective ethical analysis of AI systems, rooted in Brandon Scott Copeland's Bachelor's thesis at IU University of Applied Sciences (2025). V4 closes the gap with IBM AI Fairness 360 while preserving a unique advantage AIF360 cannot match: simultaneous analysis through **seven distinct cultural ethical lenses**.

> **Design principle:** Cultural elements are co-equal to statistical elements. Every statistical metric added in V4 carries a cultural-lens extension. A Western fairness threshold is not an Ubuntu fairness threshold — EthiViz honours both simultaneously.

---

## What Makes EthiViz Different

Most bias detection tools (AIF360, Fairlearn, Google's What-If Tool) measure fairness using a single standard — typically a Western liberal framework centred on individual rights and statistical parity. EthiViz rejects this monoculture:

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

---

## V4 Capabilities

### AIF360 Parity — with Cultural Extensions

| Capability | AIF360 | EthiViz V4 |
|---|---|---|
| Statistical group fairness metrics | ✅ | ✅ |
| Individual fairness metrics | ✅ | ✅ |
| Pre-processing bias mitigation | ✅ | ✅ |
| In-processing bias mitigation | ✅ | ✅ |
| Post-processing bias correction | ✅ | ✅ |
| ML model fairness evaluation | ✅ | ✅ |
| scikit-learn API compatibility | ✅ | ✅ |
| Per-tradition fairness thresholds | ❌ | ✅ |
| Cultural group definitions per tradition | ❌ | ✅ |
| Cultural lens analysis (7 traditions) | ❌ | ✅ |
| WEAT / iWEAT embedding tests | ❌ | ✅ |
| Image analysis (Fitzpatrick skin tone, CLIP) | ❌ | ✅ |
| Fairness heatmap across traditions | ❌ | ✅ |
| Cultural Representation Equity Index | ❌ | ✅ |
| Bootstrap confidence intervals | ❌ | ✅ |
| Regulatory mapping (EU AI Act, GDPR, CCPA) | ❌ | ✅ |

---

## Ethical Traditions

EthiViz V4 analyses content through seven ethical lenses simultaneously.

| Tradition | Core Values | Bias Categories Detected |
|---|---|---|
| **Western** | Individual rights, equal opportunity, statistical parity | Racial bias, gender bias, stereotyping, rights violations |
| **Ubuntu** | Community harmony, relational impact, collective benefit | Cultural erasure, community devaluation, African essentialism |
| **Confucian** | Social harmony, role appropriateness, hierarchical respect | Hierarchical disrespect, face violations, relational bias |
| **Islamic** | Dignity preservation, equitable treatment, harm prevention | Orientalism, Islamic essentialism, violent stereotyping |
| **Indigenous / First Nations** | CARE Principles, seven-generations stewardship | Erasure of oral tradition, land commodification framing |
| **Buddhist** | Ahimsa, right speech, interdependence | Essentialist categorisation, attachment to identity labels |
| **Hindu / Dharmic** | Dharma, satya, ahimsa | Caste stereotyping, colonial framing, dharmic misrepresentation |

---

## Quick Start

### Python library

```python
from ethiviz.api import Analyzer
from ethiviz.context.deployment import DeploymentContext

ctx = DeploymentContext(
    region="NG",
    domain="hiring",
    primary_community="african",
    regulatory_framework="gdpr"
)

analyzer = Analyzer(deployment_context=ctx)
result = analyzer.analyze([
    "African applicants tend to lack the required work ethic.",
    "The candidate demonstrated strong analytical skills.",
])

report = result.generate_report()
report.to_html("bias_report.html")
print(f"Consensus bias score: {result.consensus_score:.3f}")
```

### Group fairness metrics

```python
from ethiviz.metrics.group_fairness import GroupFairnessCalculator

calc = GroupFairnessCalculator()
result = calc.compute(
    y_true=[1, 0, 1, 0, 1, 0],
    y_pred=[1, 0, 0, 0, 1, 1],
    group_memberships={
        "western_v1": [1, 1, 0, 0, 1, 0],
        "ubuntu_v1":  [1, 0, 1, 0, 0, 1],
    }
)
for tid, score in result.per_tradition.items():
    print(f"{tid}: SPD={score.spd:.3f}, severity={score.severity}")
```

### scikit-learn pipeline

```python
from sklearn.linear_model import LogisticRegression
from ethiviz.integration.sklearn_api import EthiVizPipeline

pipe = EthiVizPipeline(
    estimator=LogisticRegression(),
    tradition_id="ubuntu_v1",
    repair_level=0.8,
)
pipe.fit(X_train, y_train)
predictions = pipe.predict(X_test)
```

### New cultural lenses

```python
from ethiviz.lenses.indigenous import IndigenousLens
from ethiviz.lenses.buddhist import BuddhistLens
from ethiviz.lenses.hindu import HinduLens

lens = IndigenousLens()
score = lens.score("Traditional knowledge should be freely commercialised by corporations.")
print(f"Indigenous bias score: {score.overall_score:.3f}")
```

---

## Installation

```bash
# Core (no optional dependencies)
pip install -e .

# With semantic embeddings (recommended)
pip install -e ".[semantic]"

# Full install (includes vision, explainability, multilingual)
pip install -e ".[full]"

# Development
pip install -e ".[dev,semantic,batch,multilingual]"
```

**Requires Python 3.10+**

---

## Running the Web Platform

The platform has two components that run simultaneously:

| Component | Default port | Command |
|-----------|-------------|---------|
| Flask API (backend) | 5001 | `python3 Scripts/api_server.py` |
| React UI (frontend) | 5173 | `cd project && npm run dev` |

**Quickest start** (from the parent `Ethiviz/` directory):

```bash
bash start_ethiviz.sh
```

Or from inside `Ethiviz_V4/`:

```bash
bash start.sh
```

Then open `http://localhost:5173` in your browser.

**Port configuration:** if you change either port, update:
- `API_BASE_URL` in [project/src/components/ConfigPanel.tsx](project/src/components/ConfigPanel.tsx)
- CORS origin list in [Scripts/api_server.py](Scripts/api_server.py)

---

## Project Structure

```
Ethiviz_V4/
├── ethiviz/
│   ├── api.py                          # Analyzer — primary entry point
│   ├── frameworks/
│   │   ├── builtin/
│   │   │   ├── western_v1.yaml
│   │   │   ├── ubuntu_v1.yaml
│   │   │   ├── confucian_v2.yaml
│   │   │   ├── islamic_v1.yaml
│   │   │   ├── indigenous_v1.yaml
│   │   │   ├── buddhist_v1.yaml
│   │   │   └── hindu_v1.yaml
│   │   └── conflict.py                 # Cross-tradition conflict resolution
│   ├── lenses/                         # One module per tradition
│   ├── metrics/
│   │   ├── group_fairness.py           # SPD, DI, EOD, AOD, Theil Index
│   │   └── individual_fairness.py      # Consistency, sample distortion
│   ├── mitigation/
│   │   ├── preprocessing.py            # Reweighing, Disparate Impact Remover
│   │   ├── inprocessing.py             # Prejudice Remover
│   │   └── postprocessing.py           # Calibrated EO, Reject Option Classification
│   ├── evaluation/
│   │   └── structured_dataset.py       # CulturalDataset, ModelBiasEvaluator
│   ├── integration/
│   │   └── sklearn_api.py              # EthiVizPipeline, CulturalBiasTransformer
│   ├── embeddings/
│   │   ├── model.py                    # Sentence-transformer wrapper
│   │   ├── semantic_detector.py
│   │   └── prototypes/                 # 7 tradition prototype YAML files
│   ├── analysis/
│   │   ├── weat.py                     # WEAT & iWEAT with bootstrap CI
│   │   ├── ubuntu_metrics.py
│   │   ├── demographics.py
│   │   ├── intersectional.py
│   │   └── cultural_inclusion.py
│   ├── vision/
│   │   ├── skin_tone.py                # ITA-based Fitzpatrick scale (I–VI)
│   │   ├── face_detector.py            # MediaPipe face detection
│   │   ├── cultural_element_detector.py # CLIP zero-shot detection
│   │   └── object_detector.py
│   ├── scoring/
│   │   ├── multi_framework.py          # Multi-tradition aggregation
│   │   ├── calibration.py              # Platt scaling
│   │   ├── confidence.py               # Bootstrap CI
│   │   └── drift.py                    # Score drift monitoring
│   ├── context/
│   │   ├── deployment.py               # DeploymentContext (region, domain)
│   │   ├── regulatory.py               # EU AI Act, GDPR, CCPA mapping
│   │   └── weights.py                  # WVS-calibrated tradition weights
│   ├── storage/
│   │   └── job_store.py                # SQLite persistent job store
│   ├── reporting/
│   │   ├── html_report.py              # HTML + JSON export
│   │   ├── explainability.py           # LIME/SHAP attribution reports
│   │   └── provenance.py               # Evidence provenance chains
│   ├── sample_data/                    # 140+ curated texts (20 per tradition)
│   └── utils/                          # Batch processing, reproducibility
│
├── project/                            # React 18 + Vite frontend
│   └── src/components/
│       ├── ConfigPanel.tsx             # Analysis configuration + file upload
│       ├── MainContent.tsx             # Results rendering
│       ├── ExportButton.tsx            # HTML / JSON download
│       ├── CompareMode.tsx             # Side-by-side dataset comparison
│       ├── CrossCulturalEquityDashboard.tsx
│       └── visualizations/
│           └── CulturalFairnessHeatmap.tsx
│
├── Scripts/
│   └── api_server.py                   # Flask REST API (SQLite job store)
│
├── examples/
│   └── text_analysis.py
│
├── tests/
│   ├── test_smoke.py                   # Core smoke tests
│   ├── test_v4_upgrades.py             # V4 upgrade tests
│   └── test_v5_tier4.py               # Extended V4 tier tests
│
├── pyproject.toml
└── start.sh
```

---

## Analysis Capabilities

### Text Analysis
- **Input formats:** CSV, XLSX, JSON, TXT
- **NLP pipeline:** spaCy (`en_core_web_sm`), NLTK, optional transformer-based sentiment
- **Embedding tests:** WEAT and iWEAT (intersectional WEAT) with effect sizes, p-values, and 95% bootstrap confidence intervals
- **Multilingual:** English, Arabic, Mandarin, Spanish, Hindi, French with script-aware tokenisation
- **Per-tradition output:** bias score, ethics score, cultural marker detections, flagged items, recommendations, calibrated confidence intervals
- **Explainability:** LIME token attributions per tradition

### Image Analysis
- **Input formats:** PNG, JPG, JPEG, WEBP, GIF
- **Face detection:** MediaPipe; CPU-capable, no GPU required
- **Skin tone:** ITA-based Fitzpatrick scale (I–VI) estimation
- **Cultural elements:** CLIP zero-shot detection of cultural symbols, clothing, settings
- **Diversity metrics:** Shannon entropy diversity index across skin tone and representation dimensions
- **Explainability:** SHAP region attributions

### Ethical Scoring
- All scores calibrated via Platt scaling against a reference corpus
- Bootstrap 95% confidence intervals on every score
- Conflict taxonomy: when traditions disagree, the disagreement is typed and resolved with a principled strategy
- Synergy amplification: when multiple traditions independently converge on the same finding, the consensus signal is amplified

### Regulatory Compliance
- Automatic mapping of findings to EU AI Act, GDPR, and CCPA obligations
- HTML reports with evidence provenance chains for compliance documentation

---

## API Reference

Base URL: `http://localhost:5001`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit analysis job → returns `job_id` |
| `GET` | `/api/analyze/status/{job_id}` | Poll job status: `pending` / `processing` / `completed` / `failed` |
| `GET` | `/api/analyze/results/{job_id}` | Retrieve full results |
| `GET` | `/api/analyze/results/{job_id}/export` | Download HTML or JSON report |
| `GET` | `/api/sample-data` | List curated sample datasets |
| `GET` | `/api/jobs` | List recent jobs (persisted across restarts via SQLite) |
| `POST` | `/api/compare` | Compare two datasets side-by-side by `job_id` |

### Request format (`POST /api/analyze`)

```
Content-Type: multipart/form-data

analysis_type        : "text" | "image" | "text_and_image"
data_source_type     : "upload" | "sample"
selected_traditions  : ["western", "ubuntu", "confucian", "islamic",
                        "indigenous", "buddhist", "hindu"]
advanced_options     : JSON string — nlp_model, feature_level, batch_size
text_file            : file upload (CSV, XLSX, JSON, TXT)
image_files          : one or more file uploads (PNG, JPG, WEBP, GIF)
```

---

## Running Tests

```bash
# All tests
python3 -m pytest tests/ -q

# Extended V4 tests only
python3 -m pytest tests/test_v5_tier4.py -v
```

---

## Dependencies

**Core (always installed):**
numpy, pandas, pyyaml, pydantic, scikit-learn, jinja2, scipy

**Optional extras:**

| Extra | What it enables | Key packages |
|-------|----------------|-------------|
| `semantic` | Sentence-embedding analysis | sentence-transformers |
| `vision` | Image analysis | mediapipe, opencv, pillow, transformers, torch |
| `explainability` | LIME / SHAP attributions | lime, shap |
| `multilingual` | Arabic, Mandarin, etc. | langdetect, jieba, stanza |
| `batch` | Progress bars for large batches | tqdm |
| `aif360` | AIF360 interop | aif360 |
| `dev` | Testing and linting | pytest, black, ruff, mypy |

---

## Academic Context

EthiViz is the computational implementation of:

> Copeland, B. S. (2025). *Cross-Cultural Bias Detection in AI Systems: A Computational Framework for Multi-Perspective Ethical Analysis*. IU University of Applied Sciences.

The thesis argues that existing AI bias detection tools are epistemologically Western-centric and proposes a pluralistic alternative. EthiViz is that alternative.

This software is not legal advice. Regulatory compliance mappings are informational only.

---

## License

Apache License 2.0
