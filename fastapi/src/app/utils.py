import json
import sqlite3
import re
from uuid import uuid4
DB_PATH = "/app/data/metadata.db"
TARGET_ID = 3
NEW_VALUE = "REPLACED_BY_SCRIPT"

# canonical schema as a Python dict (was previously embedded as an unquoted string)
SCHEMA_COLUMNS = {
    "school_year": {"type": "string", "description": "Academic school year in which the intervention took place, e.g. \"2024/2025\"."},
    "date": {"type": "string", "description": "Exact calendar date of the intervention or feedback in ISO 8601 format (YYYY-MM-DD), e.g. \"2025-03-15\"."},
    "year": {"type": "integer", "description": "Four-digit year associated with the intervention date, e.g. 2025."},
    "month": {"type": "integer", "description": "Numeric month (1–12) associated with the intervention date."},
    "semester": {"type": "string", "description": "Academic semester or term in which the intervention took place (e.g. \"1\" for first semester, \"2\" for second semester)."},
    "intervention": {"type": "string", "description": "Short title or name of the intervention, program, or activity."},
    "intervention_type": {"type": "string", "description": "Category or type of the intervention (e.g. \"Workshop\", \"Counseling\", \"Training\", \"Campaign\")."},
    "intervention_detail": {"type": "string", "description": "Detailed description of the intervention content, methods, duration, objectives, and other relevant characteristics."},
    "target_group": {"type": "string", "description": "the primary audience for the intervention."},
    "name_of_participant": {"type": "string", "description": "Name of the person participating in the intervention or providing feedback."},
    "organization_school": {"type": "string", "description": "Name of the school or organization where the intervention was implemented."},
    "school_grade": {"type": "string", "description": "Grade or level of the students involved in the intervention (e.g. \"Grade 5\")."},
    "school_type": {"type": "string", "description": "Type of educational institution (e.g. \"primary\", \"lower secondary\", \"upper secondary\")."},
    "region": {"type": "string", "description": "Geographical region, district, municipality, or administrative area of the school or organization."},
    "feedback": {"type": "string", "description": "Qualitative feedback on the intervention (e.g. perceived impact, satisfaction, suggestions)."}
}

def replace_row_columns_with_string(db_path: str = DB_PATH, target_id: int = TARGET_ID, new_value: str = NEW_VALUE) -> bool:
    """
    Safely update the 'columns' field for a given id in schema_metadata.
    - Uses parameterized SQL to avoid injection.
    - Serializes SCHEMA_COLUMNS as JSON by default; if new_value is provided and not the default
      sentinel, it will be used verbatim (expected to be a JSON string).
    Returns True if a row was updated, False otherwise.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        if new_value == NEW_VALUE:
            columns_json = json.dumps(SCHEMA_COLUMNS, ensure_ascii=False)
        else:
            columns_json = new_value  # caller-supplied JSON string
        cur.execute("UPDATE schema_metadata SET columns = ? WHERE id = ?", (columns_json, target_id))
        conn.commit()
        updated = cur.rowcount if cur.rowcount is not None else 0
        return updated > 0
    except sqlite3.Error as e:
        print("SQLite error:", e)
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    ok = replace_row_columns_with_string()
    print("Updated:" , ok)