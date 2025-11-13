# Implementation Plan

- [ ] 1. Enable required GCP APIs
  - Enable Eventarc API in the GCP project
  - Enable Pub/Sub API for dead letter queue
  - Verify APIs are enabled using gcloud or Terraform
  - _Requirements: 1.1, 9.4_

- [ ] 2. Create service account for Eventarc trigger
  - Create infra/terraform/iam.tf if it doesn't exist
  - Define google_service_account resource for eventarc-trigger-sa
  - Add display_name and description
  - _Requirements: 4.1, 4.5_

- [ ] 3. Configure service account permissions
  - Add Cloud Run Invoker role for MIME Decoder service
  - Add Eventarc Event Receiver role at project level
  - Ensure no Cloud Storage permissions are granted
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 4. Create dead letter Pub/Sub topic
  - Create infra/terraform/eventarc.tf
  - Define google_pubsub_topic resource for dead letter queue
  - Set message_retention_duration to 7 days (604800s)
  - Add labels for identification
  - _Requirements: 5.1, 5.2, 5.5_

- [ ] 5. Create dead letter Pub/Sub subscription
  - Define google_pubsub_subscription resource
  - Set ack_deadline_seconds to 600 (10 minutes)
  - Enable retain_acked_messages for audit trail
  - Set message_retention_duration to 7 days
  - _Requirements: 5.3, 5.4_


- [ ] 6. Define Terraform variables for Eventarc configuration
  - Add variables to infra/terraform/variables.tf
  - Define var.region with default "europe-west1"
  - Define var.eventarc_trigger_name with default "${var.project_name}-storage-trigger"
  - Define var.event_filter_prefix for optional file prefix filtering
  - _Requirements: 6.4, 8.5, 9.2_

- [ ] 7. Create Eventarc trigger resource
  - Define google_eventarc_trigger resource in eventarc.tf
  - Set name using var.eventarc_trigger_name
  - Set location to var.region (EU)
  - Configure service_account to use eventarc-trigger-sa
  - _Requirements: 1.1, 1.2, 1.5, 8.1, 9.1_

- [ ] 8. Configure event matching criteria
  - Add matching_criteria for event type: google.cloud.storage.object.v1.finalized
  - Add matching_criteria for bucket name from Cloud Storage bucket resource
  - Add optional matching_criteria for object prefix if var.event_filter_prefix is set
  - _Requirements: 1.2, 1.4, 6.1, 6.2_

- [ ] 9. Configure event destination
  - Add destination block pointing to MIME Decoder Cloud Run service
  - Reference google_cloud_run_service.mime_decoder.name
  - Set region to var.region
  - _Requirements: 1.3, 8.3_

- [ ] 10. Configure retry and dead letter queue
  - Add transport block with pubsub configuration
  - Reference dead letter topic ID
  - Configure retry_policy with max_retry_duration
  - Set exponential backoff parameters
  - _Requirements: 2.2, 2.3, 2.4, 5.2_


- [ ] 11. Add Terraform outputs
  - Create or update infra/terraform/outputs.tf
  - Output eventarc_trigger_name
  - Output dead_letter_topic_name
  - Output dead_letter_subscription_name
  - _Requirements: 9.3_

- [ ] 12. Add resource dependencies
  - Ensure Eventarc trigger depends_on Cloud Storage bucket
  - Ensure Eventarc trigger depends_on MIME Decoder Cloud Run service
  - Ensure service account IAM bindings are created before trigger
  - _Requirements: 9.4_

- [ ] 13. Configure monitoring and alerting
  - Document Cloud Monitoring metrics in README or monitoring.md
  - Create alert policy for high failure rate (>10% failures)
  - Create alert policy for DLQ growth (>100 unacked messages)
  - Create alert policy for high latency (p95 > 30s)
  - Create alert policy for no events (0 events for >1 hour)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 14. Test Eventarc trigger
  - Apply Terraform configuration to create resources
  - Upload a test file to Cloud Storage bucket
  - Verify OBJECT_FINALIZE event is emitted
  - Check MIME Decoder logs for event receipt
  - Verify event payload contains correct metadata
  - _Requirements: 2.1, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 15. Test retry mechanism
  - Temporarily make MIME Decoder return 500 error
  - Upload a test file
  - Verify Eventarc retries with exponential backoff
  - Check Cloud Logging for retry attempts
  - Verify event eventually reaches dead letter queue
  - _Requirements: 2.2, 2.3, 2.4_


- [ ] 16. Test event filtering
  - Upload files to different paths in the bucket
  - Verify only files matching the configured prefix trigger events
  - Test with temporary/system files to ensure they're ignored
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 17. Verify regional configuration
  - Confirm Eventarc trigger is created in EU region
  - Verify trigger only processes events from EU bucket
  - Check MIME Decoder is deployed in EU region
  - Verify dead letter topic is in EU region
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 18. Document deployment process
  - Create or update infra/terraform/README.md
  - Document prerequisites (APIs, existing resources)
  - Document Terraform deployment steps
  - Add testing instructions
  - Add troubleshooting section
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 19. Verify security configuration
  - Audit service account permissions
  - Verify least-privilege access
  - Check that service account cannot access Cloud Storage objects
  - Verify HTTPS is used for event delivery
  - Confirm authentication is required for MIME Decoder invocation
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 20. Create monitoring dashboard
  - Create Cloud Monitoring dashboard for Eventarc metrics
  - Add charts for event_count, delivery_success_count, delivery_failure_count
  - Add chart for delivery_latency percentiles
  - Add chart for DLQ message count
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_
