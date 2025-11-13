# User PWA

## Responsibilities

User PWA is the frontend Progressive Web Application that provides the user interface:

1. **File upload interface**
   - Initiating upload by calling Backend's initiate_upload() with region_id, filename, and MIME type
   - Receiving session_uri and file_id from Backend
   - Uploading file chunks directly to Cloud Storage using session_uri
   - Handling resumable upload protocol for large files

2. **Upload progress tracking**
   - Displaying upload progress to the user
   - Handling upload errors and retries
   - Receiving upload_complete confirmation from Cloud Storage

3. **Processing status display**
   - Receiving status updates from Backend
   - Displaying data health metrics
   - Showing file preview
   - Presenting processing logs to the user

4. **User interaction**
   - File selection and validation
   - Region selection for data locality
   - Interactive feedback during upload and processing

## Motivation

**Why a separate User PWA component is needed:**

1. **Direct upload to storage**
   - Uploads files directly to Cloud Storage after receiving session_uri
   - Reduces load on Backend (no proxying of file data)
   - Better performance for large files using resumable uploads

2. **Progressive Web App benefits**
   - Works offline when cached
   - Installable on user devices
   - Cross-platform (web, mobile, desktop) with single codebase
   - No app store deployment needed

3. **User experience**
   - Real-time upload progress feedback
   - Immediate response to user actions
   - Asynchronous status updates for processing
   - Rich interactive interface

4. **Separation of concerns**
   - Frontend logic separated from backend API
   - Can be developed and deployed independently
   - Different scaling characteristics than Backend
   - Can be served from CDN for global performance
