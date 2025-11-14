# BigQuery Infrastructure Configuration
# This file defines BigQuery datasets and tables for the EduScale data warehouse

# Enable BigQuery API
resource "google_project_service" "bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"

  disable_on_destroy = false
}

# Core BigQuery Dataset
# Contains dimension and fact tables for the data warehouse
resource "google_bigquery_dataset" "core" {
  dataset_id  = var.bigquery_dataset_id
  location    = var.region
  description = "Core dataset for EduScale data warehouse (dimensions and facts)"

  depends_on = [google_project_service.bigquery]
}

# Staging BigQuery Dataset
# Contains temporary tables for data loading operations
# Tables automatically expire after configured number of days
resource "google_bigquery_dataset" "staging" {
  dataset_id  = var.bigquery_staging_dataset_id
  location    = var.region
  description = "Staging dataset for temporary data loading operations"

  # Auto-delete staging tables after configured days
  default_table_expiration_ms = var.bigquery_staging_table_expiration_days * 24 * 60 * 60 * 1000

  depends_on = [google_project_service.bigquery]
}

# Dimension Tables
# These tables store slowly changing dimensions for the data warehouse

# Region Dimension Table
resource "google_bigquery_table" "dim_region" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "dim_region"

  schema = jsonencode([
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "region_name", type = "STRING", mode = "NULLABLE" },
    { name = "from_date", type = "DATE", mode = "NULLABLE" },
    { name = "to_date", type = "DATE", mode = "NULLABLE" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# School Dimension Table
resource "google_bigquery_table" "dim_school" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "dim_school"

  schema = jsonencode([
    { name = "school_name", type = "STRING", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "NULLABLE" },
    { name = "from_date", type = "DATE", mode = "NULLABLE" },
    { name = "to_date", type = "DATE", mode = "NULLABLE" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Time Dimension Table
resource "google_bigquery_table" "dim_time" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "dim_time"

  schema = jsonencode([
    { name = "date", type = "DATE", mode = "REQUIRED" },
    { name = "year", type = "INTEGER", mode = "NULLABLE" },
    { name = "month", type = "INTEGER", mode = "NULLABLE" },
    { name = "day", type = "INTEGER", mode = "NULLABLE" },
    { name = "quarter", type = "INTEGER", mode = "NULLABLE" },
    { name = "day_of_week", type = "INTEGER", mode = "NULLABLE" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Fact Tables
# These tables store transactional data with partitioning and clustering for performance

# Attendance Fact Table
# Stores student attendance records
resource "google_bigquery_table" "fact_attendance" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "fact_attendance"

  # Partition by date for query performance and cost optimization
  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  # Cluster by region_id for regional queries
  clustering = ["region_id"]

  schema = jsonencode([
    { name = "date", type = "DATE", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "school_name", type = "STRING", mode = "NULLABLE" },
    { name = "student_id", type = "STRING", mode = "NULLABLE" },
    { name = "student_name", type = "STRING", mode = "NULLABLE" },
    { name = "present", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "absent", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "file_id", type = "STRING", mode = "REQUIRED" },
    { name = "ingest_timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Assessment Fact Table
# Stores student assessment results
resource "google_bigquery_table" "fact_assessment" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "fact_assessment"

  # Partition by date for query performance and cost optimization
  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  # Cluster by region_id for regional queries
  clustering = ["region_id"]

  schema = jsonencode([
    { name = "date", type = "DATE", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "school_name", type = "STRING", mode = "NULLABLE" },
    { name = "student_id", type = "STRING", mode = "NULLABLE" },
    { name = "student_name", type = "STRING", mode = "NULLABLE" },
    { name = "subject", type = "STRING", mode = "NULLABLE" },
    { name = "test_score", type = "FLOAT", mode = "NULLABLE" },
    { name = "file_id", type = "STRING", mode = "REQUIRED" },
    { name = "ingest_timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Intervention Fact Table
# Stores educational intervention data
resource "google_bigquery_table" "fact_intervention" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "fact_intervention"

  # Partition by date for query performance and cost optimization
  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  # Cluster by region_id for regional queries
  clustering = ["region_id"]

  schema = jsonencode([
    { name = "date", type = "DATE", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "school_name", type = "STRING", mode = "NULLABLE" },
    { name = "intervention_type", type = "STRING", mode = "NULLABLE" },
    { name = "participants_count", type = "INTEGER", mode = "NULLABLE" },
    { name = "file_id", type = "STRING", mode = "REQUIRED" },
    { name = "ingest_timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Observations Table
# Stores unstructured/mixed data that doesn't fit into fact tables
resource "google_bigquery_table" "observations" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "observations"

  # Partition by ingest_timestamp for time-based queries
  time_partitioning {
    type  = "DAY"
    field = "ingest_timestamp"
  }

  # Cluster by region_id for regional filtering
  clustering = ["region_id"]

  schema = jsonencode([
    { name = "file_id", type = "STRING", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "text_content", type = "STRING", mode = "NULLABLE" },
    { name = "detected_entities", type = "JSON", mode = "NULLABLE" },
    { name = "sentiment_score", type = "FLOAT64", mode = "NULLABLE" },
    { name = "original_content_type", type = "STRING", mode = "NULLABLE" },
    { name = "audio_duration_ms", type = "INT64", mode = "NULLABLE" },
    { name = "audio_confidence", type = "FLOAT64", mode = "NULLABLE" },
    { name = "audio_language", type = "STRING", mode = "NULLABLE" },
    { name = "page_count", type = "INT64", mode = "NULLABLE" },
    { name = "source_table_type", type = "STRING", mode = "NULLABLE" },
    { name = "ingest_timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Observation Targets Table
# Junction table linking observations to detected entities (teachers, students, subjects, etc.)
resource "google_bigquery_table" "observation_targets" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "observation_targets"

  # Partition by ingest_timestamp for time-based queries
  time_partitioning {
    type  = "DAY"
    field = "ingest_timestamp"
  }

  # Cluster by observation_id and target_type for efficient queries
  clustering = ["observation_id", "target_type"]

  schema = jsonencode([
    { name = "observation_id", type = "STRING", mode = "REQUIRED" },
    { name = "target_type", type = "STRING", mode = "REQUIRED" },
    { name = "target_id", type = "STRING", mode = "REQUIRED" },
    { name = "relevance_score", type = "FLOAT64", mode = "NULLABLE" },
    { name = "confidence", type = "STRING", mode = "NULLABLE" },
    { name = "ingest_timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}

# Ingest Runs Tracking Table
# Tracks all ingestion pipeline executions for audit and debugging
resource "google_bigquery_table" "ingest_runs" {
  dataset_id = google_bigquery_dataset.core.dataset_id
  table_id   = "ingest_runs"

  # Partition by created_at for time-based queries
  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  # Cluster by region_id and status for filtering
  clustering = ["region_id", "status"]

  schema = jsonencode([
    { name = "file_id", type = "STRING", mode = "REQUIRED" },
    { name = "region_id", type = "STRING", mode = "REQUIRED" },
    { name = "status", type = "STRING", mode = "REQUIRED" },
    { name = "step", type = "STRING", mode = "NULLABLE" },
    { name = "error_message", type = "STRING", mode = "NULLABLE" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "updated_at", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  depends_on = [google_bigquery_dataset.core]
}
