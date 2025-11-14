"""Clean layer storage module.

This module writes normalized DataFrames as Parquet files to the clean layer
(intermediate storage before BigQuery loading).
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CleanLocation:
    """Location of clean layer Parquet file."""

    uri: str
    size_bytes: int


def write_clean_parquet(
    df: pd.DataFrame,
    table_type: str,
    region_id: str,
    file_id: str,
) -> CleanLocation:
    """Write DataFrame to Parquet in clean layer.

    Args:
        df: Normalized and validated DataFrame
        table_type: Table type (ATTENDANCE, ASSESSMENT, etc.)
        region_id: Region ID
        file_id: File ID

    Returns:
        CleanLocation with URI and size

    Path structure:
        - GCS: gs://{bucket}/clean/{table_type}/region={region_id}/file_id={file_id}.parquet
        - Local: {base_path}/clean/{table_type}/region={region_id}/{file_id}.parquet
    """
    if df.empty:
        logger.warning("Empty DataFrame, skipping write")
        return CleanLocation(uri="", size_bytes=0)

    # Compute path
    if settings.STORAGE_BACKEND == "gcs":
        uri = _compute_gcs_path(table_type, region_id, file_id)
        size_bytes = _write_to_gcs(df, uri)
    else:
        uri = _compute_local_path(table_type, region_id, file_id)
        size_bytes = _write_to_local(df, uri)

    logger.info(
        f"Wrote clean Parquet: table_type={table_type}, "
        f"region={region_id}, file={file_id}, "
        f"uri={uri}, size={size_bytes} bytes"
    )

    return CleanLocation(uri=uri, size_bytes=size_bytes)


def _compute_gcs_path(table_type: str, region_id: str, file_id: str) -> str:
    """Compute GCS path for clean Parquet file.

    Args:
        table_type: Table type
        region_id: Region ID
        file_id: File ID

    Returns:
        GCS URI
    """
    bucket = settings.GCS_BUCKET_NAME
    path = f"clean/{table_type}/region={region_id}/file_id={file_id}.parquet"
    return f"gs://{bucket}/{path}"


def _compute_local_path(table_type: str, region_id: str, file_id: str) -> str:
    """Compute local path for clean Parquet file.

    Args:
        table_type: Table type
        region_id: Region ID
        file_id: File ID

    Returns:
        Local file path
    """
    base_path = settings.CLEAN_LAYER_BASE_PATH
    path = f"{base_path}/clean/{table_type}/region={region_id}/{file_id}.parquet"
    return path


def _write_to_gcs(df: pd.DataFrame, uri: str) -> int:
    """Write DataFrame to GCS as Parquet.

    Args:
        df: DataFrame to write
        uri: GCS URI

    Returns:
        File size in bytes
    """
    from google.cloud import storage

    # Parse GCS URI
    if not uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {uri}")

    parts = uri[5:].split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1]

    # Write to temporary file first
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
        df.to_parquet(tmp_file.name, engine="pyarrow", compression="snappy")
        tmp_path = tmp_file.name

    try:
        # Upload to GCS
        client = storage.Client(project=settings.GCP_PROJECT_ID)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(tmp_path)

        # Get file size
        blob.reload()
        size_bytes = blob.size

        logger.debug(f"Uploaded to GCS: {uri}, size={size_bytes}")
        return size_bytes

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def _write_to_local(df: pd.DataFrame, path: str) -> int:
    """Write DataFrame to local filesystem as Parquet.

    Args:
        df: DataFrame to write
        path: Local file path

    Returns:
        File size in bytes
    """
    # Create directories if needed
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write Parquet
    df.to_parquet(file_path, engine="pyarrow", compression="snappy")

    # Get file size
    size_bytes = file_path.stat().st_size

    logger.debug(f"Wrote to local: {path}, size={size_bytes}")
    return size_bytes
