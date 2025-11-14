"""AI-powered column mapping module.

This module maps source DataFrame columns to canonical concepts using
semantic embeddings and type matching.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from eduscale.tabular.concepts import ConceptsCatalog, embed_texts

logger = logging.getLogger(__name__)


@dataclass
class ColumnMapping:
    """Mapping from source column to canonical concept."""

    source_column: str
    concept_key: str | None
    score: float
    status: Literal["AUTO", "LOW_CONFIDENCE", "UNKNOWN"]
    candidates: list[tuple[str, float]]  # Top-3 candidates with scores


def map_columns(
    df: pd.DataFrame, table_type: str, catalog: ConceptsCatalog
) -> list[ColumnMapping]:
    """Map DataFrame columns to canonical concepts using AI.

    Args:
        df: DataFrame with columns to map
        table_type: Classified table type
        catalog: Concepts catalog

    Returns:
        List of ColumnMapping objects for each column

    Algorithm:
        1. For each column: build description with samples, generate embedding, infer dtype
        2. Compute cosine similarity with all concept embeddings
        3. Apply type-based score adjustments
        4. Assign status: AUTO (>=0.75), LOW_CONFIDENCE (0.55-0.75), UNKNOWN (<0.55)
        5. Store top-3 candidates for explainability
    """
    if df.empty:
        logger.warning("Empty DataFrame, returning empty mappings")
        return []

    mappings = []

    for col in df.columns:
        mapping = _map_single_column(df, col, catalog)
        mappings.append(mapping)

        logger.info(
            f"Mapped column '{col}' -> '{mapping.concept_key}' "
            f"(status={mapping.status}, score={mapping.score:.3f})"
        )

    return mappings


def _map_single_column(
    df: pd.DataFrame, col: str, catalog: ConceptsCatalog
) -> ColumnMapping:
    """Map a single column to a concept.

    Args:
        df: DataFrame
        col: Column name
        catalog: Concepts catalog

    Returns:
        ColumnMapping for the column
    """
    # Build column description with samples
    description = _build_column_description(df, col)

    # Generate embedding for column
    col_embedding = embed_texts([description])[0]

    # Infer column data type
    col_dtype = _infer_column_type(df[col])

    # Compute similarity with all concepts
    concept_scores = []

    for concept in catalog.concepts:
        # Compute cosine similarity
        similarity = float(
            cosine_similarity(
                col_embedding.reshape(1, -1), concept.embedding.reshape(1, -1)
            )[0][0]
        )

        # Apply type-based score adjustments
        adjusted_score = _adjust_score_by_type(similarity, col_dtype, concept.expected_type)

        concept_scores.append((concept.key, adjusted_score))

    # Sort by score (descending)
    concept_scores.sort(key=lambda x: x[1], reverse=True)

    # Get top-3 candidates
    top_candidates = concept_scores[:3]

    # Get best match
    best_concept, best_score = top_candidates[0]

    # Assign status based on score
    if best_score >= 0.75:
        status = "AUTO"
        concept_key = best_concept
    elif best_score >= 0.55:
        status = "LOW_CONFIDENCE"
        concept_key = best_concept
    else:
        status = "UNKNOWN"
        concept_key = None

    return ColumnMapping(
        source_column=col,
        concept_key=concept_key,
        score=best_score,
        status=status,
        candidates=top_candidates,
    )


def _build_column_description(df: pd.DataFrame, col: str, max_samples: int = 5) -> str:
    """Build text description for a column.

    Args:
        df: DataFrame
        col: Column name
        max_samples: Maximum number of sample values

    Returns:
        Text description combining column name and sample values
    """
    # Start with column name
    description = f"Column name: {col}"

    # Add sample values
    sample_values = df[col].dropna().head(max_samples).tolist()

    if sample_values:
        sample_str = ", ".join(str(v) for v in sample_values)
        description += f". Sample values: {sample_str}"

    return description


def _infer_column_type(series: pd.Series) -> str:
    """Infer the data type of a column.

    Args:
        series: pandas Series

    Returns:
        One of: "number", "date", "string", "categorical"
    """
    # Check if numeric
    if pd.api.types.is_numeric_dtype(series):
        return "number"

    # Check if datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # Try to parse as datetime
    try:
        pd.to_datetime(series.dropna().head(10), errors="raise")
        return "date"
    except (ValueError, TypeError):
        pass

    # Check if categorical (low cardinality)
    unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
    if unique_ratio < 0.1 and series.nunique() < 50:
        return "categorical"

    # Default to string
    return "string"


def _adjust_score_by_type(
    similarity: float, col_type: str, concept_type: str
) -> float:
    """Adjust similarity score based on type matching.

    Args:
        similarity: Base cosine similarity score
        col_type: Inferred column type
        concept_type: Expected concept type

    Returns:
        Adjusted score

    Adjustments:
        - +0.1 if numeric column and concept type is "number"
        - +0.1 if datetime column and concept type is "date"
        - +0.05 if string column and concept type is "string" or "categorical"
        - -0.15 if types don't match
    """
    adjusted = similarity

    # Exact type matches get bonus
    if col_type == "number" and concept_type == "number":
        adjusted += 0.1
    elif col_type == "date" and concept_type == "date":
        adjusted += 0.1
    elif col_type in ["string", "categorical"] and concept_type in [
        "string",
        "categorical",
    ]:
        adjusted += 0.05
    # Type mismatch penalty
    elif col_type != concept_type:
        adjusted -= 0.15

    # Ensure score stays in valid range [0, 1]
    adjusted = max(0.0, min(1.0, adjusted))

    return adjusted
