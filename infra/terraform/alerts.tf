# Cloud Monitoring Alert Policies for Eventarc Integration
# These alerts monitor event delivery health and notify on failures

# Email notification channel for alerts
resource "google_monitoring_notification_channel" "eventarc_email" {
  count        = var.enable_monitoring_alerts && var.alert_email != "" ? 1 : 0
  display_name = "Eventarc Alerts Email"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.alert_email
  }
}

# Alert Policy 1: High Failure Rate (>10% failures over 5 minutes)
resource "google_monitoring_alert_policy" "eventarc_high_failure_rate" {
  count        = var.enable_eventarc && var.enable_monitoring_alerts ? 1 : 0
  display_name = "Eventarc High Failure Rate"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "Delivery failure rate > 10%"

    condition_threshold {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/delivery_failure_count"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${google_eventarc_trigger.storage_trigger[0].name}"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 0.1 # 10%
      duration        = "300s" # 5 minutes

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.eventarc_email[0].id] : []

  alert_strategy {
    auto_close = "1800s" # Auto-close after 30 minutes
  }

  documentation {
    content = <<-EOT
      ## Eventarc High Failure Rate Alert

      The event delivery failure rate has exceeded 10% over the last 5 minutes.

      ### Possible Causes:
      - MIME Decoder service is down or returning 5xx errors
      - Cloud Storage bucket permissions issues
      - Network connectivity problems
      - Service timeout due to slow processing

      ### Remediation Steps:
      1. Check MIME Decoder service logs:
         ```
         gcloud logging read 'resource.type="cloud_run_revision" resource.labels.service_name="mime-decoder" severity>=ERROR' --limit=20
         ```

      2. Check service health:
         ```
         curl https://<mime-decoder-url>/health
         ```

      3. Review failed events in Cloud Logging for error details

      4. If service is down, check Cloud Run service status and restart if needed
    EOT
  }

  depends_on = [google_eventarc_trigger.storage_trigger[0]]
}

# Alert Policy 2: High Latency (p95 > 30 seconds)
resource "google_monitoring_alert_policy" "eventarc_high_latency" {
  count        = var.enable_eventarc && var.enable_monitoring_alerts ? 1 : 0
  display_name = "Eventarc High Delivery Latency"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "P95 delivery latency > 30 seconds"

    condition_threshold {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/delivery_latency"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${google_eventarc_trigger.storage_trigger[0].name}"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 30000 # 30 seconds in milliseconds
      duration        = "300s" # 5 minutes

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.eventarc_email[0].id] : []

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content = <<-EOT
      ## Eventarc High Latency Alert

      The 95th percentile event delivery latency has exceeded 30 seconds.

      ### Possible Causes:
      - MIME Decoder service is slow (CPU/memory constrained)
      - High volume of events causing queueing
      - Network latency between Eventarc and Cloud Run
      - Cold start delays due to service scaling

      ### Remediation Steps:
      1. Check MIME Decoder resource utilization:
         ```
         gcloud monitoring timeseries list \
           --filter='metric.type="run.googleapis.com/container/cpu/utilizations" resource.labels.service_name="mime-decoder"'
         ```

      2. Consider increasing Cloud Run resources (CPU/memory) in eventarc.tf

      3. Increase minimum instance count to reduce cold starts

      4. Review MIME Decoder processing logic for optimization opportunities
    EOT
  }

  depends_on = [google_eventarc_trigger.storage_trigger[0]]
}

# Alert Policy 3: No Events (0 events for >1 hour)
resource "google_monitoring_alert_policy" "eventarc_no_events" {
  count        = var.enable_eventarc && var.enable_monitoring_alerts ? 1 : 0
  display_name = "Eventarc No Events Received"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "No events received for 1 hour"

    condition_absent {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/event_count"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${google_eventarc_trigger.storage_trigger[0].name}"
      EOT

      duration = "3600s" # 1 hour

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.eventarc_email[0].id] : []

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content = <<-EOT
      ## Eventarc No Events Alert

      No events have been received by the Eventarc trigger for over 1 hour.

      ### Possible Causes:
      - No files are being uploaded to Cloud Storage
      - Eventarc trigger is misconfigured or disabled
      - Cloud Storage event emission is not working
      - Event filters are too restrictive

      ### Remediation Steps:
      1. Check if Eventarc trigger is active:
         ```
         gcloud eventarc triggers describe ${google_eventarc_trigger.storage_trigger[0].name} --location=${var.region}
         ```

      2. Verify Cloud Storage bucket has files:
         ```
         gsutil ls gs://${google_storage_bucket.uploads.name}/
         ```

      3. Test by uploading a file:
         ```
         echo "test" | gsutil cp - gs://${google_storage_bucket.uploads.name}/test.txt
         ```

      4. Check Eventarc logs for any errors:
         ```
         gcloud logging read 'resource.type="eventarc.googleapis.com/trigger"' --limit=20
         ```

      **Note:** This alert may trigger during expected periods of no uploads (e.g., weekends, holidays)
    EOT
  }

  depends_on = [google_eventarc_trigger.storage_trigger[0]]
}
