from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from swx_api.app.services import ingestion_service, sample_data
from swx_api.app.services.llm_client import LLMClient, LLMConfig


def _themes_path(dataset_name: str) -> Path:
    return ingestion_service.paths.analytics_themes_dir / f"{dataset_name}.json"


def _ensure_dirs() -> None:
    ingestion_service.paths.analytics_themes_dir.mkdir(parents=True, exist_ok=True)


def _load_text(dataset_path: Path) -> str:
    if dataset_path.suffix.lower() == ".txt":
        return dataset_path.read_text(encoding="utf-8")

    if dataset_path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(dataset_path)
        except Exception:
            return ""
        text_columns = df.select_dtypes(include=["object"]).columns
        if not len(text_columns):
            return ""
        combined = "\n".join(
            df[column].dropna().astype(str).str.strip().str.cat(sep=" ")
            for column in text_columns
        )
        return combined[:8000]

    return ""


def extract_dataset_themes(dataset_name: str, dataset_path: Path) -> Optional[Dict[str, object]]:
    text = _load_text(dataset_path)
    if not text.strip():
        return None

    config = LLMConfig.from_env()
    themes = LLMClient(config).extract_themes(text)
    if not themes:
        return None

    _ensure_dirs()
    payload = {
        "dataset": dataset_name,
        "themes": themes,
        "generated_at": datetime.utcnow().isoformat(),
    }
    _themes_path(dataset_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_themes(dataset_name: str) -> Optional[Dict[str, object]]:
    themes_file = _themes_path(dataset_name)
    if themes_file.exists():
        try:
            return json.loads(themes_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    dataset = next((d for d in ingestion_service.list_datasets() if d["name"] == dataset_name), None)
    if not dataset:
        return None

    return extract_dataset_themes(dataset_name, Path(dataset["normalized_path"]))


def get_all_themes() -> List[Dict[str, object]]:
    themes: List[Dict[str, object]] = []
    for dataset in ingestion_service.list_datasets():
        payload = load_themes(dataset["name"])
        if payload:
            themes.append(payload)
    return themes or sample_data.get_sample_themes()

