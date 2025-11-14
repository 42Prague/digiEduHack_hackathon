"""BigQuery Data Warehouse client.

This module handles loading data from clean layer Parquet files into BigQuery,
including staging tables and MERGE operations to core tables.
"""

import logging
from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LoadJobResult:
    """Result of BigQuery load job."""

    bytes_processed: int
    cache_hit: bool
    rows_loaded: int


@dataclass
class MergeResult:
    """Result of MERGE operation."""

    rows_merged: int
    rows_inserted: int
    rows_updated: int


class DwhClient:
    """BigQuery Data Warehouse client."""

    def __init__(self):
        """Initialize BigQuery client."""
        self.project_id = settings.bigquery_project
        self.dataset_id = settings.BIGQUERY_DATASET_ID
        self.staging_dataset_id = settings.bigquery_staging_dataset
        
        # Debug: Log what we got from settings
        logger.info(
            f"BigQuery config: GCP_PROJECT_ID={settings.GCP_PROJECT_ID}, "
            f"bigquery_project={settings.bigquery_project}"
        )
        
        # Initialize client - if project_id is empty, let it auto-detect
        self.client = bigquery.Client(project=self.project_id if self.project_id else None)
        
        # If project_id was empty, try to get it from the client
        if not self.project_id:
            try:
                self.project_id = self.client.project
                logger.info(f"Auto-detected BigQuery project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to auto-detect BigQuery project: {e}")
                raise ValueError(
                    "BigQuery project ID is required. Set GCP_PROJECT_ID environment variable."
                )

        logger.info(
            f"Initialized DwhClient: project={self.project_id}, "
            f"dataset={self.dataset_id}, staging={self.staging_dataset_id}"
        )

    def load_parquet_to_staging(
        self,
        table_type: str,
        clean_uri: str,
        file_id: str,
        region_id: str,
    ) -> LoadJobResult:
        """Load Parquet from GCS to staging table.

        Args:
            table_type: Table type (ATTENDANCE, ASSESSMENT, etc.)
            clean_uri: GCS URI of clean Parquet file
            file_id: File ID
            region_id: Region ID

        Returns:
            LoadJobResult with job statistics

        Staging table naming: stg_{table_type_lower}
        """
        staging_table_name = f"stg_{table_type.lower()}"
        table_ref = f"{self.project_id}.{self.staging_dataset_id}.{staging_table_name}"

        logger.info(
            f"Loading Parquet to staging: {clean_uri} -> {table_ref}"
        )

        # Configure load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            # Auto-detect schema from Parquet
            autodetect=True,
        )

        # Start load job
        load_job = self.client.load_table_from_uri(
            clean_uri,
            table_ref,
            job_config=job_config,
        )

        # Wait for job to complete
        load_job.result()

        # Get job statistics
        bytes_processed = load_job.total_bytes_processed or 0
        cache_hit = load_job.cache_hit or False
        rows_loaded = load_job.output_rows or 0

        logger.info(
            f"Load job completed: bytes={bytes_processed}, "
            f"rows={rows_loaded}, cache_hit={cache_hit}"
        )

        return LoadJobResult(
            bytes_processed=bytes_processed,
            cache_hit=cache_hit,
            rows_loaded=rows_loaded,
        )

    def merge_staging_to_core(
        self,
        table_type: str,
        file_id: str,
        region_id: str,
    ) -> MergeResult:
        """MERGE staging data into core tables.

        Args:
            table_type: Table type
            file_id: File ID
            region_id: Region ID

        Returns:
            MergeResult with merge statistics

        Note: This is a simplified implementation. In production, would use
        proper MERGE statements with deduplication logic based on table type.
        """
        staging_table_name = f"stg_{table_type.lower()}"
        core_table_name = self._get_core_table_name(table_type)

        staging_table_ref = f"{self.project_id}.{self.staging_dataset_id}.{staging_table_name}"
        core_table_ref = f"{self.project_id}.{self.dataset_id}.{core_table_name}"

        logger.info(
            f"Merging staging to core: {staging_table_ref} -> {core_table_ref}"
        )

        # For now, use simple INSERT (in production, would use MERGE with deduplication)
        query = f"""
        INSERT INTO `{core_table_ref}`
        SELECT * FROM `{staging_table_ref}`
        WHERE file_id = @file_id AND region_id = @region_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("file_id", "STRING", file_id),
                bigquery.ScalarQueryParameter("region_id", "STRING", region_id),
            ]
        )

        # Execute query
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()

        # Get statistics
        rows_inserted = query_job.num_dml_affected_rows or 0

        logger.info(f"Merge completed: rows_inserted={rows_inserted}")

        return MergeResult(
            rows_merged=rows_inserted,
            rows_inserted=rows_inserted,
            rows_updated=0,
        )

    def _get_core_table_name(self, table_type: str) -> str:
        """Get core table name for table type.

        Args:
            table_type: Table type

        Returns:
            Core table name

        Mapping:
            ATTENDANCE -> fact_attendance
            ASSESSMENT -> fact_assessment
            INTERVENTION -> fact_intervention
            FEEDBACK -> feedback
            RELATIONSHIP -> (varies by specific junction table)
        """
        table_mapping = {
            "ATTENDANCE": "fact_attendance",
            "ASSESSMENT": "fact_assessment",
            "INTERVENTION": "fact_intervention",
            "FEEDBACK": "feedback",
            "RELATIONSHIP": "observations",  # Default for relationships
        }

        return table_mapping.get(table_type, "observations")

    def create_staging_table_if_not_exists(self, table_type: str, schema: list[bigquery.SchemaField]) -> None:
        """Create staging table if it doesn't exist.

        Args:
            table_type: Table type
            schema: BigQuery schema fields
        """
        staging_table_name = f"stg_{table_type.lower()}"
        table_ref = f"{self.project_id}.{self.staging_dataset_id}.{staging_table_name}"

        table = bigquery.Table(table_ref, schema=schema)

        # Create table if not exists
        try:
            self.client.create_table(table, exists_ok=True)
            logger.info(f"Created staging table: {table_ref}")
        except Exception as e:
            logger.warning(f"Failed to create staging table: {e}")

    def insert_observation(
        self,
        observation: dict[str, Any],
        targets: list[dict[str, Any]] | None = None,
    ) -> int:
        """Insert observation and targets directly to BigQuery.

        Args:
            observation: Observation record dict
            targets: List of observation_target dicts (optional)

        Returns:
            Number of rows inserted

        This method inserts free-form observations directly to BigQuery without
        going through the staging/merge flow.
        """
        rows_inserted = 0

        # Insert observation
        observation_table_ref = f"{self.project_id}.{self.dataset_id}.observations"
        
        try:
            errors = self.client.insert_rows_json(observation_table_ref, [observation])
            if errors:
                logger.error(f"Failed to insert observation: {errors}")
            else:
                rows_inserted += 1
                logger.info(f"Inserted observation: file_id={observation.get('file_id')}")
        except Exception as e:
            logger.error(f"Exception inserting observation: {e}")

        # Insert observation targets if provided
        if targets:
            targets_table_ref = f"{self.project_id}.{self.dataset_id}.observation_targets"
            
            try:
                errors = self.client.insert_rows_json(targets_table_ref, targets)
                if errors:
                    logger.error(f"Failed to insert observation_targets: {errors}")
                else:
                    rows_inserted += len(targets)
                    logger.info(f"Inserted {len(targets)} observation_targets")
            except Exception as e:
                logger.error(f"Exception inserting observation_targets: {e}")

        return rows_inserted
