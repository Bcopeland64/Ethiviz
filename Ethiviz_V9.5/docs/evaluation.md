# V9.5 Evaluation Workflow

## Purpose and limits

The evaluator measures how per-lens scores compare with a supplied set of human-reviewed
binary labels and can compare score distributions between reference and current datasets
using Evidently AI. It is an evaluation utility, not a learned replacement model or an
automated claim that a lens is accurate, fair, culturally valid, or safe for consequential
use. No labeled corpus or threshold is provided as ground truth by this repository.

## Annotation contract

The input CSV must include one non-empty `text` field per record. For supervised
evaluation, add a `label_<framework_id>` column for each lens with annotations, using
`0` and `1` according to a documented, domain-specific protocol. Blank annotations are
excluded from that lens's calculation. Each lens is evaluated only against its matching
label column; annotations must not be copied across lenses without a defensible protocol.

Before using annotations, document the intended use and population, data provenance and
consent, annotator qualifications, label definitions, adjudication method, sample design,
language/domain coverage, and held-out review procedure. Keep source records under the
appropriate access, retention, and deletion controls. Do not put personal or sensitive
text into reports or commit evaluation data.

## Metrics

For each labeled lens, the JSON output reports thresholded accuracy, precision, recall,
F1, a confusion matrix, ROC AUC when both label classes exist, Brier score, and the
existing reliability-bucket calibration summary. Scores and metrics are conditional on
the selected threshold, corpus, label definitions, and analysis configuration. A single
aggregate metric can hide disagreement across languages, domains, and communities;
review those slices only where data collection is consented and statistically
meaningful. No built-in threshold is a validated decision boundary.

When `--reference` is supplied, the optional Evidently HTML report compares numeric lens
scores and text lengths between the two corpora. Drift is a prompt for investigation,
not proof of harm, model regression, or changed validity. Keep environment, code revision,
framework/prototype version, semantic-vs-lexical configuration, threshold, annotation
protocol, and corpus version with the evaluation record.

## Run

Install the optional dependency and run from `Ethiviz_V9.5/`:

```bash
pip install -e ".[evaluation]"
python Scripts/evaluate_system.py \
  --input /path/to/reviewed-evaluation.csv \
  --frameworks western_v1 ubuntu_v1 \
  --output /path/to/evaluation.json
```

For distribution comparison:

```bash
python Scripts/evaluate_system.py \
  --input /path/to/current.csv \
  --reference /path/to/reference.csv \
  --output /path/to/drift-summary.json \
  --html-output /path/to/drift-report.html
```

The JSON output contains aggregate values only. Evidently's report is built from numeric
scores and text lengths, not the original text. Treat reports as potentially sensitive
evaluation records nonetheless and apply the deployment's access and retention policy.
