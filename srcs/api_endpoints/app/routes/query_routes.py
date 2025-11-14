from flask import Blueprint, request, jsonify
from ..logic.retrieval_logic import retrieve
from ..logic.generation_logic import generate_answer

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
