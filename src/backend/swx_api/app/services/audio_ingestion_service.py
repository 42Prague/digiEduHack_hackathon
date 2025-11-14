"""
Audio Ingestion Service
-----------------------
Handles audio/transcript file ingestion with metadata, transcription, and cultural analysis.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from swx_api.app.services.metadata_validator import (
    validate_metadata,
    validate_file_extension,
    determine_file_type,
)
from swx_api.app.services.cultural_analysis_service import analyze_cultural_transcript
from swx_api.app.services.ingestion_service import paths

logger = logging.getLogger("audio_ingestion")


class AudioIngestionPaths:
    """Manages folder structure for audio/transcript processing."""
    
    def __init__(self, base_data_dir: Path):
        self.base_dir = base_data_dir
        
        # Define all required directories
        self.raw_audio_dir = self.base_dir / "raw" / "audio"
        self.raw_transcripts_dir = self.base_dir / "raw" / "transcripts"
        self.processed_metadata_dir = self.base_dir / "processed" / "metadata"
        self.processed_clean_text_dir = self.base_dir / "processed" / "clean_text"
        self.processed_transcripts_dir = self.base_dir / "processed" / "transcripts"
        self.analysis_cultural_dir = self.base_dir / "analysis" / "cultural"
        self.analysis_themes_dir = self.base_dir / "analysis" / "themes"
        self.analysis_metrics_dir = self.base_dir / "analysis" / "metrics"
        
        # Create all directories
        for dir_path in [
            self.raw_audio_dir,
            self.raw_transcripts_dir,
            self.processed_metadata_dir,
            self.processed_clean_text_dir,
            self.processed_transcripts_dir,
            self.analysis_cultural_dir,
            self.analysis_themes_dir,
            self.analysis_metrics_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Initialize paths using existing ingestion paths structure
audio_paths = AudioIngestionPaths(paths.data_dir)


def save_raw_file(file_content: bytes, filename: str, file_type: str, record_uuid: uuid.UUID) -> Path:
    """
    Save raw file to appropriate directory.
    
    Args:
        file_content: File bytes
        filename: Original filename
        file_type: 'audio' or 'transcript'
        record_uuid: UUID for the record
        
    Returns:
        Path to saved file
    """
    ext = Path(filename).suffix.lower()
    
    if file_type == "audio":
        target_dir = audio_paths.raw_audio_dir
    else:
        target_dir = audio_paths.raw_transcripts_dir
    
    saved_path = target_dir / f"{record_uuid}{ext}"
    saved_path.write_bytes(file_content)
    
    logger.info(f"Saved raw {file_type} file: {saved_path}")
    return saved_path


def save_metadata(metadata: Dict[str, Any], record_uuid: uuid.UUID, original_filename: str) -> Path:
    """
    Save metadata JSON file.
    
    Args:
        metadata: Metadata dictionary
        record_uuid: UUID for the record
        original_filename: Original filename
        
    Returns:
        Path to saved metadata file
    """
    metadata_payload = {
        "uuid": str(record_uuid),
        "original_filename": original_filename,
        **metadata,
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    
    metadata_path = audio_paths.processed_metadata_dir / f"{record_uuid}.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved metadata: {metadata_path}")
    return metadata_path


def transcribe_audio(audio_path: Path) -> Optional[str]:
    """
    Transcribe audio file using Whisper.
    
    For now, returns None (placeholder). In production, integrate:
    - Local Whisper model
    - Or Whisper API
    - Or other transcription service
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Transcribed text or None if transcription fails
    """
    # TODO: Implement Whisper transcription
    # For now, log and return None
    logger.warning(f"Audio transcription not yet implemented for: {audio_path}")
    logger.info("Placeholder: Would transcribe audio using Whisper here")
    
    # Placeholder implementation would be:
    # import whisper
    # model = whisper.load_model("base")
    # result = model.transcribe(str(audio_path))
    # return result["text"]
    
    return None


def save_transcript(transcript_text: str, record_uuid: uuid.UUID) -> Path:
    """
    Save transcript text to processed directory.
    
    Args:
        transcript_text: Transcribed or uploaded text
        record_uuid: UUID for the record
        
    Returns:
        Path to saved transcript file
    """
    transcript_path = audio_paths.processed_transcripts_dir / f"{record_uuid}.txt"
    transcript_path.write_text(transcript_text, encoding="utf-8")
    
    logger.info(f"Saved transcript: {transcript_path}")
    return transcript_path


def clean_transcript(transcript_text: str) -> str:
    """
    Clean transcript text (optional step).
    
    Args:
        transcript_text: Raw transcript text
        
    Returns:
        Cleaned transcript text
    """
    # Basic cleaning: remove extra whitespace, normalize line breaks
    cleaned = " ".join(transcript_text.split())
    return cleaned


def save_clean_text(clean_text: str, record_uuid: uuid.UUID) -> Path:
    """
    Save cleaned transcript text.
    
    Args:
        clean_text: Cleaned transcript text
        record_uuid: UUID for the record
        
    Returns:
        Path to saved clean text file
    """
    clean_path = audio_paths.processed_clean_text_dir / f"{record_uuid}.txt"
    clean_path.write_text(clean_text, encoding="utf-8")
    
    logger.info(f"Saved clean text: {clean_path}")
    return clean_path


def save_cultural_analysis(analysis: Dict[str, Any], record_uuid: uuid.UUID) -> Path:
    """
    Save cultural analysis results.
    
    Args:
        analysis: Cultural analysis dictionary
        record_uuid: UUID for the record
        
    Returns:
        Path to saved cultural analysis file
    """
    analysis_path = audio_paths.analysis_cultural_dir / f"{record_uuid}.json"
    with analysis_path.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved cultural analysis: {analysis_path}")
    return analysis_path


def process_audio_ingestion(
    file_content: bytes,
    filename: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main pipeline for audio/transcript ingestion.
    
    Steps:
    1. Validate metadata and file
    2. Generate UUID
    3. Save raw file
    4. Save metadata
    5. Transcribe (if audio) or use text directly
    6. Clean transcript (optional)
    7. Run cultural analysis
    8. Save all artifacts
    
    Args:
        file_content: File bytes
        filename: Original filename
        metadata: Metadata dictionary
        
    Returns:
        Dictionary with processing results
    """
    # Step 1: Validate
    is_valid, error_msg = validate_metadata(metadata)
    if not is_valid:
        raise ValueError(f"Metadata validation failed: {error_msg}")
    
    is_valid, error_msg = validate_file_extension(filename)
    if not is_valid:
        raise ValueError(f"File validation failed: {error_msg}")
    
    # Step 2: Generate UUID
    record_uuid = uuid.uuid4()
    file_type = determine_file_type(filename)
    
    # Step 3: Save raw file
    raw_file_path = save_raw_file(file_content, filename, file_type, record_uuid)
    
    # Step 4: Save metadata
    metadata_path = save_metadata(metadata, record_uuid, filename)
    
    # Step 5: Transcription
    transcript_text = None
    if file_type == "audio":
        transcript_text = transcribe_audio(raw_file_path)
        if not transcript_text:
            logger.warning(f"Transcription failed for {filename}, continuing without transcript")
    else:
        # For text files, use content directly
        try:
            transcript_text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            logger.error(f"Failed to decode text file {filename}")
            raise ValueError("Invalid text file encoding")
    
    # Step 6: Clean transcript (if available)
    clean_text_path = None
    cleaned_text = None  # Initialize to avoid UnboundLocalError
    if transcript_text:
        cleaned_text = clean_transcript(transcript_text)
        clean_text_path = save_clean_text(cleaned_text, record_uuid)
        transcript_path = save_transcript(cleaned_text, record_uuid)
    else:
        transcript_path = None
    
    # Step 7: Cultural analysis
    cultural_analysis = None
    cultural_analysis_path = None
    if cleaned_text: # Use cleaned text for analysis
        try:
            cultural_analysis = analyze_cultural_transcript(cleaned_text)
            cultural_analysis_path = save_cultural_analysis(cultural_analysis, record_uuid)
            logger.info(f"Cultural analysis completed for {record_uuid}")
        except Exception as e:
            logger.error(f"Cultural analysis failed for {record_uuid}: {e}", exc_info=True)
            cultural_analysis = None
    
    # Step 7.5: Generate DQ report for transcript
    dq_report_path = None
    if cleaned_text:
        try:
            from swx_api.app.services.data_quality_service import generate_dq_report
            dq_report = generate_dq_report(
                dataset_id=str(record_uuid),
                data=cleaned_text,
                metadata={"classification": "transcript", "file_type": file_type}
            )
            dq_report_path = dq_report.get("report_path")
            logger.info(f"DQ report generated for transcript {record_uuid}: score={dq_report.get('dq_score', 0)}")
        except Exception as e:
            logger.warning(f"DQ report generation failed for {record_uuid}: {e}")
            dq_report_path = None
    
    # Prepare file paths dictionary
    file_paths = {
        "raw_file": str(raw_file_path),
        "metadata": str(metadata_path),
    }
    
    if transcript_path:
        file_paths["transcript"] = str(transcript_path)
    if clean_text_path:
        file_paths["clean_text"] = str(clean_text_path)
    if cultural_analysis_path:
        file_paths["cultural_analysis"] = str(cultural_analysis_path)
    if dq_report_path:
        file_paths["dq_report"] = str(dq_report_path)
    
    # cleaned_text is already set above, no need to reassign
    
    result = {
        "id": str(record_uuid),
        "file_type": file_type,
        "original_filename": filename,
        "file_paths": file_paths,
        "upload_metadata": metadata,  # Store as upload_metadata for DB
        "metadata": metadata,  # Also include as metadata for response compatibility
        "transcript_text": transcript_text,
        "clean_text": cleaned_text,
        "raw_file_path": str(raw_file_path),
        "transcript_path": str(transcript_path) if transcript_path else None,
        "transcript_available": transcript_text is not None,
        "cultural_analysis": cultural_analysis,
        "dq_report_path": dq_report_path,
        "cultural_analysis_data": {
            "mindset_shift_score": cultural_analysis.get("mindset_shift_score", 0) if cultural_analysis else 0,
            "collaboration_score": cultural_analysis.get("collaboration_score", 0) if cultural_analysis else 0,
            "teacher_confidence_score": cultural_analysis.get("teacher_confidence_score", 0) if cultural_analysis else 0,
            "municipality_cooperation_score": cultural_analysis.get("cooperation_municipality_score", 0) if cultural_analysis else 0,
            "sentiment_score": cultural_analysis.get("sentiment", 50) if cultural_analysis else 50,
            "themes": cultural_analysis.get("themes", []) if cultural_analysis else [],
            "practical_change": cultural_analysis.get("practical_change", "") if cultural_analysis else None,
            "mindset_change": cultural_analysis.get("mindset_change", "") if cultural_analysis else None,
            "impact_summary": cultural_analysis.get("impact_summary", "") if cultural_analysis else None,
            "culture_change_detected": cultural_analysis.get("culture_change_detected", False) if cultural_analysis else False,
        } if cultural_analysis else None,
    }
    
    return result

