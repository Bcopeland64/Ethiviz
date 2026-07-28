# Changelog

## 0.6.0

Three phases of work on cultural-nuance detection: repairing metrics that were
structurally unable to measure what they documented, making multilingual
analysis real and honest about its own limits, and adding cross-cultural
reasoning at the dimension level.

Test suite: 81 → 162 tests.

### Breaking changes

- `calculate_intersectional_analysis()` returns `Dict[str, IntersectionResult]`
  instead of `Dict[str, float]`.
- `BuddhistLens`, `HinduLens`, `IndigenousLens` no longer accept a `registry=`
  keyword (it was accepted and silently unused).
- `cultural_inclusion_index()` returns a Jensen-Shannon similarity where it
  previously returned a key-overlap fraction. Existing thresholds are invalid.
- Scores shift across all seven lenses (severity weighting, negation guard,
  per-language calibration, blend renormalisation). Identical input yields
  different output.
- `iWEATAnalyzer.compound_effect` returns real values where it previously
  returned exactly `0.0` for every input.
- `RegulatoryMapper` triggers on worst-case rather than mean bias, so datasets
  that previously produced no obligations may now produce them.

**Migration:** any Platt calibration fitted under 0.5.0 (`scoring/
calibration_data/`) and any drift baselines (`scoring/drift_snapshots/`) are
invalid against 0.6.0 scores and must be refit, not carried forward.

### Fixed — metrics that could not measure what they claimed

- `DualEthicsFramework.resolve_conflict()` referenced bare names instead of
  `self.*` and raised `NameError` on every call. It had never worked.
- Intersectional analysis computed `score_a * score_b`, which is always less
  than or equal to either input, so it structurally inverted the compound
  disadvantage it documented. Rebuilt on a noisy-OR independence baseline with
  an amplification ratio that distinguishes superadditive (Crenshaw),
  independent, and buffered interactions.
- `cultural_inclusion_index()` ignored the reference distribution's values
  entirely — a balanced target and a 98/1/1 target both returned `1.0`. Rebuilt
  on Jensen-Shannon divergence over actual proportions.
- The iWEAT compound effect computed `actual - (axis1_effect + axis2_effect)`,
  which expands to zero for every possible input. The headline intersectionality
  metric was mathematically guaranteed to return `0.0`. Replaced with the
  difference-in-differences interaction term; the permutation test is now
  two-sided so negative interactions are detectable.
- `iWEATAnalyzer` measured association with an unnormalised dot product while
  `WEATAnalyzer` used cosine similarity, so the two disagreed on the same
  inputs and association strength was conflated with embedding magnitude.
- A `max()` over an empty sequence crashed dimension scoring in all seven
  lenses whenever `use_semantic=False`.

### Fixed — silent failure modes

- `_run_weat` swallowed every exception with a bare `except Exception: pass`,
  making a malformed word list indistinguishable from "no bias found". Failures
  are now logged and excluded explicitly.
- `run_iweat=True` assigned an empty dict; the public parameter silently did
  nothing. Now wired to real iWEAT execution.
- Regex patterns matched stereotypes being *quoted in order to refute them*
  ("the myth that African cultures are primitive" scored as biased). Added a
  shared negation guard across all seven lenses.
- Several patterns fired on bare topic-word co-occurrence rather than the
  harmful claim — "sustainably harvest timber from the forest" and "police
  vowed to prevent any attack on religious minorities" both scored as harms.
- `library_version` in provenance records read the *installed* distribution's
  metadata, so a record could name a different version than the source that
  produced it, or `"dev"` when run from a checkout.

### Multilingual

- Prototype translation coverage completed across all six supported languages;
  Buddhist, Hindu and Indigenous went from 0–70% to full coverage.
- Added per-language similarity calibration. The embedding model represents
  some languages coarsely enough that every sentence looks similar to every
  other, which inflated all dimensions uniformly — Hindi benign text scored
  0.72–0.82 across every dimension. Scores are now calibrated against each
  language's measured background similarity.
- The lexical (regex) channel exists only in English. It previously scored a
  structural `0.0` for other languages, deducting a flat 30% that read as "less
  biased" rather than "less measurable". The semantic channel is now
  renormalised to full weight when the lexical channel is unavailable.
- `LensScore` gained `analysis_coverage` and `warnings`; confidence now scales
  with how much of the pipeline actually applied instead of being a flat
  0.88/0.55. Degradation is reported through the API rather than to stdout.
- Language is detected per text rather than from `dataset[0]`, so a mixed
  corpus is no longer scored entirely in the first text's language.

### Added — dimension-level cross-cultural reasoning

- `frameworks/dimension_map.py` reads ten shared moral constructs beneath the
  per-lens scalars (e.g. Islamic `dignity_violation` and Hindu `dignity_harm`
  both express human dignity), reporting cross-tradition consensus and —
  critically — harms visible through only one tradition, which a single
  consensus score averages into invisibility.
- `ScoredResult.tradition_specific_findings()` and `.consensus_findings()`.
- WEAT word lists for `buddhist_v1`, `hindu_v1` and `indigenous_v1`; all seven
  lenses now produce suites (previously four, with three silently skipped).

### Lens parity and internals

- Buddhist, Hindu and Indigenous lenses gained dedicated per-category regex,
  tradition-weighted dimensions and specific recommendations, replacing a
  generic scorer that broadcast one undifferentiated regex hit across every
  dimension at equal weight.
- Prototype `severity` (hand-graded 0.60–1.00) was loaded but never used; it
  now scales each prototype's contribution.
- Conflict detection and synergy amplification extended to cover all seven
  lenses.
- Per-lens duplicated scoring and bootstrap code lifted into `EthicalLens`.
- Framework-level results now carry `peak`/`p90` alongside the mean, so
  concentrated harm is not diluted by corpus size.

### Testing

- The embedding mock returned an all-ones vector for every input, making cosine
  similarity exactly 1.0 for every pair. Lenses could not distinguish a matching
  prototype from an unrelated one, and assertions of the form "biased text
  scores high" passed without exercising the detector. Replaced with
  deterministic bag-of-words embeddings that preserve relative structure.
- Smoke tests asserting absolute thresholds (one asserted `> 0.5` on a
  dimension weighted `0.05`, unreachable legitimately) rewritten to assert
  structural properties that hold independent of embedding scale.

### Known limitations

- Prototype translations and non-English WEAT word lists are machine-generated
  and unreviewed. They are semantic anchors that directly determine scores, so
  a mistranslation silently corrupts every result in that language. Each file
  records this in a `translation_provenance` block; have a fluent reviewer
  confirm before treating non-English output as authoritative.
- All six supported languages are colonial/majority languages. The Indigenous
  lens cannot currently analyse text in the languages of the communities it
  exists to protect; adding those requires community partnership and
  CARE-aligned data governance, not machine translation.
- `compute_age_distribution` and `compute_gender_distribution` remain stubs.
- Calibrator and drift-monitor state is shared across requests on a
  process-wide `Analyzer`.
