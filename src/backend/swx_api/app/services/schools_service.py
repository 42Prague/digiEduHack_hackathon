from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from swx_api.app.services import ingestion_service, sample_data

logger = logging.getLogger("schools_service")


NAME_CANDIDATE_COLUMNS = ["name", "school_name", "institution", "title"]
REGION_COLUMNS = ["region", "district", "praha_district", "kraj"]


def _load_school_frames() -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    for dataset in ingestion_service.list_datasets():
        path = Path(dataset["normalized_path"])
        if path.suffix.lower() != ".csv":
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue

        name_column = _detect_name_column(df)
        if not name_column:
            continue

        df = df.copy()
        df["_dataset"] = dataset["name"]
        df["_name_column"] = name_column
        frames.append(df)
    return frames


def _detect_name_column(df: pd.DataFrame) -> Optional[str]:
    for column in df.columns:
        if column.lower() in NAME_CANDIDATE_COLUMNS:
            return column
    return None


def search_schools(query: str, limit: int = 20) -> List[Dict[str, object]]:
    query_lower = query.lower()
    results: List[Dict[str, object]] = []

    for frame in _load_school_frames():
        name_column = frame["_name_column"].iloc[0]
        region_column = next((col for col in REGION_COLUMNS if col in frame.columns), None)

        mask = frame[name_column].astype(str).str.lower().str.contains(query_lower)
        if region_column:
            mask |= frame[region_column].astype(str).str.lower().str.contains(query_lower)

        matches = frame[mask].head(limit - len(results))
        for _, row in matches.iterrows():
            results.append(
                {
                    "dataset": row["_dataset"],
                    "name": row[name_column],
                    "region": row.get(region_column),
                    "attributes": _extract_row_attributes(row, exclude=[name_column, region_column]),
                }
            )
            if len(results) >= limit:
                return results

    if results:
        return results

    # Fallback to sample data for demo readiness
    return sample_data.search_sample_schools(query)[:limit]


def compare_schools(names: Sequence[str], metric: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """
    Compare schools by their attributes and cultural analysis scores.
    
    Args:
        names: List of school names to compare
        metric: Optional metric to focus on. Options:
            - "collaboration_score"
            - "mindset_shift_score"
            - "sentiment"
            - "teacher_confidence"
            - "intervention_effectiveness" (derived from multiple scores)
    
    Returns:
        Dictionary mapping school names to their attributes and scores
    """
    name_set = {name.strip().lower() for name in names if name.strip()}
    comparisons: Dict[str, Dict[str, float]] = {}

    # Load cultural analysis data from summaries
    cultural_data = _load_cultural_analysis_data()

    for frame in _load_school_frames():
        name_column = frame["_name_column"].iloc[0]
        numeric_columns = frame.select_dtypes(include=["number"]).columns
        if numeric_columns.empty:
            continue

        for _, row in frame.iterrows():
            normalized_name = str(row[name_column]).strip().lower()
            if normalized_name not in name_set:
                continue
            
            school_name = str(row[name_column])
            school_data: Dict[str, float] = {
                column: float(row[column]) for column in numeric_columns
            }
            
            # Add cultural analysis scores if available
            if school_name in cultural_data:
                cultural = cultural_data[school_name]
                school_data["collaboration_score"] = float(cultural.get("collaboration_score", 0))
                school_data["mindset_shift_score"] = float(cultural.get("mindset_shift_score", 0))
                school_data["teacher_confidence_score"] = float(cultural.get("teacher_confidence_score", 0))
                school_data["cooperation_municipality_score"] = float(cultural.get("cooperation_municipality_score", 0))
                school_data["sentiment"] = float(cultural.get("sentiment", 50))
                
                # Calculate intervention_effectiveness as weighted average
                effectiveness = (
                    cultural.get("collaboration_score", 0) * 0.25 +
                    cultural.get("mindset_shift_score", 0) * 0.25 +
                    cultural.get("teacher_confidence_score", 0) * 0.25 +
                    cultural.get("cooperation_municipality_score", 0) * 0.25
                )
                school_data["intervention_effectiveness"] = float(effectiveness)
            
            comparisons[school_name] = school_data

    if comparisons:
        # Filter by metric if specified
        if metric:
            filtered_comparisons: Dict[str, Dict[str, float]] = {}
            metric_key = _normalize_metric_name(metric)
            for school_name, data in comparisons.items():
                if metric_key in data:
                    filtered_comparisons[school_name] = {metric_key: data[metric_key]}
            if filtered_comparisons:
                return filtered_comparisons
        return comparisons

    return sample_data.compare_sample_schools(list(names))


def _load_cultural_analysis_data() -> Dict[str, Dict[str, Any]]:
    """
    Load cultural analysis data from all dataset summaries.
    Maps school/dataset names to their cultural analysis scores.
    """
    from pathlib import Path
    import json
    from swx_api.app.services import ingestion_service
    
    cultural_data: Dict[str, Dict[str, Any]] = {}
    
    for dataset in ingestion_service.list_datasets():
        summary_path = Path(dataset.get("summary_path", ""))
        if not summary_path.exists():
            continue
        
        try:
            with summary_path.open("r", encoding="utf-8") as fp:
                summary_data = json.load(fp)
                summary = summary_data.get("summary", {})
                
                # Check if this dataset has cultural analysis
                if "cultural_analysis" in summary:
                    dataset_name = summary.get("name", dataset["name"])
                    cultural_data[dataset_name] = summary["cultural_analysis"]
                # Also check for direct fields (backward compatibility)
                elif "mindset_shift_score" in summary:
                    dataset_name = summary.get("name", dataset["name"])
                    cultural_data[dataset_name] = {
                        "mindset_shift_score": summary.get("mindset_shift_score", 0),
                        "collaboration_score": summary.get("collaboration_score", 0),
                        "teacher_confidence_score": summary.get("teacher_confidence_score", 0),
                        "cooperation_municipality_score": summary.get("cooperation_municipality_score", 0),
                        "sentiment": summary.get("sentiment", 50),
                    }
        except Exception:
            continue
    
    return cultural_data


def _normalize_metric_name(metric: str) -> str:
    """Normalize metric name to match stored field names."""
    metric_lower = metric.lower().replace("_", "").replace("-", "")
    mappings = {
        "collaborationscore": "collaboration_score",
        "mindsetshift": "mindset_shift_score",
        "mindsetshiftscore": "mindset_shift_score",
        "sentiment": "sentiment",
        "teacherconfidence": "teacher_confidence_score",
        "teacherconfidencescore": "teacher_confidence_score",
        "interventioneffectiveness": "intervention_effectiveness",
    }
    return mappings.get(metric_lower, metric)


def compare_by_dimension(
    db,
    dimension: str,
    school_type: Optional[str] = None,
    intervention_type: Optional[str] = None,
    participant_role: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare data by dimension (school_type, intervention_type, participant_role).
    
    Args:
        db: Database session
        dimension: Dimension to compare by ('school_type', 'intervention_type', 'participant_role')
        school_type: Optional filter by school type
        intervention_type: Optional filter by intervention type
        participant_role: Optional filter by participant role
        date_from: Optional start date filter (YYYY-MM-DD)
        date_to: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        Comparison dictionary grouped by dimension
    """
    from sqlmodel import select
    from swx_api.app.models.transcript import Transcript
    from swx_api.app.models.cultural_analysis import CulturalAnalysis
    from datetime import datetime
    
    try:
        # Build query
        from sqlalchemy import text
        query = select(Transcript)
        
        # Apply filters (using PostgreSQL JSONB syntax)
        if school_type:
            query = query.where(text("upload_metadata->>'school_type' = :school_type").bindparams(school_type=school_type))
        if intervention_type:
            query = query.where(text("upload_metadata->>'intervention_type' = :intervention_type").bindparams(intervention_type=intervention_type))
        if participant_role:
            query = query.where(text("upload_metadata->>'participant_role' = :participant_role").bindparams(participant_role=participant_role))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.where(Transcript.created_at >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.where(Transcript.created_at <= date_to_obj)
            except ValueError:
                pass
        
        transcripts = db.exec(query).all()
    except Exception as e:
        logger.error(f"Database error in compare_by_dimension: {e}")
        return {"dimension": dimension, "groups": {}}
    
    if not transcripts:
        return {"dimension": dimension, "groups": {}}
    
    # Group by dimension
    groups = {}
    
    for transcript in transcripts:
        dimension_value = transcript.upload_metadata.get(dimension)
        if not dimension_value:
            continue
        
        if dimension_value not in groups:
            groups[dimension_value] = {
                "count": 0,
                "scores": {
                    "mindset_shift": [],
                    "collaboration": [],
                    "teacher_confidence": [],
                    "municipality_cooperation": [],
                    "sentiment": [],
                }
            }
        
        # Get cultural analysis
        from swx_api.app.services.transcript_db_service import get_cultural_analysis_by_transcript_id
        analysis = get_cultural_analysis_by_transcript_id(db, transcript.id)
        
        if analysis:
            groups[dimension_value]["count"] += 1
            groups[dimension_value]["scores"]["mindset_shift"].append(analysis.mindset_shift_score)
            groups[dimension_value]["scores"]["collaboration"].append(analysis.collaboration_score)
            groups[dimension_value]["scores"]["teacher_confidence"].append(analysis.teacher_confidence_score)
            groups[dimension_value]["scores"]["municipality_cooperation"].append(analysis.municipality_cooperation_score)
            groups[dimension_value]["scores"]["sentiment"].append(analysis.sentiment_score)
    
    # Calculate averages for each group
    result_groups = {}
    for dimension_value, data in groups.items():
        count = data["count"]
        if count > 0:
            result_groups[dimension_value] = {
                "count": count,
                "avg_mindset_shift": sum(data["scores"]["mindset_shift"]) / count,
                "avg_collaboration": sum(data["scores"]["collaboration"]) / count,
                "avg_teacher_confidence": sum(data["scores"]["teacher_confidence"]) / count,
                "avg_municipality_cooperation": sum(data["scores"]["municipality_cooperation"]) / count,
                "avg_sentiment": sum(data["scores"]["sentiment"]) / count,
            }
    
    return {
        "dimension": dimension,
        "groups": result_groups,
    }


def _extract_row_attributes(row: pd.Series, exclude: List[Optional[str]]) -> Dict[str, object]:
    excluded = {col for col in exclude if col}
    excluded.update({"_dataset", "_name_column"})
    return {
        column: row[column]
        for column in row.index
        if column not in excluded and not pd.isna(row[column])
    }

