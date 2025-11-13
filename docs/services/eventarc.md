# Eventarc

## Responsibilities

Eventarc is Google Cloud's event routing service that connects Cloud Storage to the processing pipeline:

1. **Event subscription**
   - Subscribing to OBJECT_FINALIZE events from Cloud Storage
   - Filtering events based on bucket and object criteria
   - Managing event triggers configuration

2. **Event delivery**
   - Reliably delivering events to MIME Decoder
   - Providing at-least-once delivery guarantee
   - Handling retries on delivery failures
   - Managing dead-letter queues for failed events

3. **Event transformation**
   - Converting Cloud Storage events to HTTP requests
   - Formatting event payload with file metadata
   - Adding authentication headers for Cloud Run invocation

4. **Decoupling services**
   - Separating event source (Cloud Storage) from event consumer (MIME Decoder)
   - Enabling asynchronous processing flow
   - No direct coupling between upload and processing services

## Motivation

**Why Eventarc is needed:**

1. **Event-driven architecture**
   - Enables reactive processing triggered by file uploads
   - No polling required for detecting new files
   - Immediate processing start after upload completion
   - Cloud-native event routing

2. **Reliability guarantees**
   - At-least-once delivery ensures no events are lost
   - Automatic retries with exponential backoff
   - Dead-letter queue for failed events
   - Audit trail of event delivery

3. **Service decoupling**
   - Cloud Storage doesn't need to know about MIME Decoder
   - MIME Decoder doesn't need to poll Cloud Storage
   - Services can be developed and scaled independently
   - Easy to add new event consumers without changing producers

4. **Operational simplicity**
   - Managed service with no infrastructure to maintain
   - Built-in monitoring and logging
   - Automatic scaling with event volume
   - Native integration with Google Cloud services

5. **Flexible routing**
   - Can filter events by object prefix, suffix, bucket
   - Can route different events to different services
   - Supports multiple consumers for the same event
   - Easy to add new processing pipelines
