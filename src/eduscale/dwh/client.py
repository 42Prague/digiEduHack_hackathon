"""BigQuery Data Warehouse client.

This module handles loading data from clean layer Parquet files into BigQuery,
including staging tables and MERGE operations to core tables.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
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

    def upsert_dimension_regions(self, regions: list[dict[str, Any]]) -> int:
        """Upsert regions into dim_region table.

        Args:
            regions: List of region dicts with region_id, region_name, from_date, to_date

        Returns:
            Number of rows upserted
        """
        if not regions:
            return 0

        table_ref = f"{self.project_id}.{self.dataset_id}.dim_region"

        # Use MERGE to upsert (insert or update)
        for region in regions:
            region_id = region.get("region_id")
            region_name = region.get("region_name")
            from_date = region.get("from_date")
            to_date = region.get("to_date")

            if not region_id:
                logger.warning("Skipping region without region_id")
                continue

            query = f"""
            MERGE `{table_ref}` AS target
            USING (
                SELECT 
                    @region_id AS region_id,
                    @region_name AS region_name,
                    @from_date AS from_date,
                    @to_date AS to_date
            ) AS source
            ON target.region_id = source.region_id
            WHEN MATCHED THEN
                UPDATE SET
                    region_name = COALESCE(source.region_name, target.region_name),
                    from_date = COALESCE(source.from_date, target.from_date),
                    to_date = COALESCE(source.to_date, target.to_date)
            WHEN NOT MATCHED THEN
                INSERT (region_id, region_name, from_date, to_date)
                VALUES (source.region_id, source.region_name, source.from_date, source.to_date)
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("region_id", "STRING", region_id),
                    bigquery.ScalarQueryParameter("region_name", "STRING", region_name),
                    bigquery.ScalarQueryParameter("from_date", "DATE", from_date),
                    bigquery.ScalarQueryParameter("to_date", "DATE", to_date),
                ]
            )

            try:
                query_job = self.client.query(query, job_config=job_config)
                query_job.result()
            except Exception as e:
                logger.error(f"Failed to upsert region {region_id}: {e}")

        logger.info(f"Upserted {len(regions)} regions to dim_region")
        return len(regions)

    def upsert_dimension_schools(self, schools: list[dict[str, Any]]) -> int:
        """Upsert schools into dim_school table.

        Args:
            schools: List of school dicts with school_name, region_id, from_date, to_date

        Returns:
            Number of rows upserted
        """
        if not schools:
            return 0

        table_ref = f"{self.project_id}.{self.dataset_id}.dim_school"

        # Use MERGE to upsert (insert or update)
        for school in schools:
            school_name = school.get("school_name")
            region_id = school.get("region_id")
            from_date = school.get("from_date")
            to_date = school.get("to_date")

            if not school_name:
                logger.warning("Skipping school without school_name")
                continue

            query = f"""
            MERGE `{table_ref}` AS target
            USING (
                SELECT 
                    @school_name AS school_name,
                    @region_id AS region_id,
                    @from_date AS from_date,
                    @to_date AS to_date
            ) AS source
            ON target.school_name = source.school_name
            WHEN MATCHED THEN
                UPDATE SET
                    region_id = COALESCE(source.region_id, target.region_id),
                    from_date = COALESCE(source.from_date, target.from_date),
                    to_date = COALESCE(source.to_date, target.to_date)
            WHEN NOT MATCHED THEN
                INSERT (school_name, region_id, from_date, to_date)
                VALUES (source.school_name, source.region_id, source.from_date, source.to_date)
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("school_name", "STRING", school_name),
                    bigquery.ScalarQueryParameter("region_id", "STRING", region_id),
                    bigquery.ScalarQueryParameter("from_date", "DATE", from_date),
                    bigquery.ScalarQueryParameter("to_date", "DATE", to_date),
                ]
            )

            try:
                query_job = self.client.query(query, job_config=job_config)
                query_job.result()
            except Exception as e:
                logger.error(f"Failed to upsert school {school_name}: {e}")

        logger.info(f"Upserted {len(schools)} schools to dim_school")
        return len(schools)

    def upsert_dimension_time(self, dates: list[date]) -> int:
        """Upsert dates into dim_time table.

        Args:
            dates: List of date objects

        Returns:
            Number of rows upserted
        """
        if not dates:
            return 0

        table_ref = f"{self.project_id}.{self.dataset_id}.dim_time"

        rows_upserted = 0

        for date_obj in dates:
            if isinstance(date_obj, datetime):
                date_obj = date_obj.date()
            elif isinstance(date_obj, str):
                # Try to parse date string
                try:
                    date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00")).date()
                except Exception:
                    logger.warning(f"Could not parse date: {date_obj}")
                    continue

            year = date_obj.year
            month = date_obj.month
            day = date_obj.day
            quarter = (month - 1) // 3 + 1
            day_of_week = date_obj.weekday() + 1  # Monday=1, Sunday=7

            query = f"""
            MERGE `{table_ref}` AS target
            USING (
                SELECT 
                    @date AS date,
                    @year AS year,
                    @month AS month,
                    @day AS day,
                    @quarter AS quarter,
                    @day_of_week AS day_of_week
            ) AS source
            ON target.date = source.date
            WHEN NOT MATCHED THEN
                INSERT (date, year, month, day, quarter, day_of_week)
                VALUES (source.date, source.year, source.month, source.day, source.quarter, source.day_of_week)
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("date", "DATE", date_obj),
                    bigquery.ScalarQueryParameter("year", "INTEGER", year),
                    bigquery.ScalarQueryParameter("month", "INTEGER", month),
                    bigquery.ScalarQueryParameter("day", "INTEGER", day),
                    bigquery.ScalarQueryParameter("quarter", "INTEGER", quarter),
                    bigquery.ScalarQueryParameter("day_of_week", "INTEGER", day_of_week),
                ]
            )

            try:
                query_job = self.client.query(query, job_config=job_config)
                query_job.result()
                rows_upserted += 1
            except Exception as e:
                logger.error(f"Failed to upsert date {date_obj}: {e}")

        logger.info(f"Upserted {rows_upserted} dates to dim_time")
        return rows_upserted

    def sync_dimensions_from_facts(self) -> dict[str, int]:
        """Sync dimension tables from fact tables.

        Extracts unique values from fact tables and upserts them into dimension tables.

        Returns:
            Dict with counts of rows synced per dimension table
        """
        results = {}

        # Sync dim_time from all fact tables
        try:
            query = f"""
            SELECT DISTINCT date
            FROM `{self.project_id}.{self.dataset_id}.fact_assessment`
            WHERE date IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT date
            FROM `{self.project_id}.{self.dataset_id}.fact_intervention`
            WHERE date IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT date
            FROM `{self.project_id}.{self.dataset_id}.fact_attendance`
            WHERE date IS NOT NULL
            """
            query_job = self.client.query(query)
            dates = [row.date for row in query_job.result()]
            results["dim_time"] = self.upsert_dimension_time(dates)
        except Exception as e:
            logger.warning(f"Could not sync dim_time: {e}")
            results["dim_time"] = 0

        # Sync dim_region from fact tables
        try:
            query = f"""
            SELECT DISTINCT region_id, CAST(NULL AS STRING) AS region_name
            FROM `{self.project_id}.{self.dataset_id}.fact_assessment`
            WHERE region_id IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT region_id, CAST(NULL AS STRING) AS region_name
            FROM `{self.project_id}.{self.dataset_id}.fact_intervention`
            WHERE region_id IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT region_id, CAST(NULL AS STRING) AS region_name
            FROM `{self.project_id}.{self.dataset_id}.fact_attendance`
            WHERE region_id IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT region_id, CAST(NULL AS STRING) AS region_name
            FROM `{self.project_id}.{self.dataset_id}.observations`
            WHERE region_id IS NOT NULL
            """
            query_job = self.client.query(query)
            regions = [{"region_id": row.region_id, "region_name": None} for row in query_job.result()]
            results["dim_region"] = self.upsert_dimension_regions(regions)
        except Exception as e:
            logger.warning(f"Could not sync dim_region: {e}")
            results["dim_region"] = 0

        # Sync dim_school from fact tables
        try:
            query = f"""
            SELECT DISTINCT school_name, region_id
            FROM `{self.project_id}.{self.dataset_id}.fact_assessment`
            WHERE school_name IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT school_name, region_id
            FROM `{self.project_id}.{self.dataset_id}.fact_intervention`
            WHERE school_name IS NOT NULL
            UNION DISTINCT
            SELECT DISTINCT school_name, region_id
            FROM `{self.project_id}.{self.dataset_id}.fact_attendance`
            WHERE school_name IS NOT NULL
            """
            query_job = self.client.query(query)
            schools = [
                {"school_name": row.school_name, "region_id": row.region_id}
                for row in query_job.result()
            ]
            results["dim_school"] = self.upsert_dimension_schools(schools)
        except Exception as e:
            logger.warning(f"Could not sync dim_school: {e}")
            results["dim_school"] = 0

        logger.info(f"Synced dimensions from fact tables: {results}")
        return results
