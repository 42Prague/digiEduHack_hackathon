# Requirements Document

## Introduction

The Eventarc Integration provides event-driven automation for the data processing pipeline.
When files are uploaded to Cloud Storage, Eventarc automatically triggers the MIME Decoder service to begin processing. This eliminates the need for polling and ensures immediate processing of uploaded files.

## Glossary

- **Eventarc**: Google Cloud's event routing service that connects event sources to event consumers
- **OBJECT_FINALIZE Event**: Cloud Storage event emitted when a file upload completes
- **Event Trigger**: Configuration that subscribes to specific events and routes them to a target service

- **Event Payload**: JSON data containing file metadata (bucket, object name, content type, size)
- **Dead Letter Queue**: Storage for events that fail to be delivered after retries
- **Service Account**: Identity used by Eventarc to invoke Cloud Run services
- **Event Filter**: Criteria for selecting which events to process (e.g., specific bucket or file prefix)

## Requirements


### Requirement 1: Event Trigger Configuration

**User Story:** As a DevOps engineer, I want Eventarc triggers configured via Terraform, so that event routing is reproducible and version-controlled.

#### Acceptance Criteria

1. THE Eventarc Trigger SHALL be defined in Terraform configuration files
2. WHEN the trigger is created, THE Eventarc Trigger SHALL subscribe to OBJECT_FINALIZE events from the configured Cloud Storage bucket
3. WHEN an OBJECT_FINALIZE event occurs, THE Eventarc Trigger SHALL route the event to the MIME Decoder Cloud Run service
4. THE Eventarc Trigger SHALL include event filters for bucket name and optional object prefix
5. THE Eventarc Trigger SHALL use a dedicated service account with Cloud Run Invoker permissions


### Requirement 2: Event Delivery Guarantees

**User Story:** As a system architect, I want at-least-once delivery guarantees, so that no uploaded files are lost or missed.

#### Acceptance Criteria

1. WHEN an OBJECT_FINALIZE event is emitted, THE Eventarc SHALL deliver the event to the MIME Decoder at least once
2. WHEN the MIME Decoder returns an error response, THE Eventarc SHALL retry delivery with exponential backoff
3. THE Eventarc SHALL retry failed deliveries up to a configured maximum number of attempts
4. WHEN all retry attempts are exhausted, THE Eventarc SHALL route the event to a dead letter queue
5. THE Eventarc SHALL preserve event ordering for events from the same file


### Requirement 3: Event Payload Format

**User Story:** As a developer, I want standardized event payloads, so that the MIME Decoder can reliably extract file metadata.

#### Acceptance Criteria

1. WHEN an event is delivered, THE Eventarc SHALL include the Cloud Storage bucket name in the event payload
2. WHEN an event is delivered, THE Eventarc SHALL include the object name (file path) in the event payload
3. WHEN an event is delivered, THE Eventarc SHALL include the content type in the event payload
4. WHEN an event is delivered, THE Eventarc SHALL include the file size in bytes in the event payload
5. WHEN an event is delivered, THE Eventarc SHALL include the event timestamp in the event payload
6. THE event payload SHALL follow the CloudEvents specification format


### Requirement 4: Service Account and Permissions

**User Story:** As a security engineer, I want least-privilege service accounts, so that Eventarc has only the permissions it needs.

#### Acceptance Criteria

1. THE Eventarc Trigger SHALL use a dedicated service account (eventarc-trigger-sa)
2. THE service account SHALL have Cloud Run Invoker role for the MIME Decoder service
3. THE service account SHALL have Eventarc Event Receiver role
4. THE service account SHALL NOT have permissions to read or write Cloud Storage objects
5. THE service account SHALL be created and managed via Terraform


### Requirement 5: Dead Letter Queue Configuration

**User Story:** As a DevOps engineer, I want fa
iled events captured, so that I can investigate and reprocess them.

#### Acceptance Criteria

1. THE Eventarc Trigger SHALL configure a Pub/Sub topic as the dead letter queue
2. WHEN an event fails after all retry attempts, THE Eventarc SHALL publish the event to the dead letter topic
3. THE dead letter message SHALL include the original event payload
4. THE dead letter message SHALL include error details and retry history
5. THE dead letter topic SHALL be created and managed via Terraform


### Requirement 6: Event Filtering

**User Story:** As a system architect, I want to filter events by file location, so that only relevant files trigger processing.


#### Acceptance Criteria

1. THE Eventarc Trigger SHALL filter events by bucket name matching the configured upload bucket
2. WHERE a file prefix is configured, THE Eventarc Trigger SHALL only process files matching the prefix
3. THE Eventarc Trigger SHALL ignore events from temporary or system files
4. THE event filters SHALL be configurable via Terraform variables


### Requirement 7: Monitoring and Observability

**User Story:** As a DevOps engineer, I want event delivery metrics, so that I can monitor pipeline health.

#### Acceptance Criteria


1. THE Eventarc SHALL emit metrics for total events received
2. THE Eventarc SHALL emit metrics for successful deliveries
3. THE Eventarc SHALL emit metrics for failed deliveries
4. THE Eventarc SHALL emit metrics for retry attempts
5. THE Eventarc SHALL log all event deliveries with timestamps and status
6. THE metrics SHALL be available in Cloud Monitoring


### Requirement 8: Regional Configuration

**User Story:** As a compliance officer, I want events processed in the EU region, so that we maintain data locality.


#### Acceptance Criteria

1. THE Eventarc Trigger SHALL be created in the EU region
2. THE Eventarc Trigger SHALL only process events from EU-region Cloud Storage buckets
3. THE MIME Decoder Cloud Run service SHALL be deployed in the EU region
4. THE dead letter Pub/Sub topic SHALL be created in the EU region
5. THE region SHALL be configurable via Terraform variables

### Requirement 9: Terraform Configuration Structure

**User Story:** As a DevOps engineer, I want modular Terraform configuration, so that I can reuse and maintain the infrastructure code easily.

#### Acceptance Criteria

1. THE Eventarc configuration SHALL be defined in infra/terraform/eventarc.tf
2. THE Terraform configuration SHALL use variables for all configurable parameters
3. THE Terraform configuration SHALL output the trigger name and dead letter topic name
4. THE Terraform configuration SHALL depend on Cloud Storage bucket and MIME Decoder service resources
5. THE Terraform configuration SHALL use consistent naming conventions with other infrastructure components
