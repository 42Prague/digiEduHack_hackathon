from flask import Blueprint, jsonify
from ..logic.hello_logic import get_hello_message

hello_bp = Blueprint("hello", __name__, url_prefix="/api")

@hello_bp.route("/hello", methods=["GET"])
def hello():
    message = get_hello_message()
    return jsonify({"message": message})
