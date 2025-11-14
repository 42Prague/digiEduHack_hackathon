import os
import requests
import json

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
# OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:1.5b")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

def ask_llm(prompt: str):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": "json",  # Llama 3.1 supports this
        "stream": False,
    }
    
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    raw = data.get("response", "")

    raw = raw.strip()

    # Parse only the first JSON object, ignore trailing junk
    try:
        decoder = json.JSONDecoder()
        obj, idx = decoder.raw_decode(raw)
        # optional: if you want to see if there's trailing stuff:
        leftover = raw[idx:].strip()
        if leftover:
            print("NOTE: LLM returned extra trailing content after JSON, ignoring it.")
            print("TRAILING (truncated):", leftover[:200])
        return obj
    except json.JSONDecodeError as e:
        # make debugging easier
        print("!!! JSON DECODE ERROR !!!", e)
        print("RAW (truncated):", raw[:400])
        raise
