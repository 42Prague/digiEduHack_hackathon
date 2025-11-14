import os
import math
from typing import Dict, Any, Optional

from sqlmodel import Session

from .models import FileMeta
from .ollama_client import ask_llm  # helper for calling ollama

UPLOAD_DIR = "/data/uploads"  # or whatever tusd uses inside /data

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

    session.add(file_meta)
