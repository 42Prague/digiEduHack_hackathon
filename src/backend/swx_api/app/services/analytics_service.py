from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from swx_api.app.services import ingestion_service, sample_data

logger = logging.getLogger("analytics")


METRIC_FIELDS = ["mean", "median", "std", "min", "max"]
REGION_CANDIDATE_COLUMNS = ["region", "district", "praha_district", "kraj"]


def _metrics_path(dataset_name: str) -> Path:
    return ingestion_service.paths.analytics_metrics_dir / f"{dataset_name}.json"


def _ensure_dirs() -> None:
    ingestion_service.paths.analytics_metrics_dir.mkdir(parents=True, exist_ok=True)


def _load_dataframe(dataset_path: Path) -> Optional[pd.DataFrame]:
    if dataset_path.suffix.lower() != ".csv":
        return None
    try:
        return pd.read_csv(dataset_path)
    except Exception:
        return None


def calculate_dataset_metrics(dataset_name: str, dataset_path: Path) -> Optional[Dict[str, Dict[str, float]]]:
    df = _load_dataframe(dataset_path)
    if df is None or df.empty:
        return None

    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.empty:
        return None

    metrics: Dict[str, Dict[str, float]] = {}
    for column in numeric_df.columns:
        series = numeric_df[column].dropna()
        if series.empty:
            continue
        metrics[column] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std(ddof=0)),
            "min": float(series.min()),
            "max": float(series.max()),
        }

    if not metrics:
        return None

    _ensure_dirs()
    payload = {
        "dataset": dataset_name,
        "metrics": metrics,
        "row_count": int(len(df)),
        "generated_at": datetime.utcnow().isoformat(),
    }

    metrics_path = _metrics_path(dataset_name)
    metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def refresh_all_metrics() -> List[Dict[str, Dict[str, float]]]:
    datasets = ingestion_service.list_datasets()
    snapshots: List[Dict[str, Dict[str, float]]] = []
    for dataset in datasets:
        dataset_path = Path(dataset["normalized_path"])
        payload = calculate_dataset_metrics(dataset["name"], dataset_path)
        if payload:
            snapshots.append(payload)
    return snapshots


def load_metrics(dataset_name: str) -> Optional[Dict[str, Dict[str, float]]]:
    metrics_file = _metrics_path(dataset_name)
    if not metrics_file.exists():
        dataset = next((d for d in ingestion_service.list_datasets() if d["name"] == dataset_name), None)
        if not dataset:
            return None
        payload = calculate_dataset_metrics(dataset_name, Path(dataset["normalized_path"]))
        if not payload:
            return None
        return payload

    try:
        return json.loads(metrics_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def get_combined_metrics() -> Dict[str, object]:
    refresh_all_metrics()

    combined: Dict[str, Dict[str, float]] = {}
    datasets = []
    for metrics_file in ingestion_service.paths.analytics_metrics_dir.glob("*.json"):
        try:
            payload = json.loads(metrics_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        dataset_name = payload.get("dataset")
        metrics = payload.get("metrics", {})
        if not dataset_name or not metrics:
            continue

        datasets.append(dataset_name)
        for column, stats in metrics.items():
            column_metrics = combined.setdefault(column, {field: [] for field in METRIC_FIELDS})
            for field in METRIC_FIELDS:
                value = stats.get(field)
                if value is not None:
                    column_metrics[field].append(float(value))

    summary: Dict[str, Dict[str, float]] = {}
    for column, values in combined.items():
        summary[column] = {
            field: float(pd.Series(series).mean()) if series else 0.0
            for field, series in values.items()
        }

    if datasets and summary:
        return {
            "datasets": datasets,
            "metrics": summary,
            "generated_at": datetime.utcnow().isoformat(),
        }

    return sample_data.get_sample_metrics()


def get_metric_trend(metric_name: str, db_session=None) -> Dict[str, object]:
    """
    Get metric trends from datasets and transcripts.
    
    For sentiment_score and other cultural metrics, check transcripts with cultural analysis.
    For other metrics, check datasets.
    """
    region_values: Dict[str, List[float]] = defaultdict(list)
    time_series_data: List[Dict[str, Any]] = []  # For time-based trends

    # Check if this is a cultural analysis metric (from transcripts)
    cultural_metrics = {
        "sentiment_score", "sentiment", "mindset_shift_score", "collaboration_score",
        "teacher_confidence_score", "municipality_cooperation_score"
    }
    
    if metric_name.lower() in cultural_metrics and db_session:
        try:
            from swx_api.app.models.transcript import Transcript
            from swx_api.app.models.cultural_analysis import CulturalAnalysis
            from sqlmodel import select
            
            # Get all transcripts directly from database
            stmt = select(Transcript)
            transcripts = db_session.exec(stmt).all()
            
            for transcript in transcripts:
                if not transcript.id:
                    continue
                
                # Get cultural analysis for this transcript
                cultural_stmt = select(CulturalAnalysis).where(CulturalAnalysis.transcript_id == transcript.id)
                cultural = db_session.exec(cultural_stmt).first()
                
                if not cultural:
                    continue
                
                # Map metric name to cultural analysis field
                metric_map = {
                    "sentiment_score": cultural.sentiment_score,
                    "sentiment": cultural.sentiment_score,
                    "mindset_shift_score": cultural.mindset_shift_score,
                    "collaboration_score": cultural.collaboration_score,
                    "teacher_confidence_score": cultural.teacher_confidence_score,
                    "municipality_cooperation_score": cultural.municipality_cooperation_score,
                }
                
                score = metric_map.get(metric_name.lower())
                if score is None:
                    continue
                
                # Extract region from upload_metadata (JSONB field)
                region = None
                if transcript.upload_metadata:
                    if isinstance(transcript.upload_metadata, dict):
                        region = transcript.upload_metadata.get("region_id")
                
                if region:
                    region_values[str(region)].append(float(score))
                
                # For time series (sentiment over time)
                if metric_name.lower() in ("sentiment_score", "sentiment"):
                    # Get date from metadata or created_at
                    date_value = None
                    if transcript.upload_metadata and isinstance(transcript.upload_metadata, dict):
                        date_value = transcript.upload_metadata.get("interview_date")
                    if not date_value and transcript.created_at:
                        date_value = transcript.created_at.isoformat() if hasattr(transcript.created_at, 'isoformat') else str(transcript.created_at)
                    
                    if date_value:
                        time_series_data.append({
                            "date": str(date_value),
                            "value": float(score),
                            "region": str(region) if region else "unknown",
                        })
        except Exception as e:
            logger.warning(f"Error fetching transcript trends: {e}", exc_info=True)

    # Also check datasets (for non-cultural metrics)
    for dataset in ingestion_service.list_datasets():
        dataset_path = Path(dataset["normalized_path"])
        df = _load_dataframe(dataset_path)
        if df is None or metric_name not in df.columns:
            continue

        region_column = next((col for col in REGION_CANDIDATE_COLUMNS if col in df.columns), None)
        if not region_column:
            continue

        metric_series = pd.to_numeric(df[metric_name], errors="coerce").dropna()
        if metric_series.empty:
            continue

        grouped = df[[region_column, metric_name]].dropna()
        grouped[metric_name] = pd.to_numeric(grouped[metric_name], errors="coerce")
        grouped = grouped.dropna(subset=[metric_name])

        if grouped.empty:
            continue

        region_stats = grouped.groupby(region_column)[metric_name].agg(["mean", "count"])
        for region, row in region_stats.iterrows():
            region_values[str(region)].extend([float(row["mean"])] * int(row["count"]))

    results = []
    for region, values in region_values.items():
        if not values:
            continue
        series = pd.Series(values)
        results.append(
            {
                "region": region,
                "mean": float(series.mean()),
                "median": float(series.median()),
                "count": int(series.count()),
            }
        )

    response = {
        "metric": metric_name,
        "results": sorted(results, key=lambda item: item["mean"], reverse=True) if results else [],
        "generated_at": datetime.utcnow().isoformat(),
    }
    
    # Add time series data for sentiment trends
    if time_series_data and metric_name.lower() in ("sentiment_score", "sentiment"):
        # Group by month (defaultdict already imported at top)
        monthly_data = defaultdict(list)
        for item in time_series_data:
            date_str = item["date"]
            if isinstance(date_str, str):
                # Extract YYYY-MM from date
                if "T" in date_str:
                    month_key = date_str[:7]  # YYYY-MM
                else:
                    month_key = date_str[:7] if len(date_str) >= 7 else date_str[:4]
                monthly_data[month_key].append(item["value"])
        
        # Calculate monthly averages
        time_series = [
            {
                "date": month,
                "value": sum(values) / len(values),
            }
            for month, values in sorted(monthly_data.items())
        ]
        response["time_series"] = time_series

    if results or time_series_data:
        return response

    return sample_data.get_sample_trend(metric_name)


def calculate_cost_benefit(intervention_name: str, metric_name: str, intervention_cost: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate cost-benefit analysis for an intervention.
    
    Compares intervention costs vs outcome improvements to determine ROI.
    
    Args:
        intervention_name: Name of the intervention (e.g., "teacher_training", "mentoring")
        metric_name: Outcome metric to measure (e.g., "student_satisfaction", "test_scores")
        intervention_cost: Optional cost per intervention unit (if None, uses sample data)
        
    Returns:
        Dict with ROI, cost per improvement unit, and effectiveness metrics
    """
    from swx_api.app.services import ingestion_service, sample_data
    
    # Try to find intervention data in datasets
    intervention_data: List[Dict[str, Any]] = []
    outcome_data: List[Dict[str, Any]] = []
    
    for dataset in ingestion_service.list_datasets():
        dataset_path = Path(dataset["normalized_path"])
        df = _load_dataframe(dataset_path)
        if df is None:
            continue
        
        # Look for intervention-related columns
        intervention_cols = [col for col in df.columns if intervention_name.lower() in col.lower() or "intervention" in col.lower()]
        metric_cols = [col for col in df.columns if metric_name.lower() in col.lower() or "score" in col.lower() or "satisfaction" in col.lower()]
        
        if intervention_cols and metric_cols:
            intervention_col = intervention_cols[0]
            metric_col = metric_cols[0]
            
            # Get before/after or treatment/control groups
            if "before" in df.columns or "after" in df.columns:
                # Time-series data
                before_col = next((c for c in df.columns if "before" in c.lower()), None)
                after_col = next((c for c in df.columns if "after" in c.lower()), None)
                if before_col and after_col:
                    improvement = pd.to_numeric(df[after_col], errors="coerce") - pd.to_numeric(df[before_col], errors="coerce")
                    outcome_data.extend(improvement.dropna().tolist())
            else:
                # Cross-sectional: compare intervention vs control
                intervention_group = df[df[intervention_col].notna()]
                if not intervention_group.empty:
                    outcomes = pd.to_numeric(intervention_group[metric_col], errors="coerce").dropna()
                    outcome_data.extend(outcomes.tolist())
    
    # Calculate metrics
    if not outcome_data:
        # Use sample data
        return sample_data.get_sample_cost_benefit(intervention_name, metric_name, intervention_cost)
    
    avg_improvement = float(pd.Series(outcome_data).mean())
    median_improvement = float(pd.Series(outcome_data).median())
    participant_count = len(outcome_data)
    
    # Estimate cost if not provided (sample data)
    if intervention_cost is None:
        # Default costs per participant (in CZK)
        default_costs = {
            "teacher_training": 5000.0,
            "mentoring": 3000.0,
            "workshop": 2000.0,
            "coaching": 4000.0,
        }
        intervention_cost = default_costs.get(intervention_name.lower(), 3000.0)
    
    total_cost = intervention_cost * participant_count
    cost_per_improvement = total_cost / avg_improvement if avg_improvement > 0 else float('inf')
    
    # Calculate ROI (assuming value of 1 point improvement = 100 CZK)
    value_per_point = 100.0
    total_value = avg_improvement * participant_count * value_per_point
    roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "intervention": intervention_name,
        "metric": metric_name,
        "participants": participant_count,
        "average_improvement": round(avg_improvement, 2),
        "median_improvement": round(median_improvement, 2),
        "cost_per_participant": round(intervention_cost, 2),
        "total_cost": round(total_cost, 2),
        "cost_per_improvement_unit": round(cost_per_improvement, 2),
        "roi_percentage": round(roi, 2),
        "total_value_generated": round(total_value, 2),
        "generated_at": datetime.utcnow().isoformat(),
    }

