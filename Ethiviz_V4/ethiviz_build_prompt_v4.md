# EthiViz — Claude Code Build Prompt (v5, improved)

## Authorship and academic context

This library is the computational implementation of a Bachelor's thesis by Brandon Scott
Copeland, "Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis" (IU University of Applied Sciences, September 2025). The
thesis argues that existing AI bias detection tools are Western-centric and proposes EthiViz as
a pluralistic alternative that analyses bias through four distinct ethical lenses: Western, Ubuntu,
Confucian, and Islamic. The code in Appendix A of the thesis contains the seed implementation.

This v5 build prompt implements thirty-four upgrades beyond the thesis proof-of-concept,
organised into four tiers.

> **Design principle:** Cultural elements are co-equal to statistical elements throughout.
> Every statistical metric added in Tier 4 carries a cultural-lens extension that gives the
> metric meaning within each tradition's own value system. A Western fairness threshold is
> not an Ubuntu fairness threshold — the tool must honour both simultaneously.

**Tier 1 — Core technical validity (v3 upgrades, preserved):**
1. Semantic embeddings — multilingual sentence embeddings replace regex matching
2. Composite Ubuntu metrics — three-component diversity measurement
3. WEAT analysis — statistically rigorous bias measurement with effect sizes and p-values
4. Conflict taxonomy — typed framework disagreements with principled resolution strategies
5. Explainability layer — LIME/SHAP token and region attributions
6. WVS-grounded weights — empirically derived bias_criteria weights
7. Confidence intervals — bootstrap 95% CIs on all scores

**Tier 2 — Learning and calibration (new in v4):**
8. Active learning loop — low-confidence detections surfaced for expert review; confirmed
   cases written back to prototype store with provenance tracking
9. Score calibration — Platt scaling against a reference corpus so scores are calibrated
   probabilities, not raw similarity values
10. Drift monitoring — KL-divergence alerting when score distributions shift over time

**Tier 3 — Language, vision, and research infrastructure (new in v4):**
11. Multilingual pipeline — language detection, per-language prototype variants, script-aware
    tokenisation for LIME/SHAP in Arabic, Mandarin, and Hindi
12. Concrete CV pipeline — MediaPipe face detection, ITA skin tone estimation, CLIP-based
    cultural element detection; all CPU-capable
13. Deployment context — DeploymentContext object enabling context-weighted aggregation
    and regulatory compliance mapping
14. Synergy amplification — MultiFrameworkScorer amplifies signal when synergistic lenses
    independently converge on the same finding
15. Regulatory mapper — maps findings to EU AI Act, GDPR, CCPA obligations with evidence
    provenance chains in HTML output
16. Intersectional WEAT (iWEAT) — original methodological extension measuring compound
    bias at identity intersections beyond the Caliskan et al. single-dimension design
17. WEAT benchmark validation — validates effect sizes against Caliskan et al. published
    figures to quantify trust in results for a given embedding model
18. Batch processing infrastructure — tqdm progress, checkpointing, parallel execution,
    reproducibility records
19. Dataset versioning hooks — FrameworkRegistry tracks which YAML hashes were used
    so analyses are reproducible after framework updates
20. Multilingual WEAT word lists — per-language translations of target and attribute sets

**Tier 4 — AI Fairness 360 parity + cultural deepening (new in v5):**

*Statistical parity with cultural extensions (Upgrades 21–22):*
21. Cultural group fairness metrics suite — Statistical Parity Difference (SPD), Disparate
    Impact ratio (DI), Equal Opportunity Difference (EOD), Average Odds Difference (AOD),
    Theil Index, and Mean Difference; each metric computed per tradition using that
    tradition's definition of protected groups, with WVS-calibrated acceptance thresholds
22. Individual fairness metrics — consistency metric and sample distortion metric with
    culturally-proximate similarity groupings (individuals similar by expressed cultural
    values, not only by demographic category)

*Bias mitigation pipeline with per-tradition fairness constraints (Upgrades 23–25):*
23. Pre-processing debiasing — Reweighing and Disparate Impact Remover adapted for
    cultural group parity; lens-weighted feature importance protects culturally salient
    features from over-correction
24. In-processing debiasing — Adversarial Debiasing with multi-head adversary (one head
    per tradition) and Prejudice Remover Regularizer with DeploymentContext-weighted
    regularization term
25. Post-processing correction — Calibrated Equalized Odds with per-tradition threshold
    tables and Reject Option Classification widened for individuals underrepresented in
    the PrototypeStore coverage statistics

*ML model evaluation (Upgrades 26–27):*
26. Structured dataset evaluator — CulturalDataset wrapper (analogous to AIF360
    BinaryLabelDataset) for tabular data; ModelBiasEvaluator for any sklearn classifier;
    automatic before/after mitigation comparison report per tradition
27. Scikit-learn compatible API — CulturalBiasTransformer (TransformerMixin),
    CulturalFairnessScorer, and EthiVizPipeline (Pipeline subclass) for drop-in
    integration with existing ML workflows

*Cultural deepening — unique to EthiViz (Upgrades 28–30):*
28. Extended cultural traditions — three new ethical lenses: Indigenous / First Nations
    (land-relational ethics, seven-generations principle, CARE Principles, FNIGC protocols),
    Buddhist (ahimsa, pratītyasamutpāda, compassionate speech), and Hindu / Dharmic
    (dharmic duty, ahimsa, satya); each implemented as a YAML framework with full
    prototype coverage and multilingual word lists
29. Per-tradition fairness severity thresholds + heatmap — each tradition's YAML gains a
    severity_thresholds block (low / moderate / high / critical) calibrated from WVS data
    and tradition-specific literature; React frontend gains a Fairness Heatmap component
    showing severity ratings across all traditions for the same content
30. Cross-cultural equity dashboard — Lens Balance Indicator, Synergy/Conflict Rate Chart,
    Cultural Representation Equity Index (CREI), and Tradition Divergence Map (D3 force
    graph); alerts when one tradition dominates signal output

*Platform infrastructure (Upgrades 31–34):*
31. Persistent job storage — SQLite backend replaces in-memory job dictionary; schema
    covers jobs, results (per-tradition metrics with CIs), and audit_log; enables historical
    tracking and cross-session drift monitoring baseline
32. Full sample data integration — curated per-tradition sample datasets (50 texts per
    tradition, 20 diverse images) with pre-computed reference results for sanity checking
33. Frontend report export — backend renders HTML/PDF from existing html_report.py;
    React Export button triggers download; report template gives cultural lens findings
    equal visual weight to statistical metrics
34. Dataset comparison mode — POST /api/compare endpoint accepting two job_ids or file
    uploads; React "Compare" mode in ConfigPanel; side-by-side per-tradition metric diff

All design decisions remain traceable to the thesis. The Appendix A functions (Figures A1–A9)
are preserved unchanged as the authoritative proof-of-concept implementation. All upgrades
layer on top without replacing them.

> **Note on v3 content.** Upgrades 1–7 are described as "preserved from v3" throughout this
> document, but v3 is not attached. Treat every "carried forward from v3" instruction as
> "implement from scratch using the dataclass signatures, method contracts, and test cases
> specified in this document." The specifications here are authoritative; do not invent behaviour
> not described.

---

## Module dependency order

The project layers cleanly. **No module in an earlier layer may import from a later layer.**

```
utils → frameworks → embeddings → analysis → vision → lenses → scoring → context → metrics → mitigation → evaluation → integration → reporting → api
```

Concretely:
- `utils/` has no ethiviz imports
- `frameworks/` imports only from `utils/`
- `embeddings/` imports from `utils/` and `frameworks/`
- `analysis/` imports from `embeddings/`, `frameworks/`, and `utils/`
- `vision/` imports from `utils/`
- `lenses/` imports from `embeddings/`, `analysis/`, `frameworks/`, and `utils/`
- `scoring/` imports from `lenses/`, `embeddings/`, `frameworks/`, and `utils/`
- `context/` imports from `scoring/`, `frameworks/`, and `utils/`
- `metrics/` imports from `scoring/`, `frameworks/`, and `utils/`  *(Tier 4)*
- `mitigation/` imports from `metrics/`, `scoring/`, `frameworks/`, and `utils/`  *(Tier 4)*
- `evaluation/` imports from `metrics/`, `mitigation/`, `frameworks/`, and `utils/`  *(Tier 4)*
- `integration/` imports from `evaluation/`, `mitigation/`, `metrics/`, and `utils/`  *(Tier 4)*
- `reporting/` imports from all preceding layers
- `api/` imports from all preceding layers

Violating this order will cause circular import errors. Verify the import graph before
proceeding past step 34 (v4) or step 48 (v5) in the build sequence.

---

## Repository structure

```
ethiviz/
├── README.md
├── pyproject.toml
├── LICENSE                                         # Apache 2.0
├── CONTRIBUTING.md
│
├── ethiviz/
│   ├── __init__.py
│   ├── api.py                                      # Analyzer — unified entry point
│   │
│   ├── frameworks/
│   │   ├── __init__.py
│   │   ├── base.py                                 # CulturalFramework, FrameworkRegistry
│   │   ├── loader.py                               # FrameworkLoader
│   │   ├── conflict.py                             # ConflictTaxonomy, ConflictResolver
│   │   ├── compatibility.py                        # CompatibilityMatrix
│   │   ├── wvs_calibration.py                      # WVSWeightCalibrator (Upgrade 6)
│   │   ├── versioning.py                           # FrameworkVersionTracker (Upgrade 19)
│   │   └── builtin/
│   │       ├── western_v1.yaml
│   │       ├── ubuntu_v1.yaml
│   │       ├── confucian_v2.yaml
│   │       ├── islamic_v1.yaml
│   │       ├── indigenous_v1.yaml                  # Tier 4 — Upgrade 28
│   │       ├── buddhist_v1.yaml                    # Tier 4 — Upgrade 28
│   │       └── hindu_v1.yaml                       # Tier 4 — Upgrade 28
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── model.py                                # EmbeddingModel (MiniLM-L12-v2)
│   │   ├── semantic_detector.py                    # SemanticBiasDetector
│   │   ├── prototype_store.py                      # PrototypeStore (read + write-back)
│   │   ├── prototype_learner.py                    # PrototypeLearner (Upgrade 8)
│   │   ├── language_detection.py                   # LanguageDetector (Upgrade 11)
│   │   └── prototypes/
│   │       ├── western_v1_prototypes.yaml
│   │       ├── ubuntu_v1_prototypes.yaml
│   │       ├── confucian_v2_prototypes.yaml
│   │       ├── islamic_v1_prototypes.yaml
│   │       ├── indigenous_v1_prototypes.yaml       # Tier 4 — Upgrade 28
│   │       ├── buddhist_v1_prototypes.yaml         # Tier 4 — Upgrade 28
│   │       └── hindu_v1_prototypes.yaml            # Tier 4 — Upgrade 28
│   │
│   ├── lenses/
│   │   ├── __init__.py
│   │   ├── base.py                                 # EthicalLens ABC, LensScore dataclass
│   │   ├── western.py
│   │   ├── ubuntu.py
│   │   ├── confucian.py
│   │   ├── islamic.py
│   │   ├── indigenous.py                           # Tier 4 — Upgrade 28
│   │   ├── buddhist.py                             # Tier 4 — Upgrade 28
│   │   └── hindu.py                                # Tier 4 — Upgrade 28
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── dual_framework.py                       # DualEthicsFramework (Figure A1)
│   │   ├── image_analysis.py                       # ImageAnalysisResult (Figure A2)
│   │   ├── intersectional.py                       # calculate_intersectional_analysis (A3)
│   │   ├── cultural_inclusion.py                   # cultural_inclusion_index (A4)
│   │   ├── recommendations.py                      # generate_recommendations (A5)
│   │   ├── dignity.py                              # calculate_dignity_preservation (A6)
│   │   ├── demographics.py                         # skin_tone, age, cultural_elements (A7–A9)
│   │   ├── ubuntu_metrics.py                       # Composite diversity metrics (Upgrade 2)
│   │   ├── weat.py                                 # WEAT + iWEAT (Upgrades 3, 16, 17)
│   │   └── weat_lists/
│   │       ├── western_v1.yaml
│   │       ├── ubuntu_v1.yaml
│   │       ├── confucian_v2.yaml
│   │       └── islamic_v1.yaml
│   │
│   ├── vision/                                     # Upgrade 12 — concrete CV pipeline
│   │   ├── __init__.py
│   │   ├── face_detector.py                        # MediaPipe face detection
│   │   ├── skin_tone.py                            # ITA-based Fitzpatrick estimation
│   │   ├── cultural_element_detector.py            # CLIP zero-shot cultural detection
│   │   ├── object_detector.py                      # CLIP zero-shot object detection
│   │   └── backends/
│   │       ├── __init__.py
│   │       ├── base.py                             # FaceAttributeBackend protocol
│   │       └── deepface_backend.py                 # DeepFace gender/age (optional)
│   │
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── base.py                                 # BiasDetector ABC, BiasCandidate
│   │   ├── text.py                                 # TextBiasDetector
│   │   ├── image.py                                # ImageBiasDetector (uses vision/)
│   │   └── multimodal.py                           # MultiModalDetector
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── base.py                                 # ScoredResult, FrameworkScore
│   │   ├── multi_framework.py                      # MultiFrameworkScorer (+ synergy)
│   │   ├── quantifier.py                           # BiasQuantifier
│   │   ├── aggregation.py                          # Aggregation strategies
│   │   ├── confidence.py                           # Bootstrap CI (Upgrade 7)
│   │   ├── calibration.py                          # PlattCalibrator (Upgrade 9)
│   │   └── drift.py                                # DriftMonitor (Upgrade 10)
│   │
│   ├── context/                                    # Upgrade 13
│   │   ├── __init__.py
│   │   ├── deployment.py                           # DeploymentContext dataclass
│   │   ├── weights.py                              # Context-weighted aggregation tables
│   │   └── regulatory.py                           # RegulatoryMapper (Upgrade 15)
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── base.py                                 # BiasReport dataclass
│   │   ├── mitigation.py                           # MitigationAdvisor
│   │   ├── html_report.py                          # BiasReport.to_html()
│   │   ├── json_report.py                          # BiasReport.to_json()
│   │   ├── explainability.py                       # LIME/SHAP (Upgrade 5)
│   │   ├── provenance.py                           # EvidenceChain, ProvenanceRecord
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── aif360_adapter.py
│   │       └── fairlearn_adapter.py
│   │
│   ├── metrics/                                    # Tier 4 — Upgrades 21–22
│   │   ├── __init__.py
│   │   ├── group_fairness.py                       # SPD, DI, EOD, AOD, Theil (Upgrade 21)
│   │   └── individual_fairness.py                  # Consistency, sample distortion (Upgrade 22)
│   │
│   ├── mitigation/                                 # Tier 4 — Upgrades 23–25
│   │   ├── __init__.py
│   │   ├── preprocessing.py                        # Reweighing, DI Remover (Upgrade 23)
│   │   ├── inprocessing.py                         # Adversarial Debiasing, Prejudice Remover (24)
│   │   └── postprocessing.py                       # Calibrated Eq. Odds, Reject Option (25)
│   │
│   ├── evaluation/                                 # Tier 4 — Upgrade 26
│   │   ├── __init__.py
│   │   └── structured_dataset.py                   # CulturalDataset, ModelBiasEvaluator
│   │
│   ├── integration/                                # Tier 4 — Upgrade 27
│   │   ├── __init__.py
│   │   └── sklearn_api.py                          # CulturalBiasTransformer, EthiVizPipeline
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validation.py
│       ├── caching.py
│       ├── types.py
│       ├── batch.py                                # Batch processing (Upgrade 18)
│       └── reproducibility.py                      # ReproducibilityRecord (Upgrade 18)
│
├── tests/
│   ├── conftest.py                                 # mock_embedding_model fixture
│   ├── fixtures/
│   │   ├── sample_text.csv
│   │   ├── sample_images/
│   │   └── custom_framework.yaml
│   ├── test_frameworks.py
│   ├── test_embeddings.py
│   ├── test_prototype_learner.py
│   ├── test_language_detection.py
│   ├── test_lenses.py
│   ├── test_analysis.py
│   ├── test_ubuntu_metrics.py
│   ├── test_weat.py
│   ├── test_vision.py
│   ├── test_conflict.py
│   ├── test_calibration.py
│   ├── test_drift.py
│   ├── test_context.py
│   ├── test_explainability.py
│   ├── test_regulatory.py
│   ├── test_provenance.py
│   ├── test_batch.py
│   ├── test_versioning.py
│   ├── test_confidence.py
│   ├── test_detection.py
│   ├── test_scoring.py
│   ├── test_reporting.py
│   ├── test_api.py
│   ├── test_adapters.py
│   ├── test_group_fairness.py                      # Tier 4 — Upgrade 21
│   ├── test_individual_fairness.py                 # Tier 4 — Upgrade 22
│   ├── test_mitigation_pre.py                      # Tier 4 — Upgrade 23
│   ├── test_mitigation_in.py                       # Tier 4 — Upgrade 24
│   ├── test_mitigation_post.py                     # Tier 4 — Upgrade 25
│   ├── test_structured_dataset.py                  # Tier 4 — Upgrade 26
│   ├── test_sklearn_api.py                         # Tier 4 — Upgrade 27
│   ├── test_extended_traditions.py                 # Tier 4 — Upgrade 28
│   └── test_comparison_mode.py                     # Tier 4 — Upgrade 34
│
├── examples/
│   ├── quickstart.py
│   ├── uci_adult_case_study.py
│   ├── computer_vision_case_study.py
│   ├── weat_demo.py
│   ├── iweat_demo.py
│   ├── conflict_resolution_demo.py
│   ├── explainability_demo.py
│   ├── calibration_demo.py
│   ├── drift_monitoring_demo.py
│   ├── multilingual_demo.py
│   ├── deployment_context_demo.py
│   ├── regulatory_report_demo.py
│   ├── batch_processing_demo.py
│   ├── aif360_parity_demo.py                       # Tier 4 — Upgrades 21–27
│   ├── cultural_traditions_demo.py                 # Tier 4 — Upgrade 28
│   ├── fairness_heatmap_demo.py                    # Tier 4 — Upgrade 29
│   └── dataset_comparison_demo.py                  # Tier 4 — Upgrade 34
│
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── frameworks.md
    ├── lenses.md
    ├── upgrades_v3.md
    ├── upgrades_v4.md
    ├── upgrades_v5.md                              # Tier 4 — all 14 new upgrades
    └── api_reference.md
```

---

## Core data models

All dataclasses from v3 and v4 are preserved. The following additions are made for v5.

### `ethiviz/lenses/base.py` — `LensScore`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class LensScore:
    lens_id: str
    overall_score: float
    calibrated_score: float | None          # None until PlattCalibrator is fitted
    dimension_scores: dict[str, float]
    flagged_items: list[str]
    recommendations: list[str]
    confidence: float
    confidence_interval_95: tuple[float, float]
    bootstrap_n: int
    raw_evidence: dict[str, Any]
    token_attributions: list[tuple[str, float]] = field(default_factory=list)
    semantic_similarity_scores: dict[str, float] = field(default_factory=dict)
    language_detected: str = "en"           # ISO 639-1 code
    prototype_version_hash: str = ""        # SHA-256 prefix of prototype YAML used
```

### `ethiviz/scoring/base.py` — `ScoredResult`

```python
@dataclass
class ScoredResult:
    candidates: list[BiasCandidate]
    framework_scores: list[FrameworkScore]
    consensus_score: float | None
    conflicts: list[FrameworkConflict]
    synergy_amplifications: list[str]        # which lens pairs were amplified
    weat_results: dict[str, WEATTestSuite] | None
    iweat_results: dict[str, iWEATResult] | None
    deployment_context: DeploymentContext | None
    reproducibility: ReproducibilityRecord   # always populated
    metadata: dict[str, Any]

    def generate_report(self) -> BiasReport: ...
    def top_biases(self, n: int = 5) -> list[BiasCandidate]: ...
    def filter_by_framework(self, framework_id: str) -> ScoredResult: ...
```

### Tier 4 additions — `ethiviz/metrics/group_fairness.py` — `GroupFairnessResult`

```python
@dataclass
class TraditionFairnessScore:
    tradition_id: str
    spd: float                                    # Statistical Parity Difference
    disparate_impact: float                       # DI ratio (1.0 = parity)
    equal_opportunity_diff: float                 # EOD
    average_odds_diff: float                      # AOD
    theil_index: float                            # Generalised entropy inequality measure
    mean_difference: float                        # Raw representation gap
    severity: str                                 # "low" | "moderate" | "high" | "critical"
    threshold_source: str                         # e.g., "WVS_wave_7" or "tradition_literature"

@dataclass
class GroupFairnessResult:
    per_tradition: dict[str, TraditionFairnessScore]
    overall_consensus: float | None               # None if traditions significantly disagree
    conflicts: list[str]                          # tradition pairs whose SPD judgements diverge
    mitigation_recommended: list[str]             # tradition IDs where severity >= "high"
```

### Tier 4 additions — `ethiviz/evaluation/structured_dataset.py` — `CulturalDataset`

```python
@dataclass
class CulturalDataset:
    df: pd.DataFrame
    label_col: str
    protected_attrs: dict[str, str]               # attr_name -> tradition_id mapping
    favorable_label: int | str = 1
    unfavorable_label: int | str = 0

    def fairness_metrics(self) -> GroupFairnessResult: ...
    def compare_with(self, other: CulturalDataset) -> dict[str, Any]: ...
```

---

## Prototype YAML specification

Each prototype YAML (`*_prototypes.yaml`) must contain **at least 10 entries** covering the
major bias categories defined in that framework's `bias_criteria` keys.

**Severity** must be one of: `0.25`, `0.50`, `0.75`, `1.00`.

**Category** values must align exactly with the framework's `bias_criteria` keys. Examples:
- `islamic_v1`: `violent_stereotyping`, `islamic_essentialism`, `gender_essentialism`, `orientalism`
- `ubuntu_v1`: `cultural_erasure`, `community_devaluation`, `ubuntu_violation`, `african_essentialism`
- `western_v1`: `racial_bias`, `gender_bias`, `individual_rights_violation`, `stereotyping`
- `confucian_v2`: `hierarchical_disrespect`, `collectivist_harm`, `face_violation`, `relational_bias`

Each entry uses this structure (the `translations` block is added in Upgrade 11/20):

```yaml
# ethiviz/embeddings/prototypes/islamic_v1_prototypes.yaml
prototypes:
  - id: islamic_essentialism_001
    text: "All Muslims are terrorists or support terrorism."
    severity: 1.00
    category: violent_stereotyping
    language: en
    translations:
      ar: "جميع المسلمين إرهابيون أو يدعمون الإرهاب."
      es: "Todos los musulmanes son terroristas o apoyan el terrorismo."
      fr: "Tous les musulmans sont des terroristes ou soutiennent le terrorisme."
      hi: "सभी मुसलमान आतंकवादी हैं या आतंकवाद का समर्थन करते हैं।"
      zh: "所有穆斯林都是恐怖分子或支持恐怖主义。"
  # ... at least 9 more entries covering all bias_criteria categories
```

`PrototypeStore.load(lens_id, language="en")` must accept a `language` parameter and return
the appropriate translation for each prototype. When a translation is missing, fall back to
English and log: `"No '{language}' translation for prototype '{id}' in '{lens_id}'. Falling back
to English. Consider adding a translation."`

---

## `tests/conftest.py` — mock embedding model

The `mock_embedding_model` fixture must be `autouse=True`. It patches
`EmbeddingModel.instance()` to return a deterministic mock that returns
`numpy.zeros((n, 384), dtype=float32)` for any `encode(texts)` call where `n = len(texts)`.
This prevents any test from downloading model weights.

```python
# tests/conftest.py
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_embedding_model():
    mock = MagicMock()
    mock.encode.side_effect = lambda texts: np.zeros(
        (len(texts), 384), dtype=np.float32
    )
    with patch("ethiviz.embeddings.model.EmbeddingModel.instance", return_value=mock):
        yield mock
```

---

## Upgrades 1–7 (v3, implement from scratch)

All seven v3 upgrades must be implemented. v3 source is not attached — derive every
implementation from the dataclass signatures, method contracts, and test cases in this document.

- **Upgrade 1** — `ethiviz/embeddings/` with `EmbeddingModel` (wraps
  `sentence-transformers/all-MiniLM-L12-v2`; expose `MODEL_ID` constant and
  `EmbeddingModel.instance()` singleton), `SemanticBiasDetector`, `PrototypeStore`.
- **Upgrade 2** — `ethiviz/analysis/ubuntu_metrics.py` with `shannon_diversity`,
  `intersectional_diversity`, `representational_specificity`, `ubuntu_composite_score`.
- **Upgrade 3** — `ethiviz/analysis/weat.py` with `WEATAnalyzer`, `WEATResult`,
  `WEATTestSuite` and per-lens YAML word lists under `weat_lists/`.
- **Upgrade 4** — `ethiviz/frameworks/conflict.py` with `ConflictType` (enum),
  `ResolutionStrategy` (enum), `FrameworkConflict`, `ConflictResolver`, `KNOWN_CONFLICTS`
  dict, `DEFAULT_RESOLUTION` dict, `CONFLICT_RATIONALE` dict keyed by `ConflictType`.
- **Upgrade 5** — `ethiviz/reporting/explainability.py` with `LIMETextExplainer`,
  `SHAPTextExplainer`, `TextExplanation`, `ImageExplanation`.
- **Upgrade 6** — `ethiviz/frameworks/wvs_calibration.py` with `WVSWeightCalibrator`,
  `WVSCalibrationResult`, `DIMENSION_TO_WVS` mapping.
- **Upgrade 7** — `ethiviz/scoring/confidence.py` with `bootstrap_text_ci`,
  `bootstrap_image_ci`, `BootstrapCI`.

All four ethical framework YAML files (`western_v1.yaml`, `ubuntu_v1.yaml`,
`confucian_v2.yaml`, `islamic_v1.yaml`) must be fully authored with `bias_criteria`,
`weights`, `validation`, and `metadata` blocks. All four lens implementations
(`WesternLens`, `UbuntuLens`, `ConfucianLens`, `IslamicLens`) must implement
`score(text: str) -> LensScore` with a 70/30 semantic/regex blend, a `use_semantic`
toggle, and stub upgrade classes that raise `NotImplementedError` with thesis-citing messages.
All nine Appendix A functions (Figures A1–A9) must be implemented as described in the
thesis and referenced in the relevant `analysis/` modules.

---

## Upgrade 8 — Active learning loop

**Rationale.** Prototype YAML files are static knowledge that will drift out of date as language
and bias patterns evolve. When the semantic detector produces a similarity score in the
ambiguous range (0.55–0.75 — neither clearly biased nor clearly clean) it has found a case the
prototype collection did not anticipate. An active learning loop surfaces them for expert review
and writes confirmed findings back to the prototype store with full provenance tracking.

### `ethiviz/embeddings/prototype_learner.py`

```python
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml
from ethiviz.embeddings.prototype_store import PrototypeStore, PROTOTYPES_DIR

@dataclass
class UncertainCase:
    """A detection result in the ambiguous similarity range requiring expert review."""
    case_id: str
    lens_id: str
    input_text: str
    bias_score: float
    top_prototype_id: str
    top_prototype_similarity: float
    language: str
    dataset_source: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

@dataclass
class ConfirmedPrototype:
    """An expert-confirmed bias case ready for write-back to prototype store."""
    case_id: str
    lens_id: str
    prototype_id: str         # assigned by expert
    text: str
    severity: float           # 0.0–1.0
    category: str             # bias category matching framework bias_criteria key
    language: str
    confirmed_by: str         # reviewer identifier
    confirmed_at: str
    source_case_id: str       # links back to UncertainCase.case_id
    provenance: dict[str, Any] = field(default_factory=dict)

class PrototypeLearner:
    """
    Active learning loop for prototype store maintenance.

    Collects uncertain detections (similarity 0.55–0.75), queues them for
    expert review, and writes confirmed cases back to the prototype YAML
    with full provenance tracking.

    Every write-back records: who confirmed it, when, what similarity score
    triggered the review, which dataset it came from, and the library version.
    This provenance chain makes the prototype evolution auditable.

    Example:
        >>> learner = PrototypeLearner()
        >>> uncertain = learner.collect_uncertain(lens_scores, dataset_source="news_corpus")
        >>> print(f"{len(uncertain)} cases queued for review")
        12 cases queued for review
        >>> confirmed = ConfirmedPrototype(
        ...     case_id=uncertain[0].case_id,
        ...     lens_id="islamic_v1",
        ...     prototype_id="islamic_essentialism_011",
        ...     text=uncertain[0].input_text,
        ...     severity=0.80,
        ...     category="islamic_essentialism",
        ...     language="en",
        ...     confirmed_by="expert_001",
        ...     confirmed_at=datetime.now(timezone.utc).isoformat(),
        ...     source_case_id=uncertain[0].case_id,
        ... )
        >>> learner.write_back([confirmed])
    """
    UNCERTAINTY_LOWER = 0.55
    UNCERTAINTY_UPPER = 0.75
    QUEUE_DIR = PROTOTYPES_DIR / "review_queue"

    def __init__(self) -> None:
        self.QUEUE_DIR.mkdir(exist_ok=True)

    def collect_uncertain(
        self,
        lens_scores: list[Any],       # list[LensScore]
        dataset_source: str,
        texts: list[str] | None = None,
    ) -> list[UncertainCase]:
        """
        Scan LensScore objects for detections in the uncertainty band.
        Returns UncertainCase objects and persists them to the review queue.
        """
        uncertain = []
        for score in lens_scores:
            for proto_id, sim in score.semantic_similarity_scores.items():
                if self.UNCERTAINTY_LOWER <= sim <= self.UNCERTAINTY_UPPER:
                    case_id = hashlib.sha256(
                        f"{score.lens_id}:{proto_id}:{sim}:{dataset_source}".encode()
                    ).hexdigest()[:16]
                    case = UncertainCase(
                        case_id=case_id,
                        lens_id=score.lens_id,
                        input_text=score.raw_evidence.get("input_text", ""),
                        bias_score=score.overall_score,
                        top_prototype_id=proto_id,
                        top_prototype_similarity=sim,
                        language=score.language_detected,
                        dataset_source=dataset_source,
                    )
                    uncertain.append(case)
        self._persist_queue(uncertain)
        return uncertain

    def get_review_queue(self, lens_id: str | None = None) -> list[UncertainCase]:
        """Load all pending review cases, optionally filtered by lens."""
        cases = []
        for path in self.QUEUE_DIR.glob("*.json"):
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            case = UncertainCase(**data)
            if lens_id is None or case.lens_id == lens_id:
                cases.append(case)
        return cases

    def write_back(self, confirmed: list[ConfirmedPrototype]) -> dict[str, int]:
        """
        Write confirmed prototypes back to the appropriate prototype YAML file.
        Returns {lens_id: n_written} summary.
        Raises ValueError if a prototype_id already exists in the YAML.
        """
        written: dict[str, int] = {}
        by_lens: dict[str, list[ConfirmedPrototype]] = {}
        for c in confirmed:
            by_lens.setdefault(c.lens_id, []).append(c)

        for lens_id, cases in by_lens.items():
            path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            existing_ids = {p["id"] for p in data["prototypes"]}
            new_entries = []
            for c in cases:
                if c.prototype_id in existing_ids:
                    raise ValueError(
                        f"Prototype ID '{c.prototype_id}' already exists in "
                        f"{lens_id}_prototypes.yaml. Use a unique ID."
                    )
                entry = {
                    "id": c.prototype_id,
                    "text": c.text,
                    "severity": c.severity,
                    "category": c.category,
                    "language": c.language,
                    "provenance": {
                        "confirmed_by": c.confirmed_by,
                        "confirmed_at": c.confirmed_at,
                        "source_case_id": c.source_case_id,
                        "active_learning": True,
                        **c.provenance,
                    },
                }
                new_entries.append(entry)
                existing_ids.add(c.prototype_id)

            data["prototypes"].extend(new_entries)
            with path.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

            for c in cases:
                queue_path = self.QUEUE_DIR / f"{c.source_case_id}.json"
                if queue_path.exists():
                    queue_path.unlink()

            written[lens_id] = len(new_entries)
        return written

    def _persist_queue(self, cases: list[UncertainCase]) -> None:
        for case in cases:
            path = self.QUEUE_DIR / f"{case.case_id}.json"
            if not path.exists():
                with path.open("w", encoding="utf-8") as f:
                    json.dump(case.__dict__, f, indent=2, ensure_ascii=False)
```

---

## Upgrade 9 — Score calibration

**Rationale.** Raw lens scores are cosine similarities to prototype embeddings — ordinal, not
probabilistic. Platt scaling maps them to calibrated probabilities using a reference corpus,
making outputs statistically defensible and comparable across datasets and lens versions.

> **Storage.** `CALIBRATION_DIR` defaults to `~/.ethiviz/calibration_data/` (never relative to
> `__file__`). Accept an optional `calibration_dir: Path | None = None` argument in `__init__`.

### `ethiviz/scoring/calibration.py`

```python
from __future__ import annotations
import json
import numpy as np
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CalibrationRecord:
    lens_id: str
    n_positive: int
    n_negative: int
    platt_a: float
    platt_b: float
    calibration_auc: float
    fitted_at: str
    reference_corpus: str

class PlattCalibrator:
    """
    Platt scaling calibration for lens bias scores.

    Maps raw 0.0–1.0 scores to calibrated probabilities via logistic regression
    fit on a reference corpus. After calibration, 0.72 means "in the top ~28%
    most biased texts in the reference corpus", not just "high cosine similarity."

    Calibration data is persisted to ~/.ethiviz/calibration_data/ by default.

    Example:
        >>> cal = PlattCalibrator()
        >>> cal.fit("western_v1", [0.2, 0.8, 0.3, 0.9, 0.1, 0.7],
        ...         [0, 1, 0, 1, 0, 1], "ethiviz_v4_reference")
        >>> cal.calibrate(0.72, "western_v1")
        0.847
    """
    DEFAULT_CALIBRATION_DIR = Path.home() / ".ethiviz" / "calibration_data"

    def __init__(self, calibration_dir: Path | None = None) -> None:
        self.CALIBRATION_DIR = calibration_dir or self.DEFAULT_CALIBRATION_DIR
        self.CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, CalibrationRecord] = {}
        self._params: dict[str, tuple[float, float]] = {}
        self._load_saved()

    def fit(
        self,
        lens_id: str,
        raw_scores: list[float],
        labels: list[int],          # 0 = clean, 1 = biased
        reference_corpus: str,
        test_fraction: float = 0.2,
        random_seed: int = 42,
    ) -> CalibrationRecord:
        """Fit Platt parameters via logistic regression. Persists to disk."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score
        from datetime import datetime, timezone

        X = np.array(raw_scores).reshape(-1, 1)
        y = np.array(labels)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_fraction, random_state=random_seed, stratify=y
        )
        lr = LogisticRegression()
        lr.fit(X_train, y_train)
        a = float(lr.coef_[0][0])
        b = float(lr.intercept_[0])
        auc = float(roc_auc_score(y_test, lr.predict_proba(X_test)[:, 1]))

        record = CalibrationRecord(
            lens_id=lens_id,
            n_positive=int(np.sum(y == 1)),
            n_negative=int(np.sum(y == 0)),
            platt_a=a, platt_b=b,
            calibration_auc=auc,
            fitted_at=datetime.now(timezone.utc).isoformat(),
            reference_corpus=reference_corpus,
        )
        self._records[lens_id] = record
        self._params[lens_id] = (a, b)
        self._save(lens_id, record)
        return record

    def calibrate(self, raw_score: float, lens_id: str) -> float:
        """
        Apply Platt calibration. Returns probability in [0.0, 1.0].
        Raises RuntimeError if not fitted for this lens.
        """
        if lens_id not in self._params:
            raise RuntimeError(
                f"Calibrator not fitted for lens '{lens_id}'. "
                f"Call fit() first. Fitted lenses: {list(self._params.keys())}"
            )
        a, b = self._params[lens_id]
        return float(1.0 / (1.0 + np.exp(-(a * raw_score + b))))

    def calibrate_batch(self, raw_scores: list[float], lens_id: str) -> list[float]:
        return [self.calibrate(s, lens_id) for s in raw_scores]

    def is_fitted(self, lens_id: str) -> bool:
        return lens_id in self._params

    def _save(self, lens_id: str, record: CalibrationRecord) -> None:
        path = self.CALIBRATION_DIR / f"{lens_id}_calibration.json"
        with path.open("w") as f:
            json.dump(record.__dict__, f, indent=2)

    def _load_saved(self) -> None:
        for path in self.CALIBRATION_DIR.glob("*_calibration.json"):
            with path.open() as f:
                data = json.load(f)
            record = CalibrationRecord(**data)
            self._records[record.lens_id] = record
            self._params[record.lens_id] = (record.platt_a, record.platt_b)
```

`LensScore.calibrated_score` is `None` when no calibrator is available, float otherwise.
The `Analyzer` applies calibration automatically when a `PlattCalibrator` has been fitted.
The HTML report displays both raw and calibrated scores, with a note when unfitted.

---

## Upgrade 10 — Drift monitoring

**Rationale.** The thesis section 1.1 identifies data drift as a known failure mode. A
`DriftMonitor` storing score distributions over time and alerting on KL-divergence exceedance
turns EthiViz from a point-in-time audit tool into a continuous monitoring system.

> **Storage.** `SNAPSHOT_DIR` defaults to `~/.ethiviz/drift_snapshots/`. Accept an optional
> `snapshot_dir: Path | None = None` argument in `__init__`.

### `ethiviz/scoring/drift.py`

```python
from __future__ import annotations
import json
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from scipy.special import rel_entr

@dataclass
class ScoreSnapshot:
    lens_id: str
    snapshot_id: str
    dataset_source: str
    scores: list[float]
    mean: float
    std: float
    histogram: list[float]           # 10-bin normalised histogram
    histogram_bin_edges: list[float]
    n_samples: int
    recorded_at: str

@dataclass
class DriftAlert:
    lens_id: str
    baseline_snapshot_id: str
    current_snapshot_id: str
    kl_divergence: float
    threshold: float
    drift_detected: bool
    interpretation: str
    recommended_action: str

class DriftMonitor:
    """
    Temporal drift detection for bias score distributions.

    Records score distribution snapshots and computes KL divergence against a
    stored baseline. Implements the ADWIN conceptual approach from thesis
    section 6.1.1, using KL divergence rather than a sliding window mean.

    Snapshots are stored in ~/.ethiviz/drift_snapshots/ by default.

    Example:
        >>> monitor = DriftMonitor()
        >>> monitor.record_snapshot("western_v1", [0.2, 0.3, 0.25],
        ...                         "corpus_jan", set_as_baseline=True)
        >>> alert = monitor.check_drift("western_v1", [0.7, 0.75, 0.8], "corpus_jul")
        >>> alert.drift_detected
        True
    """
    DEFAULT_SNAPSHOT_DIR = Path.home() / ".ethiviz" / "drift_snapshots"
    DEFAULT_THRESHOLD = 0.10
    N_BINS = 10

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        snapshot_dir: Path | None = None,
    ) -> None:
        self.threshold = threshold
        self.SNAPSHOT_DIR = snapshot_dir or self.DEFAULT_SNAPSHOT_DIR
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def record_snapshot(
        self,
        lens_id: str,
        scores: list[float],
        dataset_source: str,
        set_as_baseline: bool = False,
    ) -> ScoreSnapshot:
        arr = np.array(scores, dtype=float)
        hist, edges = np.histogram(arr, bins=self.N_BINS, range=(0.0, 1.0))
        hist_norm = hist / (hist.sum() + 1e-8)
        snapshot = ScoreSnapshot(
            lens_id=lens_id,
            snapshot_id=f"{lens_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
            dataset_source=dataset_source,
            scores=scores,
            mean=float(arr.mean()),
            std=float(arr.std()),
            histogram=hist_norm.tolist(),
            histogram_bin_edges=edges.tolist(),
            n_samples=len(scores),
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save_snapshot(snapshot, is_baseline=set_as_baseline)
        return snapshot

    def check_drift(
        self,
        lens_id: str,
        current_scores: list[float],
        dataset_source: str,
    ) -> DriftAlert:
        """
        Compare current scores against the stored baseline.
        Raises RuntimeError if no baseline exists for this lens.
        """
        baseline = self._load_baseline(lens_id)
        if baseline is None:
            raise RuntimeError(
                f"No baseline snapshot for lens '{lens_id}'. "
                f"Call record_snapshot(..., set_as_baseline=True) first."
            )
        current = self.record_snapshot(lens_id, current_scores, dataset_source)

        p = np.array(baseline.histogram) + 1e-8
        q = np.array(current.histogram) + 1e-8
        p /= p.sum()
        q /= q.sum()
        kl = float(np.sum(rel_entr(p, q)))

        drift_detected = kl > self.threshold
        mean_delta = current.mean - baseline.mean

        if not drift_detected:
            interpretation = (
                f"No significant drift detected (KL={kl:.3f} ≤ threshold={self.threshold}). "
                f"Score distribution is stable relative to baseline."
            )
            action = "Continue monitoring. No action required."
        elif mean_delta > 0:
            interpretation = (
                f"Significant distribution shift detected (KL={kl:.3f} > threshold={self.threshold}). "
                f"Current mean ({current.mean:.3f}) is higher than baseline ({baseline.mean:.3f}), "
                f"suggesting increased bias or new patterns not covered by current prototypes."
            )
            action = (
                f"Review prototype store for the '{lens_id}' lens. "
                "Consider running PrototypeLearner.collect_uncertain() on the current "
                "dataset. Re-calibrate PlattCalibrator if previously fitted."
            )
        else:
            interpretation = (
                f"Significant distribution shift detected (KL={kl:.3f} > threshold={self.threshold}). "
                f"Current scores are lower than baseline, possibly indicating improvement "
                f"or model changes affecting detection sensitivity."
            )
            action = (
                "Investigate whether dataset composition has changed or upstream "
                "model changes have affected bias detection sensitivity."
            )

        return DriftAlert(
            lens_id=lens_id,
            baseline_snapshot_id=baseline.snapshot_id,
            current_snapshot_id=current.snapshot_id,
            kl_divergence=kl,
            threshold=self.threshold,
            drift_detected=drift_detected,
            interpretation=interpretation,
            recommended_action=action,
        )

    def _save_snapshot(self, snapshot: ScoreSnapshot, is_baseline: bool) -> None:
        path = self.SNAPSHOT_DIR / f"{snapshot.snapshot_id}.json"
        with path.open("w") as f:
            json.dump(snapshot.__dict__, f, indent=2)
        if is_baseline:
            baseline_path = self.SNAPSHOT_DIR / f"{snapshot.lens_id}_baseline.json"
            with baseline_path.open("w") as f:
                json.dump(snapshot.__dict__, f, indent=2)

    def _load_baseline(self, lens_id: str) -> ScoreSnapshot | None:
        path = self.SNAPSHOT_DIR / f"{lens_id}_baseline.json"
        if not path.exists():
            return None
        with path.open() as f:
            data = json.load(f)
        return ScoreSnapshot(**data)
```

---

## Upgrade 11 — Multilingual pipeline

**Rationale.** The thesis claims support for English, Arabic, Mandarin, Spanish, Hindi, and French.
MiniLM supports all six, but v3 prototypes are English-only. Cross-lingual embedding alignment
is imperfect — an Arabic sentence semantically identical to an English prototype will score lower
due to alignment noise. The fix: detect language, load language-appropriate prototypes, and
use script-aware tokenisation for LIME/SHAP so non-Latin-script visualisations are meaningful.

### `ethiviz/embeddings/language_detection.py`

```python
from __future__ import annotations
from dataclasses import dataclass

SUPPORTED_LANGUAGES = {
    "en": "English", "ar": "Arabic", "zh": "Mandarin",
    "es": "Spanish", "hi": "Hindi",  "fr": "French",
}

SCRIPT_TOKENIZERS = {
    "zh": "jieba", "ar": "stanza", "hi": "stanza",
    "en": "whitespace", "es": "whitespace", "fr": "whitespace",
}

@dataclass
class LanguageDetectionResult:
    language_code: str       # ISO 639-1
    language_name: str
    confidence: float
    script: str              # "latin" | "arabic" | "chinese" | "devanagari"
    tokenizer_required: str

class LanguageDetector:
    """
    Language detection for all lens scoring. Uses langdetect with a fixed seed
    for reproducibility. Falls back to English for unsupported languages.

    Example:
        >>> d = LanguageDetector()
        >>> r = d.detect("جميع المسلمين يدعمون العنف")
        >>> r.language_code, r.script, r.tokenizer_required
        ('ar', 'arabic', 'stanza')
    """
    def detect(self, text: str) -> LanguageDetectionResult:
        try:
            from langdetect import detect as _detect, DetectorFactory
            DetectorFactory.seed = 42
            code = _detect(text)
        except Exception:
            code = "en"
        if code not in SUPPORTED_LANGUAGES:
            code = "en"
        script = {"ar": "arabic", "zh": "chinese", "hi": "devanagari"}.get(code, "latin")
        return LanguageDetectionResult(
            language_code=code,
            language_name=SUPPORTED_LANGUAGES[code],
            confidence=0.90,
            script=script,
            tokenizer_required=SCRIPT_TOKENIZERS.get(code, "whitespace"),
        )
```

### Script-aware tokenisation (`ScriptAwareTokenizer`)

Add to `ethiviz/reporting/explainability.py`. The `LIMETextExplainer` must use this class
before running its perturbation loop. LIME's default whitespace split produces meaningless
single-character tokens for Mandarin and broken morphemes for Arabic/Hindi.

```python
class ScriptAwareTokenizer:
    def tokenize(self, text: str, script: str) -> list[str]:
        if script == "chinese":
            try:
                import jieba
                return list(jieba.cut(text))
            except ImportError:
                raise ImportError("pip install ethiviz[multilingual]")
        elif script in ("arabic", "devanagari"):
            try:
                import stanza
                lang = "ar" if script == "arabic" else "hi"
                nlp = stanza.Pipeline(lang, processors="tokenize", verbose=False)
                doc = nlp(text)
                return [w.text for sent in doc.sentences for w in sent.words]
            except ImportError:
                raise ImportError("pip install ethiviz[multilingual]")
        else:
            return text.split()
```

---

## Upgrade 12 — Concrete computer vision pipeline

**Rationale.** v3 `demographics.py` uses mock values with no production implementation.
Case Study 2 (intersectional bias in CV systems) requires real demographic analysis of images.

**Design constraints:** CPU-only (no GPU required), no proprietary API keys, all components
implement pluggable protocols so users can substitute their own models.

### `ethiviz/vision/face_detector.py`

```python
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class DetectedFace:
    bounding_box: tuple[int, int, int, int]    # (x, y, w, h)
    confidence: float
    face_image: np.ndarray                     # cropped face region, RGB (H, W, 3)

class MediaPipeFaceDetector:
    """CPU face detection via Google MediaPipe. Requires: pip install ethiviz[vision]"""
    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        try:
            import mediapipe as mp
            self._detector = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=min_detection_confidence
            )
        except ImportError:
            raise ImportError("mediapipe required: pip install ethiviz[vision]")

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        results = self._detector.process(image)
        faces = []
        if not results.detections:
            return faces
        h, w = image.shape[:2]
        for det in results.detections:
            bb = det.location_data.relative_bounding_box
            x = max(0, int(bb.xmin * w))
            y = max(0, int(bb.ymin * h))
            fw = min(int(bb.width * w), w - x)
            fh = min(int(bb.height * h), h - y)
            faces.append(DetectedFace(
                bounding_box=(x, y, fw, fh),
                confidence=det.score[0] if det.score else 0.0,
                face_image=image[y:y + fh, x:x + fw],
            ))
        return faces
```

### `ethiviz/vision/skin_tone.py`

```python
from __future__ import annotations
import numpy as np
from dataclasses import dataclass

FITZPATRICK_SCALE = {
    "Type_I": "Very light", "Type_II": "Light", "Type_III": "Medium light",
    "Type_IV": "Medium",    "Type_V": "Medium dark", "Type_VI": "Dark",
}

# ITA thresholds: (lower_bound, Fitzpatrick_type). Evaluated highest-first.
ITA_THRESHOLDS = [
    (55.0, "Type_I"), (41.0, "Type_II"), (28.0, "Type_III"),
    (10.0, "Type_IV"), (-30.0, "Type_V"), (-90.0, "Type_VI"),
]

@dataclass
class SkinToneEstimate:
    fitzpatrick_type: str
    description: str
    ita_value: float
    confidence: float

class ITASkinToneEstimator:
    """
    Fitzpatrick skin tone estimation via Individual Typology Angle (ITA).
    ITA = arctan((L* − 50) / b*) × (180 / π). No trained model required.
    Published method: Del Bino et al. (2006). Requires: pip install ethiviz[vision]
    """
    def estimate(self, face_image: np.ndarray) -> SkinToneEstimate:
        try:
            import cv2
        except ImportError:
            raise ImportError("opencv-python required: pip install ethiviz[vision]")

        lab = cv2.cvtColor(face_image, cv2.COLOR_RGB2LAB).astype(float)
        mask = lab[:, :, 0] > 20
        if mask.sum() < 10:
            return SkinToneEstimate("Type_IV", "Medium", 10.0, 0.3)

        L_mean = float(lab[mask, 0].mean()) * (100.0 / 255.0)
        b_mean = float(lab[mask, 2].mean()) - 128.0

        ita = (90.0 if L_mean > 50 else -90.0) if abs(b_mean) < 1e-3 else \
              float(np.degrees(np.arctan((L_mean - 50.0) / b_mean)))

        fitz_type = "Type_VI"
        for threshold, ftype in ITA_THRESHOLDS:
            if ita >= threshold:
                fitz_type = ftype
                break

        return SkinToneEstimate(
            fitzpatrick_type=fitz_type,
            description=FITZPATRICK_SCALE[fitz_type],
            ita_value=ita,
            confidence=0.80 if mask.sum() > 100 else 0.50,
        )
```

### `ethiviz/vision/cultural_element_detector.py`

```python
from __future__ import annotations
from dataclasses import dataclass

CULTURAL_ELEMENT_QUERIES = {
    "religious_symbols": [
        "hijab", "niqab", "turban", "kippah", "cross", "crucifix",
        "prayer beads", "rosary", "bindi", "tilak", "Buddhist robes",
    ],
    "cultural_clothing": [
        "sari", "kimono", "hanbok", "dashiki", "kente cloth",
        "cheongsam", "thobe", "dirndl", "kufi",
    ],
    "cultural_landmarks": [
        "mosque", "temple", "cathedral", "synagogue", "pagoda", "shrine", "stupa",
    ],
}

@dataclass
class CulturalElementResult:
    found_elements: dict[str, list[str]]
    essentialism_risk: dict[str, float]
    cultural_landmarks: list[str]
    diversity_count: int

class CLIPCulturalDetector:
    """
    Zero-shot cultural element detection via OpenAI CLIP.
    CPU-capable. No training data, no API key.
    Requires: pip install ethiviz[vision]
    """
    def __init__(self, confidence_threshold: float = 0.25) -> None:
        self.threshold = confidence_threshold
        self._model = None
        self._processor = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        except ImportError:
            raise ImportError("transformers required: pip install ethiviz[vision]")

    def detect(self, image: "np.ndarray") -> CulturalElementResult:
        import torch
        from PIL import Image as PILImage
        self._load_model()

        pil_image = PILImage.fromarray(image)
        found: dict[str, list[str]] = {cat: [] for cat in CULTURAL_ELEMENT_QUERIES}

        for category, queries in CULTURAL_ELEMENT_QUERIES.items():
            inputs = self._processor(text=queries, images=pil_image,
                                     return_tensors="pt", padding=True)
            with torch.no_grad():
                logits = self._model(**inputs).logits_per_image[0]
            probs = logits.softmax(dim=0).tolist()
            for item, prob in zip(queries, probs):
                if prob >= self.threshold:
                    found[category].append(item)

        essentialism_risk = {
            cat: (0.7 if len(items) == 1 else 0.0 if len(items) == 0
                  else max(0.0, 0.7 - (len(items) - 1) * 0.15))
            for cat, items in found.items()
        }
        return CulturalElementResult(
            found_elements=found,
            essentialism_risk=essentialism_risk,
            cultural_landmarks=found.get("cultural_landmarks", []),
            diversity_count=sum(len(v) for v in found.values()),
        )
```

### `ethiviz/vision/backends/base.py`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class FaceAttributeBackend(Protocol):
    def predict_gender(self, face_image: "np.ndarray") -> dict[str, float]:
        """Returns {"male": p, "female": p} probabilities."""
        ...
    def predict_age_group(self, face_image: "np.ndarray") -> dict[str, float]:
        """Returns {"child": p, "young_adult": p, "adult": p, ...} probabilities."""
        ...
```

### Updated `ethiviz/analysis/demographics.py`

```python
from ethiviz.vision.face_detector import MediaPipeFaceDetector
from ethiviz.vision.skin_tone import ITASkinToneEstimator

def compute_skin_tone_distribution(image: "np.ndarray") -> dict[str, float]:
    """Detect faces, estimate Fitzpatrick type per face, return normalised distribution."""
    faces = MediaPipeFaceDetector().detect(image)
    if not faces:
        return {}
    counts: dict[str, int] = {}
    for face in faces:
        est = ITASkinToneEstimator().estimate(face.face_image)
        counts[est.description] = counts.get(est.description, 0) + 1
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}
```

---

## Upgrades 13 & 14 — Deployment context and synergy amplification

### `ethiviz/context/deployment.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class DeploymentContext:
    """
    Encodes the cultural and regulatory context of a deployment.

    Example:
        >>> ctx = DeploymentContext(
        ...     region="NG", domain="hiring",
        ...     primary_community="african", regulatory_framework="gdpr"
        ... )
    """
    region: str                  # ISO 3166-1 alpha-2 country code
    domain: str                  # "hiring"|"healthcare"|"content_moderation"
                                 # |"education"|"finance"|"general"
    primary_community: str       # "african"|"east_asian"|"muslim_majority"
                                 # |"western"|"south_asian"|"global"
    regulatory_framework: str    # "gdpr"|"ccpa"|"eu_ai_act"|"none"
    additional_regulations: list[str] = field(default_factory=list)
    notes: str = ""
```

### `ethiviz/context/weights.py`

```python
from __future__ import annotations

CONTEXT_WEIGHTS: dict[tuple[str, str], dict[str, float]] = {
    ("african", "hiring"):              {"ubuntu_v1": 0.40, "western_v1": 0.25, "confucian_v2": 0.10, "islamic_v1": 0.25},
    ("african", "healthcare"):          {"ubuntu_v1": 0.45, "western_v1": 0.25, "confucian_v2": 0.05, "islamic_v1": 0.25},
    ("east_asian", "education"):        {"confucian_v2": 0.40, "western_v1": 0.25, "ubuntu_v1": 0.15, "islamic_v1": 0.20},
    ("east_asian", "hiring"):           {"confucian_v2": 0.40, "western_v1": 0.30, "ubuntu_v1": 0.15, "islamic_v1": 0.15},
    ("muslim_majority", "hiring"):      {"islamic_v1": 0.40, "western_v1": 0.25, "ubuntu_v1": 0.20, "confucian_v2": 0.15},
    ("muslim_majority", "content_moderation"): {"islamic_v1": 0.45, "western_v1": 0.25, "ubuntu_v1": 0.20, "confucian_v2": 0.10},
    ("western", "hiring"):              {"western_v1": 0.45, "ubuntu_v1": 0.25, "confucian_v2": 0.15, "islamic_v1": 0.15},
    ("global", "general"):              {"western_v1": 0.25, "ubuntu_v1": 0.25, "confucian_v2": 0.25, "islamic_v1": 0.25},
}

def get_weights(context: "DeploymentContext") -> dict[str, float]:
    """Look up context-specific weights; falls back to equal weighting."""
    key = (context.primary_community, context.domain)
    if key in CONTEXT_WEIGHTS:
        return CONTEXT_WEIGHTS[key]
    community_key = (context.primary_community, "general")
    if community_key in CONTEXT_WEIGHTS:
        return CONTEXT_WEIGHTS[community_key]
    return {"western_v1": 0.25, "ubuntu_v1": 0.25, "confucian_v2": 0.25, "islamic_v1": 0.25}
```

### Upgrade 14 — Synergy amplification (`ethiviz/scoring/multi_framework.py`)

```python
SYNERGY_PAIRS = [
    ("ubuntu_v1", "islamic_v1"),    # Both sensitive to essentialism
    ("ubuntu_v1", "confucian_v2"),  # Both emphasise communal harmony
    ("confucian_v2", "islamic_v1"), # Both balance individual/collective
]
SYNERGY_AMPLIFICATION_FACTOR = 1.15   # 15% amplification when pair agrees

def _apply_synergy_amplification(
    framework_scores: list["FrameworkScore"],
    threshold: float = 0.50,
) -> tuple[list["FrameworkScore"], list[str]]:
    """
    Amplify both scores in a synergy pair when both exceed threshold (cap at 1.0).
    Rationale: two independent philosophical traditions converging on the same harm
    is stronger evidence than one tradition alone.
    Returns (updated_scores, list_of_amplified_pair_descriptions).
    """
    score_map = {fs.framework_id: fs for fs in framework_scores}
    amplified_pairs: list[str] = []
    for lens_a, lens_b in SYNERGY_PAIRS:
        if lens_a not in score_map or lens_b not in score_map:
            continue
        if score_map[lens_a].overall_score >= threshold and score_map[lens_b].overall_score >= threshold:
            score_map[lens_a] = _amplify(score_map[lens_a])
            score_map[lens_b] = _amplify(score_map[lens_b])
            amplified_pairs.append(
                f"{lens_a} + {lens_b} (both ≥ {threshold:.2f}; "
                f"convergent signal amplified by {int((SYNERGY_AMPLIFICATION_FACTOR-1)*100)}%)"
            )
    return list(score_map.values()), amplified_pairs

def _amplify(fs: "FrameworkScore") -> "FrameworkScore":
    import dataclasses
    return dataclasses.replace(fs, overall_score=min(1.0, fs.overall_score * SYNERGY_AMPLIFICATION_FACTOR))
```

---

## Upgrade 15 — Regulatory mapper and evidence provenance

**Rationale.** Ethics officers and auditors think in terms of regulatory obligations, not lens scores.
The regulatory mapper translates EthiViz findings into specific obligations under EU AI Act,
GDPR, and CCPA.

> **Region-based condition.** The `_conditions_met` method must fully implement `region_in_`
> conditions. Parse `"region_in_US,CA"` as: check `context.region in {"US", "CA"}`. Do not
> leave this branch as `pass` — it silently skips CCPA triggers for all non-EU deployments.

### `ethiviz/context/regulatory.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class RegulatoryObligation:
    regulation: str
    article: str
    obligation_text: str
    triggered_by: list[str]
    severity: str               # "critical"|"high"|"medium"|"informational"
    recommended_action: str
    evidence_chain: list[str]

@dataclass
class ComplianceMapping:
    deployment_context: "DeploymentContext"
    obligations: list[RegulatoryObligation]
    overall_compliance_risk: str    # "critical"|"high"|"medium"|"low"
    disclaimer: str = (
        "This mapping is informational only and does not constitute legal advice. "
        "Consult a qualified legal professional for compliance decisions."
    )

REGULATORY_RULES: list[dict[str, Any]] = [
    {
        "regulation": "EU_AI_Act", "article": "Article 10(2)",
        "trigger_conditions": ["racial_profiling_score > 0.5", "demographic_imbalance"],
        "obligation": (
            "High-risk AI systems must use training, validation, and testing data sets "
            "that are relevant, sufficiently representative, and free of errors. "
            "Detected demographic imbalances may indicate non-compliance."
        ),
        "severity": "critical",
        "action": "Conduct a data governance review. Apply re-weighting or re-sampling.",
    },
    {
        "regulation": "EU_AI_Act", "article": "Article 13",
        "trigger_conditions": ["overall_bias_score > 0.3"],
        "obligation": (
            "High-risk AI systems shall be sufficiently transparent to enable "
            "deployers to interpret the system's output appropriately."
        ),
        "severity": "high",
        "action": "Document bias detection results. Use EthiViz provenance chains.",
    },
    {
        "regulation": "GDPR", "article": "Article 22",
        "trigger_conditions": ["automated_decision_making", "demographic_bias_detected"],
        "obligation": (
            "Data subjects have the right not to be subject to decisions based "
            "solely on automated processing with legal or significant effects."
        ),
        "severity": "critical",
        "action": "Implement human oversight for automated decisions where bias is detected.",
    },
    {
        "regulation": "GDPR", "article": "Article 5(1)(f)",
        "trigger_conditions": ["dignity_violation_score > 0.5"],
        "obligation": (
            "Personal data shall be processed with appropriate security and integrity. "
            "Dignity violations may indicate inadequate safeguards for sensitive data."
        ),
        "severity": "high",
        "action": "Review data processing agreements for sensitive data categories.",
    },
    {
        "regulation": "CCPA", "article": "Section 1798.100",
        "trigger_conditions": ["demographic_bias_detected", "region_in_US,CA"],
        "obligation": (
            "Consumers have the right to know about personal information collected "
            "and how it affects decisions made about them."
        ),
        "severity": "medium",
        "action": "Update privacy policy. Provide opt-out mechanism for data sale.",
    },
    {
        "regulation": "EU_AI_Act", "article": "Article 9",
        "trigger_conditions": ["weat_effect_size > 0.8"],
        "obligation": (
            "Providers of high-risk AI systems shall maintain a risk management system "
            "throughout the entire lifecycle. High WEAT effect sizes require documentation."
        ),
        "severity": "high",
        "action": "Document WEAT findings. Implement mitigation measures before deployment.",
    },
]

class RegulatoryMapper:
    """
    Maps EthiViz findings to regulatory obligations. Not legal advice.

    Example:
        >>> mapper = RegulatoryMapper()
        >>> mapping = mapper.map(scored_result, ctx)
        >>> [o.article for o in mapping.obligations]
        ['Article 10(2)', 'Article 22']
    """
    def map(self, scored_result: Any, context: "DeploymentContext") -> ComplianceMapping:
        applicable = self._get_applicable_regulations(context)
        findings = self._extract_findings(scored_result)
        obligations = []

        for rule in REGULATORY_RULES:
            if rule["regulation"] not in applicable:
                continue
            if self._conditions_met(rule["trigger_conditions"], findings, context):
                triggered_by = self._identify_triggers(rule["trigger_conditions"], findings)
                evidence = self._build_evidence_chain(triggered_by, scored_result)
                obligations.append(RegulatoryObligation(
                    regulation=rule["regulation"],
                    article=rule["article"],
                    obligation_text=rule["obligation"],
                    triggered_by=triggered_by,
                    severity=rule["severity"],
                    recommended_action=rule["action"],
                    evidence_chain=evidence,
                ))

        severity_order = {"critical": 0, "high": 1, "medium": 2, "informational": 3}
        obligations.sort(key=lambda o: severity_order.get(o.severity, 99))

        return ComplianceMapping(
            deployment_context=context,
            obligations=obligations,
            overall_compliance_risk=self._overall_risk(obligations),
        )

    def _get_applicable_regulations(self, context: "DeploymentContext") -> set[str]:
        regs = {context.regulatory_framework.upper().replace("-", "_")}
        regs.update(r.upper() for r in context.additional_regulations)
        if context.region in ("US", "CA") or context.regulatory_framework == "ccpa":
            regs.add("CCPA")
        return regs

    def _extract_findings(self, result: Any) -> dict[str, Any]:
        scores = {fs.framework_id: fs.overall_score for fs in result.framework_scores}
        return {
            "overall_bias_score": max(scores.values()) if scores else 0.0,
            "demographic_bias_detected": scores.get("western_v1", 0) > 0.3,
            "dignity_violation_score": (
                result.framework_scores[3].dimension_scores.get("karamah_preservation", 1.0)
                if len(result.framework_scores) > 3 else 0.0
            ),
            "weat_effect_size": max(
                (abs(r.effect_size) for suite in (result.weat_results or {}).values()
                 for r in suite.results), default=0.0
            ),
            "racial_profiling_score": scores.get("western_v1", 0),
            "demographic_imbalance": any(
                fs.dimension_scores.get("group_harmony_score", 1.0) < 0.6
                for fs in result.framework_scores
            ),
        }

    def _conditions_met(
        self,
        conditions: list[str],
        findings: dict[str, Any],
        context: "DeploymentContext | None" = None,
    ) -> bool:
        for cond in conditions:
            if ">" in cond:
                key, val = cond.split(">")
                if findings.get(key.strip(), 0) <= float(val.strip()):
                    return False
            elif cond.startswith("region_in_"):
                # "region_in_US,CA" → check context.region in {"US", "CA"}
                allowed = set(cond[len("region_in_"):].split(","))
                if context is None or context.region not in allowed:
                    return False
            elif not findings.get(cond, False):
                return False
        return True

    def _identify_triggers(self, conditions: list[str], findings: dict) -> list[str]:
        return [c for c in conditions if findings.get(c.split(">")[0].strip(), False)]

    def _build_evidence_chain(self, triggers: list[str], result: Any) -> list[str]:
        chain = []
        for fs in result.framework_scores:
            for item in fs.flagged_candidates[:3]:
                chain.append(f"{fs.framework_id}:{item}")
        if result.weat_results:
            for suite in result.weat_results.values():
                for r in suite.tests_flagged[:2]:
                    chain.append(f"WEAT:{r}")
        return chain[:10]

    def _overall_risk(self, obligations: list[RegulatoryObligation]) -> str:
        for level in ("critical", "high", "medium"):
            if any(o.severity == level for o in obligations):
                return level
        return "low"
```

### `ethiviz/reporting/provenance.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class EvidenceItem:
    evidence_type: str       # "prototype_match"|"weat_test"|"co_occurrence"
                             # |"demographic_imbalance"|"dignity_violation"
    evidence_id: str
    evidence_text: str
    similarity_or_score: float
    lens_id: str
    language: str

@dataclass
class ProvenanceRecord:
    """
    Full provenance chain for one bias finding.
    Included in BiasReport.to_html() as an expandable <details> section.
    """
    finding_summary: str
    lens_scores: dict[str, float]
    evidence_items: list[EvidenceItem]
    prototype_versions: dict[str, str]       # lens_id → YAML hash at analysis time
    weat_results_summary: list[str]
    conflict_summary: list[str]
    calibration_applied: bool
    confidence_intervals: dict[str, tuple[float, float]]
    reproducibility_id: str
```

---

## Upgrades 16 & 17 — Intersectional WEAT and benchmark validation

### Upgrade 16 — iWEAT (`ethiviz/analysis/weat.py`)

**Rationale.** The original WEAT tests one dimension at a time. iWEAT measures compound
bias at identity intersections — an original methodological contribution of this thesis.

> **Key ordering contract.** `iWEATAnalyzer.run()` requires exactly 4 identity combinations
> in a 2×2 design. The compound effect computation assumes insertion-order positions:
> `[0]` = focal×dim1 (e.g. Black woman), `[1]` = focal×dim2 (Black man),
> `[2]` = other×dim1 (white woman), `[3]` = other×dim2 (white man).
> Validate `len(identity_combinations) == 4` and raise `ValueError` if not.
> Document the required ordering prominently in the docstring.

```python
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from itertools import combinations

@dataclass
class iWEATResult:
    test_name: str
    lens_id: str
    identity_combinations: list[str]
    individual_effects: dict[str, float]
    combination_effects: dict[str, float]
    compound_effect: float
    p_value: float
    confidence_interval_95: tuple[float, float]
    interpretation: str

class iWEATAnalyzer:
    """
    Intersectional WEAT. Extends Caliskan et al. (2017) to measure compound bias.

    Requires exactly 4 identity combinations in this canonical order:
      {"focal_group_dim1": [...], "focal_group_dim2": [...],
       "other_group_dim1": [...], "other_group_dim2": [...]}
    Example canonical order:
      {"Black_woman": [...], "Black_man": [...],
       "white_woman": [...], "white_man": [...]}

    Passing keys in a different order silently changes the sign of compound_effect.
    Use the canonical ordering consistently.
    """
    def __init__(self, n_permutations: int = 5_000) -> None:
        self.n_permutations = n_permutations

    def run(
        self,
        test_name: str,
        lens_id: str,
        identity_combinations: dict[str, list[str]],
        attribute_x: list[str],
        attribute_y: list[str],
    ) -> iWEATResult:
        if len(identity_combinations) != 4:
            raise ValueError(
                "iWEAT requires exactly 4 identity combinations for a 2×2 design. "
                f"Got {len(identity_combinations)}."
            )
        from ethiviz.embeddings.model import EmbeddingModel
        model = EmbeddingModel.instance()

        combo_embeddings = {
            label: model.encode(terms).mean(axis=0)
            for label, terms in identity_combinations.items()
        }
        ax_embs = model.encode(attribute_x)
        ay_embs = model.encode(attribute_y)

        def assoc(emb: np.ndarray) -> float:
            return float(np.dot(ax_embs, emb).mean()) - float(np.dot(ay_embs, emb).mean())

        assocs = {label: assoc(emb) for label, emb in combo_embeddings.items()}
        labels = list(identity_combinations.keys())

        individual_effects = {
            f"{labels[i]}_vs_{labels[j]}": assocs[labels[i]] - assocs[labels[j]]
            for i, j in combinations(range(len(labels)), 2)
        }

        bw, bm, ww, wm = [assocs[k] for k in labels]
        race_effect   = ((bw + bm) / 2) - ((ww + wm) / 2)
        gender_effect = ((bw + ww) / 2) - ((bm + wm) / 2)
        actual        = bw - wm
        compound      = actual - (race_effect + gender_effect)

        rng = np.random.default_rng(seed=42)
        all_assocs = list(assocs.values())

        perm_compounds = []
        for _ in range(self.n_permutations):
            p = rng.permutation(all_assocs)
            r = ((p[0] + p[1]) / 2) - ((p[2] + p[3]) / 2)
            g = ((p[0] + p[2]) / 2) - ((p[1] + p[3]) / 2)
            perm_compounds.append((p[0] - p[3]) - (r + g))
        p_value = float(np.mean(np.array(perm_compounds) >= compound)) if perm_compounds else 0.5

        boot_compounds = []
        for _ in range(1000):
            idxs = rng.integers(0, 4, size=4)
            b = [all_assocs[i] for i in idxs]
            r = ((b[0] + b[1]) / 2) - ((b[2] + b[3]) / 2)
            g = ((b[0] + b[2]) / 2) - ((b[1] + b[3]) / 2)
            boot_compounds.append((b[0] - b[3]) - (r + g))
        ci = (float(np.percentile(boot_compounds, 2.5)),
              float(np.percentile(boot_compounds, 97.5))) if boot_compounds else (0.0, 0.0)

        return iWEATResult(
            test_name=test_name, lens_id=lens_id,
            identity_combinations=labels,
            individual_effects=individual_effects,
            combination_effects={f"{labels[i]}_vs_{labels[j]}":
                assocs[labels[i]] - assocs[labels[j]]
                for i, j in combinations(range(len(labels)), 2)},
            compound_effect=compound, p_value=p_value,
            confidence_interval_95=ci,
            interpretation=self._interpret(compound, p_value, test_name),
        )

    @staticmethod
    def _interpret(compound: float, p: float, name: str) -> str:
        if p >= 0.05:
            return f"{name}: No significant intersectional amplification (p={p:.3f})."
        strength = "strong" if abs(compound) > 0.3 else "moderate" if abs(compound) > 0.15 else "weak"
        direction = "amplified" if compound > 0 else "attenuated"
        return (
            f"{name}: {strength.capitalize()} intersectional bias {direction} "
            f"(compound={compound:.3f}, p={p:.3f}). Bias at the intersection is "
            f"{'greater' if compound > 0 else 'less'} than the sum of individual effects."
        )
```

### Upgrade 17 — WEAT benchmark validation (add to `WEATAnalyzer`)

```python
CALISKAN_BENCHMARKS = {
    "flowers_vs_insects_pleasant_unpleasant":    {"d": 1.50, "p": 0.016},
    "instruments_vs_weapons_pleasant_unpleasant":{"d": 1.53, "p": 0.012},
    "ea_names_vs_aa_names_pleasant_unpleasant":  {"d": 1.41, "p": 0.032},
    "male_vs_female_career_family":              {"d": 1.81, "p": 0.001},
    "math_vs_arts_male_female":                  {"d": 1.06, "p": 0.048},
}

BENCHMARK_WORD_LISTS = {
    "flowers_vs_insects_pleasant_unpleasant": {
        "target_a":    ["aster", "clover", "hyacinth", "marigold", "poppy", "azalea"],
        "target_b":    ["ant", "caterpillar", "flea", "hornet", "mosquito", "roach"],
        "attribute_x": ["caress", "freedom", "health", "love", "peace", "cheer"],
        "attribute_y": ["abuse", "crash", "filth", "murder", "sickness", "ugly"],
    },
    "male_vs_female_career_family": {
        "target_a":    ["brother", "father", "uncle", "grandfather", "son", "boy"],
        "target_b":    ["sister", "mother", "aunt", "grandmother", "daughter", "girl"],
        "attribute_x": ["executive", "management", "professional", "corporation", "salary", "career"],
        "attribute_y": ["home", "parents", "children", "family", "cousins", "marriage"],
    },
}

def run_benchmark_validation(self) -> dict[str, dict]:
    """
    Run Caliskan et al. (2017) benchmark tests and compare effect sizes to
    published figures. Large deviations indicate this embedding model has
    different bias characteristics than GloVe.
    """
    report = {}
    for test_name, word_lists in BENCHMARK_WORD_LISTS.items():
        result = self.run(test_name=test_name, lens_id="benchmark", **word_lists)
        published_d = CALISKAN_BENCHMARKS.get(test_name, {}).get("d")
        deviation = abs(result.effect_size - published_d) if published_d is not None else None
        if deviation is None:
            interp = "No published benchmark available for comparison."
        elif deviation < 0.3:
            interp = f"Close alignment (deviation={deviation:.2f}). Comparable to Caliskan et al."
        elif deviation < 0.7:
            interp = f"Moderate deviation (deviation={deviation:.2f}). Directionally consistent."
        else:
            interp = f"Large deviation (deviation={deviation:.2f}). Interpret WEAT effect sizes with caution."
        report[test_name] = {
            "published_d": published_d,
            "observed_d": round(result.effect_size, 3),
            "observed_p": round(result.p_value, 4),
            "deviation": round(deviation, 3) if deviation is not None else None,
            "interpretation": interp,
        }
    return report
```

---

## Upgrades 18 & 19 — Batch processing and dataset versioning

### `ethiviz/utils/reproducibility.py`

```python
from __future__ import annotations
import hashlib
import importlib.metadata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class ReproducibilityRecord:
    """Captures all state needed to reproduce an analysis result exactly."""
    analysis_id: str
    library_version: str
    embedding_model_id: str
    framework_ids: list[str]
    prototype_yaml_hashes: dict[str, str]
    framework_yaml_hashes: dict[str, str]
    random_seed: int
    n_bootstrap_samples: int
    recorded_at: str
    python_version: str

    @classmethod
    def capture(
        cls,
        framework_ids: list[str],
        random_seed: int = 42,
        n_bootstrap: int = 1000,
    ) -> "ReproducibilityRecord":
        import sys
        from ethiviz.embeddings.model import MODEL_ID
        from ethiviz.embeddings.prototype_store import PROTOTYPES_DIR

        fw_dir = Path(__file__).parent.parent / "frameworks" / "builtin"
        proto_hashes = {
            lid: _file_hash(PROTOTYPES_DIR / f"{lid}_prototypes.yaml")
            for lid in framework_ids
            if (PROTOTYPES_DIR / f"{lid}_prototypes.yaml").exists()
        }
        fw_hashes = {
            fid: _file_hash(fw_dir / f"{fid}.yaml")
            for fid in framework_ids
            if (fw_dir / f"{fid}.yaml").exists()
        }
        try:
            version = importlib.metadata.version("ethiviz")
        except importlib.metadata.PackageNotFoundError:
            version = "dev"

        analysis_id = hashlib.sha256(
            f"{version}:{framework_ids}:{random_seed}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        return cls(
            analysis_id=analysis_id,
            library_version=version,
            embedding_model_id=MODEL_ID,
            framework_ids=framework_ids,
            prototype_yaml_hashes=proto_hashes,
            framework_yaml_hashes=fw_hashes,
            random_seed=random_seed,
            n_bootstrap_samples=n_bootstrap,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
```

### `ethiviz/utils/batch.py`

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

@dataclass
class BatchProgress:
    total: int
    completed: int
    failed: int
    checkpoint_path: str | None

    @property
    def fraction_complete(self) -> float:
        return self.completed / self.total if self.total > 0 else 0.0

class BatchProcessor:
    """
    Batch processing with tqdm progress, checkpointing, and parallel execution.
    Resumes from checkpoint on restart.

    Example:
        >>> proc = BatchProcessor(checkpoint_dir="./ckpts", n_workers=4)
        >>> results = proc.process(texts, analyzer.score_text_single, "job_001")
    """
    def __init__(
        self,
        checkpoint_dir: str = "./ethiviz_checkpoints",
        n_workers: int = 1,
        show_progress: bool = True,
    ) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.n_workers = n_workers
        self.show_progress = show_progress

    def process(
        self,
        items: list[Any],
        fn: Callable[[Any], Any],
        job_id: str,
        checkpoint_every: int = 100,
    ) -> list[Any]:
        checkpoint_path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        results: dict[int, Any] = {}

        if checkpoint_path.exists():
            with checkpoint_path.open() as f:
                results = {int(k): v for k, v in json.load(f).items()}

        pending = [i for i in range(len(items)) if i not in results]

        iterator: Any = pending
        if self.show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(pending, initial=len(results), total=len(items),
                                desc=f"EthiViz batch [{job_id}]")
            except ImportError:
                pass

        if self.n_workers > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                futures = {executor.submit(fn, items[i]): i for i in pending}
                completed_count = 0
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        results[idx] = {"error": str(e)}
                    completed_count += 1
                    if completed_count % checkpoint_every == 0:
                        self._save_checkpoint(checkpoint_path, results)
        else:
            for step, idx in enumerate(iterator):
                try:
                    results[idx] = fn(items[idx])
                except Exception as e:
                    results[idx] = {"error": str(e)}
                if (step + 1) % checkpoint_every == 0:
                    self._save_checkpoint(checkpoint_path, results)

        self._save_checkpoint(checkpoint_path, results)
        return [results.get(i) for i in range(len(items))]

    def _save_checkpoint(self, path: Path, results: dict) -> None:
        serializable = {}
        for k, v in results.items():
            try:
                json.dumps(v)
                serializable[str(k)] = v
            except (TypeError, ValueError):
                serializable[str(k)] = str(v)
        with path.open("w") as f:
            json.dump(serializable, f)

    def clear_checkpoint(self, job_id: str) -> None:
        path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        if path.exists():
            path.unlink()
```

### `ethiviz/frameworks/versioning.py`

```python
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FrameworkVersion:
    framework_id: str
    yaml_hash: str
    version_string: str
    recorded_at: str

class FrameworkVersionTracker:
    """
    Records which framework YAML version was used for each analysis.
    Analyses using different YAML hashes are not directly score-comparable.

    Example:
        >>> tracker = FrameworkVersionTracker()
        >>> v1 = tracker.snapshot(["western_v1", "ubuntu_v1"])
        >>> v2 = tracker.snapshot(["western_v1", "ubuntu_v1"])
        >>> tracker.changed_since(v1, v2)
        []  # or ['western_v1'] if that YAML changed
    """
    BUILTIN_DIR = Path(__file__).parent / "builtin"

    def snapshot(self, framework_ids: list[str]) -> dict[str, FrameworkVersion]:
        from datetime import datetime, timezone
        import yaml as _yaml
        versions = {}
        for fw_id in framework_ids:
            path = self.BUILTIN_DIR / f"{fw_id}.yaml"
            if not path.exists():
                continue
            content = path.read_bytes()
            h = hashlib.sha256(content).hexdigest()[:16]
            data = _yaml.safe_load(content)
            versions[fw_id] = FrameworkVersion(
                framework_id=fw_id,
                yaml_hash=h,
                version_string=str(data.get("validation", {}).get("last_updated", "unknown")),
                recorded_at=datetime.now(timezone.utc).isoformat(),
            )
        return versions

    def changed_since(
        self,
        baseline: dict[str, FrameworkVersion],
        current: dict[str, FrameworkVersion],
    ) -> list[str]:
        all_ids = set(baseline) | set(current)
        return [
            fw_id for fw_id in all_ids
            if baseline.get(fw_id, FrameworkVersion(fw_id, "", "", "")).yaml_hash
            != current.get(fw_id, FrameworkVersion(fw_id, "", "", "")).yaml_hash
        ]
```

---

## Upgrade 20 — Multilingual WEAT word lists

Each WEAT word list YAML gains a `languages` block under every `target_a`, `target_b`,
`attribute_x`, `attribute_y` field. Shown here for the Islamic lens:

```yaml
# ethiviz/analysis/weat_lists/islamic_v1.yaml (excerpt)
tests:
  - test_name: islamic_cultural_sentiment
    target_a:
      en: [mosque, hijab, Ramadan, halal, imam, Quran, minaret, eid]
      ar: [مسجد, حجاب, رمضان, حلال, إمام, قرآن, مئذنة, عيد]
      fr: [mosquée, hijab, Ramadan, halal, imam, Coran, minaret, aïd]
      es: [mezquita, hiyab, Ramadán, halal, imán, Corán, minarete, eid]
    target_b:
      en: [church, cross, Christmas, kosher, rabbi, Bible, cathedral, Easter]
      ar: [كنيسة, صليب, كريسماس, كوشير, حاخام, إنجيل, كاتدرائية, عيد الفصح]
      fr: [église, croix, Noël, kasher, rabbin, Bible, cathédrale, Pâques]
      es: [iglesia, cruz, Navidad, kosher, rabino, Biblia, catedral, Pascua]
    attribute_x:
      en: [peace, harmony, community, faith, devotion, wisdom, compassion, justice]
      ar: [سلام, انسجام, مجتمع, إيمان, تفاني, حكمة, رحمة, عدالة]
      fr: [paix, harmonie, communauté, foi, dévotion, sagesse, compassion, justice]
      es: [paz, armonía, comunidad, fe, devoción, sabiduría, compasión, justicia]
    attribute_y:
      en: [violence, danger, extremism, threat, suspicion, foreign, hostile, aggression]
      ar: [عنف, خطر, تطرف, تهديد, شك, أجنبي, معادي, عدوان]
      fr: [violence, danger, extrémisme, menace, suspicion, étranger, hostile, agression]
      es: [violencia, peligro, extremismo, amenaza, sospecha, extranjero, hostil, agresión]
```

`WEATAnalyzer.run()` gains a `language: str = "en"` parameter. When a non-English
language is requested the word list loader returns the translated terms for that language.

---

## The `Analyzer` class

### `ethiviz/api.py` — full method contract

```python
from __future__ import annotations
from typing import Any
from ethiviz.context.deployment import DeploymentContext
from ethiviz.scoring.calibration import PlattCalibrator
from ethiviz.scoring.drift import DriftMonitor
from ethiviz.utils.reproducibility import ReproducibilityRecord

class Analyzer:
    """
    Primary entry point for EthiViz bias detection.

    Example:
        >>> from ethiviz import Analyzer
        >>> from ethiviz.context.deployment import DeploymentContext
        >>> ctx = DeploymentContext(region="DE", domain="hiring",
        ...     primary_community="western", regulatory_framework="eu_ai_act")
        >>> analyzer = Analyzer(deployment_context=ctx)
        >>> result = analyzer.analyze(["All women prefer caregiving to leadership."] * 5)
        >>> report = result.generate_report()
        >>> print(report.compliance_mapping.overall_compliance_risk)
        'high'
    """
    def __init__(
        self,
        registry: Any | None = None,
        frameworks: list[str] | None = None,
        aggregation: str = "weighted_mean",
        confidence_threshold: float = 0.6,
        deployment_context: DeploymentContext | None = None,
        calibrator: PlattCalibrator | None = None,
        drift_monitor: DriftMonitor | None = None,
        use_semantic: bool = True,
        random_seed: int = 42,
        n_bootstrap: int = 1000,
    ) -> None:
        """
        Initialise the Analyzer.

        Implementation must:
        1. Load the FrameworkRegistry (default: all four builtin frameworks).
        2. Instantiate all four lens objects (WesternLens, UbuntuLens,
           ConfucianLens, IslamicLens), passing use_semantic and the registry.
        3. Store calibrator (or create a new PlattCalibrator() if None — it will
           load any previously saved calibrations from ~/.ethiviz automatically).
        4. Store drift_monitor (or create a new DriftMonitor() if None).
        5. Store all other parameters for use in analyze().
        """
        ...

    def analyze(
        self,
        dataset: Any,              # list[str] for text; np.ndarray or list[np.ndarray] for images
        mode: str = "text",        # "text" | "image" | "multimodal"
        weights: dict[str, float] | None = None,
        run_weat: bool = False,
        run_iweat: bool = False,
        job_id: str | None = None,
        n_workers: int = 1,
    ) -> Any:                      # ScoredResult
        """
        Run the full analysis pipeline. Implementation must execute in this order:

        1.  **Language detection** (text mode): run LanguageDetector on each text;
            store detected language on each LensScore as language_detected.
        2.  **Lens scoring**: call each lens's score() method with the appropriate
            language prototype variants loaded from PrototypeStore.
        3.  **Bootstrap CIs**: compute 95% confidence intervals for each lens score
            using bootstrap_text_ci (Upgrade 7).
        4.  **Calibration**: if self.calibrator.is_fitted(lens_id), set
            LensScore.calibrated_score = self.calibrator.calibrate(raw, lens_id).
            Otherwise leave calibrated_score = None.
        5.  **Framework conflict detection**: call ConflictResolver.detect() on
            the dict of {lens_id: overall_score}.
        6.  **Synergy amplification**: call _apply_synergy_amplification() on
            the list of FrameworkScore objects.
        7.  **Context weighting** (if deployment_context is set): call get_weights()
            to override the default equal weights before computing consensus_score.
        8.  **Consensus score**: compute weighted mean of overall_scores using
            context-derived or user-supplied weights.
        9.  **WEAT** (if run_weat=True): run WEATAnalyzer for each lens's word lists.
        10. **iWEAT** (if run_iweat=True): run iWEATAnalyzer for each lens.
        11. **Regulatory mapping** (if deployment_context is set): call
            RegulatoryMapper().map(scored_result, deployment_context).
            Store the ComplianceMapping on the BiasReport, not on ScoredResult directly.
        12. **Prototype version hashing**: set LensScore.prototype_version_hash for
            each lens using FrameworkVersionTracker.
        13. **Reproducibility record**: call ReproducibilityRecord.capture() and
            attach to ScoredResult.reproducibility.
        14. **Drift recording** (if drift_monitor is set): call
            self.drift_monitor.record_snapshot() for each lens's scores.
        15. Return a fully populated ScoredResult.
        """
        ...

    def quick_scan(self, texts: list[str]) -> Any:   # returns ScoredResult
        """
        Convenience wrapper: run analyze(texts, mode="text") with default settings
        and return the ScoredResult directly. Does NOT return a BiasReport.

        Note: smoke tests call r.scored_result.framework_scores on quick_scan's
        return value — this method must return ScoredResult, not BiasReport.
        """
        ...

    def dual_lens_analysis(
        self, dataset: Any, lens_a: str, lens_b: str
    ) -> Any:
        """Run analyze() restricted to lens_a and lens_b. Returns ScoredResult."""
        ...

    def calibrate(
        self,
        reference_texts: list[str],
        reference_labels: list[int],
        reference_corpus_name: str,
    ) -> dict[str, Any]:
        """
        Score all reference_texts through each lens to get raw scores, then
        call self.calibrator.fit(lens_id, raw_scores, reference_labels, ...) for
        each lens. Returns {lens_id: CalibrationRecord}.
        """
        ...

    def set_baseline(self, dataset: Any, dataset_source: str) -> dict[str, Any]:
        """
        Score dataset and call self.drift_monitor.record_snapshot(..., set_as_baseline=True)
        for each lens. Returns {lens_id: ScoreSnapshot}.
        """
        ...

    def check_drift(self, dataset: Any, dataset_source: str) -> dict[str, Any]:
        """
        Score dataset and call self.drift_monitor.check_drift() for each lens.
        Returns {lens_id: DriftAlert}.
        """
        ...
```

---

## HTML report — updated for v4

`BiasReport.to_html()` must produce a standalone, self-contained HTML file (all CSS inline,
no external dependencies) containing these sections in order:

1. **Header** — title, dataset description, timestamp, library version,
   `ReproducibilityRecord.analysis_id` shown prominently as "Analysis ID: [hash]"
2. **Summary** — `BiasReport.summary()` paragraph
3. **Overall risk banner** — colour-coded (green/amber/red) from
   `ComplianceMapping.overall_compliance_risk`
4. **Per-lens scores table** — framework name, raw score, calibrated score (or "—" if
   unfitted), CI lower–upper, colour band, top 3 flagged items, confidence
5. **Synergy amplifications** — "Ubuntu + Islamic both flagged essentialism (amplified 15%)"
6. **Framework conflicts** — type, divergence, resolution strategy, full `CONFLICT_RATIONALE`
7. **WEAT results** (if run) — test name, effect size, CI, p-value, interpretation;
   iWEAT shown separately with compound effect highlighted
8. **Explainability** — colour-highlighted text for top-3 flagged inputs (red = bias-increasing
   tokens, green = bias-reducing) when `token_attributions` is populated
9. **Regulatory compliance** — `ComplianceMapping.obligations` sorted by severity,
   with severity badge, regulation/article, obligation text, evidence chain
10. **Recommendations** — `MitigationAdvisor` output, priority-sorted, with thesis citations
11. **Drift status** — current vs baseline comparison if `DriftMonitor` has snapshots
12. **Evidence provenance** — `<details>` expandable section per major finding, containing
    full `ProvenanceRecord` with prototype YAML hashes
13. **Reproducibility footer** — `ReproducibilityRecord` in monospace table; thesis citation:
    "Copeland, B.S. (2025). Cross-Cultural Bias Detection in AI Systems. IU University of
    Applied Sciences."; EthiViz disclaimer (not legal advice)

---

## Package configuration

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ethiviz"
version = "0.4.0"
description = "Cross-cultural AI bias detection through Western, Ubuntu, Confucian, and Islamic ethical lenses"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
keywords = ["bias", "fairness", "ai-ethics", "cross-cultural", "ubuntu", "confucian",
            "islamic", "weat", "intersectional", "decolonize-ai"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "numpy>=1.24",
    "pandas>=2.0",
    "pyyaml>=6.0",
    "pydantic>=2.4",
    "scikit-learn>=1.3",
    "jinja2>=3.1",
    "scipy>=1.11",
]

[project.optional-dependencies]
semantic      = ["sentence-transformers>=2.2"]
vision        = ["mediapipe>=0.10", "opencv-python>=4.8", "pillow>=10.0",
                 "transformers>=4.35", "torch>=2.0"]
explainability = ["lime>=0.2", "shap>=0.44"]
multilingual  = ["langdetect>=1.0", "jieba>=0.42", "stanza>=1.7"]
calibration   = []                            # uses scikit-learn from core deps
batch         = ["tqdm>=4.65"]
aif360        = ["aif360>=0.6"]
fairlearn     = ["fairlearn>=0.9"]
dev           = ["pytest>=7.4", "pytest-cov>=4.0", "black>=23.7",
                 "ruff>=0.1", "mypy>=1.5"]
full          = ["ethiviz[semantic,vision,explainability,multilingual,batch,aif360,fairlearn]"]
```

---

## Test requirements

All tests use pytest and built-in Python only. No real API calls. No GPU downloads.
The `mock_embedding_model` fixture (defined in `conftest.py` above) is `autouse=True`.

### New test modules for v4 upgrades

**`tests/test_prototype_learner.py`**
- `collect_uncertain()` returns `UncertainCase` objects for scores in [0.55, 0.75]
- `collect_uncertain()` returns empty list for scores clearly outside that range
- `write_back()` adds new entry to prototype YAML; removes from queue
- `write_back()` raises `ValueError` for duplicate `prototype_id`
- Written prototype entry contains `provenance["active_learning"] == True`
- `get_review_queue()` filters correctly by `lens_id`

**`tests/test_calibration.py`**
- `fit()` returns `CalibrationRecord` with `calibration_auc` in [0.5, 1.0]
- `calibrate(raw_score, lens_id)` returns float in [0.0, 1.0]
- `calibrate()` raises `RuntimeError` when not fitted for that `lens_id`
- Higher raw score → higher calibrated score (monotonicity)
- Saved calibration is reloaded on fresh `PlattCalibrator()` construction

**`tests/test_drift.py`**
- `record_snapshot(..., set_as_baseline=True)` persists a baseline file
- `check_drift()` returns `drift_detected=False` for identical score distributions
- `check_drift()` returns `drift_detected=True` when scores shift significantly
- `DriftAlert.kl_divergence` is non-negative
- `check_drift()` raises `RuntimeError` when no baseline exists

**`tests/test_vision.py`** (mock images only — no model downloads)
- `ITASkinToneEstimator.estimate()` returns valid `SkinToneEstimate`
- Very light pixel values → `Type_I`; very dark → `Type_VI`
- `CulturalElementResult` constructs without errors
- `FITZPATRICK_SCALE` has exactly 6 entries
- `compute_skin_tone_distribution()` returns a distribution summing to ≤ 1.0

**`tests/test_context.py`**
- `get_weights(ctx)` returns dict with exactly 4 lens keys summing to 1.0
- Falls back to equal weights for unknown community/domain combinations
- `DeploymentContext` constructs with all required fields

**`tests/test_regulatory.py`**
- `RegulatoryMapper.map()` returns non-empty obligations when bias scores are high
- Obligations are sorted: critical before high before medium
- `ComplianceMapping.disclaimer` is non-empty
- `_overall_risk()` returns "critical" when any obligation is critical
- Region-based CCPA condition triggers only when `context.region in {"US", "CA"}`

**`tests/test_weat.py`** (extended for upgrades 16 and 17)
- `iWEATAnalyzer.run()` returns `iWEATResult` with all required fields
- `compound_effect` is a float
- `run()` raises `ValueError` when `len(identity_combinations) != 4`
- `WEATAnalyzer.run_benchmark_validation()` returns dict with ≥ 1 test
- Each benchmark entry contains `published_d`, `observed_d`, `deviation`, `interpretation`

**`tests/test_batch.py`**
- `process()` returns list of same length as input
- Checkpoint file is created after processing
- Re-run with same `job_id` skips already-completed items
- `clear_checkpoint()` removes the checkpoint file
- `n_workers > 1` produces the same result set as `n_workers=1`

**`tests/test_versioning.py`**
- `snapshot()` returns dict with valid `yaml_hash` for each framework
- `changed_since()` returns empty list when no hashes changed
- `changed_since()` returns the changed framework ID when a hash differs
- `ReproducibilityRecord.capture()` returns record with 16-char `analysis_id`
- `library_version` is a non-empty string

**`tests/test_language_detection.py`**
- `detect("Hello world")` → `language_code == "en"`, `script == "latin"`
- Arabic text → `script == "arabic"`, `tokenizer_required == "stanza"`
- Chinese text → `tokenizer_required == "jieba"`
- Undetected language falls back to `"en"` without raising

**`tests/test_provenance.py`**
- `ProvenanceRecord` constructs with all fields
- `EvidenceItem` constructs with all fields
- `ProvenanceRecord.evidence_items` is a list

**`tests/test_api.py`** (extended for v4)
- `quick_scan()` returns a `ScoredResult` (not a `BiasReport`)
- `quick_scan()` result has `.scored_result` attribute giving access to `framework_scores`
- `Analyzer(deployment_context=ctx).analyze(texts)` populates `compliance_mapping`
  on the generated report
- `calibrate()` calls `PlattCalibrator.fit()` for each lens
- `check_drift()` returns a dict keyed by lens ID

---

## Build sequence

Build in this order. Run the corresponding test file before proceeding to the next group.

```
 1.  pyproject.toml, LICENSE
 2.  ethiviz/utils/types.py
 3.  ethiviz/utils/validation.py, caching.py
 4.  ethiviz/utils/reproducibility.py                     # Upgrade 18
 5.  ethiviz/utils/batch.py                               # Upgrade 18
 6.  ethiviz/frameworks/base.py
 7.  All four ethiviz/frameworks/builtin/*.yaml
 8.  ethiviz/frameworks/loader.py
 9.  ethiviz/frameworks/conflict.py                       # Upgrade 4
10.  ethiviz/frameworks/compatibility.py
11.  ethiviz/frameworks/wvs_calibration.py                # Upgrade 6
12.  ethiviz/frameworks/versioning.py                     # Upgrade 19
13.  ethiviz/embeddings/model.py                          # Upgrade 1  (defines MODEL_ID)
14.  ethiviz/embeddings/prototype_store.py                # Upgrade 1  (defines PROTOTYPES_DIR)
15.  All four ethiviz/embeddings/prototypes/*.yaml         # with translations block (Upgrade 20)
16.  ethiviz/embeddings/semantic_detector.py              # Upgrade 1
17.  ethiviz/embeddings/language_detection.py             # Upgrade 11
18.  ethiviz/embeddings/prototype_learner.py              # Upgrade 8
     → run: tests/test_embeddings.py, test_prototype_learner.py, test_language_detection.py
19.  ethiviz/analysis/image_analysis.py                   # Figure A2
20.  ethiviz/analysis/demographics.py                     # Figures A7–A9, production impl
21.  ethiviz/analysis/intersectional.py                   # Figure A3
22.  ethiviz/analysis/cultural_inclusion.py               # Figure A4
23.  ethiviz/analysis/dignity.py                          # Figure A6
24.  ethiviz/analysis/recommendations.py                  # Figure A5
25.  ethiviz/analysis/dual_framework.py                   # Figure A1
26.  ethiviz/analysis/ubuntu_metrics.py                   # Upgrade 2
27.  All four ethiviz/analysis/weat_lists/*.yaml           # multilingual (Upgrade 20)
28.  ethiviz/analysis/weat.py                             # Upgrades 3, 16, 17
     → run: tests/test_analysis.py, test_ubuntu_metrics.py, test_weat.py
29.  ethiviz/vision/backends/base.py                      # Upgrade 12
30.  ethiviz/vision/face_detector.py                      # Upgrade 12
31.  ethiviz/vision/skin_tone.py                          # Upgrade 12
32.  ethiviz/vision/cultural_element_detector.py          # Upgrade 12
33.  ethiviz/vision/object_detector.py                    # Upgrade 12
     → run: tests/test_vision.py
34.  ethiviz/lenses/base.py
35.  ethiviz/lenses/western.py    (+ TransformerUpgrade stub)
36.  ethiviz/lenses/ubuntu.py     (+ SocialGraphUpgrade stub)
37.  ethiviz/lenses/confucian.py  (+ OntologyUpgrade stub)
38.  ethiviz/lenses/islamic.py    (+ ClassifierUpgrade stub)
     → run: tests/test_lenses.py
     ⚠ Verify no circular imports before proceeding: python -c "from ethiviz.lenses import *"
39.  ethiviz/scoring/confidence.py                        # Upgrade 7
40.  ethiviz/scoring/calibration.py                       # Upgrade 9
41.  ethiviz/scoring/drift.py                             # Upgrade 10
42.  ethiviz/scoring/quantifier.py, aggregation.py
43.  ethiviz/scoring/multi_framework.py                   # + synergy (Upgrade 14)
     → run: tests/test_scoring.py, test_confidence.py, test_calibration.py, test_drift.py
44.  ethiviz/context/deployment.py                        # Upgrade 13
45.  ethiviz/context/weights.py                           # Upgrade 13
46.  ethiviz/context/regulatory.py                        # Upgrade 15
     → run: tests/test_context.py, test_regulatory.py
47.  ethiviz/reporting/provenance.py                      # Upgrade 15
48.  ethiviz/reporting/explainability.py                  # Upgrade 5
49.  ethiviz/reporting/mitigation.py
50.  ethiviz/reporting/base.py
51.  ethiviz/reporting/html_report.py                     # full 13-section template
52.  ethiviz/reporting/json_report.py
53.  ethiviz/reporting/adapters/
     → run: tests/test_reporting.py, test_provenance.py, test_explainability.py
54.  ethiviz/detection/
     → run: tests/test_detection.py
55.  ethiviz/api.py
56.  ethiviz/__init__.py
     → run: tests/test_api.py
57.  tests/conftest.py (must be done before all test runs above — write it first)
58.  All remaining test files not yet run
59.  All examples
60.  README.md, CONTRIBUTING.md, docs/upgrades_v4.md
```

---

## Acceptance criteria

All of the following must pass:

```bash
# Install
pip install -e ".[dev,semantic,batch,multilingual]"

# Full test suite with coverage
pytest tests/ --cov=ethiviz --cov-report=term-missing
# Required: ≥ 90% coverage

# Type checking and linting
mypy ethiviz/ && ruff check ethiviz/

# Smoke test 1: basic four-lens analysis
python -c "
from ethiviz import Analyzer
r = Analyzer().quick_scan([
    'The engineer debugged the code.',
    'All Muslim women wear hijabs and cannot work professionally.',
    'African people all live in poverty.',
    'Women are naturally better suited to care roles than leadership.',
])
scores = {fs.framework_id: fs.overall_score for fs in r.framework_scores}
assert scores['islamic_v1'] > 0.5, 'Islamic lens failed to flag essentialist text'
assert scores['ubuntu_v1'] > 0.5, 'Ubuntu lens failed to flag African essentialism'
print('Smoke test 1 passed. Scores:', {k: round(v, 3) for k, v in scores.items()})
"

# Smoke test 2: deployment context and regulatory mapping
python -c "
from ethiviz import Analyzer
from ethiviz.context.deployment import DeploymentContext
ctx = DeploymentContext(region='DE', domain='hiring',
    primary_community='western', regulatory_framework='eu_ai_act')
analyzer = Analyzer(deployment_context=ctx)
result = analyzer.analyze(
    ['All women are better at caregiving than leadership.'] * 5,
    mode='text'
)
report = result.generate_report()
assert report.compliance_mapping is not None
assert len(report.compliance_mapping.obligations) > 0
print('Smoke test 2 passed. Regulatory obligations:',
      [o.article for o in report.compliance_mapping.obligations])
"

# Smoke test 3: WEAT and iWEAT
python -c "
from ethiviz.analysis.weat import WEATAnalyzer, iWEATAnalyzer
w = WEATAnalyzer(n_permutations=100)
result = w.run(
    test_name='gender_career', lens_id='western_v1',
    target_a=['he', 'man'], target_b=['she', 'woman'],
    attribute_x=['career', 'engineer'], attribute_y=['family', 'nurse'],
)
assert isinstance(result.effect_size, float)
assert 0.0 <= result.p_value <= 1.0
bv = w.run_benchmark_validation()
assert len(bv) > 0
iw = iWEATAnalyzer(n_permutations=100)
ir = iw.run(
    test_name='race_gender', lens_id='western_v1',
    identity_combinations={'Black_woman': ['Black woman'], 'Black_man': ['Black man'],
                           'white_woman': ['white woman'], 'white_man': ['white man']},
    attribute_x=['career', 'professional'],
    attribute_y=['domestic', 'family'],
)
assert isinstance(ir.compound_effect, float)
print('Smoke test 3 passed. d=', round(result.effect_size, 3),
      'compound=', round(ir.compound_effect, 3))
"

# Smoke test 4: calibration and drift
python -c "
from ethiviz.scoring.calibration import PlattCalibrator
from ethiviz.scoring.drift import DriftMonitor
cal = PlattCalibrator()
cal.fit('western_v1', [0.2, 0.8, 0.3, 0.9, 0.1, 0.7, 0.4, 0.6],
        [0, 1, 0, 1, 0, 1, 0, 1], 'smoke_test_corpus')
cp = cal.calibrate(0.72, 'western_v1')
assert 0.0 <= cp <= 1.0
dm = DriftMonitor()
dm.record_snapshot('western_v1', [0.2, 0.25, 0.3], 'baseline', set_as_baseline=True)
alert = dm.check_drift('western_v1', [0.7, 0.75, 0.8], 'current')
assert alert.drift_detected == True
print('Smoke test 4 passed. calibrated=', round(cp, 3), 'drift=', alert.drift_detected)
"

# Smoke test 5: batch processing and reproducibility
python -c "
import tempfile
from ethiviz.utils.batch import BatchProcessor
from ethiviz.utils.reproducibility import ReproducibilityRecord
with tempfile.TemporaryDirectory() as d:
    proc = BatchProcessor(checkpoint_dir=d, show_progress=False)
    results = proc.process(
        items=['text one', 'text two', 'text three'],
        fn=lambda t: len(t),
        job_id='smoke_test_batch',
    )
    assert results == [8, 8, 10]
rec = ReproducibilityRecord.capture(['western_v1', 'ubuntu_v1'])
assert len(rec.analysis_id) == 16
assert rec.library_version != ''
print('Smoke test 5 passed. batch results=', results, 'analysis_id=', rec.analysis_id)
"

# Smoke test 6: conflict detection and synergy amplification
python -c "
from ethiviz.frameworks.conflict import ConflictResolver, ConflictType
resolver = ConflictResolver()
conflicts = resolver.detect({'western_v1': 0.2, 'ubuntu_v1': 0.85})
assert len(conflicts) == 1
assert conflicts[0].conflict_type == ConflictType.INDIVIDUAL_VS_COMMUNAL
from ethiviz.scoring.multi_framework import _apply_synergy_amplification
from ethiviz.scoring.base import FrameworkScore
scores = [
    FrameworkScore('ubuntu_v1',  'Ubuntu',  0.65, {}, 0.9, [], (0.5, 0.8), 100, {}),
    FrameworkScore('islamic_v1', 'Islamic', 0.70, {}, 0.85, [], (0.55, 0.85), 100, {}),
]
amplified, pairs = _apply_synergy_amplification(scores, threshold=0.50)
assert len(pairs) == 1
assert amplified[0].overall_score > 0.65
print('Smoke test 6 passed. Conflict:', conflicts[0].conflict_type.value)
print('Synergy amplification:', pairs)
"

# Smoke test 7: language detection
python -c "
from ethiviz.embeddings.language_detection import LanguageDetector
d = LanguageDetector()
en = d.detect('The engineer fixed the bug.')
assert en.language_code == 'en'
assert en.script == 'latin'
print('Smoke test 7 passed. Language:', en.language_code, 'Script:', en.script)
"

# Smoke test 8: active learning queue
python -c "
from ethiviz.embeddings.prototype_learner import PrototypeLearner
learner = PrototypeLearner()
queue = learner.get_review_queue()
print(f'Smoke test 8 passed. Review queue has {len(queue)} items.')
"
```

All four stub `NotImplementedError` classes must be present and raise with thesis-citing
messages. The UCI Adult case study and CV case study examples must run to completion.
`mypy ethiviz/` must report zero errors. `ruff check ethiviz/` must report zero errors.
