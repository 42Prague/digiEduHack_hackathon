from __future__ import annotations
from typing import Any, Dict, List


def load_files(limit: int | None = None) -> Dict[str, Any]:
    """
    Dummy implementation: returns a small list of example files and summaries.
    Replace with real logic that inspects your data store.
    """
    files: List[Dict[str, Any]] = [
        {
            "id": "region_a_scores_2023",
            "name": "Region A – test scores 2023",
            "summary": "Student ID, subject, test score, test date, intervention type.",
        },
        {
            "id": "region_b_scores_2023",
            "name": "Region B – test scores 2023",
            "summary": "Student ID, exam result, test date, activity type.",
        },
        {
            "id": "interventions_2022_2024",
            "name": "Regions A+B – interventions 2022–2024",
            "summary": "Region, intervention type, start/end dates, teacher training, mentoring.",
        },
    ]
    if limit is not None:
        files = files[:limit]
    return {"files": files}


def find_relevant_files(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Dummy implementation: picks some fake 'relevant' files.
    Later you can implement semantic similarity over your summaries.
    """
    # In a real impl, use embeddings + cosine similarity against summaries.
    all_files = load_files(limit=None)["files"]
    return {
        "query": query,
        "files": all_files[: min(top_k, len(all_files))],
        "note": "Dummy result; replace with semantic search over file summaries.",
    }


def temporal_search(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Dummy implementation: pretend we filtered to a subset of files / periods.
    Later, connect this to your time-series / event data.
    """
    return {
        "start_date": start_date,
        "end_date": end_date,
        "files": [
            {
                "id": "region_a_scores_6m_after_join.pdf",
                "name": "Region A – 6 months after joining",
                "summary": "Scores and interventions in the 6-month window after region onboarding.",
            }
        ],
        "note": "Dummy temporal filter; connect to real date-indexed records later.",
    }
