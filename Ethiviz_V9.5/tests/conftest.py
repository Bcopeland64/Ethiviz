# tests/conftest.py
import re
import zlib

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

EMBED_DIM = 384  # MiniLM-L12-v2 dimensionality


def _word_vector(word: str) -> np.ndarray:
    """Deterministic pseudo-random unit vector for a single token."""
    seed = zlib.crc32(word.encode("utf-8")) & 0xFFFFFFFF
    return np.random.default_rng(seed).standard_normal(EMBED_DIM)


def fake_embed(text: str) -> np.ndarray:
    """
    Deterministic bag-of-words embedding.

    Texts sharing vocabulary land close together; unrelated texts land roughly
    orthogonal. That is the minimum realism a semantic-similarity test needs.

    The previous fixture returned an all-ones vector for *every* input, so
    cosine similarity was exactly 1.0 for every (input, prototype) pair. Under
    that mock a lens could not distinguish a matching prototype from an
    unrelated one, every dimension scored maximally, and any assertion of the
    form "biased text scores high" passed without exercising the detector at
    all. It also made background-relative calibration untestable, since signal
    and background were identical by construction.

    Works across scripts (Arabic, Devanagari, CJK) because tokens are hashed
    as raw unicode words rather than matched against an English lexicon.
    """
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    if not tokens:
        return np.zeros(EMBED_DIM, dtype=np.float32)
    vec = np.sum([_word_vector(t) for t in tokens], axis=0)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)


@pytest.fixture(autouse=True)
def mock_embedding_model():
    """
    Prevents tests from downloading model weights, while still producing
    embeddings with realistic relative structure (see fake_embed).
    """
    mock = MagicMock()

    def _encode(texts):
        if isinstance(texts, list):
            return np.vstack([fake_embed(t) for t in texts])
        return fake_embed(texts).reshape(1, -1)

    mock.encode.side_effect = _encode
    with patch("ethiviz.embeddings.model.EmbeddingModel.instance", return_value=mock):
        yield mock
