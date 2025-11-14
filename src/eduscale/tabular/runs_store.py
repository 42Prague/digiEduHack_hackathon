"""Ingest runs tracking module.

This module tracks ingestion pipeline execution in BigQuery for audit and monitoring.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from google.cloud import bigquery

from eduscale.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class IngestRun:
    """Ingest run record."""

    file_id: str
    region_id: str
    status: Literal["STARTED", "DONE", "FAILED"]
    step: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class RunsStore:
    """Store for tracking ingest runs in BigQuery."""

    def __init__(self):
        """Initialize runs store."""
        self.project_id = settings.bigquery_project
        self.dataset_id = settings.BIGQUERY_DATASET_ID
        self.table_name = "ingest_runs"
        self.client = bigquery.Client(project=self.project_id)

        # Ensure table exists
        self._ensure_table_exists()

        logger.info(
            f"Initialized RunsStore: {self.project_id}.{self.dataset_id}.{self.table_name}"
        )

    def start_run(self, file_id: str, region_id: str) -> IngestRun:
        """Start a new ingest run.

        Args:
            file_id: File ID
            region_id: Region ID

        Returns:
            IngestRun record
        """
        now = datetime.now(timezone.utc)

        run = IngestRun(
            file_id=file_id,
            region_id=region_id,
            status="STARTED",
            step="LOAD_RAW",
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        # Insert into BigQuery
        self._insert_run(run)

        logger.info(f"Started ingest run: file_id={file_id}, region_id={region_id}")

        return run

    def update_run_step(
        self,
        file_id: str,
        step: str,
        status: Literal["STARTED", "DONE", "FAILED"] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update ingest run step and status.

        Args:
            file_id: File ID
            step: Current pipeline step
            status: Status (optional, defaults to current status)
            error_message: Error message if failed
        """
        now = datetime.now(timezone.utc)

        # Build UPDATE query
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"

        if status:
            query = f"""
            UPDATE `{table_ref}`
            SET step = @step,
                status = @status,
                error_message = @error_message,
                updated_at = @updated_at
            WHERE file_id = @file_id
            ORDER BY created_at DESC
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("file_id", "STRING", file_id),
                    bigquery.ScalarQueryParameter("step", "STRING", step),
                    bigquery.ScalarQueryParameter("status", "STRING", status),
                    bigquery.ScalarQueryParameter("error_message", "STRING", error_message),
                    bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
                ]
            )
        else:
            query = f"""
            UPDATE `{table_ref}`
            SET step = @step,
                updated_at = @updated_at
            WHERE file_id = @file_id
            ORDER BY created_at DESC
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("file_id", "STRING", file_id),
                    bigquery.ScalarQueryParameter("step", "STRING", step),
                    bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
                ]
            )

        # Execute update
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()

        logger.info(
            f"Updated run: file_id={file_id}, step={step}, status={status}"
        )

    def get_run(self, file_id: str) -> IngestRun | None:
        """Get ingest run by file_id.

        Args:
            file_id: File ID

        Returns:
            IngestRun or None if not found
        """
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"

        query = f"""
        SELECT file_id, region_id, status, step, error_message, created_at, updated_at
        FROM `{table_ref}`
        WHERE file_id = @file_id
        ORDER BY created_at DESC
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("file_id", "STRING", file_id),
            ]
        )

        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())

        if not results:
            return None

        row = results[0]
        return IngestRun(
            file_id=row.file_id,
            region_id=row.region_id,
            status=row.status,
            step=row.step,
            error_message=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _insert_run(self, run: IngestRun) -> None:
        """Insert run record into BigQuery.

        Args:
            run: IngestRun to insert
        """
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"

        rows_to_insert = [
            {
                "file_id": run.file_id,
                "region_id": run.region_id,
                "status": run.status,
                "step": run.step,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
            }
        ]

        errors = self.client.insert_rows_json(table_ref, rows_to_insert)

        if errors:
            logger.error(f"Failed to insert run: {errors}")
            raise RuntimeError(f"Failed to insert run: {errors}")

    def _ensure_table_exists(self) -> None:
        """Ensure ingest_runs table exists in BigQuery."""
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"

        schema = [
            bigquery.SchemaField("file_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("region_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("step", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("error_message", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        table = bigquery.Table(table_ref, schema=schema)

        # Partition by created_at, cluster by region_id and status
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="created_at",
        )
        table.clustering_fields = ["region_id", "status"]

        try:
            self.client.create_table(table, exists_ok=True)
            logger.info(f"Ensured table exists: {table_ref}")
        except Exception as e:
            logger.warning(f"Failed to create table: {e}")
