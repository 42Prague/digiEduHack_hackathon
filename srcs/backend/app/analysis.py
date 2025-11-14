import os
import math
from typing import Dict, Any
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
- Prefer short, machine-friendly keys in English using snake_case
  (e.g. "student_name", "school_year", "math_grade", "attendance_percentage").
- Preserve original Czech text in values where appropriate (teacher comments, subject names, etc.).
- Use numbers for anything that looks numeric (grades, counts, percentages, points, years, hours, etc.).
- If you are unsure about a value, either omit the field or add a boolean flag like "<field>_uncertain": true.

Required structure:
- The top-level JSON MUST contain:
  - "summary": short natural-language summary of the document (2–4 sentences).
  - "data": an object that groups all other extracted fields.

Inside "data":
- You are free to create any keys and nested objects that best represent the information in the document.
- Group related fields into nested objects (for example: "student", "school", "class", "grades", "behavior", "attendance", "evaluation", "meta").
- Use arrays when there are repeated elements (for example: list of subjects, list of semesters/terms, list of teacher comments).
- For arrays, each item should be an object with consistent fields
  (for example: subjects might have "name", "area", "grade", "comment", "is_core_subject").

Focus on extracting:
- All explicit identifiers (student name, school, class, academic year, term, document type).
- All explicit or implicit metrics (grades, points, percentages, rankings, levels, counts of absences, etc.).
- Any temporal information (dates, school year, term/semester, period).
- Any categorical labels (subject names, behavior categories, assessment labels, pass/fail, etc.).
- Any free-text comments or evaluations from teachers.
- Any information about performance trends, strengths, weaknesses, recommendations.

Document content (possibly truncated):

\"\"\"{sample}\"\"\"
"""

def analyze_file(session: Session, file_meta: FileMeta) -> None:
    # resolve path from tus_id (depends on how tusd stores files; adjust)
    path = os.path.join(UPLOAD_DIR, file_meta.tus_id)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    text = extract_text_from_file(path)
    basic_stats = compute_basic_stats(text)

    prompt = build_llm_prompt(text)
    # print(f"PROMPT: {prompt}")
    llm_json = ask_llm(prompt)

    file_meta.extracted_text = text  # optional, maybe store only if small
    file_meta.basic_stats = basic_stats
    file_meta.llm_summary = llm_json

    session.add(file_meta)
