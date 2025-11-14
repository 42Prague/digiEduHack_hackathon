import os
import math
from datetime import datetime
from typing import Dict, Any, Optional, Literal, Sequence, Tuple

from sqlmodel import Session

from .models import FileMeta
from .ollama_client import ask_llm  # helper for calling ollama

UPLOAD_DIR = "/data/uploads"  # or whatever tusd uses inside /data

FieldType = Literal["list", "string", "date"]
FieldSchema = Sequence[Tuple[str, FieldType]]

ATTENDANCE_SCHEMA: FieldSchema = [
    ("school_year", "list"),
    ("date", "date"),
    ("year", "list"),
    ("month", "list"),
    ("semester", "list"),
    ("intervention", "list"),
    ("intervention_type", "list"),
    ("intervention_detail", "string"),
    ("target_group", "list"),
    ("participant_name", "string"),
    ("organization_school", "list"),
    ("school_grade", "list"),
    ("school_type", "list"),
    ("region", "list"),
    ("feedback", "string"),
]

FEEDBACK_SCHEMA: FieldSchema = [
    ("school_year", "list"),
    ("date", "date"),
    ("year", "list"),
    ("month", "list"),
    ("semester", "list"),
    ("participant_name", "string"),
    ("organization_school", "list"),
    ("school_grade", "list"),
    ("school_type", "list"),
    ("region", "list"),
    ("intervention", "list"),
    ("intervention_type", "list"),
    ("intervention_detail", "string"),
    ("target_group", "list"),
    ("overall_satisfaction", "list"),
    ("lecturer_performance_and_skills", "list"),
    ("planned_goals", "list"),
    ("gained_professional_development", "list"),
    ("open_feedback", "string"),
]

def extract_text_from_file(path: str) -> str:
    # Very rough sketch, you can branch by extension
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif path.lower().endswith(".docx"):
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        # assume plaintext
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def compute_basic_stats(text: str) -> Dict[str, Any]:
    words = text.split()
    word_count = len(words)
    sentences = [s for s in text.replace("\n", " ").split(".") if s.strip()]
    sentence_count = max(len(sentences), 1)
    avg_words_per_sentence = word_count / sentence_count
    char_count = len(text)
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": avg_words_per_sentence,
        "char_count": char_count,
    }


def build_llm_prompt(text: str) -> str:
    MAX_CHARS = 8000
    sample = text[:MAX_CHARS]

    return f"""
You are a backend service analyzing educational documents (often Czech school reports).

Your goal is to transform each document into a single, rich JSON object that captures as much machine-readable information as possible for later dashboards and analytics.

Rules:
- Return ONLY ONE JSON OBJECT and nothing else.
- Do not include backticks.
- Do not include explanations before or after the JSON.
- Do not include multiple JSON objects.
- Prefer short, machine-friendly keys in English using snake_case.
- Preserve original Czech text where appropriate.
- Use numbers where applicable.
- If uncertain, either omit the field or add "<field>_uncertain": true.

Required top-level structure:
- The top-level JSON MUST contain:
  - "summary": 2–4 sentence natural-language summary.
  - "data": an object containing all extracted structured information.
  - "data.type": one of:
      - "attendance_checklist"
      - "feedback_form"
      - "record"

All documents:
- "data" MUST include **all core fields**, even if empty or null.

============
ATTENDANCE CHECKLIST SCHEMA
============
If the document appears to be an attendance checklist (sign-in sheets, lists of participants, presence marks, checkboxes, etc.),
set:
  data.type = "attendance_checklist"

Then include every one of these fields exactly with the shown types (empty if missing):

  "school_year": list
  "date": string (ISO-like or original)
  "year": list
  "month": list
  "semester": list
  "intervention": list
  "intervention_type": list
  "intervention_detail": string
  "target_group": list
  "participant_name": string
  "organization_school": list
  "school_grade": list
  "school_type": list
  "region": list
  "feedback": string

Example notes:
- A list means: [] if missing
- A string means: "" if missing

============
FEEDBACK FORM SCHEMA
============
If the document appears to be a feedback form (evaluations, satisfaction surveys, session feedback),
set:
  data.type = "feedback_form"

Then include every one of these fields exactly with the shown types (empty if missing):

  "school_year": list
  "date": string
  "year": list
  "month": list
  "semester": list
  "participant_name": string
  "organization_school": list
  "school_grade": list
  "school_type": list
  "region": list
  "intervention": list
  "intervention_type": list
  "intervention_detail": string
  "target_group": list
  "overall_satisfaction": list
  "lecturer_performance_and_skills": list
  "planned_goals": list
  "gained_professional_development": list
  "open_feedback": string

============
GENERIC RECORD SCHEMA
============
If the document does NOT clearly match attendance_checklist or feedback_form,
then:
  data.type = "record"

Add any additional structure relevant for the record (student, school, evaluations, behaviors, recommendations, grades, events, etc.).

Focus on extracting:
- Identifiers (student, school, academic year, class, region)
- Metrics (grades, points, absences, percentages, ratings)
- Temporal info (dates, periods, semesters)
- Categories (type of document, intervention type)
- Teacher/student comments
- Trends, strengths, weaknesses
- Recommendations

Document content (possibly truncated):

\"\"\"{sample}\"\"\"
"""

def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _clean_to_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip() or None


def _normalize_list(value: Any) -> Optional[list[Any]]:
    if isinstance(value, list):
        normalized = []
        for item in value:
            cleaned = _clean_to_string(item)
            if cleaned is not None:
                normalized.append(cleaned)
        return normalized or None

    cleaned = _clean_to_string(value)
    if cleaned is None:
        return None
    return [cleaned]


def _normalize_date(value: Any) -> Optional[str]:
    cleaned = _clean_to_string(value)
    if not cleaned:
        return None

    known_formats = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y")
    for fmt in known_formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.date().isoformat()
        except ValueError:
            continue
    return cleaned


def _normalize_field_value(value: Any, field_type: FieldType) -> Optional[Any]:
    if field_type == "list":
        return _normalize_list(value)
    if field_type == "date":
        return _normalize_date(value)
    return _clean_to_string(value)


def _extract_expected_fields(data: Dict[str, Any], schema: FieldSchema) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {}
    for field, field_type in schema:
        if field not in data:
            continue
        normalized = _normalize_field_value(data[field], field_type)
        if normalized is not None:
            payload[field] = normalized
    return payload or None


def _extract_record_payload(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {}
    for key, value in data.items():
        if key == "type":
            continue
        if _is_empty_value(value):
            continue
        payload[key] = value
    return payload or None


def apply_structured_metadata(file_meta: FileMeta, llm_json: Dict[str, Any]) -> None:
    file_meta.analysis_summary_text = None
    file_meta.analysis_type = None
    file_meta.attendance_data = None
    file_meta.feedback_data = None
    file_meta.record_data = None

    if not isinstance(llm_json, dict):
        return

    summary = llm_json.get("summary")
    if isinstance(summary, str):
        cleaned_summary = summary.strip()
        file_meta.analysis_summary_text = cleaned_summary or None

    data = llm_json.get("data")
    if not isinstance(data, dict):
        return

    declared_type = data.get("type") if isinstance(data.get("type"), str) else None
    recognized_type = declared_type if declared_type in {"attendance_checklist", "feedback_form", "record"} else None

    if recognized_type == "attendance_checklist":
        file_meta.attendance_data = _extract_expected_fields(data, ATTENDANCE_SCHEMA)
        file_meta.analysis_type = recognized_type
        return

    if recognized_type == "feedback_form":
        file_meta.feedback_data = _extract_expected_fields(data, FEEDBACK_SCHEMA)
        file_meta.analysis_type = recognized_type
        return

    record_payload = _extract_record_payload(data)
    if record_payload:
        file_meta.record_data = record_payload
        file_meta.analysis_type = recognized_type or "record"
    elif recognized_type:
        file_meta.analysis_type = recognized_type

def analyze_file(
    session: Session,
    file_meta: FileMeta,
    override_text: Optional[str] = None,
) -> None:
    """
    Analyze the file and generate metadata.

    If override_text is provided (e.g. a Whisper transcript for audio),
    use that instead of reading/extracting from the original file.
    """
    if override_text is not None:
        text = override_text
    else:
        # resolve path from tus_id (depends on how tusd stores files; adjust if needed)
        path = os.path.join(UPLOAD_DIR, file_meta.tus_id)
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        text = extract_text_from_file(path)

    basic_stats = compute_basic_stats(text)
    prompt = build_llm_prompt(text)
    llm_json = ask_llm(prompt)

    file_meta.extracted_text = text  # optional, maybe store only if small
    file_meta.basic_stats = basic_stats
    file_meta.llm_summary = llm_json
    apply_structured_metadata(file_meta, llm_json)

    session.add(file_meta)
