# ethiviz/api.py
from __future__ import annotations
import numpy as np
from typing import Any, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from ethiviz.context.deployment import DeploymentContext
from ethiviz.scoring.calibration import PlattCalibrator
from ethiviz.scoring.drift import DriftMonitor
from ethiviz.utils.batch import BatchProcessor
from ethiviz.utils.reproducibility import ReproducibilityRecord
from ethiviz.frameworks.loader import FrameworkLoader
from ethiviz.frameworks.base import FrameworkRegistry
from ethiviz.lenses.western import WesternLens
from ethiviz.lenses.ubuntu import UbuntuLens
from ethiviz.lenses.confucian import ConfucianLens
from ethiviz.lenses.islamic import IslamicLens
from ethiviz.lenses.buddhist import BuddhistLens
from ethiviz.lenses.hindu import HinduLens
from ethiviz.lenses.indigenous import IndigenousLens
from ethiviz.scoring.base import ScoredResult, FrameworkScore, BiasCandidate
from ethiviz.scoring.multi_framework import MultiFrameworkScorer
from ethiviz.context.weights import get_weights
from ethiviz.context.regulatory import RegulatoryMapper
from ethiviz.reporting.base import BiasReport
from ethiviz.embeddings.language_detection import LanguageDetector
from ethiviz.analysis.weat import WEATAnalyzer, iWEATAnalyzer, WEATTestSuite, load_weat_tests
from ethiviz.frameworks.conflict import ConflictResolver


class Analyzer:
    """
    Primary entry point for EthiViz bias detection.

    Example:
        >>> from ethiviz.api import Analyzer
        >>> from ethiviz.context.deployment import DeploymentContext
        >>> ctx = DeploymentContext(region="US", domain="hiring",
        ...     primary_community="western", regulatory_framework="gdpr")
        >>> analyzer = Analyzer(deployment_context=ctx)
        >>> result = analyzer.analyze(["All women prefer caregiving to leadership."] * 5)
        >>> report = result.generate_report()
        >>> print(result.consensus_score)
    """

    def __init__(
        self,
        registry: FrameworkRegistry | None = None,
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
        self.registry = registry or FrameworkLoader().load_builtin()
        self.framework_ids = frameworks or self.registry.registered_ids
        self.deployment_context = deployment_context
        self.calibrator = calibrator or PlattCalibrator()
        self.drift_monitor = drift_monitor or DriftMonitor()
        self.use_semantic = use_semantic
        self.random_seed = random_seed
        self.n_bootstrap = n_bootstrap
        self.lang_detector = LanguageDetector()

        self.lenses: dict[str, Any] = {
            "western_v1": WesternLens(use_semantic=use_semantic),
            "ubuntu_v1": UbuntuLens(use_semantic=use_semantic),
            "confucian_v2": ConfucianLens(use_semantic=use_semantic),
            "islamic_v1": IslamicLens(use_semantic=use_semantic),
            "buddhist_v1": BuddhistLens(use_semantic=use_semantic),
            "hindu_v1": HinduLens(use_semantic=use_semantic),
            "indigenous_v1": IndigenousLens(use_semantic=use_semantic),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        dataset: List[str],
        mode: str = "text",
        weights: dict[str, float] | None = None,
        run_weat: bool = False,
        run_iweat: bool = False,
        dataset_source: str = "unknown",
        job_id: str | None = None,
        n_workers: int = 1,
    ) -> ScoredResult:
        """
        Analyse a dataset for bias through all registered ethical lenses.

        Returns a ScoredResult containing per-framework scores, per-text
        candidate scores, WEAT results (when run_weat=True), and full
        reproducibility metadata.
        """
        if not dataset:
            return ScoredResult(
                [], [], 0.0, [], [], None, None, self.deployment_context,
                ReproducibilityRecord.capture(self.framework_ids), {}
            )

        # 1. Language detection (use first text as representative)
        lang_res = self.lang_detector.detect(dataset[0])
        language = lang_res.language_code

        # 2. Parallel lens scoring across every text
        active_ids = [fid for fid in self.framework_ids if fid in self.lenses]

        def score_text(text: str) -> dict[str, Any]:
            return {fid: self.lenses[fid].score(text, language=language) for fid in active_ids}

        max_workers = min(max(1, len(dataset)), 8) if n_workers <= 1 else n_workers
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            all_lens_results = list(executor.map(score_text, dataset))

        # 3. Aggregate per framework; apply calibration + drift monitoring
        avg_framework_scores: list[FrameworkScore] = []
        candidates: list[BiasCandidate] = []
        per_text_scores: dict[str, list[float]] = {fid: [] for fid in active_ids}

        for fid in active_ids:
            text_scores = [res[fid].overall_score for res in all_lens_results]
            per_text_scores[fid] = text_scores
            avg_score = float(np.mean(text_scores))

            # Merge all dimension scores across texts (mean per dimension)
            all_dim_keys: set[str] = set()
            for res in all_lens_results:
                all_dim_keys.update(res[fid].dimension_scores.keys())
            dim_scores: dict[str, float] = {}
            for dim in all_dim_keys:
                dim_scores[dim] = float(np.mean([
                    res[fid].dimension_scores.get(dim, 0.0) for res in all_lens_results
                ]))

            # Calibration (Upgrade 9)
            calibrated: float | None = None
            if self.calibrator.is_fitted(fid):
                calibrated = self.calibrator.calibrate(avg_score, fid)

            # Drift monitoring (Upgrade 10)
            if self.drift_monitor:
                try:
                    self.drift_monitor.check_drift(fid, text_scores, dataset_source)
                except RuntimeError:
                    self.drift_monitor.record_snapshot(
                        fid, text_scores, dataset_source, set_as_baseline=True
                    )

            # Confidence interval (Upgrade 7) — bootstrap over per-text scores
            rng = np.random.default_rng(self.random_seed)
            arr = np.array(text_scores, dtype=float)
            boot_means = [
                rng.choice(arr, size=len(arr), replace=True).mean()
                for _ in range(min(self.n_bootstrap, 500))
            ]
            ci = (float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5)))

            avg_framework_scores.append(FrameworkScore(
                framework_id=fid,
                framework_name=fid.replace("_", " ").title(),
                overall_score=avg_score,
                calibrated_score=calibrated,
                dimension_scores=dim_scores,
                confidence=lang_res.confidence,
                flagged_candidates=[
                    dataset[i] for i, s in enumerate(text_scores) if s > 0.5
                ],
                confidence_interval_95=ci,
                bootstrap_n=self.n_bootstrap,
                raw_evidence={
                    "language": language,
                    "per_text_scores": text_scores,
                },
            ))

            for i, (res, score) in enumerate(zip(all_lens_results, text_scores)):
                if score > 0.5:
                    candidates.append(BiasCandidate(
                        text=dataset[i],
                        score=score,
                        lens_id=fid,
                        metadata={"dimension_scores": res[fid].dimension_scores},
                    ))

        # 4a. Conflict detection (Upgrade 4)
        score_map = {fs.framework_id: fs.overall_score for fs in avg_framework_scores}
        conflicts = ConflictResolver().detect(score_map)

        # 4b. Multi-framework aggregation + synergy amplification (Upgrade 14)
        scorer = MultiFrameworkScorer()
        effective_weights = weights
        if not effective_weights and self.deployment_context:
            effective_weights = get_weights(self.deployment_context)

        consensus, final_scores, synergy = scorer.aggregate(
            avg_framework_scores, weights=effective_weights
        )

        # 5. WEAT analysis (Upgrades 3, 17, 20)
        weat_results: dict[str, WEATTestSuite] | None = None
        if run_weat:
            weat_results = self._run_weat(active_ids, language)

        # 6. iWEAT (Upgrade 16) — placeholder for explicit calls
        iweat_results = None
        if run_iweat:
            iweat_results = {}

        # 7. Reproducibility record (Upgrade 18)
        repro = ReproducibilityRecord.capture(
            self.framework_ids,
            random_seed=self.random_seed,
            n_bootstrap=self.n_bootstrap,
        )

        result = ScoredResult(
            candidates=candidates,
            framework_scores=final_scores,
            consensus_score=consensus,
            conflicts=conflicts,
            synergy_amplifications=synergy,
            weat_results=weat_results,
            iweat_results=iweat_results,
            deployment_context=self.deployment_context,
            reproducibility=repro,
            metadata={
                "language_detected": language,
                "n_texts": len(dataset),
                "per_text_scores": per_text_scores,
                "texts": dataset,
                "source_type": "text",
            },
        )
        # Attach generate_report to this result instance
        result.generate_report = lambda: self._make_report(result)
        return result

    def quick_scan(self, texts: list[str]) -> BiasReport:
        """Single-call convenience wrapper that returns a BiasReport directly."""
        result = self.analyze(texts)
        mapping = None
        if self.deployment_context:
            mapping = RegulatoryMapper().map(result, self.deployment_context)
        return BiasReport(scored_result=result, compliance_mapping=mapping)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_weat(
        self, lens_ids: list[str], language: str
    ) -> dict[str, WEATTestSuite]:
        """Run all WEAT tests defined in weat_lists/ for each active lens."""
        weat_analyzer = WEATAnalyzer(n_permutations=1000)
        suites: dict[str, WEATTestSuite] = {}

        for lens_id in lens_ids:
            tests = load_weat_tests(lens_id, language=language)
            if not tests:
                continue
            results = []
            flagged = []
            for t in tests:
                try:
                    r = weat_analyzer.run(
                        test_name=t["test_name"],
                        lens_id=lens_id,
                        target_a=t["target_a"],
                        target_b=t["target_b"],
                        attribute_x=t["attribute_x"],
                        attribute_y=t["attribute_y"],
                    )
                    results.append(r)
                    if r.p_value < 0.05:
                        flagged.append(r.test_name)
                except Exception:
                    pass
            if results:
                suites[lens_id] = WEATTestSuite(
                    lens_id=lens_id,
                    results=results,
                    tests_flagged=flagged,
                )
        return suites

    def _make_report(self, result: ScoredResult) -> BiasReport:
        mapping = None
        if self.deployment_context:
            try:
                mapping = RegulatoryMapper().map(result, self.deployment_context)
            except Exception:
                pass
        return BiasReport(scored_result=result, compliance_mapping=mapping)
