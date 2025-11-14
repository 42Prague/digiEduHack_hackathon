from flask import Blueprint, request, jsonify
import json
from srcs.helpers.to_txt_conversion import convert_to_text
from ..logic.ingest_logic import ingest_document
from ..db.vector_store import VectorStore
import tempfile

ingest_bp = Blueprint("ingest", __name__)


@ingest_bp.route("/ingest", methods=["POST"])
def ingest():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"error": "Missing file upload"}), 400

    # Temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.filename}") as tmp:
        uploaded_file.save(tmp.name)
        tmp_path = tmp.name

    # Convert file → text
    text = convert_to_text(tmp_path)

    if not text:
        return jsonify({"error": "Missing text"}), 400

    # Parse metadata from form-data
    body = request.form or {}
    metadata_raw = body.get("metadata")
    metadata = None
    if metadata_raw:
        try:
            metadata = json.loads(metadata_raw)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON in metadata"}), 400

    # Use the text as before
    result = ingest_document(text, metadata=metadata)
    return jsonify({"status": "ok", **result}), 201


@ingest_bp.route("/ingest/clear", methods=["POST"])
def clear():
    # helper to clear DB during dev
    VectorStore().clear()
    return jsonify({"status": "cleared"})
