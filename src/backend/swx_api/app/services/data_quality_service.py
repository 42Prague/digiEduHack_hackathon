"""
Data Quality Service
--------------------
Implements data quality scoring and reporting pipeline.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from swx_api.app.services.ingestion_service import paths

logger = logging.getLogger("data_quality")


# PII detection patterns
PII_PATTERNS = {
    "emails": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phones": re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "names": re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'),  # Simple name pattern
}


def calculate_dq_score(
    schema_correctness: float,
    missing_value_rate: float,
    pii_presence: float,
    normalization_quality: float
) -> int:
    """
    Calculate Data Quality Score using weighted formula.
    
    Args:
        schema_correctness: 0-1 score for schema validation
        missing_value_rate: 0-1 rate of missing values (lower is better)
        pii_presence: 0-1 rate of PII found (lower is better)
        normalization_quality: 0-1 score for normalization
        
    Returns:
        DQ Score (0-100)
    """
    # Weighted formula
    score = (
        0.40 * (schema_correctness * 100) +
        0.20 * ((1 - missing_value_rate) * 100) +
        0.20 * ((1 - pii_presence) * 100) +
        0.20 * (normalization_quality * 100)
    )
    return int(max(0, min(100, score)))


def detect_pii(text: str) -> Dict[str, int]:
    """
    Detect PII in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with PII counts
    """
    counts = {
        "emails": len(PII_PATTERNS["emails"].findall(text)),
        "phones": len(PII_PATTERNS["phones"].findall(text)),
        "names": len(PII_PATTERNS["names"].findall(text)),
    }
    return counts


def analyze_schema_issues(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Analyze schema issues in data.
    
    Args:
        data: Data dictionary or structure to analyze
        
    Returns:
        List of schema issues
    """
    issues = []
    
    # Check for required metadata fields
    required_fields = ["school_id", "region_id", "school_type", "intervention_type"]
    if isinstance(data, dict):
        for field in required_fields:
            if field not in data:
                issues.append({
                    "column": field,
                    "issue": f"Missing required field: {field}"
                })
    
    return issues


def generate_dq_report(
    dataset_id: str,
    data: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive Data Quality report.
    
    Args:
        dataset_id: Unique identifier for the dataset
        data: The data to analyze (can be text, dict, or structured data)
        metadata: Optional metadata dictionary
        
    Returns:
        DQ Report dictionary
    """
    total_rows = 1  # Default for single records
    valid_rows = 0
    invalid_rows = 0
    missing_values = {}
    pii_found = {"names": 0, "emails": 0, "phones": 0}
    schema_issues = []
    normalization_fixes = []
    
    # Analyze based on data type
    if isinstance(data, str):
        # Text data analysis
        pii_counts = detect_pii(data)
        pii_found = pii_counts
        valid_rows = 1 if len(data.strip()) > 0 else 0
        invalid_rows = 1 - valid_rows
        
        # Check for missing content
        if not data or not data.strip():
            missing_values["content"] = 1
        
    elif isinstance(data, dict):
        # Dictionary/structured data analysis
        total_rows = 1
        schema_issues = analyze_schema_issues(data)
        
        # Check for missing values
        for key, value in data.items():
            if value is None or value == "":
                missing_values[key] = missing_values.get(key, 0) + 1
        
        # Check for PII in string values
        for value in data.values():
            if isinstance(value, str):
                pii_counts = detect_pii(value)
                pii_found["emails"] += pii_counts["emails"]
                pii_found["phones"] += pii_counts["phones"]
                pii_found["names"] += pii_counts["names"]
        
        valid_rows = 1 if len(schema_issues) == 0 else 0
        invalid_rows = 1 - valid_rows
    
    # Calculate scores
    schema_correctness = 1.0 - (len(schema_issues) * 0.1)  # Penalty per issue
    schema_correctness = max(0.0, min(1.0, schema_correctness))
    
    total_cells = sum(missing_values.values()) if missing_values else 1
    missing_value_rate = total_cells / max(1, total_rows * 10)  # Normalize
    
    total_pii = sum(pii_found.values())
    pii_presence = min(1.0, total_pii / 100.0)  # Normalize (100 PII = 100%)
    
    normalization_quality = 1.0 if len(normalization_fixes) == 0 else 0.8  # Good if no fixes needed
    
    dq_score = calculate_dq_score(
        schema_correctness,
        missing_value_rate,
        pii_presence,
        normalization_quality
    )
    
    # Prepare report
    report = {
        "dq_score": dq_score,
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "missing_values": missing_values,
        "pii_found_and_masked": pii_found,
        "schema_issues": schema_issues,
        "normalization_fixes": normalization_fixes,
        "quarantined_rows_path": f"/data/processed/quarantine/{dataset_id}.json",
    }
    
    # Save report to file
    report_path = paths.data_dir / "processed" / "clean" / f"{dataset_id}_dq_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Add the report path to the report itself
    report["report_path"] = str(report_path)
    
    logger.info(f"Generated DQ report for {dataset_id}: score={dq_score}, path={report_path}")
    
    return report


def get_dq_report(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a saved DQ report.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        DQ Report dictionary or None if not found
    """
    report_path = paths.data_dir / "processed" / "clean" / f"{dataset_id}_dq_report.json"
    
    if not report_path.exists():
        return None
    
    try:
        with report_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading DQ report for {dataset_id}: {e}")
        return None

