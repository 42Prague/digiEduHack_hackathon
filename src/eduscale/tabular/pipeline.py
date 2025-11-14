"""Main pipeline orchestration for tabular ingestion.

This module contains the main pipeline logic including frontmatter parsing,
DataFrame loading, and orchestration of all pipeline stages.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class FrontmatterData:
    """Parsed frontmatter metadata from text files."""

    # Top-level fields
    file_id: str
    region_id: str
    text_uri: str
    event_id: str | None
    file_category: str | None

    # Original file metadata (from 'original' section)
    original_filename: str | None
    original_content_type: str | None
    original_size_bytes: int | None
    bucket: str | None
    object_path: str | None
    uploaded_at: str | None

    # Extraction metadata (from 'extraction' section)
    extraction_method: str | None
    extraction_timestamp: str | None
    extraction_success: bool | None
    extraction_duration_ms: int | None

    # Content metrics (from 'content' section)
    text_length: int | None
    word_count: int | None
    character_count: int | None

    # Document-specific metadata (from 'document' section)
    page_count: int | None
    sheet_count: int | None
    slide_count: int | None

    # Audio-specific metadata (from 'audio' section)
    audio_duration_seconds: float | None
    audio_sample_rate: int | None
    audio_channels: int | None
    audio_confidence: float | None
    audio_language: str | None


def parse_frontmatter(text_content: str) -> tuple[FrontmatterData | None, str]:
    """Parse YAML frontmatter and return metadata + clean text.

    Args:
        text_content: Full text content potentially containing YAML frontmatter

    Returns:
        Tuple of (frontmatter_data, text_without_frontmatter)
        If no frontmatter found or parsing fails, returns (None, original_text)

    The frontmatter format is:
        ---
        file_id: "abc123"
        region_id: "region-01"
        text_uri: "gs://bucket/text/abc123.txt"
        event_id: "cloudevent-xyz"
        file_category: "text" | "audio" | "tabular"
        
        original:
          filename: "doc.pdf"
          content_type: "application/pdf"
          size_bytes: 123456
          bucket: "bucket-name"
          object_path: "uploads/region/abc123.pdf"
          uploaded_at: "2025-01-14T10:30:00Z"
        
        extraction:
          method: "pdfplumber" | "google-speech-to-text"
          timestamp: "2025-01-14T10:31:00Z"
          duration_ms: 1234
          success: true
        
        content:
          text_length: 1234
          word_count: 987
          character_count: 1234
        
        document:
          page_count: 5
          sheet_count: 3
          slide_count: 10
        
        audio:
          duration_seconds: 123.45
          sample_rate: 16000
          channels: 1
          confidence: 0.95
          language: "en-US"
        ---
        <actual text content>
    """
    # Check if text starts with frontmatter delimiter
    if not text_content.startswith("---\n"):
        logger.debug("No frontmatter found (doesn't start with '---')")
        return None, text_content

    # Find the second delimiter
    try:
        # Split on first occurrence after the opening ---
        parts = text_content[4:].split("\n---\n", 1)
        if len(parts) != 2:
            logger.warning("Frontmatter delimiter not properly closed")
            return None, text_content

        yaml_content, clean_text = parts

        # Parse YAML
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            return None, text_content

        if not isinstance(data, dict):
            logger.warning("Frontmatter is not a valid YAML dictionary")
            return None, text_content

        # Extract top-level fields
        file_id = data.get("file_id", "")
        region_id = data.get("region_id", "")
        text_uri = data.get("text_uri", "")
        event_id = data.get("event_id")
        file_category = data.get("file_category")

        # Extract nested 'original' section
        original = data.get("original", {})
        original_filename = original.get("filename")
        original_content_type = original.get("content_type")
        original_size_bytes = original.get("size_bytes")
        bucket = original.get("bucket")
        object_path = original.get("object_path")
        uploaded_at = original.get("uploaded_at")

        # Extract nested 'extraction' section
        extraction = data.get("extraction", {})
        extraction_method = extraction.get("method")
        extraction_timestamp = extraction.get("timestamp")
        extraction_success = extraction.get("success")
        extraction_duration_ms = extraction.get("duration_ms")

        # Extract nested 'content' section
        content = data.get("content", {})
        text_length = content.get("text_length")
        word_count = content.get("word_count")
        character_count = content.get("character_count")

        # Extract nested 'document' section
        document = data.get("document", {})
        page_count = document.get("page_count")
        sheet_count = document.get("sheet_count")
        slide_count = document.get("slide_count")

        # Extract nested 'audio' section
        audio = data.get("audio", {})
        audio_duration_seconds = audio.get("duration_seconds")
        audio_sample_rate = audio.get("sample_rate")
        audio_channels = audio.get("channels")
        audio_confidence = audio.get("confidence")
        audio_language = audio.get("language")

        frontmatter = FrontmatterData(
            file_id=file_id,
            region_id=region_id,
            text_uri=text_uri,
            event_id=event_id,
            file_category=file_category,
            original_filename=original_filename,
            original_content_type=original_content_type,
            original_size_bytes=original_size_bytes,
            bucket=bucket,
            object_path=object_path,
            uploaded_at=uploaded_at,
            extraction_method=extraction_method,
            extraction_timestamp=extraction_timestamp,
            extraction_success=extraction_success,
            extraction_duration_ms=extraction_duration_ms,
            text_length=text_length,
            word_count=word_count,
            character_count=character_count,
            page_count=page_count,
            sheet_count=sheet_count,
            slide_count=slide_count,
            audio_duration_seconds=audio_duration_seconds,
            audio_sample_rate=audio_sample_rate,
            audio_channels=audio_channels,
            audio_confidence=audio_confidence,
            audio_language=audio_language,
        )

        # Log parsed metadata
        log_msg = (
            f"Parsed frontmatter for file_id={file_id}, "
            f"category={file_category}, "
            f"content_type={original_content_type}, "
            f"text_length={text_length}"
        )
        if audio_duration_seconds is not None:
            log_msg += f", audio_duration={audio_duration_seconds:.2f}s"
        if page_count is not None:
            log_msg += f", pages={page_count}"
        logger.info(log_msg)

        return frontmatter, clean_text.strip()

    except Exception as e:
        logger.error(f"Unexpected error parsing frontmatter: {e}")
        return None, text_content


import io
import re
from typing import Literal

import pandas as pd

from eduscale.core.config import settings


@dataclass
class TabularSource:
    """Source information for tabular data."""

    file_id: str
    region_id: str
    text_uri: str
    frontmatter: FrontmatterData


def load_dataframe_from_text(
    text_content: str, frontmatter: FrontmatterData
) -> pd.DataFrame:
    """Load text into DataFrame based on content type from frontmatter.

    Args:
        text_content: Clean text content (without frontmatter)
        frontmatter: Parsed frontmatter metadata

    Returns:
        pandas DataFrame with loaded data

    Raises:
        ValueError: If text cannot be parsed or exceeds row limit
        RuntimeError: If content type is not supported
    """
    content_type = frontmatter.original_content_type or "text/plain"

    logger.info(
        f"Loading DataFrame from text, content_type={content_type}, "
        f"text_length={len(text_content)}"
    )

    # Detect format from content type
    df = None

    if content_type in [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        # CSV or Excel (already converted to CSV text)
        df = _load_csv_text(text_content)

    elif content_type == "text/tab-separated-values":
        # TSV
        df = _load_csv_text(text_content, sep="\t")

    elif content_type == "application/json":
        # JSON or JSONL
        df = _load_json_text(text_content)

    elif content_type in ["application/pdf", "text/plain"] and frontmatter.extraction_method:
        # PDF or plain text that was extracted - treat as free-form observation
        df = pd.DataFrame({"text_content": [text_content]})

    else:
        # Try to auto-detect format
        logger.warning(f"Unknown content_type={content_type}, attempting auto-detection")
        df = _auto_detect_and_load(text_content)

    if df is None or df.empty:
        raise ValueError(f"Failed to load DataFrame from text, content_type={content_type}")

    # Normalize column names
    df.columns = df.columns.str.strip()
    original_columns = df.columns.tolist()

    # Convert to lower_snake_case
    df.columns = [_to_snake_case(col) for col in df.columns]

    logger.info(f"Normalized column names: {original_columns} -> {df.columns.tolist()}")

    # Drop completely empty columns
    empty_cols = df.columns[df.isna().all()].tolist()
    if empty_cols:
        logger.info(f"Dropping empty columns: {empty_cols}")
        df = df.drop(columns=empty_cols)

    # Check row limit
    if len(df) > settings.INGEST_MAX_ROWS:
        raise ValueError(
            f"DataFrame exceeds maximum rows: {len(df)} > {settings.INGEST_MAX_ROWS}"
        )

    logger.info(f"Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")

    return df


def _load_csv_text(text_content: str, sep: str = ",") -> pd.DataFrame:
    """Load CSV text into DataFrame.

    Args:
        text_content: CSV text content
        sep: Separator character (default: comma)

    Returns:
        pandas DataFrame
    """
    # Try UTF-8 first
    try:
        df = pd.read_csv(
            io.StringIO(text_content),
            sep=sep,
            engine="python",
            encoding="utf-8",
            on_bad_lines="skip",
        )
        return df
    except Exception as e:
        logger.warning(f"Failed to load with UTF-8 encoding: {e}")

    # Fallback to cp1250 (Central European)
    try:
        df = pd.read_csv(
            io.StringIO(text_content),
            sep=sep,
            engine="python",
            encoding="cp1250",
            on_bad_lines="skip",
        )
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV with cp1250 encoding: {e}")
        raise


def _load_json_text(text_content: str) -> pd.DataFrame:
    """Load JSON text into DataFrame.

    Handles both single JSON objects and JSONL (line-delimited JSON).

    Args:
        text_content: JSON text content

    Returns:
        pandas DataFrame
    """
    import json

    # Try single JSON object first
    try:
        data = json.loads(text_content)
        if isinstance(data, dict):
            # Single object - normalize
            df = pd.json_normalize(data)
        elif isinstance(data, list):
            # Array of objects
            df = pd.json_normalize(data)
        else:
            raise ValueError(f"Unexpected JSON type: {type(data)}")
        return df
    except json.JSONDecodeError:
        # Try JSONL (line-by-line)
        logger.info("Single JSON parse failed, trying JSONL")
        lines = text_content.strip().split("\n")
        records = []
        for line in lines:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line: {line[:50]}...")
                    continue

        if not records:
            raise ValueError("No valid JSON records found")

        df = pd.json_normalize(records)
        return df


def _auto_detect_and_load(text_content: str) -> pd.DataFrame:
    """Auto-detect format and load DataFrame.

    Args:
        text_content: Text content

    Returns:
        pandas DataFrame

    Raises:
        ValueError: If format cannot be detected
    """
    # Try CSV with different separators
    for sep in [",", "\t", "|", ";"]:
        try:
            df = _load_csv_text(text_content, sep=sep)
            if len(df.columns) > 1:  # At least 2 columns
                logger.info(f"Auto-detected separator: '{sep}'")
                return df
        except Exception:
            continue

    # Try JSON
    try:
        df = _load_json_text(text_content)
        logger.info("Auto-detected format: JSON")
        return df
    except Exception:
        pass

    # If all else fails, treat as free-form text
    logger.warning("Could not auto-detect format, treating as free-form text")
    return pd.DataFrame({"text_content": [text_content]})


def _to_snake_case(text: str) -> str:
    """Convert text to lower_snake_case.

    Args:
        text: Input text

    Returns:
        snake_case version of text
    """
    # Replace spaces and hyphens with underscores
    text = re.sub(r"[\s\-]+", "_", text)
    # Insert underscore before uppercase letters
    text = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
    # Convert to lowercase
    text = text.lower()
    # Remove multiple underscores
    text = re.sub(r"_+", "_", text)
    # Remove leading/trailing underscores
    text = text.strip("_")
    return text



from datetime import datetime, timezone
from typing import Any

from eduscale.tabular.analysis.entity_resolver import (
    EntityCache,
    resolve_entity,
)
from eduscale.tabular.analysis.llm_client import LLMClient


@dataclass
class ObservationRecord:
    """Record for free-form text observation."""

    file_id: str
    region_id: str
    text_content: str
    detected_entities: list[dict[str, Any]]
    sentiment_score: float
    original_content_type: str | None
    audio_duration_ms: int | None
    audio_confidence: float | None
    audio_language: str | None
    page_count: int | None
    ingest_timestamp: datetime


@dataclass
class ObservationTarget:
    """Junction record linking observation to detected entity."""

    observation_id: str  # Will be file_id for now
    target_type: str  # teacher, student, parent, subject, region, school
    target_id: str  # Canonical entity ID
    relevance_score: float
    confidence: str  # HIGH, MEDIUM, LOW


def process_free_form_text(
    text_content: str,
    frontmatter: FrontmatterData,
    entity_cache: EntityCache,
) -> tuple[ObservationRecord, list[ObservationTarget]]:
    """Process free-form text (PDF, audio transcript, unstructured feedback).

    Args:
        text_content: Clean text content (without frontmatter)
        frontmatter: Parsed frontmatter metadata
        entity_cache: Loaded entity cache for resolution

    Returns:
        Tuple of (observation_record, observation_targets)

    Algorithm:
        1. Extract entity mentions using LLM
        2. Apply entity resolution to each mention
        3. Compute sentiment score using LLM
        4. Create observation record with metadata
        5. Create observation_targets junction records
    """
    logger.info(
        f"Processing free-form text: file_id={frontmatter.file_id}, "
        f"content_type={frontmatter.original_content_type}, "
        f"text_length={len(text_content)}"
    )

    # Initialize LLM client
    llm_client = LLMClient()

    # Step 1: Extract entity mentions using LLM
    detected_entities = []
    if settings.LLM_ENABLED:
        try:
            entities = llm_client.extract_entities(text_content)
            detected_entities = entities
            logger.info(f"Extracted {len(entities)} entity mentions")
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
    else:
        logger.info("LLM disabled, skipping entity extraction")

    # Step 2: Apply entity resolution to each mention
    observation_targets = []
    for entity in detected_entities:
        entity_text = entity.get("text", "")
        entity_type_hint = entity.get("type", "")  # person, subject, location

        if not entity_text:
            continue

        # Map LLM entity type to our entity types
        # For "person", we need to determine if it's teacher/student/parent
        # We'll try all three and take the best match
        if entity_type_hint == "person":
            # Try teacher, student, parent
            best_match = None
            best_score = 0.0

            for entity_type in ["teacher", "student", "parent"]:
                match = resolve_entity(
                    source_value=entity_text,
                    entity_type=entity_type,
                    region_id=frontmatter.region_id,
                    cache=entity_cache,
                    value_type="name",
                )

                if match.similarity_score > best_score:
                    best_score = match.similarity_score
                    best_match = match

            if best_match and best_match.entity_id:
                target = ObservationTarget(
                    observation_id=frontmatter.file_id,
                    target_type=best_match.entity_type,
                    target_id=best_match.entity_id,
                    relevance_score=best_match.similarity_score,
                    confidence=best_match.confidence,
                )
                observation_targets.append(target)
                logger.debug(
                    f"Resolved person '{entity_text}' to {best_match.entity_type}: "
                    f"{best_match.entity_id} (score={best_match.similarity_score:.3f})"
                )

        elif entity_type_hint == "subject":
            match = resolve_entity(
                source_value=entity_text,
                entity_type="subject",
                region_id=frontmatter.region_id,
                cache=entity_cache,
                value_type="name",
            )

            if match.entity_id:
                target = ObservationTarget(
                    observation_id=frontmatter.file_id,
                    target_type="subject",
                    target_id=match.entity_id,
                    relevance_score=match.similarity_score,
                    confidence=match.confidence,
                )
                observation_targets.append(target)
                logger.debug(
                    f"Resolved subject '{entity_text}' to {match.entity_id} "
                    f"(score={match.similarity_score:.3f})"
                )

        elif entity_type_hint == "location":
            # Try region or school
            for entity_type in ["region", "school"]:
                match = resolve_entity(
                    source_value=entity_text,
                    entity_type=entity_type,
                    region_id=frontmatter.region_id,
                    cache=entity_cache,
                    value_type="name",
                )

                if match.entity_id:
                    target = ObservationTarget(
                        observation_id=frontmatter.file_id,
                        target_type=entity_type,
                        target_id=match.entity_id,
                        relevance_score=match.similarity_score,
                        confidence=match.confidence,
                    )
                    observation_targets.append(target)
                    logger.debug(
                        f"Resolved location '{entity_text}' to {entity_type}: "
                        f"{match.entity_id} (score={match.similarity_score:.3f})"
                    )
                    break  # Take first match

    logger.info(f"Created {len(observation_targets)} observation targets")

    # Step 3: Compute sentiment score using LLM
    sentiment_score = 0.0
    if settings.LLM_ENABLED:
        try:
            sentiment_score = llm_client.analyze_sentiment(text_content)
            logger.info(f"Sentiment score: {sentiment_score:.3f}")
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
    else:
        logger.info("LLM disabled, skipping sentiment analysis")

    # Step 4: Create observation record with metadata
    # Convert audio duration from seconds to milliseconds if available
    audio_duration_ms = None
    if frontmatter.audio_duration_seconds is not None:
        audio_duration_ms = int(frontmatter.audio_duration_seconds * 1000)

    observation = ObservationRecord(
        file_id=frontmatter.file_id,
        region_id=frontmatter.region_id,
        text_content=text_content,
        detected_entities=detected_entities,
        sentiment_score=sentiment_score,
        original_content_type=frontmatter.original_content_type,
        audio_duration_ms=audio_duration_ms,
        audio_confidence=frontmatter.audio_confidence,
        audio_language=frontmatter.audio_language,
        page_count=frontmatter.page_count,
        ingest_timestamp=datetime.now(timezone.utc),
    )

    # Log observation creation with metadata
    log_msg = (
        f"Created observation record: file_id={observation.file_id}, "
        f"entities={len(detected_entities)}, "
        f"targets={len(observation_targets)}, "
        f"sentiment={sentiment_score:.3f}"
    )
    if audio_duration_ms:
        log_msg += f", audio_duration={audio_duration_ms}ms"
    if frontmatter.audio_language:
        log_msg += f", audio_lang={frontmatter.audio_language}"
    logger.info(log_msg)

    return observation, observation_targets



import time
from typing import Literal

from eduscale.tabular.classifier import classify_table
from eduscale.tabular.concepts import load_concepts_catalog
from eduscale.tabular.mapping import map_columns
from eduscale.tabular.normalize import normalize_dataframe


@dataclass
class IngestContext:
    """Context information for ingestion run."""

    file_id: str
    region_id: str
    table_type: str
    rows_count: int
    text_uri: str


@dataclass
class IngestResult:
    """Result of ingestion pipeline execution."""

    file_id: str
    status: Literal["INGESTED", "FAILED"]
    table_type: str | None
    rows_loaded: int | None
    clean_location: str | None
    bytes_processed: int | None
    cache_hit: bool | None
    error_message: str | None
    warnings: list[str]
    processing_time_ms: int


def process_tabular_text(
    text_content: str,
    frontmatter: FrontmatterData | None = None,
) -> IngestResult:
    """Execute complete ingestion pipeline for tabular text.

    This is the main orchestration function that coordinates all pipeline stages:
    1. Parse frontmatter (if not already parsed)
    2. Detect content type (TABULAR vs FREE_FORM)
    3. Route to appropriate processing path
    4. Track pipeline steps
    5. Handle errors and return result

    Args:
        text_content: Full text content (may include frontmatter)
        frontmatter: Pre-parsed frontmatter (optional, will parse if None)

    Returns:
        IngestResult with status and metadata

    Raises:
        ValueError: If required metadata is missing
        RuntimeError: If processing fails
    """
    start_time = time.time()
    warnings = []

    try:
        # Step 1: Parse frontmatter if not provided
        if frontmatter is None:
            frontmatter, clean_text = parse_frontmatter(text_content)
            if frontmatter is None:
                raise ValueError("No frontmatter found in text content")
        else:
            # Frontmatter already parsed, extract clean text
            _, clean_text = parse_frontmatter(text_content)

        logger.info(
            f"Starting ingestion pipeline: file_id={frontmatter.file_id}, "
            f"region_id={frontmatter.region_id}, "
            f"content_type={frontmatter.original_content_type}"
        )

        # Step 2: Detect content type and route
        content_type = frontmatter.original_content_type or "text/plain"

        # Determine if content is TABULAR or FREE_FORM
        is_tabular = _is_tabular_content_type(content_type)

        if is_tabular:
            # TABULAR processing path
            result = _process_tabular_path(
                clean_text=clean_text,
                frontmatter=frontmatter,
                warnings=warnings,
            )
        else:
            # FREE_FORM processing path
            result = _process_free_form_path(
                clean_text=clean_text,
                frontmatter=frontmatter,
                warnings=warnings,
            )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result.processing_time_ms = processing_time_ms

        logger.info(
            f"Ingestion completed: file_id={frontmatter.file_id}, "
            f"status={result.status}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        error_message = f"{type(e).__name__}: {str(e)}"

        logger.error(
            f"Ingestion failed: file_id={frontmatter.file_id if frontmatter else 'unknown'}, "
            f"error={error_message}",
            exc_info=True,
        )

        return IngestResult(
            file_id=frontmatter.file_id if frontmatter else "unknown",
            status="FAILED",
            table_type=None,
            rows_loaded=None,
            clean_location=None,
            bytes_processed=None,
            cache_hit=None,
            error_message=error_message,
            warnings=warnings,
            processing_time_ms=processing_time_ms,
        )


def _is_tabular_content_type(content_type: str) -> bool:
    """Determine if content type is tabular.

    Args:
        content_type: MIME content type

    Returns:
        True if tabular, False if free-form
    """
    tabular_types = [
        "text/csv",
        "text/tab-separated-values",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    # Check if content type matches tabular types
    if content_type in tabular_types:
        return True

    # JSON can be either tabular or free-form
    # We'll try to load it and see if it's structured
    if content_type == "application/json":
        return True  # Try tabular first, will fallback if needed

    # Everything else is free-form
    return False


def _process_tabular_path(
    clean_text: str,
    frontmatter: FrontmatterData,
    warnings: list[str],
) -> IngestResult:
    """Process tabular data through the full pipeline.

    Pipeline steps:
    1. Load DataFrame
    2. Classify table type
    3. Map columns to concepts
    4. Normalize data
    5. Validate with Pandera
    6. Write to clean layer
    7. Load to BigQuery

    Args:
        clean_text: Clean text content (without frontmatter)
        frontmatter: Parsed frontmatter metadata
        warnings: List to collect warnings

    Returns:
        IngestResult with status and metadata
    """
    logger.info(f"Processing TABULAR path for file_id={frontmatter.file_id}")

    try:
        # Step 1: Load DataFrame
        df = load_dataframe_from_text(clean_text, frontmatter)
        logger.info(f"Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")

        # Step 2: Classify table type
        catalog = load_concepts_catalog(settings.CONCEPT_CATALOG_PATH)
        table_type, confidence = classify_table(df, catalog)
        logger.info(f"Classified as {table_type} with confidence {confidence:.3f}")

        # If confidence is too low, treat as FREE_FORM
        if confidence < 0.4:
            logger.warning(
                f"Low classification confidence ({confidence:.3f}), "
                f"routing to FREE_FORM processing"
            )
            warnings.append(f"Low classification confidence: {confidence:.3f}")
            return _process_free_form_path(clean_text, frontmatter, warnings)

        # Step 3: Map columns to concepts
        mappings = map_columns(df, table_type, catalog)
        logger.info(f"Mapped {len(mappings)} columns")

        # Check if we have enough AUTO mappings
        auto_mappings = [m for m in mappings if m.status == "AUTO"]
        if len(auto_mappings) < 2:
            warnings.append(
                f"Only {len(auto_mappings)} AUTO mappings found, "
                f"data quality may be low"
            )

        # Step 4: Normalize data
        df_normalized = normalize_dataframe(
            df_raw=df,
            table_type=table_type,
            mappings=mappings,
            region_id=frontmatter.region_id,
            file_id=frontmatter.file_id,
        )
        logger.info(f"Normalized DataFrame: {len(df_normalized)} rows")

        # Step 5: Write to clean layer (Parquet)
        from eduscale.tabular.clean_layer import write_clean_parquet
        
        clean_location = None
        try:
            clean_location_obj = write_clean_parquet(
                df=df_normalized,
                table_type=table_type,
                region_id=frontmatter.region_id,
                file_id=frontmatter.file_id,
            )
            clean_location = clean_location_obj.uri
            logger.info(f"Wrote clean Parquet: {clean_location}")
        except Exception as e:
            logger.error(f"Failed to write clean Parquet: {e}")
            warnings.append(f"Clean layer write failed: {str(e)}")

        # Step 6: Load to BigQuery via staging → core flow
        from eduscale.dwh.client import DwhClient
        
        load_result = None
        merge_result = None
        
        if clean_location:
            try:
                dwh_client = DwhClient()
                
                # Load Parquet to staging table
                load_result = dwh_client.load_parquet_to_staging(
                    table_type=table_type,
                    clean_uri=clean_location,
                    file_id=frontmatter.file_id,
                    region_id=frontmatter.region_id,
                )
                logger.info(
                    f"Loaded {load_result.rows_loaded} rows to staging table: {table_type}"
                )
                
                # MERGE staging to core table
                merge_result = dwh_client.merge_staging_to_core(
                    table_type=table_type,
                    file_id=frontmatter.file_id,
                    region_id=frontmatter.region_id,
                )
                logger.info(
                    f"Merged {merge_result.rows_inserted} rows to core table: {table_type}"
                )
                
                # Sync dimension tables from fact tables
                # Extract unique dates, regions, and schools from normalized DataFrame
                try:
                    # Extract dates
                    if "date" in df_normalized.columns:
                        dates = df_normalized["date"].dropna().unique().tolist()
                        if dates:
                            dwh_client.upsert_dimension_time(dates)
                    
                    # Extract regions
                    if "region_id" in df_normalized.columns:
                        regions = df_normalized["region_id"].dropna().unique().tolist()
                        if regions:
                            region_dicts = [
                                {"region_id": r, "region_name": None}
                                for r in regions
                            ]
                            dwh_client.upsert_dimension_regions(region_dicts)
                    
                    # Extract schools
                    if "school_name" in df_normalized.columns:
                        schools_df = df_normalized[["school_name", "region_id"]].dropna(
                            subset=["school_name"]
                        ).drop_duplicates()
                        if not schools_df.empty:
                            school_dicts = [
                                {
                                    "school_name": row["school_name"],
                                    "region_id": row.get("region_id"),
                                }
                                for _, row in schools_df.iterrows()
                            ]
                            dwh_client.upsert_dimension_schools(school_dicts)
                except Exception as e:
                    logger.warning(f"Failed to sync dimension tables: {e}")
                    # Don't fail the whole pipeline if dimension sync fails
                    
            except Exception as e:
                logger.error(f"Failed to load tabular data to BigQuery: {e}")
                warnings.append(f"BigQuery load failed: {str(e)}")

        return IngestResult(
            file_id=frontmatter.file_id,
            status="INGESTED",
            table_type=table_type,
            rows_loaded=len(df_normalized),
            clean_location=clean_location,
            bytes_processed=load_result.bytes_processed if load_result else None,
            cache_hit=load_result.cache_hit if load_result else None,
            error_message=None,
            warnings=warnings,
            processing_time_ms=0,  # Will be set by caller
        )

    except Exception as e:
        logger.error(f"TABULAR processing failed: {e}", exc_info=True)
        raise


def _process_free_form_path(
    clean_text: str,
    frontmatter: FrontmatterData,
    warnings: list[str],
) -> IngestResult:
    """Process free-form text through entity extraction and sentiment analysis.

    Pipeline steps:
    1. Extract entity mentions using LLM
    2. Apply entity resolution
    3. Compute sentiment score
    4. Create observation record
    5. Store in observations table

    Args:
        clean_text: Clean text content (without frontmatter)
        frontmatter: Parsed frontmatter metadata
        warnings: List to collect warnings

    Returns:
        IngestResult with status and metadata
    """
    logger.info(f"Processing FREE_FORM path for file_id={frontmatter.file_id}")

    try:
        # Load entity cache from BigQuery dimension tables
        from eduscale.tabular.analysis.entity_resolver import load_entity_cache

        entity_cache = load_entity_cache(frontmatter.region_id)

        # Process free-form text
        observation, targets = process_free_form_text(
            text_content=clean_text,
            frontmatter=frontmatter,
            entity_cache=entity_cache,
        )

        logger.info(
            f"Created observation with {len(targets)} targets, "
            f"sentiment={observation.sentiment_score:.3f}"
        )

        # Store observation and targets in BigQuery
        from eduscale.dwh.client import DwhClient
        
        try:
            dwh_client = DwhClient()
            
            # Convert observation to dict for BigQuery
            # Convert detected_entities list to JSON string for BigQuery
            detected_entities_json = json.dumps(observation.detected_entities) if observation.detected_entities else None
            
            observation_dict = {
                "file_id": observation.file_id,
                "region_id": observation.region_id,
                "text_content": observation.text_content,
                "detected_entities": detected_entities_json,
                "sentiment_score": observation.sentiment_score,
                "original_content_type": observation.original_content_type,
                "audio_duration_ms": observation.audio_duration_ms,
                "audio_confidence": observation.audio_confidence,
                "audio_language": observation.audio_language,
                "page_count": observation.page_count,
                "ingest_timestamp": observation.ingest_timestamp.isoformat(),
            }
            
            # Convert targets to dicts for BigQuery
            target_dicts = []
            ingest_timestamp = observation.ingest_timestamp.isoformat()
            for target in targets:
                target_dicts.append({
                    "observation_id": target.observation_id,
                    "target_type": target.target_type,
                    "target_id": target.target_id,
                    "relevance_score": target.relevance_score,
                    "confidence": target.confidence,
                    "ingest_timestamp": ingest_timestamp,
                })
            
            # Insert to BigQuery
            rows_inserted = dwh_client.insert_observation(observation_dict, target_dicts)
            logger.info(f"Inserted {rows_inserted} rows to BigQuery")
            
            # Sync dimension tables - at least region_id
            try:
                # Upsert region
                if observation.region_id:
                    dwh_client.upsert_dimension_regions([
                        {"region_id": observation.region_id, "region_name": None}
                    ])
                
                # Upsert date from ingest_timestamp if available
                if observation.ingest_timestamp:
                    ingest_date = observation.ingest_timestamp.date()
                    dwh_client.upsert_dimension_time([ingest_date])
            except Exception as e:
                logger.warning(f"Failed to sync dimension tables for observation: {e}")
                # Don't fail the whole pipeline if dimension sync fails
            
        except Exception as e:
            logger.error(f"Failed to insert observation to BigQuery: {e}")
            warnings.append(f"BigQuery insert failed: {str(e)}")

        return IngestResult(
            file_id=frontmatter.file_id,
            status="INGESTED",
            table_type="FREE_FORM",
            rows_loaded=1,  # One observation record
            clean_location=None,
            bytes_processed=None,
            cache_hit=None,
            error_message=None,
            warnings=warnings,
            processing_time_ms=0,  # Will be set by caller
        )

    except Exception as e:
        logger.error(f"FREE_FORM processing failed: {e}", exc_info=True)
        raise
