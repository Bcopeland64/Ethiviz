# EthiViz Version 9.5 Evaluation Plan

## Purpose

V9.5 adds a repeatable evaluation interface for EthiViz's existing seven-lens Analyzer.
It supports comparison to externally supplied human-reviewed labels and optional
reference/current distribution monitoring with Evidently AI. It does not add a validated
dataset, replace the Analyzer, certify results, or authorize consequential use.

## Implementation status

| Area | Status | Delivered | Still open |
|---|---|---|---|
| Supervised score evaluation | Implemented as tooling | CLI supports per-lens binary labels and reports accuracy, precision, recall, F1, conditional ROC AUC, Brier score, calibration gap, and confusion matrix. | Qualified annotation protocol, consented corpus, independent review, adequate sample sizes, and held-out evidence. |
| Distribution monitoring | Implemented as optional tooling | Evidently `DataDriftPreset` compares numeric lens scores and text lengths for reference/current inputs. | Representative reference profiles, operational monitoring/alerting, and qualified interpretation of material drift. |
| Privacy | Implemented in report shape | Aggregate JSON and numeric-only drift reports do not copy source text. | Dataset access, retention, deletion, backups, and operator controls remain deployment-specific. |
| Reproducibility | Partial | Explicit framework selection, threshold, semantic/lexical mode, machine-readable metrics, and CI tests. | Record and preserve corpus/annotation revisions, full environment, trained artifacts (if applicable), and approved evaluation runs. |
| Governance | Open | Documentation makes evidence limitations and reviewer requirements explicit. | Named evaluation owner, community authorization, independent review, risk acceptance, and use-specific approval. |

## Input contract

The current CSV requires a non-empty `text` column. Supervised labels are provided as
`label_<framework_id>` columns with values `0`, `1`, or blank. Annotation meaning is not
prescribed by the tool and must be agreed and documented by qualified reviewers for each
use context. A separate reference CSV can be used without labels for drift comparisons.
No sample labels or ground-truth examples are shipped.

## Release and claims

The V9.5 evaluator is infrastructure for collecting evidence, not the evidence itself.
Do not publish accuracy, calibration, fairness, cultural-validity, or production-readiness
claims until a suitable corpus, consent/provenance, reviewer qualifications, adjudication,
held-out analysis, limitations, and accountable approval are documented. Drift alerts do
not establish that a score is incorrect or harmful. Use the existing V9 operational
limitations and the [AI Governance Assessment](AI_Governance_Assessment/README.md) for
the broader release gates.
