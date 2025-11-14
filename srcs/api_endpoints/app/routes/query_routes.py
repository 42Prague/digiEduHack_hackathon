from flask import Blueprint, request, jsonify
from ..logic.retrieval_logic import retrieve
from ..logic.generation_logic import generate_answer, generate_structured_data

query_bp = Blueprint("query", __name__)

@query_bp.route("/query", methods=["POST"])
def query():
    """
    POST /api/query
    JSON body: {"query": "..." , "top_k": 3}
    Response: {"answer": "...", "used_context": [...chunks...]}
    """
    body = request.get_json(force=True)
    q = body.get("query")
    if not q:
        return jsonify({"error": "Missing 'query' in body"}), 400
    top_k = int(body.get("top_k", 3))
    regions = body.get("regions", None)
    retrieved = retrieve(q, regions = regions, top_k=top_k, )
    context_chunks = [r["chunk"] for r in retrieved]
    if not context_chunks:
        # no context found, still call model but warn or return "no context"
        return jsonify({"answer": "No relevant context found in the database.", "used_context": []})
    answer = generate_answer(q, context_chunks)
    return jsonify({"answer": answer, "used_context": context_chunks})


generate_data_bp = Blueprint("generate_data", __name__)

@generate_data_bp.route("/generate-data", methods=["POST"])
def generate_data():
    """
    POST /api/generate-data
    JSON body: {"query": "...", "top_k": 3}
    Returns: {"data": [...], "used_context": [...]}
    """
    body = request.get_json(force=True)
    q = body.get("query")
    if not q:
        return jsonify({"error": "Missing 'query' field"}), 400

    top_k = int(body.get("top_k", 3))
    regions = body.get("regions", None)

    # Retrieve relevant chunks
    retrieved = retrieve(q, regions=regions, top_k=top_k)
    context_chunks = [r["chunk"] for r in retrieved]

    if not context_chunks:
        return jsonify({"data": [], "used_context": []})

    # Generate structured dataset
    data = generate_structured_data(q, context_chunks)

    return jsonify({
        "data": data,
        "used_context": context_chunks
    })