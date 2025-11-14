-- Update observations table schema to match code requirements
-- Run this in BigQuery console or via bq command

-- Add new columns to observations table
ALTER TABLE `jedouedu.jedouscale_core.observations`
ADD COLUMN IF NOT EXISTS text_content STRING,
ADD COLUMN IF NOT EXISTS detected_entities JSON,
ADD COLUMN IF NOT EXISTS sentiment_score FLOAT,
ADD COLUMN IF NOT EXISTS original_content_type STRING,
ADD COLUMN IF NOT EXISTS audio_duration_ms INTEGER,
ADD COLUMN IF NOT EXISTS audio_confidence FLOAT,
ADD COLUMN IF NOT EXISTS audio_language STRING,
ADD COLUMN IF NOT EXISTS page_count INTEGER;

-- Rename observation_text to text_content if it exists and text_content doesn't
-- Note: This is a manual step - BigQuery doesn't support RENAME COLUMN directly
-- You may need to create a new table and copy data, or use a view

-- Create observation_targets table if it doesn't exist
CREATE TABLE IF NOT EXISTS `jedouedu.jedouscale_core.observation_targets` (
  observation_id STRING NOT NULL,
  target_type STRING NOT NULL,
  target_id STRING NOT NULL,
  relevance_score FLOAT,
  confidence STRING,
  ingest_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(ingest_timestamp)
CLUSTER BY observation_id, target_type;

