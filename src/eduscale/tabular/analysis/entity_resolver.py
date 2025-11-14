"""Entity resolution module for matching entity names and IDs to canonical entities.

This module resolves entity variations (typos, initials, different formats) to
canonical entity IDs from BigQuery dimension tables using fuzzy matching and embeddings.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from Levenshtein import distance as levenshtein_distance
from sklearn.metrics.pairwise import cosine_similarity

from eduscale.tabular.concepts import embed_texts

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """Result of entity resolution."""

    entity_id: str
    entity_name: str
    entity_type: str
    similarity_score: float
    match_method: Literal["ID_EXACT", "NAME_EXACT", "FUZZY", "EMBEDDING", "NEW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    source_value: str  # Original value from source data


@dataclass
class EntityCache:
    """In-memory cache of entities for fast lookups during ingestion run."""

    # Name-based lookups (normalized_name -> entity_id)
    teachers: dict[str, str] = field(default_factory=dict)
    students: dict[str, str] = field(default_factory=dict)
    parents: dict[str, str] = field(default_factory=dict)
    regions: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    schools: dict[str, str] = field(default_factory=dict)

    # ID-based lookups (source_id -> canonical_entity_id)
    teacher_ids: dict[str, str] = field(default_factory=dict)
    student_ids: dict[str, str] = field(default_factory=dict)
    parent_ids: dict[str, str] = field(default_factory=dict)
    region_ids: dict[str, str] = field(default_factory=dict)
    subject_ids: dict[str, str] = field(default_factory=dict)
    school_ids: dict[str, str] = field(default_factory=dict)

    # Embeddings for semantic matching (entity_id -> embedding)
    teacher_embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    student_embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    parent_embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    region_embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    subject_embeddings: dict[str, np.ndarray] = field(default_factory=dict)
    school_embeddings: dict[str, np.ndarray] = field(default_factory=dict)

    # Reverse lookup (entity_id -> entity_name)
    entity_names: dict[str, str] = field(default_factory=dict)


def normalize_name(name: str) -> str:
    """Normalize name for matching.

    Args:
        name: Input name

    Returns:
        Normalized name

    Normalization steps:
        1. Convert to lowercase
        2. Remove extra whitespace
        3. Strip leading/trailing whitespace
        4. Remove periods from initials
        5. Standardize punctuation
    """
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Remove periods (common in initials)
    normalized = normalized.replace(".", "")

    # Replace multiple spaces with single space
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized


def expand_initials(name: str, region_id: str) -> list[str]:
    """Expand initials to common full names.

    Args:
        name: Name with initials (e.g., "И. Петров")
        region_id: Region ID for region-specific name databases

    Returns:
        List of candidate full names (max 5)

    Example:
        "И. Петров" -> ["иван петров", "игорь петров", "илья петров"]
    """
    # Check if name contains single-letter initials
    parts = name.split()
    if not parts:
        return []

    # Look for single letter or single letter with period
    initial_pattern = re.compile(r"^[а-яa-z]\.?$", re.IGNORECASE)

    candidates = []

    # Common Russian first names by initial
    russian_names = {
        "а": ["александр", "алексей", "андрей", "анна", "анастасия"],
        "б": ["борис"],
        "в": ["владимир", "виктор", "валентина", "вера"],
        "г": ["григорий", "георгий"],
        "д": ["дмитрий", "даниил", "дарья"],
        "е": ["евгений", "елена", "екатерина"],
        "ж": ["жанна"],
        "з": ["захар"],
        "и": ["иван", "игорь", "илья", "ирина"],
        "к": ["константин"],
        "л": ["леонид", "людмила"],
        "м": ["михаил", "максим", "мария", "марина"],
        "н": ["николай", "наталья"],
        "о": ["олег", "ольга"],
        "п": ["павел", "петр", "полина"],
        "р": ["роман"],
        "с": ["сергей", "светлана"],
        "т": ["татьяна", "тимофей"],
        "у": ["ульяна"],
        "ф": ["федор"],
        "ю": ["юрий", "юлия"],
        "я": ["яков"],
    }

    # Check if first part is an initial
    if len(parts) >= 2 and initial_pattern.match(parts[0]):
        initial = normalize_name(parts[0])[0]  # Get first letter
        last_name = " ".join(parts[1:])

        # Get common names for this initial
        first_names = russian_names.get(initial, [])

        # Generate candidates
        for first_name in first_names[:5]:  # Max 5 candidates
            candidate = f"{first_name} {normalize_name(last_name)}"
            candidates.append(candidate)

    return candidates


def resolve_entity(
    source_value: str,
    entity_type: str,
    region_id: str,
    cache: EntityCache,
    value_type: Literal["id", "name"] = "name",
    threshold_fuzzy: float = 0.85,
    threshold_embedding: float = 0.75,
) -> EntityMatch:
    """Resolve entity from source data to canonical ID.

    Args:
        source_value: Source ID or name
        entity_type: Type of entity (teacher, student, parent, region, subject, school)
        region_id: Region ID for context
        cache: Entity cache with loaded entities
        value_type: Whether source_value is "id" or "name"
        threshold_fuzzy: Threshold for fuzzy matching (default: 0.85)
        threshold_embedding: Threshold for embedding matching (default: 0.75)

    Returns:
        EntityMatch with match_method="NEW" if no match found

    Algorithm:
        1. If value_type == "id": Check cache for exact ID match
        2. Normalize input value (name)
        3. Check cache for exact normalized name match
        4. Try fuzzy matching with Levenshtein distance
        5. If name contains initials, expand and try all candidates
        6. Try embedding-based similarity matching
        7. If no match found, return NEW entity marker
    """
    if not source_value:
        logger.warning(f"Empty source_value for entity_type={entity_type}")
        return EntityMatch(
            entity_id="",
            entity_name="",
            entity_type=entity_type,
            similarity_score=0.0,
            match_method="NEW",
            confidence="LOW",
            source_value=source_value,
        )

    # Get appropriate cache dictionaries
    name_cache, id_cache, embedding_cache = _get_cache_dicts(cache, entity_type)

    # Step 1: ID exact match
    if value_type == "id" and source_value in id_cache:
        canonical_id = id_cache[source_value]
        entity_name = cache.entity_names.get(canonical_id, "")
        logger.debug(f"ID exact match: {source_value} -> {canonical_id}")
        return EntityMatch(
            entity_id=canonical_id,
            entity_name=entity_name,
            entity_type=entity_type,
            similarity_score=1.0,
            match_method="ID_EXACT",
            confidence="HIGH",
            source_value=source_value,
        )

    # Step 2: Normalize name
    normalized = normalize_name(source_value)

    # Step 3: Name exact match
    if normalized in name_cache:
        canonical_id = name_cache[normalized]
        entity_name = cache.entity_names.get(canonical_id, "")
        logger.debug(f"Name exact match: {normalized} -> {canonical_id}")
        return EntityMatch(
            entity_id=canonical_id,
            entity_name=entity_name,
            entity_type=entity_type,
            similarity_score=1.0,
            match_method="NAME_EXACT",
            confidence="HIGH",
            source_value=source_value,
        )

    # Step 4: Fuzzy matching
    best_fuzzy_match = _fuzzy_match(normalized, name_cache, threshold_fuzzy)
    if best_fuzzy_match:
        canonical_id, score = best_fuzzy_match
        entity_name = cache.entity_names.get(canonical_id, "")
        confidence = "HIGH" if score >= 0.85 else "MEDIUM"
        logger.debug(f"Fuzzy match: {normalized} -> {canonical_id} (score={score:.3f})")
        return EntityMatch(
            entity_id=canonical_id,
            entity_name=entity_name,
            entity_type=entity_type,
            similarity_score=score,
            match_method="FUZZY",
            confidence=confidence,
            source_value=source_value,
        )

    # Step 5: Expand initials and try fuzzy matching
    candidates = expand_initials(source_value, region_id)
    for candidate in candidates:
        if candidate in name_cache:
            canonical_id = name_cache[candidate]
            entity_name = cache.entity_names.get(canonical_id, "")
            logger.debug(f"Initial expansion match: {source_value} -> {candidate} -> {canonical_id}")
            return EntityMatch(
                entity_id=canonical_id,
                entity_name=entity_name,
                entity_type=entity_type,
                similarity_score=0.80,  # Slightly lower confidence for initial expansion
                match_method="FUZZY",
                confidence="MEDIUM",
                source_value=source_value,
            )

    # Step 6: Embedding-based matching
    if embedding_cache:
        best_embedding_match = _embedding_match(
            source_value, embedding_cache, cache.entity_names, threshold_embedding
        )
        if best_embedding_match:
            canonical_id, score = best_embedding_match
            entity_name = cache.entity_names.get(canonical_id, "")
            confidence = "HIGH" if score >= 0.75 else "MEDIUM"
            logger.debug(f"Embedding match: {source_value} -> {canonical_id} (score={score:.3f})")
            return EntityMatch(
                entity_id=canonical_id,
                entity_name=entity_name,
                entity_type=entity_type,
                similarity_score=score,
                match_method="EMBEDDING",
                confidence=confidence,
                source_value=source_value,
            )

    # Step 7: No match found - mark as NEW
    logger.info(f"No match found for {entity_type}: {source_value}, marking as NEW")
    return EntityMatch(
        entity_id="",
        entity_name=source_value,
        entity_type=entity_type,
        similarity_score=0.0,
        match_method="NEW",
        confidence="LOW",
        source_value=source_value,
    )


def create_new_entity(
    entity_type: str,
    source_value: str,
    region_id: str,
) -> str:
    """Create new entity in dimension table and return new ID.

    Note: This is a placeholder. Actual implementation would insert into BigQuery.

    Args:
        entity_type: Type of entity
        source_value: Source name/value
        region_id: Region ID

    Returns:
        New entity_id (UUID or hash-based)
    """
    # Generate deterministic ID based on entity_type, source_value, and region_id
    id_string = f"{entity_type}:{region_id}:{source_value}"
    entity_id = hashlib.sha256(id_string.encode()).hexdigest()[:16]

    logger.info(
        f"Created new entity: type={entity_type}, value={source_value}, "
        f"region={region_id}, id={entity_id}"
    )

    return entity_id


def _get_cache_dicts(
    cache: EntityCache, entity_type: str
) -> tuple[dict[str, str], dict[str, str], dict[str, np.ndarray]]:
    """Get appropriate cache dictionaries for entity type.

    Args:
        cache: Entity cache
        entity_type: Type of entity

    Returns:
        Tuple of (name_cache, id_cache, embedding_cache)
    """
    if entity_type == "teacher":
        return cache.teachers, cache.teacher_ids, cache.teacher_embeddings
    elif entity_type == "student":
        return cache.students, cache.student_ids, cache.student_embeddings
    elif entity_type == "parent":
        return cache.parents, cache.parent_ids, cache.parent_embeddings
    elif entity_type == "region":
        return cache.regions, cache.region_ids, cache.region_embeddings
    elif entity_type == "subject":
        return cache.subjects, cache.subject_ids, cache.subject_embeddings
    elif entity_type == "school":
        return cache.schools, cache.school_ids, cache.school_embeddings
    else:
        logger.warning(f"Unknown entity_type: {entity_type}")
        return {}, {}, {}


def _fuzzy_match(
    normalized_name: str, name_cache: dict[str, str], threshold: float
) -> tuple[str, float] | None:
    """Find best fuzzy match using Levenshtein distance.

    Args:
        normalized_name: Normalized input name
        name_cache: Cache of normalized_name -> entity_id
        threshold: Minimum similarity threshold (0-1)

    Returns:
        Tuple of (entity_id, similarity_score) or None if no match
    """
    best_match = None
    best_score = 0.0

    for cached_name, entity_id in name_cache.items():
        # Compute Levenshtein distance
        distance = levenshtein_distance(normalized_name, cached_name)

        # Convert to similarity score (0-1)
        max_len = max(len(normalized_name), len(cached_name))
        if max_len == 0:
            continue

        similarity = 1.0 - (distance / max_len)

        if similarity >= threshold and similarity > best_score:
            best_score = similarity
            best_match = (entity_id, similarity)

    return best_match


def _embedding_match(
    source_value: str,
    embedding_cache: dict[str, np.ndarray],
    entity_names: dict[str, str],
    threshold: float,
) -> tuple[str, float] | None:
    """Find best match using embedding similarity.

    Args:
        source_value: Source name/value
        embedding_cache: Cache of entity_id -> embedding
        entity_names: Cache of entity_id -> entity_name
        threshold: Minimum similarity threshold (0-1)

    Returns:
        Tuple of (entity_id, similarity_score) or None if no match
    """
    if not embedding_cache:
        return None

    # Generate embedding for source value
    source_embedding = embed_texts([source_value])[0]

    best_match = None
    best_score = 0.0

    for entity_id, cached_embedding in embedding_cache.items():
        # Compute cosine similarity
        similarity = float(
            cosine_similarity(
                source_embedding.reshape(1, -1), cached_embedding.reshape(1, -1)
            )[0][0]
        )

        if similarity >= threshold and similarity > best_score:
            best_score = similarity
            best_match = (entity_id, similarity)

    return best_match


def load_entity_cache(region_id: str) -> EntityCache:
    """Load entities from BigQuery for the region.

    Note: This is a placeholder. Actual implementation would query BigQuery.

    Args:
        region_id: Region ID to load entities for

    Returns:
        EntityCache with loaded entities
    """
    logger.info(f"Loading entity cache for region_id={region_id}")

    # Placeholder: In real implementation, would query BigQuery dimension tables
    cache = EntityCache()

    logger.info(
        f"Loaded entity cache: "
        f"{len(cache.teachers)} teachers, "
        f"{len(cache.students)} students, "
        f"{len(cache.parents)} parents"
    )

    return cache
