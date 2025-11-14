"""AI-powered table classification module.

This module classifies DataFrames into table types (ATTENDANCE, ASSESSMENT, etc.)
using semantic embeddings and similarity matching.
"""

import logging
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from eduscale.tabular.concepts import ConceptsCatalog, embed_texts

logger = logging.getLogger(__name__)


def classify_table(df: pd.DataFrame, catalog: ConceptsCatalog) -> tuple[str, float]:
    """Classify table type using AI embeddings.

    Args:
        df: DataFrame to classify
        catalog: Concepts catalog with table type definitions

    Returns:
        Tuple of (table_type, confidence_score)
        Returns ("FREE_FORM", 0.0) if confidence is below threshold

    Algorithm:
        1. Extract features from column headers and sample values
        2. Generate embeddings for features
        3. Compute cosine similarity with table type anchors
        4. Apply softmax normalization
        5. Return type with highest score (or FREE_FORM if < 0.4)
    """
    if df.empty:
        logger.warning("Empty DataFrame, classifying as FREE_FORM")
        return "FREE_FORM", 0.0

    # Extract features from DataFrame
    features = _extract_features(df)

    if not features:
        logger.warning("No features extracted, classifying as FREE_FORM")
        return "FREE_FORM", 0.0

    # Generate embeddings for features
    logger.info(f"Generating embeddings for {len(features)} features")
    feature_embeddings = embed_texts(features)

    # Compute similarity with each table type
    table_type_scores = {}
    for table_type in catalog.table_types:
        # Compute cosine similarity between feature embeddings and table type embedding
        similarities = cosine_similarity(
            feature_embeddings, table_type.embedding.reshape(1, -1)
        )

        # Use mean similarity across all features
        mean_similarity = float(np.mean(similarities))
        table_type_scores[table_type.name] = mean_similarity

        logger.debug(
            f"Table type {table_type.name}: mean_similarity={mean_similarity:.3f}"
        )

    # Apply softmax normalization for calibrated probabilities
    scores_array = np.array(list(table_type_scores.values()))
    exp_scores = np.exp(scores_array - np.max(scores_array))  # Numerical stability
    softmax_scores = exp_scores / np.sum(exp_scores)

    # Map back to table types
    normalized_scores = dict(zip(table_type_scores.keys(), softmax_scores))

    # Get best match
    best_type = max(normalized_scores, key=normalized_scores.get)
    best_score = normalized_scores[best_type]

    logger.info(
        f"Classification result: {best_type} (confidence={best_score:.3f}), "
        f"all_scores={normalized_scores}"
    )

    # Check confidence threshold
    if best_score < 0.4:
        logger.warning(
            f"Low confidence ({best_score:.3f}), classifying as FREE_FORM"
        )
        return "FREE_FORM", best_score

    # Log contributing features
    _log_contributing_features(df, best_type, features[:5])

    return best_type, best_score


def _extract_features(df: pd.DataFrame, max_samples: int = 5) -> list[str]:
    """Extract text features from DataFrame for classification.

    Features include:
    - Column headers
    - Sample values from each column (up to max_samples non-null values)

    Args:
        df: DataFrame to extract features from
        max_samples: Maximum number of sample values per column

    Returns:
        List of feature strings
    """
    features = []

    for col in df.columns:
        # Add column header as feature
        col_feature = f"Column: {col}"

        # Get sample values (non-null)
        sample_values = df[col].dropna().head(max_samples).tolist()

        if sample_values:
            # Convert to strings and join
            sample_str = "; ".join(str(v) for v in sample_values)
            col_feature += f" | Values: {sample_str}"

        features.append(col_feature)

    return features


def _log_contributing_features(
    df: pd.DataFrame, table_type: str, top_features: list[str]
) -> None:
    """Log the top contributing features for classification decision.

    Args:
        df: Classified DataFrame
        table_type: Classified table type
        top_features: Top features that contributed to classification
    """
    logger.info(
        f"Classification decision for {table_type} based on features: "
        f"{top_features}"
    )

    # Log column headers for debugging
    logger.debug(f"DataFrame columns: {df.columns.tolist()}")
