# ethiviz/analysis/weat.py
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from itertools import combinations
from pathlib import Path
from typing import List, Dict, Any
import yaml
from ethiviz.embeddings.model import EmbeddingModel

WEAT_LISTS_DIR = Path(__file__).parent / "weat_lists"


def load_weat_tests(lens_id: str, language: str = "en") -> list[dict]:
    """
    Load WEAT test definitions for a lens from its YAML word list file.
    Returns a list of test dicts; each has test_name, target_a, target_b,
    attribute_x, attribute_y (all resolved to the requested language).
    Falls back to English when a translation is missing.
    """
    path = WEAT_LISTS_DIR / f"{lens_id}.yaml"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tests = []
    for t in data.get("tests", []):
        resolved: dict[str, Any] = {"test_name": t["test_name"]}
        for field_name in ("target_a", "target_b", "attribute_x", "attribute_y"):
            word_block = t.get(field_name, {})
            if isinstance(word_block, list):
                resolved[field_name] = word_block
            else:
                resolved[field_name] = word_block.get(language) or word_block.get("en", [])
        tests.append(resolved)
    return tests

@dataclass
class WEATResult:
    test_name: str
    lens_id: str
    effect_size: float
    p_value: float
    confidence_interval_95: tuple[float, float]
    interpretation: str

@dataclass
class WEATTestSuite:
    lens_id: str
    results: List[WEATResult]
    tests_flagged: List[str]

@dataclass
class iWEATResult:
    """
    Result of an Intersectional WEAT test.
    Measures compound bias at identity intersections.
    """
    test_name: str
    lens_id: str
    identity_combinations: list[str]      # e.g. ["Black woman", "Black man", ...]
    individual_effects: dict[str, float]  # dimension → effect size
    combination_effects: dict[str, float] # "A+B" → effect size
    compound_effect: float                # intersectional amplification term
    p_value: float
    confidence_interval_95: tuple[float, float]
    interpretation: str

class WEATAnalyzer:
    """
    Word Embedding Association Test (Caliskan et al., 2017).
    """
    def __init__(self, n_permutations: int = 5_000) -> None:
        self.n_permutations = n_permutations

    def run(
        self,
        test_name: str,
        lens_id: str,
        target_a: list[str],
        target_b: list[str],
        attribute_x: list[str],
        attribute_y: list[str],
    ) -> WEATResult:
        model = EmbeddingModel.instance()
        
        a_embs = model.encode(target_a)
        b_embs = model.encode(target_b)
        x_embs = model.encode(attribute_x)
        y_embs = model.encode(attribute_y)

        def s_w_ab(w_emb: np.ndarray) -> float:
            # Association of w with X vs Y
            cos_x = np.dot(x_embs, w_emb) / (np.linalg.norm(x_embs, axis=1) * np.linalg.norm(w_emb) + 1e-8)
            cos_y = np.dot(y_embs, w_emb) / (np.linalg.norm(y_embs, axis=1) * np.linalg.norm(w_emb) + 1e-8)
            return float(np.mean(cos_x) - np.mean(cos_y))

        s_a = np.array([s_w_ab(e) for e in a_embs])
        s_b = np.array([s_w_ab(e) for e in b_embs])
        
        test_statistic = np.sum(s_a) - np.sum(s_b)
        
        # Effect size (Cohen's d)
        all_s = np.concatenate([s_a, s_b])
        effect_size = (np.mean(s_a) - np.mean(s_b)) / (np.std(all_s) + 1e-8)
        
        # Permutation test
        combined = np.concatenate([s_a, s_b])
        n_a = len(s_a)
        rng = np.random.default_rng(seed=42)
        count = 0
        for _ in range(self.n_permutations):
            perm = rng.permutation(combined)
            if (np.sum(perm[:n_a]) - np.sum(perm[n_a:])) >= test_statistic:
                count += 1
        p_value = count / self.n_permutations

        # Bootstrap CI (Upgrade 7)
        boot_effects = []
        for _ in range(1000):
            idx_a = rng.integers(0, len(s_a), size=len(s_a))
            idx_b = rng.integers(0, len(s_b), size=len(s_b))
            boot_a = s_a[idx_a]
            boot_b = s_b[idx_b]
            boot_combined = np.concatenate([boot_a, boot_b])
            boot_effects.append((np.mean(boot_a) - np.mean(boot_b)) / (np.std(boot_combined) + 1e-8))
        ci = (
            float(np.percentile(boot_effects, 2.5)),
            float(np.percentile(boot_effects, 97.5))
        )
        
        return WEATResult(
            test_name=test_name,
            lens_id=lens_id,
            effect_size=float(effect_size),
            p_value=float(p_value),
            confidence_interval_95=ci,
            interpretation=f"WEAT effect size: {effect_size:.3f} (95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]), p={p_value:.4f}"
        )

    def run_benchmark_validation(self) -> dict[str, dict]:
        """Upgrade 17 — WEAT benchmark validation."""
        # Using snippet from lines 1982-2058 of build prompt
        CALISKAN_BENCHMARKS = {
            "flowers_vs_insects_pleasant_unpleasant": {"d": 1.50, "p": 0.016},
            "instruments_vs_weapons_pleasant_unpleasant": {"d": 1.53, "p": 0.012},
            "ea_names_vs_aa_names_pleasant_unpleasant": {"d": 1.41, "p": 0.032},
            "male_vs_female_career_family": {"d": 1.81, "p": 0.001},
            "math_vs_arts_male_female": {"d": 1.06, "p": 0.048},
        }
        BENCHMARK_WORD_LISTS = {
            "flowers_vs_insects_pleasant_unpleasant": {
                "target_a": ["aster", "clover", "hyacinth", "marigold", "poppy", "azalea"],
                "target_b": ["ant", "caterpillar", "flea", "hornet", "mosquito", "roach"],
                "attribute_x": ["caress", "freedom", "health", "love", "peace", "cheer"],
                "attribute_y": ["abuse", "crash", "filth", "murder", "sickness", "ugly"],
            },
            "male_vs_female_career_family": {
                "target_a": ["brother", "father", "uncle", "grandfather", "son", "boy"],
                "target_b": ["sister", "mother", "aunt", "grandmother", "daughter", "girl"],
                "attribute_x": ["executive", "management", "professional", "corporation",
                                "salary", "career"],
                "attribute_y": ["home", "parents", "children", "family", "cousins", "marriage"],
            },
        }
        report = {}
        for test_name, word_lists in BENCHMARK_WORD_LISTS.items():
            result = self.run(test_name=test_name, lens_id="benchmark", **word_lists)
            published = CALISKAN_BENCHMARKS.get(test_name, {})
            published_d = published.get("d", None)
            deviation = abs(result.effect_size - published_d) if published_d else None
            if deviation is not None:
                if deviation < 0.3:
                    interp = f"Close alignment with published figures (deviation={deviation:.2f}). Results are comparable to Caliskan et al. benchmarks."
                elif deviation < 0.7:
                    interp = f"Moderate deviation from published figures (deviation={deviation:.2f}). Results are directionally consistent but magnitudes differ."
                else:
                    interp = f"Large deviation from published figures (deviation={deviation:.2f}). This embedding model has substantially different bias characteristics than GloVe. Interpret WEAT effect sizes with caution."
            else:
                interp = "No published benchmark available for comparison."

            report[test_name] = {
                "published_d": published_d,
                "observed_d": round(result.effect_size, 3),
                "observed_p": round(result.p_value, 4),
                "deviation": round(deviation, 3) if deviation is not None else None,
                "interpretation": interp,
            }
        return report

class iWEATAnalyzer:
    """
    Intersectional Word Embedding Association Test.
    Upgrade 16 code from prompt.
    """
    def __init__(self, n_permutations: int = 5_000) -> None:
        self.n_permutations = n_permutations
        self._weat = WEATAnalyzer(n_permutations=n_permutations)

    def run(
        self,
        test_name: str,
        lens_id: str,
        identity_combinations: dict[str, list[str]],
        attribute_x: list[str],
        attribute_y: list[str],
    ) -> iWEATResult:
        model = EmbeddingModel.instance()

        # Compute individual dimension effects and combination effects
        individual_effects = {}
        combination_effects = {}

        # Get mean embedding per identity combination
        combo_embeddings = {}
        for label, terms in identity_combinations.items():
            embs = model.encode(terms)
            combo_embeddings[label] = embs.mean(axis=0)

        ax_embs = model.encode(attribute_x)
        ay_embs = model.encode(attribute_y)

        def assoc(emb: np.ndarray) -> float:
            cos_x = float(np.dot(ax_embs, emb).mean())
            cos_y = float(np.dot(ay_embs, emb).mean())
            return cos_x - cos_y

        # Associations for each combination
        assocs = {label: assoc(emb) for label, emb in combo_embeddings.items()}

        # Individual effects
        labels = list(identity_combinations.keys())
        for i, j in combinations(range(len(labels)), 2):
            pair_key = f"{labels[i]}_vs_{labels[j]}"
            diff = assocs[labels[i]] - assocs[labels[j]]
            individual_effects[pair_key] = diff

        # Compound effect: deviation from additivity
        combo_keys = list(assocs.keys())
        if len(combo_keys) == 4:
            # Standard 2x2 intersectional design
            k = {label: assocs[label] for label in combo_keys}
            try:
                bw = k[combo_keys[0]]  # Black woman
                bm = k[combo_keys[1]]  # Black man
                ww = k[combo_keys[2]]  # white woman
                wm = k[combo_keys[3]]  # white man
                race_effect = ((bw + bm) / 2) - ((ww + wm) / 2)
                gender_effect = ((bw + ww) / 2) - ((bm + wm) / 2)
                actual = bw - wm
                additive_prediction = race_effect + gender_effect
                compound = actual - additive_prediction
            except (KeyError, IndexError):
                compound = 0.0
        else:
            compound = 0.0

        # Permutation test on compound effect
        all_assocs = list(assocs.values())
        rng = np.random.default_rng(seed=42)
        perm_compounds = []
        for _ in range(self.n_permutations):
            perm = rng.permutation(all_assocs)
            if len(perm) == 4:
                r = ((perm[0] + perm[1]) / 2) - ((perm[2] + perm[3]) / 2)
                g = ((perm[0] + perm[2]) / 2) - ((perm[1] + perm[3]) / 2)
                a = perm[0] - perm[3]
                perm_compounds.append(a - (r + g))
        p_value = float(np.mean(np.array(perm_compounds) >= compound)) if perm_compounds else 0.5

        # Bootstrap CI
        boot_compounds = []
        for _ in range(1000):
            idxs = rng.integers(0, len(all_assocs), size=len(all_assocs))
            boot = [all_assocs[i] for i in idxs]
            if len(boot) == 4:
                r = ((boot[0] + boot[1]) / 2) - ((boot[2] + boot[3]) / 2)
                g = ((boot[0] + boot[2]) / 2) - ((boot[1] + boot[3]) / 2)
                a = boot[0] - boot[3]
                boot_compounds.append(a - (r + g))
        ci = (
            float(np.percentile(boot_compounds, 2.5)),
            float(np.percentile(boot_compounds, 97.5))
        ) if boot_compounds else (0.0, 0.0)

        interpretation = self._interpret(compound, p_value, test_name)
        return iWEATResult(
            test_name=test_name,
            lens_id=lens_id,
            identity_combinations=list(identity_combinations.keys()),
            individual_effects=individual_effects,
            combination_effects={f"{labels[i]}_vs_{labels[j]}":
                assocs[labels[i]] - assocs[labels[j]]
                for i, j in combinations(range(len(labels)), 2)},
            compound_effect=compound,
            p_value=p_value,
            confidence_interval_95=ci,
            interpretation=interpretation,
        )

    @staticmethod
    def _interpret(compound: float, p: float, name: str) -> str:
        if p >= 0.05:
            return f"{name}: No significant intersectional amplification (p={p:.3f})."
        strength = "strong" if abs(compound) > 0.3 else "moderate" if abs(compound) > 0.15 else "weak"
        direction = "amplified" if compound > 0 else "attenuated"
        return (
            f"{name}: {strength.capitalize()} intersectional bias {direction} "
            f"(compound effect={compound:.3f}, p={p:.3f}). "
            f"The bias at the intersection is {'greater' if compound > 0 else 'less'} "
            f"than the sum of individual dimension effects."
        )
