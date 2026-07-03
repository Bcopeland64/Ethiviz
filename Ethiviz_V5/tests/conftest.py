# tests/conftest.py
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_embedding_model():
    """
    Prevents tests from downloading model weights.
    Returns a constant unit vector so cosine similarity = 1.0 for all pairs,
    allowing score thresholds (> 0.5, > 0.3) in smoke tests to be exercised.
    """
    mock = MagicMock()
    # MiniLM-L12-v2 has 384 dimensions.  All-ones → cosine_sim(v, v) = 1.0.
    mock.encode.side_effect = lambda texts: np.ones(
        (len(texts) if isinstance(texts, list) else 1, 384),
        dtype=np.float32,
    )
    with patch("ethiviz.embeddings.model.EmbeddingModel.instance", return_value=mock):
        yield mock
