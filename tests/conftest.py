"""Pytest configuration and shared fixtures."""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_sentence_transformers():
    """Mock SentenceTransformer to avoid downloading models during tests."""
    mock_model = MagicMock()
    
    # Mock encode method to return dummy embeddings
    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        # Return random embeddings with dimension 768 (paraphrase-multilingual-mpnet-base-v2)
        # Use fixed seed for reproducibility in tests
        np.random.seed(42)
        return np.random.rand(len(texts), 768).astype(np.float32)
    
    mock_model.encode.side_effect = mock_encode
    
    with patch('sentence_transformers.SentenceTransformer') as mock_st:
        mock_st.return_value = mock_model
        yield mock_st


@pytest.fixture(autouse=True)
def mock_openai_client():
    """Mock OpenAI client to avoid API calls during tests."""
    mock_client = MagicMock()
    
    # Mock chat completions
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"entities": [], "sentiment": 0.5}'
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = mock_client
        yield mock_openai

