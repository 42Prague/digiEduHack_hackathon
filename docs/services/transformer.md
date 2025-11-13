# Transformer

## Responsibilities

Transformer performs conversion of various file formats into text representation:

1. **Processing by file type**
   - **text**: Extracting text from plain/markdown/html/pdf/docx/rtf
   - **image**: OCR text recognition + EXIF metadata extraction
   - **audio**: ASR audio transcription to text
   - **archive**: Unpacking and processing each file inside
   - **other**: Best-effort text extraction or skip

2. **Saving results**
   - Saving extracted text to Cloud Storage
   - Format: gs://.../text/file_id.txt (or *.txt for archives)
   - Passing metadata about the result to Tabular

3. **Forwarding to next stage**
   - Direct forwarding of text_uri(s) and metadata to Tabular
   - Does not return data to MIME Decoder

## Motivation

**Why a separate Transformer service is needed:**

1. **Isolation of complex logic**
   - Processing different formats requires different libraries and dependencies
   - OCR, ASR, PDF parsing are resource-intensive operations
   - Separation from MIME Decoder's coordinating logic

2. **Processing flexibility**
   - Each file type may require specific settings
   - Easy to add new formats without changing MIME Decoder
   - Can use different ML models for different types

3. **Scaling by workload type**
   - Image processing requires GPU
   - Audio processing requires ASR models
   - Can scale different instances for different file types

4. **Reusability**
   - Transformation logic can be used outside the processing pipeline
   - Can be called directly for file re-processing
   - Independent from file source

5. **Output standardization**
   - All file types are converted to unified text format
   - Simplifies subsequent processing in Tabular
   - Unified interface: file_id + type → text_uri + metadata
