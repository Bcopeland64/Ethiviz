import pytest
import numpy as np
from ethiviz.api import Analyzer
from ethiviz.scoring.calibration import PlattCalibrator
from ethiviz.scoring.drift import DriftMonitor
from ethiviz.analysis.weat import iWEATAnalyzer
from ethiviz.reporting.explainability import ScriptAwareTokenizer

def test_calibration_logic():
    cal = PlattCalibrator()
    # Provide enough samples to ensure both classes are in train and test splits
    scores = [0.1, 0.15, 0.2, 0.25, 0.3, 0.7, 0.75, 0.8, 0.85, 0.9]
    labels = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    cal.fit("western_v1", scores, labels, "test_corpus")
    assert cal.is_fitted("western_v1")
    prob = cal.calibrate(0.5, "western_v1")
    assert 0.0 <= prob <= 1.0

def test_drift_monitor_logic():
    monitor = DriftMonitor()
    lens_id = "western_v1"
    scores_baseline = [0.1, 0.2, 0.15, 0.1]
    monitor.record_snapshot(lens_id, scores_baseline, "base", set_as_baseline=True)
    
    scores_new = [0.8, 0.9, 0.85, 0.9]
    alert = monitor.check_drift(lens_id, scores_new, "new")
    assert alert.drift_detected is True
    assert alert.kl_divergence > 0

def test_iweat_analyzer_logic():
    analyzer = iWEATAnalyzer(n_permutations=10)
    identity_combinations = {
        "Black woman": ["term1"],
        "Black man": ["term2"],
        "white woman": ["term3"],
        "white man": ["term4"]
    }
    attribute_x = ["pleasant1"]
    attribute_y = ["unpleasant1"]
    
    result = analyzer.run("test_iweat", "western_v1", identity_combinations, attribute_x, attribute_y)
    assert result.test_name == "test_iweat"
    assert len(result.identity_combinations) == 4

def test_script_aware_tokenizer():
    import sys
    from unittest.mock import MagicMock
    
    # Mock jieba
    mock_jieba = MagicMock()
    mock_jieba.cut.return_value = ["你", "好"]
    sys.modules["jieba"] = mock_jieba
    
    # Mock stanza
    mock_stanza = MagicMock()
    mock_doc = MagicMock()
    mock_sent = MagicMock()
    mock_word = MagicMock()
    mock_word.text = "word"
    mock_sent.words = [mock_word]
    mock_doc.sentences = [mock_sent]
    mock_stanza.Pipeline.return_value = mock_stanza
    mock_stanza.return_value = mock_doc
    sys.modules["stanza"] = mock_stanza
    
    tokenizer = ScriptAwareTokenizer()
    # Whitespace
    assert tokenizer.tokenize("hello world", "latin") == ["hello", "world"]
    # Chinese
    assert tokenizer.tokenize("你好", "chinese") == ["你", "好"]
    # Arabic
    assert tokenizer.tokenize("text", "arabic") == ["word"]
    
    # Cleanup
    del sys.modules["jieba"]
    del sys.modules["stanza"]

def test_analyzer_pipeline():
    analyzer = Analyzer(frameworks=["western_v1"])
    dataset = ["This is a clean sentence.", "This is another one."]
    result = analyzer.analyze(dataset, dataset_source="test_run")
    assert result.consensus_score is not None
    assert result.reproducibility is not None
    assert "language_detected" in result.metadata
