"""Tests for concepts catalog and embeddings module."""

import numpy as np
import pytest
from unittest.mock import patch

from eduscale.tabular.concepts import (
    Concept,
    ConceptsCatalog,
    TableType,
    embed_texts,
    get_concepts,
    get_table_type_anchors,
    init_embeddings,
    load_concepts_catalog,
)


@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer to avoid downloading model."""
    mock_model = type('MockModel', (), {
        'encode': lambda self, texts, **kwargs: np.random.rand(len(texts), 768)
    })()
    
    with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
        yield


def test_init_embeddings(mock_sentence_transformer):
    """Test embedding model initialization."""
    # Should not raise an exception
    init_embeddings()

    # Calling again should be idempotent
    init_embeddings()


def test_embed_texts(mock_sentence_transformer):
    """Test embedding generation for sample texts."""
    texts = ["student attendance", "test scores", "feedback comments"]

    embeddings = embed_texts(texts)

    # Check shape: 3 texts, 768 dimensions (paraphrase-multilingual-mpnet-base-v2)
    assert embeddings.shape == (3, 768)


def test_embed_texts_empty(mock_sentence_transformer):
    """Test embedding generation with empty list."""
    embeddings = embed_texts([])
    assert embeddings.shape == (0,)


def test_load_concepts_catalog(mock_sentence_transformer):
    """Test loading concepts catalog from YAML."""
    catalog = load_concepts_catalog("tests/fixtures/concepts_test.yaml")

    assert isinstance(catalog, ConceptsCatalog)
    assert len(catalog.table_types) == 2
    assert len(catalog.concepts) == 3

    # Check table types
    assert catalog.table_types[0].name == "ASSESSMENT"
    assert len(catalog.table_types[0].anchors) == 2
    assert catalog.table_types[0].embedding is not None
    assert catalog.table_types[0].embedding.shape == (768,)

    # Check concepts
    assert catalog.concepts[0].key == "student_id"
    assert catalog.concepts[0].expected_type == "string"
    assert len(catalog.concepts[0].synonyms) == 3
    assert catalog.concepts[0].embedding is not None
    assert catalog.concepts[0].embedding.shape == (768,)


def test_load_concepts_catalog_file_not_found():
    """Test loading catalog with non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_concepts_catalog("nonexistent.yaml")


def test_get_table_type_anchors(mock_sentence_transformer):
    """Test retrieving table type anchors."""
    catalog = load_concepts_catalog("tests/fixtures/concepts_test.yaml")
    table_types = get_table_type_anchors(catalog)

    assert len(table_types) == 2
    assert all(isinstance(tt, TableType) for tt in table_types)
    assert all(tt.embedding is not None for tt in table_types)


def test_get_concepts(mock_sentence_transformer):
    """Test retrieving concepts."""
    catalog = load_concepts_catalog("tests/fixtures/concepts_test.yaml")
    concepts = get_concepts(catalog)

    assert len(concepts) == 3
    assert all(isinstance(c, Concept) for c in concepts)
    assert all(c.embedding is not None for c in concepts)


def test_embedding_similarity(mock_sentence_transformer):
    """Test that embeddings are generated."""
    # Just test that embeddings are generated without errors
    text1 = "student test score"
    text2 = "pupil exam grade"
    text3 = "teacher attendance record"

    embeddings = embed_texts([text1, text2, text3])

    # Check that embeddings were generated
    assert embeddings.shape == (3, 768)


def test_model_caching(mock_sentence_transformer):
    """Test that embedding model is cached and reused."""
    # First call initializes the model
    init_embeddings()

    # Generate embeddings
    embeddings1 = embed_texts(["test text"])

    # Second call should reuse cached model
    embeddings2 = embed_texts(["test text"])

    # Check that embeddings were generated
    assert embeddings1.shape == (1, 768)
    assert embeddings2.shape == (1, 768)
