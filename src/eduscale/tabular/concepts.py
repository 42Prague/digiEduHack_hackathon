"""Concepts catalog and embeddings module for tabular ingestion.

This module loads the concepts catalog from YAML, manages the sentence-transformers
embedding model, and provides functions for generating embeddings.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sentence_transformers import SentenceTransformer

from eduscale.core.config import settings

logger = logging.getLogger(__name__)

# Module-level cache for embedding model (lazy loading)
_embedding_model = None


@dataclass
class Concept:
    """Canonical concept definition."""

    key: str
    description: str
    expected_type: str  # "string", "number", "date", "categorical"
    synonyms: list[str]
    embedding: np.ndarray | None = None


@dataclass
class TableType:
    """Table type definition with anchor phrases."""

    name: str
    anchors: list[str]
    embedding: np.ndarray | None = None


@dataclass
class ConceptsCatalog:
    """Complete concepts catalog with table types and concepts."""

    table_types: list[TableType]
    concepts: list[Concept]


def init_embeddings() -> None:
    """Load and cache the sentence-transformers model.

    This function loads the paraphrase-multilingual-mpnet-base-v2 model
    and caches it at module level for reuse across requests.
    """
    global _embedding_model

    if _embedding_model is not None:
        logger.debug("Embedding model already loaded")
        return

    try:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info(
            f"Embedding model loaded successfully: {settings.EMBEDDING_MODEL_NAME}"
        )
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed

    Returns:
        numpy array of shape (len(texts), 768) with embeddings

    Raises:
        RuntimeError: If embedding model is not initialized
    """
    if _embedding_model is None:
        init_embeddings()

    if not texts:
        return np.array([])

    try:
        # Generate embeddings with normalization
        embeddings = _embedding_model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return np.array(embeddings)
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


def load_concepts_catalog(path: str | None = None) -> ConceptsCatalog:
    """Load concepts catalog from YAML and precompute embeddings.

    Args:
        path: Path to concepts YAML file. If None, uses CONCEPT_CATALOG_PATH from settings.

    Returns:
        ConceptsCatalog with precomputed embeddings

    Raises:
        FileNotFoundError: If catalog file doesn't exist
        yaml.YAMLError: If catalog file is malformed
    """
    if path is None:
        path = settings.CONCEPT_CATALOG_PATH

    catalog_path = Path(path)
    if not catalog_path.exists():
        raise FileNotFoundError(f"Concepts catalog not found: {path}")

    logger.info(f"Loading concepts catalog from: {path}")

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Parse table types
    table_types = []
    for tt_data in data.get("table_types", []):
        table_type = TableType(name=tt_data["name"], anchors=tt_data["anchors"])
        table_types.append(table_type)

    # Parse concepts
    concepts = []
    for c_data in data.get("concepts", []):
        concept = Concept(
            key=c_data["key"],
            description=c_data["description"],
            expected_type=c_data["expected_type"],
            synonyms=c_data["synonyms"],
        )
        concepts.append(concept)

    logger.info(
        f"Loaded {len(table_types)} table types and {len(concepts)} concepts from catalog"
    )

    # Precompute embeddings for table type anchors
    logger.info("Precomputing embeddings for table type anchors...")
    for table_type in table_types:
        # Combine all anchors into a single text for embedding
        combined_text = " | ".join(table_type.anchors)
        table_type.embedding = embed_texts([combined_text])[0]

    # Precompute embeddings for concept synonyms
    logger.info("Precomputing embeddings for concept synonyms...")
    for concept in concepts:
        # Combine description and all synonyms for richer semantic representation
        combined_text = f"{concept.description}. Synonyms: {', '.join(concept.synonyms)}"
        concept.embedding = embed_texts([combined_text])[0]

    logger.info("Embeddings precomputed successfully")

    return ConceptsCatalog(table_types=table_types, concepts=concepts)


def get_table_type_anchors(catalog: ConceptsCatalog) -> list[TableType]:
    """Get all table types with embeddings.

    Args:
        catalog: Loaded concepts catalog

    Returns:
        List of TableType objects with precomputed embeddings
    """
    return catalog.table_types


def get_concepts(catalog: ConceptsCatalog) -> list[Concept]:
    """Get all concepts with embeddings.

    Args:
        catalog: Loaded concepts catalog

    Returns:
        List of Concept objects with precomputed embeddings
    """
    return catalog.concepts
