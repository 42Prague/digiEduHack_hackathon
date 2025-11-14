from __future__ import annotations

from fastapi import APIRouter, Query

from swx_api.app.services import response_utils, sample_data
from swx_api.core.config.settings import settings
from swx_api.app.config.settings import app_settings

router = APIRouter(prefix="/config")


@router.get("/")
async def get_config(format: str = Query("json")):
    payload = {
        "project": settings.PROJECT_NAME if hasattr(settings, "PROJECT_NAME") else "EduFabric",
        "version": app_settings.PROJECT_VERSION,
        "tone_supported": True,
        "sample_datasets": [dataset["name"] for dataset in sample_data.SAMPLE_DATASETS],
        "frontend_url": settings.FRONTEND_HOST,
        "backend_url": settings.BACKEND_HOST,
    }
    return response_utils.tone_or_json(payload, format)


@router.get("/ui_contract")
async def get_ui_contract():
    """
    Return API → UI Contract with all endpoints, parameters, and response schemas.
    This allows the frontend to auto-sync with backend shapes.
    """
    return {
        "endpoints": [
            {
                "path": "/api/ingestion/ingest",
                "method": "POST",
                "params": {
                    "file": "multipart/form-data file upload"
                },
                "response_schema": {
                    "success": "boolean",
                    "dataset_id": "string",
                    "filename": "string",
                    "file_type": "string",
                    "stored_path": "string",
                    "normalized_path": "string",
                    "classification": "string (quantitative | qualitative | transcript | audio)",
                    "row_count": "integer | null",
                    "columns": "array | null",
                    "numeric_ratio": "float | null",
                    "summary": "object",
                    "summary_path": "string",
                    "dq_report_path": "string | null",
                    "auto_summary": "string | null",
                    "metadata": "object | null (only for audio uploads)",
                    "cultural_analysis": "object | null (only for transcripts)",
                },
                "example_response": {
                    "success": True,
                    "dataset_id": "test_dataset_20251113",
                    "filename": "test.csv",
                    "file_type": "file",
                    "classification": "quantitative",
                    "row_count": 100,
                    "columns": [{"name": "score", "dtype": "int64", "null_ratio": 0.0, "is_numeric": True}],
                    "dq_report_path": "/data/processed/clean/test_dataset_20251113_dq_report.json",
                }
            },
            {
                "path": "/api/ingestion/upload_audio",
                "method": "POST",
                "params": {
                    "file": "multipart/form-data file upload",
                    "metadata": "JSON string with school_id, region_id, school_type, intervention_type, participant_role, interview_date"
                },
                "response_schema": {
                    "success": "boolean",
                    "dataset_id": "string (UUID)",
                    "filename": "string",
                    "file_type": "string (audio | transcript)",
                    "classification": "string (transcript | audio)",
                    "metadata": "object",
                    "cultural_analysis": "object",
                    "dq_report_path": "string | null",
                    "auto_summary": "string | null",
                },
                "example_response": {
                    "success": True,
                    "dataset_id": "9a53e328-3ef3-4337-b8f1-ae2e612c6061",
                    "file_type": "transcript",
                    "classification": "transcript",
                    "metadata": {"school_id": "school_001", "region_id": "praha"},
                    "cultural_analysis": {"mindset_shift_score": 75, "collaboration_score": 80},
                }
            },
            {
                "path": "/api/ingestion/datasets",
                "method": "GET",
                "params": {},
                "response_schema": {
                    "type": "array",
                    "items": {
                        "dataset_name": "string",
                        "dataset_id": "string",
                        "file_type": "string (table | text)",
                        "row_count": "integer | null",
                        "columns": "array | null",
                        "dq_score": "integer | null",
                        "ingested_at": "string (ISO datetime)",
                        "summary_path": "string",
                        "dq_report_path": "string | null",
                    }
                }
            },
            {
                "path": "/api/transcripts/{id}",
                "method": "GET",
                "params": {
                    "id": "UUID string"
                },
                "response_schema": {
                    "id": "string (UUID)",
                    "metadata": "object",
                    "transcript_text": "string",
                    "clean_text": "string",
                    "cultural_analysis": "object | null",
                    "dq_report": "object | null",
                    "file_paths": "object",
                    "created_at": "string (ISO datetime)",
                    "updated_at": "string (ISO datetime)",
                }
            },
            {
                "path": "/api/transcripts/",
                "method": "GET",
                "params": {
                    "school_id": "string (optional)",
                    "region_id": "string (optional)",
                    "school_type": "string (optional)",
                    "intervention_type": "string (optional)",
                    "participant_role": "string (optional)",
                    "date_from": "string (YYYY-MM-DD, optional)",
                    "date_to": "string (YYYY-MM-DD, optional)",
                },
                "response_schema": {
                    "type": "array",
                    "items": {
                        "id": "string (UUID)",
                        "school_id": "string",
                        "region_id": "string",
                        "school_type": "string",
                        "intervention_type": "string",
                        "participant_role": "string",
                        "interview_date": "string",
                        "created_at": "string (ISO datetime)",
                    }
                }
            },
            {
                "path": "/api/analytics/recommendations",
                "method": "GET",
                "params": {
                    "school_id": "string (optional)",
                    "region_id": "string (optional)",
                },
                "response_schema": {
                    "school_recommendations": "array",
                    "region_recommendations": "array",
                    "intervention_recommendations": "array",
                    "culture_warnings": "array",
                    "strengths": "array",
                }
            },
            {
                "path": "/api/analytics/region_insights",
                "method": "GET",
                "params": {
                    "region_id": "string (required)",
                },
                "response_schema": {
                    "region_id": "string",
                    "summary": "object",
                    "top_schools": "array",
                    "schools_needing_support": "array",
                    "intervention_effectiveness": "object",
                    "frequent_themes": "array",
                }
            },
            {
                "path": "/api/schools/compare",
                "method": "GET",
                "params": {
                    "names": "string (comma-separated)",
                    "metric": "string (optional)",
                },
                "response_schema": {
                    "comparisons": "object (school_name -> metrics)"
                }
            },
        ]
    }

