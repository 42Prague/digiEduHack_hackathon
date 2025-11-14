"""Data normalization module.

This module transforms raw DataFrames to canonical structure with proper
column names, types, and metadata.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone

import pandas as pd

from eduscale.core.config import settings
from eduscale.tabular.mapping import ColumnMapping

logger = logging.getLogger(__name__)


def normalize_dataframe(
    df_raw: pd.DataFrame,
    table_type: str,
    mappings: list[ColumnMapping],
    region_id: str,
    file_id: str,
) -> pd.DataFrame:
    """Normalize DataFrame to canonical structure.

    Args:
        df_raw: Raw DataFrame with original column names
        table_type: Classified table type
        mappings: Column mappings from AI mapping
        region_id: Region ID for metadata
        file_id: File ID for metadata

    Returns:
        Normalized DataFrame with canonical columns and metadata

    Steps:
        1. Store original column names for audit
        2. Rename columns per mappings (AUTO/LOW_CONFIDENCE only)
        3. Cast types: dates, numbers, strings
        4. Add metadata columns
        5. Clean data: normalize school names, pseudonymize IDs if enabled
    """
    if df_raw.empty:
        logger.warning("Empty DataFrame, returning as-is")
        return df_raw

    df = df_raw.copy()

    # Step 1: Store original column names in metadata
    original_columns = df.columns.tolist()
    logger.info(f"Original columns: {original_columns}")

    # Step 2: Rename columns per mappings
    rename_map = {}
    for mapping in mappings:
        if mapping.status in ["AUTO", "LOW_CONFIDENCE"] and mapping.concept_key:
            rename_map[mapping.source_column] = mapping.concept_key

    if rename_map:
        df = df.rename(columns=rename_map)
        logger.info(f"Renamed columns: {rename_map}")

    # Step 3: Cast types
    df = _cast_column_types(df)

    # Step 4: Add metadata columns
    df["region_id"] = region_id
    df["file_id"] = file_id
    df["ingest_timestamp"] = datetime.now(timezone.utc)
    df["source_table_type"] = table_type

    # Step 5: Clean data
    df = _clean_data(df)

    logger.info(
        f"Normalized DataFrame: {len(df)} rows, {len(df.columns)} columns, "
        f"final columns: {df.columns.tolist()}"
    )

    return df


def _cast_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to appropriate types.

    Args:
        df: DataFrame with renamed columns

    Returns:
        DataFrame with properly typed columns
    """
    df = df.copy()

    # Date columns
    date_columns = [col for col in df.columns if "date" in col.lower() or col in ["from_date", "to_date", "uploaded_at", "timestamp"]]
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                logger.debug(f"Converted {col} to datetime")
            except Exception as e:
                logger.warning(f"Failed to convert {col} to datetime: {e}")

    # Numeric columns
    numeric_columns = [
        col
        for col in df.columns
        if any(
            keyword in col.lower()
            for keyword in [
                "score",
                "count",
                "value",
                "duration",
                "size",
                "length",
                "weight",
                "relevance",
                "impact",
                "sentiment",
            ]
        )
    ]
    for col in numeric_columns:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                logger.debug(f"Converted {col} to numeric")
            except Exception as e:
                logger.warning(f"Failed to convert {col} to numeric: {e}")

    # String columns (strip whitespace)
    string_columns = df.select_dtypes(include=["object"]).columns
    for col in string_columns:
        if col in df.columns:
            try:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' string with actual NaN
                df[col] = df[col].replace("nan", pd.NA)
            except Exception as e:
                logger.warning(f"Failed to clean string column {col}: {e}")

    return df


def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize data values.

    Args:
        df: DataFrame with typed columns

    Returns:
        DataFrame with cleaned data
    """
    df = df.copy()

    # Normalize school names
    if "school_name" in df.columns:
        df["school_name"] = df["school_name"].apply(_normalize_school_name)
        logger.debug("Normalized school names")

    # Pseudonymize IDs if enabled
    if settings.PSEUDONYMIZE_IDS:
        id_columns = [col for col in df.columns if col.endswith("_id") and col not in ["region_id", "file_id"]]
        for col in id_columns:
            if col in df.columns:
                # Store original in metadata column
                df[f"{col}_original"] = df[col]
                # Hash the ID
                df[col] = df[col].apply(_pseudonymize_id)
                logger.debug(f"Pseudonymized {col}")

    return df


def _normalize_school_name(name: str) -> str:
    """Normalize school name.

    Args:
        name: School name

    Returns:
        Normalized school name

    Normalization:
        - Remove extra spaces
        - Unify case (title case)
        - Standardize abbreviations
    """
    if pd.isna(name) or name == "":
        return name

    # Remove extra spaces
    name = re.sub(r"\s+", " ", str(name)).strip()

    # Title case
    name = name.title()

    # Standardize common abbreviations
    name = name.replace("Zs", "ZŠ")  # Základní škola
    name = name.replace("Ss", "SŠ")  # Střední škola
    name = name.replace("Gym", "Gymnázium")

    return name


def _pseudonymize_id(id_value: str) -> str:
    """Pseudonymize ID using SHA256 hash.

    Args:
        id_value: Original ID

    Returns:
        Hashed ID (first 16 characters of SHA256)
    """
    if pd.isna(id_value) or id_value == "":
        return id_value

    # Hash the ID
    hashed = hashlib.sha256(str(id_value).encode()).hexdigest()[:16]
    return hashed
