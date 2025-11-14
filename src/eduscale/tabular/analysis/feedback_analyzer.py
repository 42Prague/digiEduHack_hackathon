"""Feedback analysis module for detecting entity mentions in feedback text.

This module analyzes feedback text to identify mentioned entities (teachers, students,
subjects, etc.) and creates FeedbackTarget records linking feedback to entities.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from eduscale.core.config import settings
from eduscale.tabular.analysis.entity_resolver import (
    EntityCache,
    resolve_entity,
)
from eduscale.tabular.analysis.llm_client import LLMClient
from eduscale.tabular.concepts import embed_texts
from eduscale.tabular.pipeline import FrontmatterData

logger = logging.getLogger(__name__)


@dataclass
class FeedbackTarget:
    """Junction record linking feedback to detected entity."""

    feedback_id: str
    target_type: str  # teacher, student, parent, subject, region, school, experiment, criteria
    target_id: str  # Canonical entity ID
    relevance_score: float
    confidence: Literal["HIGH", "MEDIUM", "LOW"]


def analyze_feedback_batch(
    df_feedback: pd.DataFrame,
    region_id: str,
    frontmatter: FrontmatterData,
    entity_cache: EntityCache,
) -> list[FeedbackTarget]:
    """Analyze feedback DataFrame and return detected targets.

    This function processes feedback text to identify entity mentions using both
    LLM-based entity extraction and embedding-based similarity matching.

    Args:
        df_feedback: DataFrame with feedback data (must have feedback_id and feedback_text columns)
        region_id: Region ID for context
        frontmatter: Frontmatter metadata
        entity_cache: Loaded entity cache for resolution

    Returns:
        List of FeedbackTarget records for bulk insert to BigQuery

    Algorithm:
        1. For each feedback row, extract feedback_id and feedback_text
        2. Extract entity mentions from text using LLM
        3. Apply entity resolution to each mention
        4. Generate embedding for full feedback text
        5. Compute similarity with entity embeddings
        6. Combine LLM-based and embedding-based matches
        7. Deduplicate and select top-N targets per feedback
        8. Assign confidence levels based on scores
    """
    if df_feedback.empty:
        logger.info("Empty feedback DataFrame, skipping analysis")
        return []

    # Validate required columns
    required_cols = ["feedback_id", "feedback_text"]
    missing_cols = [col for col in required_cols if col not in df_feedback.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return []

    logger.info(f"Analyzing {len(df_feedback)} feedback records")

    all_targets = []
    llm_client = LLMClient()

    for idx, row in df_feedback.iterrows():
        feedback_id = row["feedback_id"]
        feedback_text = row.get("feedback_text", "")

        if not feedback_text or not isinstance(feedback_text, str):
            logger.debug(f"Skipping feedback {feedback_id}: empty or invalid text")
            continue

        logger.debug(f"Processing feedback {feedback_id}: {len(feedback_text)} chars")

        # Step 1: Extract entity mentions using LLM
        targets_from_llm = []
        if settings.LLM_ENABLED:
            try:
                entities = llm_client.extract_entities(feedback_text)
                logger.debug(f"Extracted {len(entities)} entity mentions from feedback {feedback_id}")

                # Step 2: Apply entity resolution to each mention
                for entity in entities:
                    entity_text = entity.get("text", "")
                    entity_type_hint = entity.get("type", "")

                    if not entity_text:
                        continue

                    # Resolve entity based on type hint
                    resolved_targets = _resolve_entity_mention(
                        entity_text=entity_text,
                        entity_type_hint=entity_type_hint,
                        feedback_id=feedback_id,
                        region_id=region_id,
                        entity_cache=entity_cache,
                    )
                    targets_from_llm.extend(resolved_targets)

            except Exception as e:
                logger.warning(f"LLM entity extraction failed for feedback {feedback_id}: {e}")

        # Step 3: Generate embedding for full feedback text
        targets_from_embedding = []
        if settings.FEEDBACK_ANALYSIS_ENABLED:
            try:
                targets_from_embedding = _embedding_based_matching(
                    feedback_text=feedback_text,
                    feedback_id=feedback_id,
                    entity_cache=entity_cache,
                )
            except Exception as e:
                logger.warning(f"Embedding-based matching failed for feedback {feedback_id}: {e}")

        # Step 4: Combine and deduplicate targets
        combined_targets = _combine_and_deduplicate_targets(
            targets_from_llm, targets_from_embedding
        )

        # Step 5: Select top-N targets
        top_targets = _select_top_targets(
            combined_targets, max_targets=settings.MAX_TARGETS_PER_FEEDBACK
        )

        all_targets.extend(top_targets)

        logger.debug(
            f"Feedback {feedback_id}: {len(targets_from_llm)} LLM targets, "
            f"{len(targets_from_embedding)} embedding targets, "
            f"{len(top_targets)} final targets"
        )

    logger.info(f"Created {len(all_targets)} feedback targets from {len(df_feedback)} feedback records")

    return all_targets


def _resolve_entity_mention(
    entity_text: str,
    entity_type_hint: str,
    feedback_id: str,
    region_id: str,
    entity_cache: EntityCache,
) -> list[FeedbackTarget]:
    """Resolve entity mention to canonical entity ID.

    Args:
        entity_text: Mentioned entity text
        entity_type_hint: Type hint from LLM (person, subject, location)
        feedback_id: Feedback ID
        region_id: Region ID
        entity_cache: Entity cache

    Returns:
        List of FeedbackTarget records (may be empty if no match)
    """
    targets = []

    if entity_type_hint == "person":
        # Try teacher, student, parent
        best_match = None
        best_score = 0.0

        for entity_type in ["teacher", "student", "parent"]:
            match = resolve_entity(
                source_value=entity_text,
                entity_type=entity_type,
                region_id=region_id,
                cache=entity_cache,
                value_type="name",
            )

            if match.similarity_score > best_score:
                best_score = match.similarity_score
                best_match = match

        if best_match and best_match.entity_id:
            confidence = _score_to_confidence(best_match.similarity_score)
            target = FeedbackTarget(
                feedback_id=feedback_id,
                target_type=best_match.entity_type,
                target_id=best_match.entity_id,
                relevance_score=best_match.similarity_score,
                confidence=confidence,
            )
            targets.append(target)

    elif entity_type_hint == "subject":
        match = resolve_entity(
            source_value=entity_text,
            entity_type="subject",
            region_id=region_id,
            cache=entity_cache,
            value_type="name",
        )

        if match.entity_id:
            confidence = _score_to_confidence(match.similarity_score)
            target = FeedbackTarget(
                feedback_id=feedback_id,
                target_type="subject",
                target_id=match.entity_id,
                relevance_score=match.similarity_score,
                confidence=confidence,
            )
            targets.append(target)

    elif entity_type_hint == "location":
        # Try region or school
        for entity_type in ["region", "school"]:
            match = resolve_entity(
                source_value=entity_text,
                entity_type=entity_type,
                region_id=region_id,
                cache=entity_cache,
                value_type="name",
            )

            if match.entity_id:
                confidence = _score_to_confidence(match.similarity_score)
                target = FeedbackTarget(
                    feedback_id=feedback_id,
                    target_type=entity_type,
                    target_id=match.entity_id,
                    relevance_score=match.similarity_score,
                    confidence=confidence,
                )
                targets.append(target)
                break  # Take first match

    return targets


def _embedding_based_matching(
    feedback_text: str,
    feedback_id: str,
    entity_cache: EntityCache,
) -> list[FeedbackTarget]:
    """Find entity matches using embedding similarity.

    Args:
        feedback_text: Feedback text
        feedback_id: Feedback ID
        entity_cache: Entity cache with embeddings

    Returns:
        List of FeedbackTarget records
    """
    targets = []

    # Generate embedding for feedback text
    feedback_embedding = embed_texts([feedback_text])[0]

    # Check similarity with all entity types
    entity_types = [
        ("teacher", entity_cache.teacher_embeddings),
        ("student", entity_cache.student_embeddings),
        ("parent", entity_cache.parent_embeddings),
        ("subject", entity_cache.subject_embeddings),
        ("region", entity_cache.region_embeddings),
        ("school", entity_cache.school_embeddings),
    ]

    for entity_type, embedding_cache in entity_types:
        if not embedding_cache:
            continue

        for entity_id, entity_embedding in embedding_cache.items():
            # Compute cosine similarity
            similarity = float(
                cosine_similarity(
                    feedback_embedding.reshape(1, -1),
                    entity_embedding.reshape(1, -1),
                )[0][0]
            )

            # Only include if above threshold
            if similarity >= settings.FEEDBACK_TARGET_THRESHOLD:
                confidence = _score_to_confidence(similarity)
                target = FeedbackTarget(
                    feedback_id=feedback_id,
                    target_type=entity_type,
                    target_id=entity_id,
                    relevance_score=similarity,
                    confidence=confidence,
                )
                targets.append(target)

    return targets


def _combine_and_deduplicate_targets(
    targets_llm: list[FeedbackTarget],
    targets_embedding: list[FeedbackTarget],
) -> list[FeedbackTarget]:
    """Combine and deduplicate targets from different sources.

    Args:
        targets_llm: Targets from LLM extraction
        targets_embedding: Targets from embedding matching

    Returns:
        Deduplicated list of targets with best scores
    """
    # Create dict keyed by (target_type, target_id)
    target_dict = {}

    for target in targets_llm + targets_embedding:
        key = (target.target_type, target.target_id)

        if key not in target_dict:
            target_dict[key] = target
        else:
            # Keep target with higher relevance score
            if target.relevance_score > target_dict[key].relevance_score:
                target_dict[key] = target

    return list(target_dict.values())


def _select_top_targets(
    targets: list[FeedbackTarget],
    max_targets: int,
) -> list[FeedbackTarget]:
    """Select top N targets by relevance score.

    Args:
        targets: List of targets
        max_targets: Maximum number of targets to return

    Returns:
        Top N targets sorted by relevance score
    """
    # Sort by relevance score descending
    sorted_targets = sorted(targets, key=lambda t: t.relevance_score, reverse=True)

    # Return top N
    return sorted_targets[:max_targets]


def _score_to_confidence(score: float) -> Literal["HIGH", "MEDIUM", "LOW"]:
    """Convert similarity score to confidence level.

    Args:
        score: Similarity score (0-1)

    Returns:
        Confidence level
    """
    if score >= 0.80:
        return "HIGH"
    elif score >= 0.65:
        return "MEDIUM"
    else:
        return "LOW"
