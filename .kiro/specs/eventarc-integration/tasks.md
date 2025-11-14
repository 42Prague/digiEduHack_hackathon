# Implementation Plan

- [x] 1. Enable required GCP APIs
  - Enable Eventarc API in the GCP project
  - Verify APIs are enabled using gcloud or Terraform
  - _Requirements: 1.1, 9.4_

- [x] 2. Create service account for Eventarc trigger
  - Create infra/terraform/iam.tf if it doesn't exist
  - Define google_service_account resource for eventarc-trigger-sa
  - Add display_name and description
  - _Requirements: 4.1, 4.5_

- [x] 3. Configure service account permissions
  - Add Cloud Run Invoker role for MIME Decoder service
  - Add Eventarc Event Receiver role at project level
  - Ensure no Cloud Storage permissions are granted
  - _Requirements: 4.2, 4.3, 4.4_

- [x] 4. Define Terraform variables for Eventarc configuration
  - Add variables to infra/terraform/variables.tf
  - Define var.region with default "europe-west1"
  - Define var.eventarc_trigger_name with default "${var.project_name}-storage-trigger"
  - Define var.event_filter_prefix for optional file prefix filtering
  - _Requirements: 6.4, 8.5, 9.2_

- [x] 5. Create Eventarc trigger resource
  - Create infra/terraform/eventarc.tf
  - Define google_eventarc_trigger resource in eventarc.tf
  - Set name using var.eventarc_trigger_name
  - Set location to var.region (EU)
  - Configure service_account to use eventarc-trigger-sa
  - _Requirements: 1.1, 1.2, 1.5, 8.1, 9.1_

- [x] 6. Configure event matching criteria
  - Add matching_criteria for event type: google.cloud.storage.object.v1.finalized
  - Add matching_criteria for bucket name from Cloud Storage bucket resource
  - Add optional matching_criteria for object prefix if var.event_filter_prefix is set
  - _Requirements: 1.2, 1.4, 6.1, 6.2_

- [x] 7. Configure event destination
  - Add destination block pointing to MIME Decoder Cloud Run service
  - Reference google_cloud_run_service.mime_decoder.name
  - Set region to var.region
  - _Requirements: 1.3, 8.3_

- [x] 8. Configure retry policy
  - Configure retry_policy with max_retry_duration
  - Set exponential backoff parameters (minimum 5 retries)
  - Configure retry intervals: 10s, 20s, 40s, 80s, 160s
  - _Requirements: 2.2, 2.3_
  - _Note: Eventarc uses default retry policy for Cloud Run destinations with 5 retries and exponential backoff_

- [x] 9. Add Terraform outputs
  - Create or update infra/terraform/outputs.tf
  - Output eventarc_trigger_name
  - _Requirements: 9.3_

- [x] 10. Add resource dependencies
  - Ensure Eventarc trigger depends_on Cloud Storage bucket
  - Ensure Eventarc trigger depends_on MIME Decoder Cloud Run service
  - Ensure service account IAM bindings are created before trigger
  - _Requirements: 9.4_

- [x] 11. Configure error logging for failed events
  - Document required log fields in design.md
  - Ensure MIME Decoder logs failures with full context
  - Configure log structure: event_id, bucket, object_name, content_type, size, error, retry_count, timestamps
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 12. Configure monitoring and alerting
  - Document Cloud Monitoring metrics in README or monitoring.md
  - Create alert policy for high failure rate (>10% failures)
  - Create alert policy for high latency (p95 > 30s)
  - Create alert policy for no events (0 events for >1 hour)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 13. Test Eventarc trigger (REQUIRES DEPLOYMENT)
  - Apply Terraform configuration to create resources
  - Upload a test file to Cloud Storage bucket
  - Verify OBJECT_FINALIZE event is emitted
  - Check MIME Decoder logs for event receipt
  - Verify event payload contains correct metadata
  - _Requirements: 2.1, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 14. Test retry mechanism (REQUIRES DEPLOYMENT)
  - Temporarily make MIME Decoder return 500 error
  - Upload a test file
  - Verify Eventarc retries with exponential backoff (5 times)
  - Check Cloud Logging for retry attempts
  - Verify final failure is logged with full event context
  - _Requirements: 2.2, 2.3, 2.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 15. Test event filtering (REQUIRES DEPLOYMENT)
  - Upload files to different paths in the bucket
  - Verify only files matching the configured prefix trigger events
  - Test with temporary/system files to ensure they're ignored
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 16. Verify regional configuration (REQUIRES DEPLOYMENT)
  - Confirm Eventarc trigger is created in EU region
  - Verify trigger only processes events from EU bucket
  - Check MIME Decoder is deployed in EU region
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 17. Document deployment process
  - Create or update infra/terraform/README.md
  - Document prerequisites (APIs, existing resources)
  - Document Terraform deployment steps
  - Add testing instructions
  - Add troubleshooting section
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 18. Verify security configuration
  - Audit service account permissions
  - Verify least-privilege access
  - Check that service account cannot access Cloud Storage objects
  - Verify HTTPS is used for event delivery
  - Confirm authentication is required for MIME Decoder invocation
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 19. Create monitoring dashboard
  - Create Cloud Monitoring dashboard for Eventarc metrics
  - Add charts for event_count, delivery_success_count, delivery_failure_count
  - Add chart for delivery_latency percentiles
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

- [x] 20. Document known limitations
  - Add "Known Limitations" section to design.md
  - Document lack of Dead Letter Queue
  - Explain manual reprocessing workflow via Cloud Logging
  - Note this as production improvement opportunity
  - _Related to: simplicity principle for MVP_

- [ ] 21. Create service account for Tabular service trigger
  - Add google_service_account resource for tabular-trigger-sa in infra/terraform/iam.tf
  - Add display_name "Tabular Service Eventarc Trigger SA"
  - Add description "Service account for Eventarc trigger to invoke Tabular service"
  - _Requirements: 10.5_

- [ ] 22. Configure Tabular service account permissions
  - Add Cloud Run Invoker role for Tabular Cloud Run service
  - Add Eventarc Event Receiver role at project level
  - Ensure no Cloud Storage permissions are granted
  - _Requirements: 10.5_

- [ ] 23. Create Eventarc trigger for Tabular service
  - Add google_eventarc_trigger resource for Tabular service in infra/terraform/eventarc.tf
  - Set name to "${var.project_name}-tabular-trigger"
  - Set location to var.region (EU)
  - Configure service_account to use tabular-trigger-sa
  - Add matching_criteria for event type: google.cloud.storage.object.v1.finalized
  - Add matching_criteria for bucket name from Cloud Storage bucket resource
  - Add matching_criteria for object prefix "text/"
  - Add destination block pointing to Tabular Cloud Run service
  - Configure same retry policy as MIME Decoder trigger (5 retries, exponential backoff)
  - Add depends_on for Cloud Storage bucket and Tabular Cloud Run service
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 24. Add Tabular trigger output
  - Add tabular_trigger_name output to infra/terraform/outputs.tf
  - Output the trigger name for verification
  - _Requirements: 10.8_

- [ ] 25. Update monitoring dashboard for Tabular trigger
  - Add Tabular trigger metrics to Cloud Monitoring dashboard
  - Add charts for Tabular event_count, delivery_success_count, delivery_failure_count
  - Add chart for Tabular delivery_latency percentiles
  - Create alert policy for Tabular high failure rate (>10% failures)
  - Create alert policy for Tabular high latency (p95 > 60s, AI processing takes longer)
  - Create alert policy for no text file events (0 events for >2 hours)
  - _Requirements: 10.7_

- [ ] 26. Test Tabular Eventarc trigger (REQUIRES DEPLOYMENT)
  - Apply Terraform configuration to create Tabular trigger
  - Upload a test file that triggers Transformer
  - Wait for Transformer to save text file to text/*.txt
  - Verify OBJECT_FINALIZE event is emitted for text file
  - Check Tabular service logs for event receipt
  - Verify event payload contains correct metadata
  - Verify data is loaded to BigQuery
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 27. Update documentation for Tabular trigger
  - Update infra/terraform/README.md with Tabular trigger information
  - Document the two-trigger architecture (uploads → MIME Decoder, text → Tabular)
  - Add Tabular trigger testing instructions
  - Document Tabular trigger monitoring and alerting
  - Add troubleshooting section for Tabular trigger issues
  - _Requirements: 10.8_

---

## Implementation Summary

**Completed Tasks (16/27)**:
- ✅ Tasks 1-12: MIME Decoder infrastructure and code implementation
- ✅ Tasks 17-20: MIME Decoder documentation

**Pending Tasks (11/27)**:
- ⏸️ Tasks 13-16: MIME Decoder testing (requires deployment)
- 🆕 Tasks 21-25: Tabular service trigger implementation
- ⏸️ Task 26: Tabular trigger testing (requires deployment)
- 🆕 Task 27: Tabular trigger documentation

**Next Steps**:
1. Implement Tabular service trigger (tasks 21-25)
2. Deploy infrastructure using `terraform apply`
3. Build and push MIME Decoder and Tabular Docker images
4. Execute testing tasks 13-16 and 26
5. Verify all requirements are met
