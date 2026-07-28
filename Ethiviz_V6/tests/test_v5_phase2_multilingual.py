"""
Phase 2 — multilingual reach and honest degradation.

Before this phase the platform was effectively an English detector: regex
patterns exist only in English (so the lexical channel scored a structural 0.0
for every other language), three lenses had 0-70% prototype translation
coverage with silent English fallback, and every result reported the same
confidence regardless. The same claim scored 0.07 in English and 0.00 in
Hindi, with identical reported confidence and no warning.
"""
from __future__ import annotations
import pathlib

import pytest
import yaml

from ethiviz.lenses.base import (
    CoverageReport,
    blend_scores,
    SEMANTIC_WEIGHT,
    REGEX_WEIGHT,
)
from ethiviz.lenses.hindu import HinduLens
from ethiviz.lenses.western import WesternLens

PROTOTYPE_DIR = pathlib.Path(__file__).parent.parent / "ethiviz/embeddings/prototypes"
SUPPORTED_LANGUAGES = ("ar", "zh", "es", "fr", "hi")


class TestBlendRenormalisation:
    def test_english_blends_both_channels(self):
        assert blend_scores(1.0, 0.0, regex_available=True) == pytest.approx(SEMANTIC_WEIGHT)
        assert blend_scores(0.0, 1.0, regex_available=True) == pytest.approx(REGEX_WEIGHT)

    def test_missing_regex_channel_renormalises_to_semantic(self):
        """Regression: a non-English input used to lose a flat 30% because the
        English-only regex channel scored 0.0, reading as 'less biased' rather
        than 'less measurable'."""
        assert blend_scores(1.0, 0.0, regex_available=False) == pytest.approx(1.0)
        assert blend_scores(0.5, 0.0, regex_available=False) == pytest.approx(0.5)

    def test_blend_is_bounded(self):
        assert blend_scores(1.0, 1.0, regex_available=True) <= 1.0
        assert blend_scores(2.0, 1.0, regex_available=False) <= 1.0


class TestCoverageReport:
    def test_full_coverage_english(self):
        c = CoverageReport("en", regex_available=True, translated_prototypes=10,
                           total_prototypes=10)
        assert c.coverage == pytest.approx(1.0)
        assert c.warnings() == []

    def test_missing_regex_reduces_coverage_and_warns(self):
        c = CoverageReport("fr", regex_available=False, translated_prototypes=10,
                           total_prototypes=10)
        assert c.coverage == pytest.approx(SEMANTIC_WEIGHT)
        assert any("Lexical" in w for w in c.warnings())

    def test_untranslated_prototypes_reduce_coverage_and_warn(self):
        c = CoverageReport("hi", regex_available=False, translated_prototypes=4,
                           total_prototypes=10)
        assert c.coverage < SEMANTIC_WEIGHT
        assert any("translation" in w for w in c.warnings())

    def test_semantic_disabled_renormalises_over_lexical_only(self):
        c = CoverageReport("en", regex_available=True, translated_prototypes=0,
                           total_prototypes=10, semantic_enabled=False)
        assert c.coverage == pytest.approx(1.0)

    def test_nothing_available_is_zero_coverage(self):
        c = CoverageReport("hi", regex_available=False, translated_prototypes=0,
                           total_prototypes=10, semantic_enabled=False)
        assert c.coverage == pytest.approx(0.0)


class TestLensReportsDegradation:
    def test_english_run_is_full_coverage_no_warnings(self):
        r = WesternLens(use_semantic=True).score("Some ordinary sentence.", language="en")
        assert r.analysis_coverage == pytest.approx(1.0)
        assert r.warnings == []

    def test_non_english_run_reports_coverage_and_warning(self):
        r = HinduLens(use_semantic=True).score(
            "जाति बुद्धि और क्षमता निर्धारित करती है।", language="hi"
        )
        assert r.analysis_coverage < 1.0
        assert r.warnings

    def test_confidence_scales_with_coverage(self):
        """Regression: confidence used to be a flat 0.88/0.55 regardless of how
        much of the pipeline actually ran."""
        lens = HinduLens(use_semantic=True)
        en = lens.score("Caste determines intelligence.", language="en")
        hi = lens.score("जाति बुद्धि और क्षमता निर्धारित करती है।", language="hi")
        assert en.confidence > hi.confidence


class TestTranslationCoverage:
    @pytest.mark.parametrize("lens_file", sorted(PROTOTYPE_DIR.glob("*_prototypes.yaml")))
    def test_every_prototype_covers_every_supported_language(self, lens_file):
        """Regression: buddhist/hindu/indigenous had 0-70% coverage, and the
        gaps silently fell back to English text compared against non-English
        input embeddings."""
        data = yaml.safe_load(lens_file.read_text(encoding="utf-8"))
        for proto in data["prototypes"]:
            translations = proto.get("translations") or {}
            missing = [l for l in SUPPORTED_LANGUAGES if l not in translations]
            assert not missing, (
                f"{lens_file.stem} prototype {proto['id']} missing: {missing}"
            )

    @pytest.mark.parametrize("lens_file", sorted(PROTOTYPE_DIR.glob("*_prototypes.yaml")))
    def test_translations_are_non_empty(self, lens_file):
        data = yaml.safe_load(lens_file.read_text(encoding="utf-8"))
        for proto in data["prototypes"]:
            for lang, text in (proto.get("translations") or {}).items():
                assert text and text.strip(), f"{proto['id']}/{lang} is empty"


class TestPerTextLanguageDetection:
    def test_mixed_language_dataset_detects_each_text(self):
        """Regression: language was detected from dataset[0] alone, so a mixed
        corpus was scored entirely in the first text's language."""
        from ethiviz.api import Analyzer

        analyzer = Analyzer(use_semantic=False, frameworks=["western_v1"])
        result = analyzer.analyze([
            "African cultures are primitive and contribute nothing.",
            "Les cultures africaines sont primitives.",
        ])
        assert result.metadata["mixed_language_dataset"] is True
        assert set(result.metadata["languages_per_text"]) == {"en", "fr"}
