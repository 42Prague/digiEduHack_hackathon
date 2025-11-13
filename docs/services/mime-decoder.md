# MIME Decoder (Cloud Run)

## Responsibilities

MIME Decoder acts as the file processing coordinator:

1. **Upload event processing**
   - Receiving OBJECT_FINALIZE events from Eventarc
   - Initiating processing by file_id

2. **File type detection**
   - Retrieving file from Cloud Storage
   - Detecting MIME type
   - Classifying into categories: text, image, audio, archive, other

3. **Processing routing**
   - Passing file_id and detected type to Transformer
   - Does not perform transformation itself, only coordinates

4. **Status relay**
   - Receiving final status from Tabular
   - Relaying processing status to Backend for user display

## Motivation

**Why a separate MIME Decoder service is needed:**

1. **Event-driven architecture**
   - Reacts to file upload events automatically
   - Separates upload process from processing pipeline
   - Ensures at-least-once processing guarantee through Eventarc

2. **Single entry point for processing**
   - Centralized file type detection
   - All files go through one component for classification
   - Simplifies monitoring and logging of processing start

3. **Separation of concerns**
   - Does not mix type detection logic with transformation logic
   - Coordinates the process but does not perform heavy operations
   - Can be a lightweight service with fast cold start

4. **Scalability**
   - Cloud Run automatically scales with high event volume
   - Each instance processes one file independently
   - No state required between requests
