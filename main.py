from pathlib import Path
from openai import OpenAI
from pdfminer.high_level import extract_text as pdf_extract
import docx2txt
from PIL import Image
import pytesseract
import pandas as pd

# ----------------------------
# CONFIG
# ----------------------------
FEATHER_API_KEY = "rc_ece268a38841081afb16a7bf0568039eaec2226a3e8a6bc801f9ee6e824fd7fd"
FEATHER_BASE_URL = "https://api.featherless.ai/v1"
client = OpenAI(base_url=FEATHER_BASE_URL, api_key=FEATHER_API_KEY)

INPUT_FOLDER = Path("input_files")
OUTPUT_FOLDER = Path("translated_files")
INPUT_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Fixed set of categories we always use
CATEGORIES = [
    "Student Info",
    "Academic Performance",
    "Attendance",
    "Behaviour & Discipline",
    "Goals & Target",
    "Goals progress/ Good status",
    "Intervention",
    "Intervention details",
    "Feedback",
    "Assessments",
    "Extraacurricular Activities",
    "Special Notes",
]

# Simple keyword map for fallback rule-based categorization
FALLBACK_KEYWORDS = {
    "Student Info": ["student", "pupil", "class", "grade", "year", "profile"],
    "Academic Performance": ["grade", "score", "marks", "achievement", "academic", "performance", "results"],
    "Attendance": ["attendance", "absent", "absence", "present", "late", "lateness", "truancy"],
    "Behaviour & Discipline": ["behaviour", "behavior", "discipline", "misconduct", "rules", "respect", "disruptive"],
    "Goals & Target": ["goal", "targets", "aim", "objective", "plan", "set a goal"],
    "Goals progress/ Good status": ["progress", "improvement", "improved", "good status", "on track", "developed"],
    "Intervention": ["intervention", "support", "assistance", "help", "action plan"],
    "Intervention details": ["session", "mentoring", "details", "strategy", "steps", "implementation"],
    "Feedback": ["feedback", "comment", "evaluation", "reflection", "reflexion", "review"],
    "Assessments": ["test", "exam", "assessment", "quiz", "evaluation", "grading"],
    "Extraacurricular Activities": ["extracurricular", "after-school", "club", "sport", "competition", "activities"],
    "Special Notes": ["note", "important", "remark", "additional", "context", "special"],
}

# ----------------------------
# FILE EXTRACTION
# ----------------------------
def extract_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    text = ""
    try:
        if ext == ".pdf":
            text = pdf_extract(file_path)
        elif ext in [".docx", ".doc"]:
            text = docx2txt.process(file_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
        elif ext == ".txt":
            text = file_path.read_text(encoding="utf-8")
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            text = df.to_string()
        elif ext in [".mp3", ".wav", ".mp4"]:
            with open(file_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="openai/whisper-large-v3",
                    file=f
                )
                text = transcript.text
        else:
            print(f"Unsupported file type: {ext}")
    except Exception as e:
        print(f"Error extracting {file_path}: {e}")
    return text.strip()

# ----------------------------
# TRANSLATION
# ----------------------------
def translate_to_english(text: str) -> str:
    """
    Translate text to English using Featherless AI.
    Handles long text by chunking.
    """
    if not text.strip():
        return ""

    CHUNK_SIZE = 2000
    chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    translated_chunks = []

    for idx, chunk in enumerate(chunks):
        try:
            prompt = (
                "Translate the following text to English, preserving meaning. "
                "Output only the translation:\n\n"
                f"{chunk}"
            )
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a translator. Only translate text to English. Do not add explanations.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            translated = response.choices[0].message.content.strip()
            translated = translated.strip('`"')  # Clean up quotes or code block markers
            translated_chunks.append(translated)
            print(f"Translated chunk {idx+1}/{len(chunks)}")
        except Exception as e:
            print(f"Translation error in chunk {idx+1}: {e}")
            translated_chunks.append(chunk)  # fallback to original

    return "\n\n".join(translated_chunks)


# ----------------------------
# FALLBACK RULE-BASED CATEGORIZATION
# ----------------------------
def rule_based_categorize(text: str) -> dict:
    """
    Very simple keyword-based categorization as a safety net
    when AI JSON parsing completely fails.
    """
    # Split into rough paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    categories = {cat: [] for cat in CATEGORIES}

    for para in paragraphs:
        lower = para.lower()
        matched_any = False
        for cat, keywords in FALLBACK_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                categories[cat].append(para)
                matched_any = True
        if not matched_any:
            categories["Special Notes"].append(para)

    # Join lists into strings
    return {cat: "\n\n".join(paras) for cat, paras in categories.items() if paras}


# ----------------------------
# AI CATEGORIZATION
# ----------------------------
def categorize_text(text: str, output_folder: Path):
    """
    Use AI to categorize the text into the fixed set of categories
    and save each category into separate files.

    If AI output is not valid JSON, falls back to rule-based categorization,
    but NEVER uses an 'Uncategorized' bucket.
    """
    import json
    import re

    if not text.strip():
        print("Empty text, nothing to categorize.")
        return

    try:
        categories_instruction = "\n".join(f"- {c}" for c in CATEGORIES)

        prompt = f"""
You are an AI that categorizes student-related data into a FIXED set of categories.

You MUST return a SINGLE valid JSON object with EXACTLY these keys:

{categories_instruction}

Rules:
- Values must be strings (you can include multiple paragraphs).
- If there is no relevant content for a category, set its value to an empty string "".
- The same piece of information may appear in multiple categories if appropriate.
- DO NOT add any other keys.
- DO NOT add explanations, comments, or markdown.
- DO NOT wrap the JSON in ```json``` or any other fences.

Text to categorize:
{text}
        """.strip()

        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You strictly output a single valid JSON object. "
                        "No markdown, no comments, no explanations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()
        print("Raw AI categorization response:")
        print(raw[:500] + ("..." if len(raw) > 500 else ""))

        # Strip markdown code fences if present
        if raw.startswith("```"):
            # Remove leading and trailing ```...``` blocks
            raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw).strip()

        # Extract the first {...} block to be safe
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in AI response.")

        json_text = raw[start : end + 1]

        try:
            ai_categories = json.loads(json_text)
        except Exception as e:
            raise ValueError(f"JSON parsing failed: {e}")

        if not isinstance(ai_categories, dict):
            raise ValueError("Parsed JSON is not an object/dict.")

        # Normalize to fixed categories
        normalized = {}
        for cat in CATEGORIES:
            # Exact key preferred
            if cat in ai_categories:
                val = ai_categories[cat]
            else:
                # Try case-insensitive match
                val = ""
                for k, v in ai_categories.items():
                    if k.strip().lower() == cat.lower():
                        val = v
                        break

            # Convert non-string values to string
            if isinstance(val, list):
                val = "\n\n".join(str(x) for x in val)
            elif not isinstance(val, str):
                val = str(val)

            normalized[cat] = val.strip()

        # If everything is empty, fallback to rule-based
        if all(not v for v in normalized.values()):
            print("AI returned all empty categories, using rule-based fallback.")
            normalized = rule_based_categorize(text)

    except Exception as e:
        print(f"Error in AI categorization: {e}")
        print("Using rule-based fallback categorization.")
        normalized = rule_based_categorize(text)

    # Save each category into a separate text file
    for cat, content in normalized.items():
        if not content.strip():
            continue  # skip empty categories
        safe_cat = "".join(c if c.isalnum() else "_" for c in cat)
        cat_file = output_folder / f"{safe_cat}.txt"
        if cat_file.exists():
            existing = cat_file.read_text(encoding="utf-8")
            cat_file.write_text(existing + "\n\n" + content, encoding="utf-8")
        else:
            cat_file.write_text(content, encoding="utf-8")
        print(f"Saved category '{cat}' -> {cat_file}")


# ----------------------------
# MAIN PROCESSING
# ----------------------------
def main():
    files = list(INPUT_FOLDER.iterdir())
    if not files:
        print("No files found in input_files folder!")
        return

    for file_path in files:
        print(f"\nProcessing file: {file_path.name}")
        text = extract_text(file_path)
        if not text:
            print("No text extracted. Skipping.")
            continue

        print("Translating...")
        translated_text = translate_to_english(text)

        # Create folder for this file to store categorized text
        file_output_folder = OUTPUT_FOLDER / file_path.stem
        file_output_folder.mkdir(parents=True, exist_ok=True)

        # Save raw translated text
        raw_file = file_output_folder / "translated.txt"
        raw_file.write_text(translated_text, encoding="utf-8")
        print(f"Saved translated text to {raw_file}")

        # AI categorization
        print("Categorizing text using AI...")
        categorize_text(translated_text, file_output_folder)

    print("\nAll files processed!")


if __name__ == "__main__":
    main()

