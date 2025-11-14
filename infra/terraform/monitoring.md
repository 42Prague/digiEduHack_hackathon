# Eventarc Integration Monitoring and Alerting

## Cloud Monitoring Metrics

Eventarc automatically emits metrics to Cloud Monitoring for event delivery tracking:

### Available Metrics

1. **eventarc.googleapis.com/trigger/event_count**
   - Description: Total number of events received by the trigger
   - Type: Counter
   - Labels: `trigger_name`, `event_type`
   - Use case: Monitor overall event volume

2. **eventarc.googleapis.com/trigger/match_count**
   - Description: Number of events matching the trigger filters
   - Type: Counter
   - Labels: `trigger_name`
   - Use case: Verify filter configuration is working correctly

3. **eventarc.googleapis.com/trigger/delivery_success_count**
   - Description: Number of successful event deliveries to MIME Decoder
   - Type: Counter
   - Labels: `trigger_name`, `destination`
   - Use case: Track successful processing

4. **eventarc.googleapis.com/trigger/delivery_failure_count**
   - Description: Number of failed event deliveries after all retries
   - Type: Counter
   - Labels: `trigger_name`, `destination`, `error_code`
   - Use case: Identify processing failures requiring investigation

5. **eventarc.googleapis.com/trigger/delivery_latency**
   - Description: Time from event emission to successful delivery
   - Type: Distribution
   - Labels: `trigger_name`
   - Use case: Monitor pipeline performance

## Cloud Logging

### Event Delivery Logs

All event deliveries are logged to Cloud Logging with the following information:
- Event ID
- Timestamp
- Delivery status (success/failure)
- Retry attempt number (if applicable)
- Error message (for failures)
- Destination service

### Query Examples

**Find all failed events in the last hour:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="mime-decoder"
severity=ERROR
timestamp>="2025-01-01T00:00:00Z"
jsonPayload.manual_reprocessing_required=true
```

**Find events for a specific file:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="mime-decoder"
jsonPayload.object_name="uploads/region-123/file-456.pdf"
```

## Recommended Alert Policies

### 1. High Failure Rate Alert

**Alert when delivery failure rate > 10% over 5 minutes**

```hcl
resource "google_monitoring_alert_policy" "eventarc_high_failure_rate" {
  display_name = "Eventarc High Failure Rate"
  combiner     = "OR"

  conditions {
    display_name = "Failure rate > 10%"

    condition_threshold {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/delivery_failure_count"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${var.eventarc_trigger_name}"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 0.1  # 10%
      duration        = "300s"  # 5 minutes

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"  # Auto-close after 30 minutes
  }
}
```

### 2. High Latency Alert

**Alert when p95 delivery latency > 30 seconds**

```hcl
resource "google_monitoring_alert_policy" "eventarc_high_latency" {
  display_name = "Eventarc High Delivery Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 30s"

    condition_threshold {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/delivery_latency"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${var.eventarc_trigger_name}"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 30000  # 30 seconds in milliseconds
      duration        = "300s"  # 5 minutes

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}
```

### 3. No Events Alert

**Alert when no events received for > 1 hour**

```hcl
resource "google_monitoring_alert_policy" "eventarc_no_events" {
  display_name = "Eventarc No Events Received"
  combiner     = "OR"

  conditions {
    display_name = "No events for 1 hour"

    condition_absent {
      filter = <<-EOT
        metric.type="eventarc.googleapis.com/trigger/event_count"
        resource.type="eventarc.googleapis.com/trigger"
        resource.labels.trigger_name="${var.eventarc_trigger_name}"
      EOT

      duration = "3600s"  # 1 hour

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}
```

## Notification Channels

### Email Notification Channel

```hcl
resource "google_monitoring_notification_channel" "email" {
  display_name = "DevOps Team Email"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}
```

### Slack Notification Channel (Optional)

```hcl
resource "google_monitoring_notification_channel" "slack" {
  display_name = "DevOps Slack Channel"
  type         = "slack"

  labels = {
    channel_name = "#devops-alerts"
  }

  sensitive_labels {
    auth_token = var.slack_webhook_token
  }
}
```

## Monitoring Dashboard

### Dashboard Configuration

```hcl
resource "google_monitoring_dashboard" "eventarc_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Eventarc Integration Dashboard"

    gridLayout = {
      widgets = [
        {
          title = "Event Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"eventarc.googleapis.com/trigger/event_count\" resource.type=\"eventarc.googleapis.com/trigger\""
                }
              }
            }]
          }
        },
        {
          title = "Delivery Success Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_success_count\" resource.type=\"eventarc.googleapis.com/trigger\""
                }
              }
            }]
          }
        },
        {
          title = "Delivery Failure Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_failure_count\" resource.type=\"eventarc.googleapis.com/trigger\""
                }
              }
            }]
          }
        },
        {
          title = "Delivery Latency (P50, P95, P99)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_50"
                    }
                  }
                }
              },
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
              },
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_99"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}
```

## Variables for Monitoring Configuration

Add these to `variables.tf`:

```hcl
variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
  default     = ""
}

variable "enable_monitoring_alerts" {
  description = "Enable Cloud Monitoring alert policies"
  type        = bool
  default     = false
}

variable "enable_monitoring_dashboard" {
  description = "Create Cloud Monitoring dashboard for Eventarc"
  type        = bool
  default     = true
}
```

## Manual Reprocessing of Failed Events

When events fail after all retries, use Cloud Logging to find failed events and manually reprocess:

1. **Query failed events:**
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision"
      resource.labels.service_name="mime-decoder"
      severity=ERROR
      jsonPayload.manual_reprocessing_required=true' \
     --limit=50 \
     --format=json \
     --project=YOUR_PROJECT_ID
   ```

2. **Extract file information from logs:**
   - `jsonPayload.bucket`
   - `jsonPayload.object_name`
   - `jsonPayload.event_id`

3. **Trigger reprocessing:**
   ```bash
   # Copy file to trigger new OBJECT_FINALIZE event
   gsutil cp gs://BUCKET/OBJECT_NAME gs://BUCKET/reprocess/OBJECT_NAME
   ```

## Cost Considerations

- Cloud Monitoring metrics: First 150 MB/month free, then $0.2580 per MB
- Cloud Logging: First 50 GB/month free, then $0.50 per GB
- Alert policies: No additional cost
- Notification channels: Cost varies by type (email is free, Slack webhook is free)

Estimated monthly cost for typical usage (1000 events/day):
- Metrics ingestion: ~5 MB/month (~$1.29)
- Logging: ~100 MB/month (within free tier)
- **Total: ~$1-2/month**
