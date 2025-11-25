import json
from pathlib import Path
import requests

def read_md():
    input_dir = Path("/home/sofiemeyer/Projects/hackathon/data_samples_eduzmena/Data samples/")
    output_dir = Path("json_outputs")
    output_dir.mkdir(exist_ok=True)

    for file_path in input_dir.glob("*.md"):
        # Read Markdown content
        text = file_path.read_text(encoding="utf-8")

        # Get summary from local LLM
        prompt = f"""
        You will be given a transcript (conversation or focus group). Extract the important,
        factual information and return ONLY valid JSON (no explanation, no extra text).

        Be concise and objective. Do NOT include opinions or filler.

        Return a JSON object with the following keys:
        - "summary": a short summary of the discussion.
        - "topics": short topic labels or categories mentioned.
        - "entities": named entities (teacher, student, parent; organizations; locations). No personal names.
        - "facts": important factual statements or claims made (short sentences).

        Transcript:
        {text}
        """
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma2:9b", "prompt": prompt, "stream": False},
        )
        summary = response.json().get("response", "")

        # Save as simple JSON
        output_file = output_dir / f"{file_path.stem}.json"
        json.dump({"filename": file_path.name, "summary": summary}, open(output_file, "w", encoding="utf-8"), indent=2)

        print(f"{file_path.name} -> {output_file.name} [success]")