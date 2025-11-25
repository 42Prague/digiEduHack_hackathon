import os
import sys
import uuid
import subprocess
from flask import Flask, request, jsonify
from pathlib import Path

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/upload", methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return "", 204

    region = request.form.get("region")
    school = request.form.get("school")
    file = request.files.get("file")

    if not region or not school or not file:
        return jsonify(error="missing fields"), 400

    filename = f"{uuid.uuid4().hex}-{file.filename}"
    saved_path = os.path.join(UPLOAD_DIR, filename)
    file.save(saved_path)

    try:
        # Import main.py functions and process the file
        sys.path.insert(0, os.path.dirname(__file__))
        from main import extract_text, translate_to_english, categorize_text
        
        # Create output folder with region+school naming
        output_name = f"{school}_Region{region}"
        output_folder = Path(__file__).parent / "translated_files" / output_name
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Extract, translate, categorize
        text = extract_text(Path(saved_path))
        translated_text = translate_to_english(text)
        categorize_text(translated_text, output_folder)
        
        # Save metadata
        metadata_file = output_folder / "metadata.txt"
        metadata_file.write_text(f"Region: {region}\nSchool: {school}\nOriginal file: {file.filename}\n")
        
        return jsonify(ok=True, output_folder=str(output_folder), message="File processed successfully")
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)