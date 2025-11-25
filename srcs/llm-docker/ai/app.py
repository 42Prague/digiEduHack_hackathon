from flask import Flask, request, jsonify, send_from_directory
import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = "openai/gpt-oss-20b:groq"  # you can change this to any HF OpenAI-compatible model

app = Flask(__name__, static_folder='.', static_url_path='')


@app.route("/")
def index():
    # serve the bundled index.html
    return send_from_directory('.', 'index.html')


@app.route("/summarize", methods=["POST"])
def summarize():
    # keep the original summarize endpoint for compatibility
    text = request.form.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    if not HF_API_KEY:
        return jsonify({"error": "HF_API_KEY not set on server"}), 500

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": "You are a concise text summarizer."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 300
    }

    try:
        r = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        response_json = r.json()
        summary = response_json["choices"][0]["message"]["content"]
    except Exception as e:
        return jsonify({"error": f"Hugging Face API request failed: {e}"}), 500

    return jsonify({"summary": summary})


@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint expects JSON: {"message": "...", "history": [{"role":"user|assistant","content":"..."}, ...], "system": "optional system prompt"}
    The frontend should keep conversation history and pass it in; the server forwards system+history+user to Hugging Face and returns assistant reply.
    """
    if not HF_API_KEY:
        return jsonify({"error": "HF_API_KEY not set on server"}), 500

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = data.get('message', '')
    history = data.get('history', []) or []
    system_prompt = data.get('system', 'You are a helpful assistant.')

    if not user_message or not str(user_message).strip():
        return jsonify({"error": "No message provided"}), 400

    # Build messages array for HF API
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        # basic validation of history items
        if isinstance(m, dict) and m.get('role') and m.get('content') is not None:
            messages.append({"role": m['role'], "content": m['content']})
    messages.append({"role": "user", "content": user_message})

    headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": HF_MODEL, "messages": messages, "max_tokens": 300}

    try:
        r = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        resp = r.json()
        reply = resp['choices'][0]['message']['content']
    except Exception as e:
        return jsonify({"error": f"Hugging Face API request failed: {e}"}), 500

    return jsonify({"reply": reply})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
