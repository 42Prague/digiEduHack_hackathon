from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger("ingestion_route")

from swx_api.app.models.ingestion_models import (
    DatasetInfo,
    IngestionResponse,
    MetricsResponse,
    SummaryResponse,
)
from swx_api.app.models.transcript import TranscriptPublic
from swx_api.app.services.ingestion_service import (
    SUPPORTED_EXTENSIONS,
    ingest_file,
    list_datasets,
    load_summary,
    gather_metrics,
    paths,
    timestamped_filename,
)
from swx_api.app.services.audio_ingestion_service import process_audio_ingestion
from swx_api.app.services.transcript_db_service import (
    create_transcript_record,
    create_cultural_analysis_record,
)
from swx_api.app.models.transcript import TranscriptCreate
from swx_api.app.models.cultural_analysis import CulturalAnalysisCreate
from swx_api.core.database.db import SessionDep

router = APIRouter(prefix="/ingestion")


def save_upload(upload_file: UploadFile) -> Path:
    filename = Path(upload_file.filename or "uploaded")
    sanitized = filename.name.replace(" ", "_")
    stored_name = timestamped_filename(sanitized)
    stored_path = paths.raw_dir / stored_name

    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return stored_path


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_dataset(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    stored_path = save_upload(file)
    try:
        result = ingest_file(stored_path, file.filename or stored_path.name)
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        file.file.close()

    return IngestionResponse.model_validate(result)


@router.get("/datasets")
async def get_datasets():
    """
    List all ingested datasets with enhanced metadata.
    
    Returns:
        List of datasets with file type, row count, columns, DQ score, etc.
    """
    datasets = list_datasets()
    enhanced_datasets = []
    
    for dataset in datasets:
        dataset_name = dataset["name"]
        summary_path = Path(dataset.get("summary_path", ""))
        
        # Load summary for additional metadata
        summary_data = None
        if summary_path.exists():
            try:
                import json
                with summary_path.open("r", encoding="utf-8") as f:
                    summary_data = json.load(f).get("summary", {})
            except Exception as e:
                logger.warning(f"Could not load summary for {dataset_name}: {e}")
        
        # Determine file type from normalized path
        normalized_path = Path(dataset.get("normalized_path", ""))
        file_type = "unknown"
        if normalized_path.exists():
            suffix = normalized_path.suffix.lower()
            if suffix in [".csv", ".xlsx"]:
                file_type = "table"
            elif suffix in [".txt", ".md", ".docx", ".json"]:
                file_type = "text"
        
        # Get DQ report
        dq_score = None
        dq_report_path = None
        try:
            from swx_api.app.services.data_quality_service import get_dq_report
            dq_report = get_dq_report(dataset_name)
            if dq_report:
                dq_score = dq_report.get("dq_score")
                dq_report_path = dq_report.get("report_path")
        except Exception:
            pass
        
        # Get ingested_at from summary
        ingested_at = None
        if summary_data:
            ingested_at = summary_data.get("generated_at")
        
        # Get columns from summary
        columns = None
        if summary_data and "metrics" in summary_data:
            columns = list(summary_data["metrics"].keys())
        
        enhanced_dataset = {
            "dataset_name": dataset_name,
            "dataset_id": dataset_name,
            "file_type": file_type,
            "row_count": summary_data.get("row_count") if summary_data else None,
            "columns": columns,
            "dq_score": dq_score,
            "ingested_at": ingested_at,
            "summary_path": dataset.get("summary_path"),
            "dq_report_path": dq_report_path,
            "normalized_path": dataset.get("normalized_path"),
            "raw_files": dataset.get("raw_files", []),
        }
        
        enhanced_datasets.append(enhanced_dataset)
    
    return enhanced_datasets


@router.get("/summaries/{dataset_name}", response_model=SummaryResponse)
async def get_summary(dataset_name: str, format: str = "json"):
    payload = load_summary(dataset_name)
    if not payload:
        raise HTTPException(status_code=404, detail="Summary not found")

    if format == "tone" and payload.get("tone"):
        return JSONResponse(content={"tone": payload["tone"]})

    return SummaryResponse.model_validate(payload)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    metrics = gather_metrics()
    return MetricsResponse.model_validate(metrics)


@router.get("/dq_report/{dataset_id}")
async def get_dq_report(dataset_id: str):
    """
    Get Data Quality report for a dataset.
    
    Args:
        dataset_id: Dataset identifier (UUID or name)
        
    Returns:
        DQ Report with scores and issues
    """
    from swx_api.app.services.data_quality_service import get_dq_report
    
    report = get_dq_report(dataset_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"DQ report not found for dataset: {dataset_id}")
    
    return report


@router.post("/upload_audio")
async def upload_audio(
    db: SessionDep,
    file: UploadFile = File(...),
    metadata: str = Form(...),
):
    """
    Upload audio or transcript file with metadata.
    
    Accepts multipart/form-data with:
    - file: Audio (.wav, .mp3, .m4a) or transcript (.txt, .json) file
    - metadata: JSON string with required metadata fields
    
    Returns:
        Unified ingestion response with success, dataset_id, cultural_analysis, etc.
    """
    try:
        # Parse metadata JSON
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metadata JSON: {str(e)}"
            )
        
        # Read file content
        file_content = await file.read()
        filename = file.filename or "uploaded_file"
        
        # Process ingestion pipeline
        try:
            result = process_audio_ingestion(file_content, filename, metadata_dict)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
        # Create transcript database record
        transcript_create = TranscriptCreate(
            file_type=result["file_type"],
            original_filename=result["original_filename"],
            file_paths=result["file_paths"],
            upload_metadata=result["metadata"],
            transcript_text=result.get("transcript_text"),
            clean_text=result.get("clean_text"),
            raw_file_path=result.get("raw_file_path"),
            transcript_path=result.get("transcript_path"),
        )
        
        # Try to create database records, but continue if it fails (table may not exist)
        transcript_record = None
        cultural_analysis_record = None
        
        try:
            # Create transcript record
            transcript_record = create_transcript_record(db, transcript_create)
            logger.info(f"Created transcript record in DB: {transcript_record.id}")
            
            # Create cultural analysis record if available
            if result.get("cultural_analysis_data"):
                cultural_data = result["cultural_analysis_data"]
                cultural_create = CulturalAnalysisCreate(
                    transcript_id=transcript_record.id,
                    mindset_shift_score=cultural_data.get("mindset_shift_score", 0),
                    collaboration_score=cultural_data.get("collaboration_score", 0),
                    teacher_confidence_score=cultural_data.get("teacher_confidence_score", 0),
                    municipality_cooperation_score=cultural_data.get("municipality_cooperation_score", 0),
                    sentiment_score=cultural_data.get("sentiment_score", 50),
                    themes=cultural_data.get("themes", []),
                    practical_change=cultural_data.get("practical_change"),
                    mindset_change=cultural_data.get("mindset_change"),
                    impact_summary=cultural_data.get("impact_summary"),
                    culture_change_detected=cultural_data.get("culture_change_detected", False),
                )
                cultural_analysis_record = create_cultural_analysis_record(db, cultural_create)
                logger.info(f"Created cultural analysis record: {cultural_analysis_record.id}")
                
        except Exception as db_error:
            # If DB table doesn't exist or connection fails, continue without DB storage
            logger.warning(f"Database insert failed (table may not exist or connection issue): {db_error}")
            logger.info("Continuing without DB storage - files saved successfully")
            # Create a mock record for response using result data
            import uuid
            from datetime import datetime, timezone
            transcript_record = type('MockRecord', (), {
                'id': uuid.UUID(result["id"]),
                'file_type': result["file_type"],
                'original_filename': result["original_filename"],
                'upload_metadata': result["metadata"],
                'created_at': datetime.now(timezone.utc)
            })()
        
        # Create unified response
        from swx_api.app.services.unified_response_service import create_unified_ingestion_response
        unified_response = create_unified_ingestion_response(
            result=result,
            file_type=result["file_type"],
            metadata=metadata_dict,
            cultural_analysis=result.get("cultural_analysis"),
        )
        
        return unified_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

