from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from docx import Document  # type: ignore[import-untyped]

from swx_api.core.utils.tone_utils import to_tone_format

from swx_api.app.services.llm_client import LLMClient, LLMConfig


SUPPORTED_TABLE_EXTENSIONS = {".csv", ".xlsx"}
SUPPORTED_TEXT_EXTENSIONS = {".md", ".docx", ".txt", ".json"}
SUPPORTED_EXTENSIONS = SUPPORTED_TABLE_EXTENSIONS | SUPPORTED_TEXT_EXTENSIONS


class IngestionPaths:
    def __init__(self) -> None:
        # Path(...).resolve(): .../backend/swx_api/app/services
        services_dir = Path(__file__).resolve().parent
        backend_dir = services_dir.parents[2]  # .../backend/swx_api/app -> parents[2] == backend
        repo_root = backend_dir.parent

        self.data_dir = (repo_root / "data").resolve()
        self.raw_dir = self.data_dir / "raw"
        self.normalized_dir = self.data_dir / "normalized"
        self.summary_dir = self.data_dir / "summaries"
        self.logs_dir = self.data_dir / "logs"
        self.analytics_dir = self.data_dir / "analytics"
        self.analytics_metrics_dir = self.analytics_dir / "metrics"
        self.analytics_themes_dir = self.analytics_dir / "themes"

        for path in (
            self.data_dir,
            self.raw_dir,
            self.normalized_dir,
            self.summary_dir,
            self.logs_dir,
            self.analytics_dir,
            self.analytics_metrics_dir,
            self.analytics_themes_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

        self.log_file = self.logs_dir / "ingest.log"


paths = IngestionPaths()

logger = logging.getLogger("ingestion")
logger.setLevel(logging.INFO)
if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == str(paths.log_file)
           for handler in logger.handlers):
    file_handler = logging.FileHandler(paths.log_file, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{3,4}\b")
NAME_REGEX = re.compile(r"\b(?:[A-ZÁČĎÉĚÍĹĽŇÓŘŠŤÚŮÝŽ][a-záčďéěíĺľňóřšťúůýž]+(?:\s+|$)){2,3}")


def timestamped_filename(original_name: str) -> str:
    suffix = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    original_path = Path(original_name)
    base = re.sub(r"\s+", "_", original_path.stem)
    return f"{base}_{suffix}{original_path.suffix.lower()}"


def mask_pii_text(text: str) -> str:
    masked = EMAIL_REGEX.sub("[REDACTED]", text)
    masked = PHONE_REGEX.sub("[REDACTED]", masked)
    masked = NAME_REGEX.sub("[REDACTED]", masked)
    return masked


def mask_pii_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    masked_df = df.copy()
    for column in masked_df.columns:
        if masked_df[column].dtype == object:
            masked_df[column] = masked_df[column].astype(str).apply(mask_pii_text)
    return masked_df


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    raise ValueError(f"Unsupported table extension: {path.suffix}")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".docx":
        document = Document(path)
        paragraphs = [para.text for para in document.paragraphs]
        return "\n".join(paragraphs)
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        # For JSON files, read as text (don't parse, treat as text content)
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported text extension: {path.suffix}")


def profile_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], float]:
    profiles: List[Dict[str, Any]] = []
    numeric_columns = 0
    total_columns = len(df.columns)

    for column in df.columns:
        series = df[column]
        dtype = str(series.dtype)
        null_ratio = float(series.isnull().sum() / max(len(series), 1))
        is_numeric = pd.api.types.is_numeric_dtype(series)
        if is_numeric:
            numeric_columns += 1
        profiles.append(
            {
                "name": str(column),
                "dtype": dtype,
                "null_ratio": round(null_ratio, 4),
                "is_numeric": is_numeric,
            }
        )

    numeric_ratio = numeric_columns / total_columns if total_columns else 0.0
    return profiles, numeric_ratio


def compute_numeric_metrics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            series = df[column].dropna()
            if series.empty:
                continue
            metrics[str(column)] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "std": float(series.std(ddof=0)),
            }
    return metrics


def extract_text_chunks(df: pd.DataFrame, max_chars: int = 8000) -> str:
    text_fragments: List[str] = []
    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            joined = " ".join(df[column].dropna().astype(str).tolist())
            if joined:
                text_fragments.append(joined)
    combined = "\n".join(text_fragments)
    return combined[:max_chars]


def infer_dataset_name(uploaded_path: Path) -> str:
    return uploaded_path.stem


REGION_CANDIDATE_COLUMNS = ["region", "district", "praha_district", "kraj", "okres", "municipality"]


def detect_regions(df: pd.DataFrame) -> List[str]:
    """Detect unique regions in a dataset."""
    regions: List[str] = []
    for col in REGION_CANDIDATE_COLUMNS:
        if col in df.columns:
            unique_regions = df[col].dropna().unique().tolist()
            regions.extend([str(r) for r in unique_regions if r])
    return sorted(list(set(regions)))


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def generate_tone(summary: Dict[str, Any]) -> Optional[str]:
    return to_tone_format(summary)


def ingest_file(file_path: Path, original_filename: str) -> Dict[str, Any]:
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    logger.info("Ingesting file=%s saved_at=%s", original_filename, file_path)

    # Initialize normalized response structure - ALL file types return the same fields
    response: Dict[str, Any] = {
        "filename": original_filename,
        "stored_path": str(file_path),
        "normalized_path": "",
        "classification": "",
        "row_count": None,  # Will be set for tables, None for text
        "numeric_ratio": None,  # Will be set for tables, None for text
        "columns": None,  # Will be set for tables, None for text
        "summary": {},
        "summary_path": "",
        "dq_report_path": None,  # Will be set after DQ generation
    }

    if file_path.suffix.lower() in SUPPORTED_TABLE_EXTENSIONS:
        df = read_table(file_path)
        row_count = int(len(df))

        column_profiles, numeric_ratio = profile_dataframe(df)
        response["row_count"] = row_count
        response["columns"] = column_profiles
        response["numeric_ratio"] = numeric_ratio

        masked_df = mask_pii_dataframe(df)

        classification = "quantitative" if numeric_ratio > 0.5 else "qualitative"
        response["classification"] = classification

        dataset_name = infer_dataset_name(file_path)
        normalized_path = paths.normalized_dir / f"{dataset_name}.csv"
        masked_df.to_csv(normalized_path, index=False)
        response["normalized_path"] = str(normalized_path)

        # Detect regions for multi-level filtering
        regions = detect_regions(masked_df)
        
        summary: Dict[str, Any] = {
            "name": dataset_name,
            "classification": classification,
            "row_count": row_count,
            "regions": regions if regions else None,
        }

        if classification == "quantitative":
            metrics = compute_numeric_metrics(masked_df)
            summary["metrics"] = metrics
        else:
            qualitative_text = extract_text_chunks(masked_df)
            summary["themes"] = get_qualitative_themes(qualitative_text)

        summary["generated_at"] = datetime.utcnow().isoformat()
        response["summary"] = summary

        summary_payload = {
            "summary": summary,
            "tone": generate_tone(summary),
        }

        summary_path = paths.summary_dir / f"{dataset_name}.json"
        save_json(summary_path, summary_payload)
        response["summary_path"] = str(summary_path)
        
        # Generate DQ report for quantitative/qualitative table data
        try:
            from swx_api.app.services.data_quality_service import generate_dq_report
            dq_report = generate_dq_report(
                dataset_id=dataset_name,
                data=masked_df.to_dict(orient="records") if classification == "quantitative" else extract_text_chunks(masked_df),
                metadata={"classification": classification, "row_count": row_count}
            )
            # Use report_path from the DQ service response
            response["dq_report_path"] = dq_report.get("report_path") or str(paths.data_dir / "processed" / "clean" / f"{dataset_name}_dq_report.json")
            logger.info(f"DQ report generated for {dataset_name}: score={dq_report.get('dq_score', 0)}")
        except Exception as e:
            logger.warning(f"DQ report generation failed for {dataset_name}: {e}")
            response["dq_report_path"] = None
    else:
        raw_text = read_text(file_path)
        masked_text = mask_pii_text(raw_text)
        dataset_name = infer_dataset_name(file_path)
        normalized_path = paths.normalized_dir / f"{dataset_name}.txt"
        normalized_path.write_text(masked_text, encoding="utf-8")

        response["classification"] = "qualitative"
        response["normalized_path"] = str(normalized_path)

        themes = get_qualitative_themes(masked_text)
        
        # AI Cultural Analysis Step (for transcripts/interviews)
        # Check if this looks like a transcript (contains interview-like content)
        is_transcript = _is_likely_transcript(masked_text)
        cultural_analysis = None
        if is_transcript:
            try:
                from swx_api.app.services import cultural_analysis_service
                cultural_analysis = cultural_analysis_service.analyze_cultural_transcript(masked_text)
                logger.info("Cultural analysis completed for transcript: %s", dataset_name)
            except Exception as e:
                logger.warning("Cultural analysis failed for %s: %s", dataset_name, e)
                cultural_analysis = None
        
        summary = {
            "name": dataset_name,
            "classification": "qualitative",
            "themes": themes,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        # Add cultural analysis fields if available
        if cultural_analysis:
            summary["cultural_analysis"] = cultural_analysis
            summary["mindset_shift_score"] = cultural_analysis.get("mindset_shift_score", 0)
            summary["collaboration_score"] = cultural_analysis.get("collaboration_score", 0)
            summary["teacher_confidence_score"] = cultural_analysis.get("teacher_confidence_score", 0)
            summary["cooperation_municipality_score"] = cultural_analysis.get("cooperation_municipality_score", 0)
            summary["sentiment"] = cultural_analysis.get("sentiment", 50)
            summary["practical_change"] = cultural_analysis.get("practical_change", "")
            summary["mindset_change"] = cultural_analysis.get("mindset_change", "")
            summary["impact_summary"] = cultural_analysis.get("impact_summary", "")

        summary_payload = {
            "summary": summary,
            "tone": generate_tone(summary),
        }
        summary_path = paths.summary_dir / f"{dataset_name}.json"
        save_json(summary_path, summary_payload)
        response["summary"] = summary
        response["summary_path"] = str(summary_path)
        
        # Generate DQ report for text files
        try:
            from swx_api.app.services.data_quality_service import generate_dq_report
            dq_report = generate_dq_report(
                dataset_id=dataset_name,
                data=masked_text,
                metadata={"classification": "qualitative", "file_type": file_path.suffix.lower()}
            )
            # Use report_path from the DQ service response
            response["dq_report_path"] = dq_report.get("report_path") or str(paths.data_dir / "processed" / "clean" / f"{dataset_name}_dq_report.json")
            logger.info(f"DQ report generated for {dataset_name}: score={dq_report.get('dq_score', 0)}")
        except Exception as e:
            logger.warning(f"DQ report generation failed for {dataset_name}: {e}")
            response["dq_report_path"] = None

    # Ensure all required fields are present (normalize response)
    # Set defaults for fields that might be missing
    if "row_count" not in response:
        response["row_count"] = None
    if "numeric_ratio" not in response:
        response["numeric_ratio"] = None
    if "columns" not in response:
        response["columns"] = None
    
    return response


def list_datasets() -> List[Dict[str, Any]]:
    datasets: List[Dict[str, Any]] = []
    for normalized_file in sorted(paths.normalized_dir.glob("*")):
        dataset_name = normalized_file.stem
        summary_path = paths.summary_dir / f"{dataset_name}.json"
        datasets.append(
            {
                "name": dataset_name,
                "normalized_path": str(normalized_file),
                "summary_path": str(summary_path) if summary_path.exists() else None,
                "raw_files": [
                    str(f)
                    for f in paths.raw_dir.glob(f"{dataset_name}*")
                ],
            }
        )
    return datasets


def load_summary(dataset_name: str) -> Optional[Dict[str, Any]]:
    summary_path = paths.summary_dir / f"{dataset_name}.json"
    if not summary_path.exists():
        return None
    with summary_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def gather_metrics() -> Dict[str, Any]:
    summaries = []
    for summary_file in paths.summary_dir.glob("*.json"):
        with summary_file.open("r", encoding="utf-8") as fp:
            summaries.append(json.load(fp))

    quantitative_count = 0
    qualitative_count = 0
    for payload in summaries:
        summary = payload.get("summary", {})
        classification = summary.get("classification")
        if classification == "quantitative":
            quantitative_count += 1
        elif classification == "qualitative":
            qualitative_count += 1

    return {
        "total_datasets": len(summaries),
        "quantitative_datasets": quantitative_count,
        "qualitative_datasets": qualitative_count,
    }


def get_qualitative_themes(text: str) -> List[str]:
    config = LLMConfig.from_env()
    if not text.strip():
        return []

    client = LLMClient(config)
    return client.extract_themes(text)


def _is_likely_transcript(text: str) -> bool:
    """
    Heuristic to detect if a text file is likely a transcript/interview.
    Looks for interview-like patterns.
    """
    text_lower = text.lower()
    
    # Check for interview indicators
    interview_keywords = [
        "interview", "transcript", "teacher said", "respondent",
        "question:", "answer:", "q:", "a:", "interviewee",
        "discussion", "conversation", "feedback session"
    ]
    
    # If any keyword appears, likely a transcript
    for keyword in interview_keywords:
        if keyword in text_lower:
            return True
    
    # Check for question-answer patterns
    if text_lower.count("?") >= 3:
        return True
    
    return False

