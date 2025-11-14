"""Tests for entity resolution."""

import numpy as np
import pytest

from eduscale.tabular.analysis.entity_resolver import (
    EntityCache,
    EntityMatch,
    normalize_name,
    expand_initials,
    resolve_entity,
    create_new_entity,
)


def test_normalize_name():
    """Test name normalization."""
    assert normalize_name("Иван Петров") == "иван петров"
    assert normalize_name("И. Петров") == "и петров"
    assert normalize_name("  Multiple   Spaces  ") == "multiple spaces"
    assert normalize_name("Name.With.Periods") == "namewithperiods"
    assert normalize_name("") == ""


def test_expand_initials():
    """Test initial expansion."""
    candidates = expand_initials("И. Петров", "region-01")

    assert len(candidates) > 0
    assert any("иван петров" in c for c in candidates)
    assert any("игорь петров" in c for c in candidates)
    assert any("илья петров" in c for c in candidates)


def test_expand_initials_no_initial():
    """Test expansion with no initials."""
    candidates = expand_initials("Иван Петров", "region-01")

    # Should return empty list if no initials found
    assert candidates == []


def test_resolve_entity_id_exact_match():
    """Test entity resolution with exact ID match."""
    cache = EntityCache()
    cache.teacher_ids["T001"] = "canonical-teacher-123"
    cache.entity_names["canonical-teacher-123"] = "Иван Петров"

    match = resolve_entity(
        source_value="T001",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="id",
    )

    assert match.entity_id == "canonical-teacher-123"
    assert match.match_method == "ID_EXACT"
    assert match.confidence == "HIGH"
    assert match.similarity_score == 1.0


def test_resolve_entity_name_exact_match():
    """Test entity resolution with exact name match."""
    cache = EntityCache()
    cache.teachers["иван петров"] = "canonical-teacher-123"
    cache.entity_names["canonical-teacher-123"] = "Иван Петров"

    match = resolve_entity(
        source_value="Иван Петров",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
    )

    assert match.entity_id == "canonical-teacher-123"
    assert match.match_method == "NAME_EXACT"
    assert match.confidence == "HIGH"
    assert match.similarity_score == 1.0


def test_resolve_entity_fuzzy_match():
    """Test entity resolution with fuzzy matching (typo)."""
    cache = EntityCache()
    cache.teachers["иван петров"] = "canonical-teacher-123"
    cache.entity_names["canonical-teacher-123"] = "Иван Петров"

    # Typo: "Иван Пeтров" (e instead of е)
    match = resolve_entity(
        source_value="Иван Пeтров",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
        threshold_fuzzy=0.80,  # Lower threshold to catch typo
    )

    assert match.entity_id == "canonical-teacher-123"
    assert match.match_method == "FUZZY"
    assert match.confidence in ["HIGH", "MEDIUM"]
    assert match.similarity_score > 0.80


def test_resolve_entity_initial_expansion():
    """Test entity resolution with initial expansion."""
    cache = EntityCache()
    cache.teachers["иван петров"] = "canonical-teacher-123"
    cache.entity_names["canonical-teacher-123"] = "Иван Петров"

    match = resolve_entity(
        source_value="И. Петров",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
    )

    # Should match through initial expansion
    assert match.entity_id == "canonical-teacher-123"
    assert match.match_method == "FUZZY"
    assert match.confidence in ["MEDIUM", "HIGH"]


def test_resolve_entity_no_match():
    """Test entity resolution with no match found."""
    cache = EntityCache()
    cache.teachers["иван петров"] = "canonical-teacher-123"

    match = resolve_entity(
        source_value="Неизвестный Учитель",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
    )

    assert match.entity_id == ""
    assert match.match_method == "NEW"
    assert match.confidence == "LOW"
    assert match.similarity_score == 0.0


def test_resolve_entity_empty_value():
    """Test entity resolution with empty value."""
    cache = EntityCache()

    match = resolve_entity(
        source_value="",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
    )

    assert match.entity_id == ""
    assert match.match_method == "NEW"
    assert match.confidence == "LOW"


def test_create_new_entity():
    """Test new entity creation."""
    entity_id = create_new_entity(
        entity_type="teacher",
        source_value="Новый Учитель",
        region_id="region-01",
    )

    # Should return a deterministic ID
    assert entity_id != ""
    assert len(entity_id) == 16  # SHA256 hash truncated to 16 chars

    # Same input should produce same ID (deterministic)
    entity_id2 = create_new_entity(
        entity_type="teacher",
        source_value="Новый Учитель",
        region_id="region-01",
    )
    assert entity_id == entity_id2


def test_resolve_entity_different_types():
    """Test entity resolution for different entity types."""
    cache = EntityCache()
    cache.students["петр иванов"] = "canonical-student-456"
    cache.entity_names["canonical-student-456"] = "Петр Иванов"

    match = resolve_entity(
        source_value="Петр Иванов",
        entity_type="student",
        region_id="region-01",
        cache=cache,
        value_type="name",
    )

    assert match.entity_id == "canonical-student-456"
    assert match.entity_type == "student"
    assert match.match_method == "NAME_EXACT"


def test_fuzzy_match_threshold():
    """Test that fuzzy matching respects threshold."""
    cache = EntityCache()
    cache.teachers["иван петров"] = "canonical-teacher-123"
    cache.entity_names["canonical-teacher-123"] = "Иван Петров"

    # Very different name should not match with high threshold
    match = resolve_entity(
        source_value="Совершенно Другое Имя",
        entity_type="teacher",
        region_id="region-01",
        cache=cache,
        value_type="name",
        threshold_fuzzy=0.85,  # High threshold
    )

    assert match.match_method == "NEW"  # Should not match


def test_entity_cache_structure():
    """Test EntityCache structure."""
    cache = EntityCache()

    # Test that all dictionaries are initialized
    assert isinstance(cache.teachers, dict)
    assert isinstance(cache.students, dict)
    assert isinstance(cache.teacher_ids, dict)
    assert isinstance(cache.teacher_embeddings, dict)
    assert isinstance(cache.entity_names, dict)

    # Test adding data
    cache.teachers["test"] = "id-123"
    assert cache.teachers["test"] == "id-123"
