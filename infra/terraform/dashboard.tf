# Cloud Monitoring Dashboard for Eventarc Integration
# Provides visibility into event delivery metrics and MIME Decoder performance

resource "google_monitoring_dashboard" "eventarc_dashboard" {
  count = var.enable_eventarc && var.enable_monitoring_dashboard ? 1 : 0
  dashboard_json = jsonencode({
    displayName = "Eventarc Integration Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        # Row 1: Event Counts
        {
          width  = 6
          height = 4
          widget = {
            title = "Event Count (Total Received)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/event_count\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Events/sec"
                scale = "LINEAR"
              }
              chartOptions = {
                mode = "COLOR"
              }
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Match Count (Filtered Events)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/match_count\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Events/sec"
                scale = "LINEAR"
              }
            }
          }
        },

        # Row 2: Delivery Success and Failure
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Delivery Success Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_success_count\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType       = "LINE"
                targetAxis     = "Y1"
                legendTemplate = "Success"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Successes/sec"
                scale = "LINEAR"
              }
              chartOptions = {
                mode = "COLOR"
              }
            }
          }
        },
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Delivery Failure Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_failure_count\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType       = "LINE"
                targetAxis     = "Y1"
                legendTemplate = "Failures"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Failures/sec"
                scale = "LINEAR"
              }
              chartOptions = {
                mode = "COLOR"
              }
              thresholds = [{
                value     = 0.1
                color     = "RED"
                direction = "ABOVE"
                label     = "High Failure Rate (>10%)"
              }]
            }
          }
        },

        # Row 3: Delivery Latency Percentiles
        {
          yPos   = 8
          width  = 12
          height = 4
          widget = {
            title = "Delivery Latency (P50, P95, P99)"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_50"
                      }
                    }
                  }
                  plotType       = "LINE"
                  targetAxis     = "Y1"
                  legendTemplate = "P50"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_95"
                      }
                    }
                  }
                  plotType       = "LINE"
                  targetAxis     = "Y1"
                  legendTemplate = "P95"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"eventarc.googleapis.com/trigger/delivery_latency\" resource.type=\"eventarc.googleapis.com/trigger\" resource.label.trigger_name=\"${google_eventarc_trigger.storage_trigger[0].name}\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_99"
                      }
                    }
                  }
                  plotType       = "LINE"
                  targetAxis     = "Y1"
                  legendTemplate = "P99"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
              chartOptions = {
                mode = "COLOR"
              }
              thresholds = [{
                value     = 30000
                color     = "YELLOW"
                direction = "ABOVE"
                label     = "High Latency (>30s)"
              }]
            }
          }
        },

        # Row 4: MIME Decoder Performance
        {
          yPos   = 12
          width  = 6
          height = 4
          widget = {
            title = "MIME Decoder Request Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.mime_decoder_service_name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Requests/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          xPos   = 6
          yPos   = 12
          width  = 6
          height = 4
          widget = {
            title = "MIME Decoder Request Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.mime_decoder_service_name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_99"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },

        # Row 5: MIME Decoder Resource Utilization
        {
          yPos   = 16
          width  = 6
          height = 4
          widget = {
            title = "MIME Decoder CPU Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.mime_decoder_service_name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "CPU Utilization (%)"
                scale = "LINEAR"
              }
              thresholds = [{
                value     = 0.8
                color     = "YELLOW"
                direction = "ABOVE"
                label     = "High CPU (>80%)"
              }]
            }
          }
        },
        {
          xPos   = 6
          yPos   = 16
          width  = 6
          height = 4
          widget = {
            title = "MIME Decoder Memory Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/memory/utilizations\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.mime_decoder_service_name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Memory Utilization (%)"
                scale = "LINEAR"
              }
              thresholds = [{
                value     = 0.8
                color     = "YELLOW"
                direction = "ABOVE"
                label     = "High Memory (>80%)"
              }]
            }
          }
        },

        # Row 6: MIME Decoder Instance Count
        {
          yPos   = 20
          width  = 12
          height = 4
          widget = {
            title = "MIME Decoder Active Instances"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/instance_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.mime_decoder_service_name}\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Instance Count"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })

  depends_on = [
    google_eventarc_trigger.storage_trigger[0]
  ]
}
