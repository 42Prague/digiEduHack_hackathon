# Cloud Storage (EU)

## Responsibilities

Cloud Storage serves as the primary object storage for all file data:

1. **File upload handling**
   - Providing resumable upload sessions created by Backend
   - Receiving file chunks from User PWA
   - Storing uploaded files with region locality (EU)
   - Returning upload completion status to User PWA

2. **Event emission**
   - Emitting OBJECT_FINALIZE events to Eventarc when upload completes
   - Triggering automatic processing pipeline

3. **File persistence**
   - Storing original uploaded files
   - Storing processed text files from Transformer (text/*.txt)
   - Providing file access to all services (MIME Decoder, Transformer, Tabular)

4. **Data locality compliance**
   - Ensuring data stays in EU region for compliance
   - Regional bucket configuration
   - Access control and security

## Motivation

**Why Cloud Storage (EU) is needed:**

1. **Scalable object storage**
   - Handles files of any size
   - Automatic scaling without capacity planning
   - Durable storage with built-in redundancy
   - Cost-effective for large volumes

2. **Direct upload pattern**
   - Users upload directly using signed URLs (session_uri)
   - No backend bottleneck for file transfer
   - Better performance and lower latency
   - Reduced backend infrastructure costs

3. **Event-driven integration**
   - Native integration with Eventarc
   - Automatic event emission on OBJECT_FINALIZE
   - Decouples upload from processing
   - Reliable event delivery

4. **Data locality and compliance**
   - EU region ensures GDPR compliance
   - Data sovereignty requirements
   - Configurable per-region buckets
   - Meets regulatory requirements

5. **Intermediate data storage**
   - Stores both original and processed files
   - Enables reprocessing without re-uploading
   - Audit trail of all file versions
   - Shared storage accessible by all services
