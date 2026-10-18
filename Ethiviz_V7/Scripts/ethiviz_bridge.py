# Scripts/ethiviz_bridge.py
"""
Bridge between api_server.py's job-queue API and the real ethiviz.Analyzer
engine.

Prior to this module, api_server.py's run_analysis_job() called the legacy
Scripts/text_analyzer.py / image_analyzer.py pipeline, which never invoked the
ethiviz package's 7-lens cultural bias engine (western, ubuntu, confucian,
islamic, buddhist, hindu, indigenous) at all. This module replaces that call
site with real Analyzer calls, and reshapes the output into the JSON shape the
React frontend (project/src/utils/types.ts) already expects.
"""
from __future__ import annotations

import io
import json
import logging
import os
import sys
import threading
from typing import Any, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Ensure the ethiviz package is importable. It's a direct sibling of Scripts/
# inside Ethiviz_V5/ (mirrors the sys.path setup already done in
# Scripts/api_server.py).
_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)
_ethiviz_root = _parent_dir
if _ethiviz_root not in sys.path:
    sys.path.insert(0, _ethiviz_root)

from ethiviz import Analyzer, DeploymentContext  # noqa: E402
from ethiviz.scoring.base import ScoredResult  # noqa: E402
from ethiviz.metrics.group_fairness import TRADITION_THRESHOLDS  # noqa: E402
from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator  # noqa: E402

try:
    from ethiviz.detection.image import ImageDetectionBackend  # noqa: E402
    HAS_VISION = True
except ImportError as exc:
    ImageDetectionBackend = None  # type: ignore[assignment,misc]
    HAS_VISION = False
    logger.warning(
        "Vision dependencies not installed (%s). Image analysis will degrade "
        "to metadata-only proxies. Install with `bash start_ethiviz.sh --with-vision`.",
        exc,
    )


# ── Tradition name <-> engine framework-id mapping ───────────────────────────
# Explicit dict, not a f"{name}_v1" formula: confucian's real id is
# "confucian_v2", and Analyzer.analyze() silently drops any id not present in
# self.lenses (ethiviz/api.py), so a wrong id would silently produce zero
# scores for that tradition rather than erroring.
TRADITION_TO_FRAMEWORK_ID = {
    "western": "western_v1",
    "ubuntu": "ubuntu_v1",
    "confucian": "confucian_v2",
    "islamic": "islamic_v1",
    "buddhist": "buddhist_v1",
    "hindu": "hindu_v1",
    "indigenous": "indigenous_v1",
}
FRAMEWORK_ID_TO_TRADITION = {v: k for k, v in TRADITION_TO_FRAMEWORK_ID.items()}
ALL_FRAMEWORK_IDS = list(TRADITION_TO_FRAMEWORK_ID.values())


def resolve_framework_ids(selected_traditions: list[str] | None) -> list[str]:
    """Map plain tradition names (e.g. 'western') to engine framework ids
    (e.g. 'western_v1'). Unrecognized or empty selections fall back to all 7
    traditions rather than silently analyzing nothing.
    """
    ids = [
        TRADITION_TO_FRAMEWORK_ID[t.strip().lower()]
        for t in (selected_traditions or [])
        if t.strip().lower() in TRADITION_TO_FRAMEWORK_ID
    ]
    if not ids:
        logger.warning(
            "No recognized traditions in %r — defaulting to all 7.", selected_traditions
        )
        return list(ALL_FRAMEWORK_IDS)
    return ids


# ── Analyzer singleton ────────────────────────────────────────────────────────
# The frontend sends no region/domain/community fields today (verified against
# ConfigPanel.tsx), so these defaults are invented, overridable via env vars —
# same pattern already used by the otherwise-unused ethiviz/server.py.
_DEFAULT_CTX = DeploymentContext(
    region=os.environ.get("ETHIVIZ_REGION", "US"),
    domain=os.environ.get("ETHIVIZ_DOMAIN", "general"),
    primary_community=os.environ.get("ETHIVIZ_COMMUNITY", "global"),
    regulatory_framework=os.environ.get("ETHIVIZ_REGULATION", "none"),
)

_analyzer: Analyzer | None = None
_analyzer_lock = threading.Lock()


def get_analyzer() -> Analyzer:
    """Lazy singleton. All 7 lenses are always active; callers post-filter
    output to the traditions the user actually selected (resolve_framework_ids)
    rather than re-instantiating Analyzer per job, which would reload embedding
    models on every request.

    Analyzer.calibrator and .drift_monitor hold mutable state shared across
    every caller — api_server.py runs each job in its own thread/queued
    task (Scripts/analysis_queue.py, Upgrade 46), so concurrent jobs do
    reach this same instance concurrently. V7 Upgrade 47 put a
    threading.RLock + atomic writes around both (ethiviz/scoring/
    calibration.py, ethiviz/scoring/drift.py), closing the race this
    docstring used to flag as open; see tests/test_concurrency.py.
    """
    global _analyzer
    if _analyzer is None:
        with _analyzer_lock:
            if _analyzer is None:
                _analyzer = Analyzer(deployment_context=_DEFAULT_CTX, use_semantic=True)
    return _analyzer


_image_backend = None
_image_backend_lock = threading.Lock()


def get_image_backend():
    """Lazy singleton for the (optional, heavy) vision detection backend.
    Returns None if vision extras aren't installed — callers must degrade
    gracefully, not crash.
    """
    global _image_backend
    if not HAS_VISION:
        return None
    if _image_backend is None:
        with _image_backend_lock:
            if _image_backend is None:
                _image_backend = ImageDetectionBackend()
    return _image_backend


# ── Text dataset loading ──────────────────────────────────────────────────────

def load_text_dataset(text_input: str) -> list[str]:
    """Parse a text_input (a file path OR raw text content) into a list of
    texts, one per analysis item.

    CSV files use pandas so a 'text' column can be extracted directly (the
    bundled sample CSVs are `text,bias_level,category,notes` — naively joining
    every column would corrupt the text with metadata). JSON supports a list of
    strings or list of {"text": ...} objects. Anything else is treated as
    newline-delimited plain text.
    """
    if text_input and os.path.exists(text_input):
        with open(text_input, "rb") as f:
            raw = f.read()
        filename = text_input
        content = None
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            raise ValueError(f"Could not decode file as text: {text_input}")
    else:
        filename = ""
        content = text_input or ""

    if filename.endswith(".csv"):
        df = pd.read_csv(io.StringIO(content))
        if "text" in df.columns:
            texts = [str(v) for v in df["text"].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
        else:
            texts = [
                " ".join(str(v) for v in row if str(v).strip())
                for row in df.values.tolist()
            ]
    elif filename.endswith(".json"):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                texts = [
                    (item.get("text") if isinstance(item, dict) else str(item))
                    for item in data if item
                ]
            elif isinstance(data, dict):
                texts = [str(v) for v in data.values() if v]
            else:
                texts = [content]
        except json.JSONDecodeError:
            texts = [content]
    else:
        texts = [ln.strip() for ln in content.splitlines() if ln.strip()]

    texts = [t for t in texts if t]
    return texts or ["(empty input)"]


# ── Severity scaling ──────────────────────────────────────────────────────────
# Upgrade 54 (V7 Phase 3): each framework's own `severity_thresholds` YAML
# block (ethiviz/frameworks/builtin/*.yaml) is now parsed into
# CulturalFramework.severity_thresholds (ethiviz/frameworks/loader.py) — this
# used to import TRADITION_THRESHOLDS from ethiviz/metrics/group_fairness.py
# instead, a table for an unrelated AIF360-style group-fairness DIFFERENCE
# metric (SPD) that happens to share the same numbers as the YAML blocks
# (verified: byte-identical), not this engine's own declared cutoffs.
# Falling back to TRADITION_THRESHOLDS only covers a framework loaded without
# its own severity_thresholds block (e.g. a custom, non-builtin YAML).
#
# The raw cutoffs (~0-0.3) are still on that AIF360-difference-metric scale,
# not this engine's 0-1 overall_score (which the engine itself already flags
# at >0.5 — see FrameworkScore.flagged_candidates in ethiviz/api.py), so they
# still need rescaling rather than being applied literally — using them as-is
# would make every flagged score (>0.5) land in "critical" immediately,
# collapsing the high/moderate/low distinction entirely. Each tradition's
# cutoffs are rescaled so the highest tradition's "critical" cutoff lands
# exactly at the engine's 0.5 flag threshold, preserving each tradition's
# relative strictness from its own declared thresholds.
_FALLBACK_THRESHOLDS = TRADITION_THRESHOLDS
_REFERENCE_CRITICAL = max(t["critical"] for t in _FALLBACK_THRESHOLDS.values())
_SEVERITY_SCALE = 0.5 / _REFERENCE_CRITICAL


def _thresholds_for(framework_id: str) -> dict[str, float]:
    framework = get_analyzer().registry.get(framework_id)
    if framework is not None and framework.severity_thresholds:
        return framework.severity_thresholds
    return _FALLBACK_THRESHOLDS.get(framework_id, _FALLBACK_THRESHOLDS["western_v1"])


def _severity_for(framework_id: str, score: float) -> str:
    cutoffs = _thresholds_for(framework_id)
    if score >= cutoffs["critical"] * _SEVERITY_SCALE:
        return "critical"
    if score >= cutoffs["high"] * _SEVERITY_SCALE:
        return "high"
    if score >= cutoffs["moderate"] * _SEVERITY_SCALE:
        return "moderate"
    if score >= cutoffs["low"] * _SEVERITY_SCALE:
        return "low"
    return "unknown"


def compute_tradition_scores(
    result: ScoredResult,
    selected_fids: list[str],
    include_statistical_metrics: bool = False,
) -> list[dict]:
    """Aggregate per-lens scores into [{tradition, score, severity, confidence}],
    keyed by framework id — matches the ported CulturalFairnessHeatmap /
    CrossCulturalEquityDashboard components' hardcoded TRADITION_LABELS keys
    (e.g. 'confucian_v2'), verified directly against those files.
    """
    out = []
    for fs in result.framework_scores:
        if fs.framework_id not in selected_fids:
            continue
        score = fs.calibrated_score if fs.calibrated_score is not None else fs.overall_score
        entry = {
            "tradition": fs.framework_id,
            "score": round(float(score), 4),
            "severity": _severity_for(fs.framework_id, score),
            "confidence": round(float(fs.confidence), 4),
        }
        # translation_reviewed is None for English (nothing to review) and for
        # lenses with an undeclared provenance block; False means the result
        # relies on an unreviewed machine translation. Only surface it when
        # there's actually a caveat, so English-only runs stay uncluttered.
        translation_reviewed = fs.raw_evidence.get("translation_reviewed")
        if translation_reviewed is not True:
            entry["translation_reviewed"] = translation_reviewed
        if fs.raw_evidence.get("warnings"):
            entry["warnings"] = fs.raw_evidence["warnings"]
        # Upgrade 51: analysis_coverage was always computed (api.py averages
        # each LensScore.analysis_coverage into raw_evidence) but discarded
        # here before it ever reached api_server.py. Only surface it as a
        # caveat, same rule as translation_reviewed/warnings above — full
        # coverage (1.0) is the common case and shouldn't clutter every
        # response.
        coverage = fs.raw_evidence.get("analysis_coverage")
        if coverage is not None and coverage < 1.0:
            entry["analysis_coverage"] = round(float(coverage), 4)
        if include_statistical_metrics:
            entry["individual_fairness"] = _compute_individual_fairness(fs)
        out.append(entry)
    return out


def _compute_individual_fairness(fs) -> dict | None:
    """Upgrade 52: 'similar inputs should get similar scores' consistency
    check (ethiviz/metrics/individual_fairness.py), run directly on the
    per-text scores this lens already produced — unlike group fairness
    (SPD/DI/EOD/AOD) or any ethiviz/mitigation/ algorithm, this needs no
    protected-attribute group labels, which nothing in this app collects.
    Returns None (rather than raising) if there are too few texts for a
    meaningful neighbor comparison, so a single-text job doesn't fail
    /api/analyze — it just gets no individual_fairness entry."""
    per_text_scores = fs.raw_evidence.get("per_text_scores") or []
    if len(per_text_scores) < 3:
        return None
    try:
        calc_result = IndividualFairnessCalculator().compute(scores=list(per_text_scores))
    except Exception:
        logger.exception("Individual fairness computation failed for %s", fs.framework_id)
        return None
    return {
        "consistency_score": round(float(calc_result.consistency_score), 4),
        "sample_distortion_score": round(float(calc_result.sample_distortion_score), 4),
        "k_neighbors": calc_result.k_neighbors,
        "interpretation": calc_result.interpretation,
    }


def _merge_tradition_scores(score_lists: list[list[dict]]) -> list[dict]:
    """Averages score/confidence across multiple tradition_scores lists (e.g.
    one per image), recomputing severity from the averaged score."""
    if not score_lists:
        return []
    by_tradition: dict[str, list[dict]] = {}
    for scores in score_lists:
        for entry in scores:
            by_tradition.setdefault(entry["tradition"], []).append(entry)
    merged = []
    for fid, entries in by_tradition.items():
        avg_score = float(np.mean([e["score"] for e in entries]))
        avg_conf = float(np.mean([e["confidence"] for e in entries]))
        merged.append({
            "tradition": fid,
            "score": round(avg_score, 4),
            "severity": _severity_for(fid, avg_score),
            "confidence": round(avg_conf, 4),
        })
    return merged


def merge_tradition_scores_across_modalities(*score_lists: list[dict]) -> list[dict]:
    """Merges tradition_scores from text and image analysis (text_and_image mode)."""
    non_empty = [s for s in score_lists if s]
    if len(non_empty) <= 1:
        return non_empty[0] if non_empty else []
    return _merge_tradition_scores(non_empty)


# ── Text analysis bridge ──────────────────────────────────────────────────────

def _build_text_analysis_items(
    dataset: list[str], result: ScoredResult, selected_fids: list[str]
) -> list[dict]:
    """One item per input text, with a `{tradition}_ethics_score` per selected
    lens, matching project/src/utils/types.ts's TextAnalysisItem shape.

    Uses result.metadata['per_text_scores'] (a {framework_id: [score, ...]}
    dict, index-aligned to `dataset`) rather than result.candidates, since
    candidates only contains entries where score > 0.5 (ethiviz/api.py) and
    would silently drop most of the per-item, per-lens data.
    """
    per_text = result.metadata.get("per_text_scores", {})
    items = []
    for i, text in enumerate(dataset):
        per_tradition = {
            fid: per_text[fid][i]
            for fid in selected_fids
            if fid in per_text and i < len(per_text[fid])
        }
        values = list(per_tradition.values())
        item: dict[str, Any] = {
            "text_id": f"text_{i}",
            "original_text": text,
            # Mean overall_score across the selected lenses for this text.
            # Higher = more concerning, matching the engine's own >0.5 flag
            # convention. A simple mean, not a validated composite metric.
            "bias_score": round(float(np.mean(values)), 4) if values else None,
            # 1 - (max-min) spread across the selected lenses' scores for this
            # text: a heuristic cross-tradition-agreement proxy (1.0 = lenses
            # agreed exactly, 0.0 = maximal disagreement). Despite the field
            # name (inherited from the legacy engine's item shape), this does
            # NOT measure lexical/demographic diversity of the text's content.
            "diversity_index": (
                round(float(1 - (max(values) - min(values))), 4) if len(values) >= 2
                else (1.0 if values else None)
            ),
        }
        for fid, score in per_tradition.items():
            item[f"{FRAMEWORK_ID_TO_TRADITION[fid]}_ethics_score"] = round(float(score), 4)
        items.append(item)
    return items


def _serialize_dimension_findings(result: ScoredResult) -> dict:
    """Upgrade 51: extracts the dimension-level cross-cultural reading
    (which shared moral constructs a dataset triggers, and whether the 7
    traditions converge on it or only one flags it) plus the scalar-level
    conflicts/synergy amplifications — all already computed by
    Analyzer.analyze() (ethiviz/api.py's `construct_readings`/`conflicts`/
    `synergy_amplifications` on ScoredResult), but previously dropped here
    before reaching api_server.py's response. `is_consensus`/
    `is_tradition_specific` are read directly off each ConstructReading
    rather than calling result.consensus_findings()/
    tradition_specific_findings() separately (which just filter on the same
    two flags) — avoids walking construct_readings three times over.
    """
    readings = [
        {
            "construct_id": r.construct_id,
            "description": r.description,
            "scores": {k: round(float(v), 4) for k, v in r.scores.items()},
            "contributing_lenses": r.contributing_lenses,
            "mean_score": round(float(r.mean_score), 4),
            "spread": round(float(r.spread), 4),
            "flagged_lenses": r.flagged_lenses,
            "is_consensus": r.is_consensus,
            "is_tradition_specific": r.is_tradition_specific,
            "distinctive_lens": r.distinctive_lens,
            "interpretation": r.interpretation,
        }
        for r in result.construct_readings
    ]
    conflicts = [
        {
            "conflict_id": c.conflict_id,
            "conflict_type": c.conflict_type.value,
            "lenses_involved": c.lenses_involved,
            "lens_a_score": round(float(c.lens_a_score), 4),
            "lens_b_score": round(float(c.lens_b_score), 4),
            "divergence_score": round(float(c.divergence_score), 4),
            "resolution_strategy": c.resolution_strategy.value,
            "rationale": c.rationale,
        }
        for c in result.conflicts
    ]
    return {
        "construct_readings": readings,
        "consensus_findings": [r for r in readings if r["is_consensus"]],
        "tradition_specific_findings": [r for r in readings if r["is_tradition_specific"]],
        "conflicts": conflicts,
        "synergy_amplifications": list(result.synergy_amplifications),
    }


def run_text_analysis(
    text_input: str,
    selected_fids: list[str],
    job_id: str = "unknown",
    progress_callback: Callable[[int, int], None] | None = None,
    include_statistical_metrics: bool = False,
) -> tuple[list[dict], list[dict], dict]:
    """Returns (text_analysis_items, tradition_scores, dimension_findings).

    dimension_findings (Upgrade 51) is scoped to the text path only: the
    image path's per-image proxy sentences (see _analyze_one_image below)
    don't represent a coherent analyzed dataset in the same sense a real
    text corpus does, so cross-cultural dimension readings over them would
    mostly reflect noise from the synthesized description rather than the
    image content itself.
    """
    dataset = load_text_dataset(text_input)
    result = get_analyzer().analyze(
        dataset=dataset, dataset_source=job_id, progress_callback=progress_callback
    )
    items = _build_text_analysis_items(dataset, result, selected_fids)
    scores = compute_tradition_scores(
        result, selected_fids, include_statistical_metrics=include_statistical_metrics
    )
    dimension_findings = _serialize_dimension_findings(result)
    return items, scores, dimension_findings


# ── Image analysis bridge ─────────────────────────────────────────────────────

def _describe_detection(detection: dict) -> str:
    skin_tones = detection.get("skin_tones") or []
    cultural_elements = detection.get("cultural_elements") or []
    return (
        f"Image depicting {detection.get('n_faces', 0)} face(s). "
        f"Detected skin tones (Fitzpatrick scale): {', '.join(skin_tones) or 'none detected'}. "
        f"Cultural elements identified: {', '.join(cultural_elements) or 'none detected'}."
    )


def _analyze_one_image(path: str, selected_fids: list[str]) -> tuple[dict, list[dict]]:
    """Runs real detection (faces/skin-tone/cultural elements) via
    ImageDetectionBackend when vision extras are installed, then synthesizes a
    descriptive proxy sentence and scores it through the same 7-lens engine —
    reusing the pattern already present (but unreachable, since ethiviz/server.py
    is dead code) at ethiviz/server.py:161-191, extended to use the fuller
    ImageDetectionBackend (faces + skin tone + cultural elements together)
    rather than skin-tone alone.
    """
    from PIL import Image as PILImage

    backend = get_image_backend()
    if backend is not None:
        try:
            img = PILImage.open(path).convert("RGB")
            detection = backend.detect(np.array(img))
            proxy = _describe_detection(detection)
        except Exception as exc:
            logger.exception("Image detection failed for %s", path)
            detection = {"n_faces": 0, "skin_tones": [], "cultural_elements": []}
            proxy = f"Image uploaded for analysis; detection failed ({exc})."
    else:
        detection = {"n_faces": 0, "skin_tones": [], "cultural_elements": []}
        proxy = (
            "Image uploaded for analysis; vision detection dependencies "
            "(mediapipe/torch/transformers) are not installed. Install with "
            "`bash start_ethiviz.sh --with-vision` for real face/skin-tone/"
            "cultural-element detection."
        )

    result = get_analyzer().analyze(dataset=[proxy], dataset_source=os.path.basename(path))
    items = _build_text_analysis_items([proxy], result, selected_fids)
    analysis = {k: v for k, v in items[0].items() if k not in ("text_id", "original_text")}
    analysis["face_count"] = detection.get("n_faces", 0)
    analysis["object_count"] = len(detection.get("cultural_elements", []))
    tradition_scores = compute_tradition_scores(result, selected_fids)
    return {
        "analysis": analysis,
        "image_url": None,
        "original_path": path,
    }, tradition_scores


def run_image_analysis(
    image_paths: list[str],
    selected_fids: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[dict, list[dict]]:
    """Returns (image_analysis_dict, tradition_scores) — tradition_scores is
    averaged across all images when there is more than one."""
    image_results: dict[str, dict] = {}
    all_scores: list[list[dict]] = []
    total = len(image_paths)
    for i, path in enumerate(image_paths):
        name = os.path.basename(path)
        item, scores = _analyze_one_image(path, selected_fids)
        image_results[name] = item
        all_scores.append(scores)
        if progress_callback:
            progress_callback(i + 1, total)

    merged_scores = _merge_tradition_scores(all_scores)
    return image_results, merged_scores


# ── SQLite persistence shaping ────────────────────────────────────────────────

def to_sqlite_payload(tradition_scores: list[dict]) -> dict[str, dict]:
    """Reshape tradition_scores into JobStore.store_results' expected
    {framework_id: {metric_name: value}} shape (ethiviz/storage/job_store.py)."""
    return {
        entry["tradition"]: {
            "overall_score": entry["score"],
            "confidence": entry.get("confidence", 0.0),
            "severity": entry.get("severity", "unknown"),
        }
        for entry in tradition_scores
    }


def reconstruct_tradition_scores(rows: list[dict]) -> list[dict]:
    """Inverse of to_sqlite_payload — used by GET /api/analyze/results/<job_id>
    when a job's full result is no longer in the in-memory _jobs_fallback dict
    (e.g. after a server restart) but its aggregate scores were persisted.
    """
    by_tradition: dict[str, dict] = {}
    for row in rows:
        fid = row.get("framework_id")
        if not fid:
            continue
        entry = by_tradition.setdefault(fid, {"tradition": fid})
        metric = row.get("metric_name")
        if row.get("value") is not None:
            entry[metric] = row["value"]
        elif row.get("extra_json"):
            try:
                entry[metric] = json.loads(row["extra_json"])
            except (TypeError, ValueError):
                pass
    out = []
    for fid, entry in by_tradition.items():
        out.append({
            "tradition": fid,
            "score": entry.get("overall_score", 0.0),
            "severity": entry.get("severity", "unknown"),
            "confidence": entry.get("confidence", 0.0),
        })
    return out
