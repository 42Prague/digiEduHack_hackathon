# Backend (Cloud Run FastAPI)

## Responsibilities

Backend handles user interaction through the PWA interface:

1. **File upload initiation**
   - Creating resumable upload sessions in Cloud Storage
   - Generating unique file_id for tracking files
   - Providing session_uri for client-side upload

2. **Processing status monitoring**
   - Receiving statuses from MIME Decoder after processing completion
   - Transmitting data health, preview, and logs information to the UI

3. **API Gateway**
   - Single entry point for all client requests
   - Processing HTTP requests from PWA

## Motivation

**Why a separate Backend service is needed:**

1. **Separation of concerns**
   - Separating client interaction from data processing business logic
   - PWA works only with Backend, unaware of the internal system architecture

2. **Server-side upload management**
   - Secure creation of upload sessions without passing credentials to the client
   - Access control and quotas at the server level

3. **Asynchronous processing**
   - Backend initiates upload but does not block during processing
   - Eventarc triggers processing automatically when upload completes

4. **Centralized status**
   - Single place for aggregating file processing statuses
   - Providing user feedback about the processing flow
