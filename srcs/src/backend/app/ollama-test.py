# import os
# import sys
# import textwrap
# from typing import Any
#
# import requests
#
#
# def _build_payload(prompt: str) -> dict[str, Any]:
#     return {
#         "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
#         "prompt": prompt,
#         "stream": False,
#     }
#
#
# def main() -> int:
#     prompt = os.getenv(
#         "BACKEND_TEST_PROMPT",
#         "Introduce yourself and mention that this response came via the backend container.",
#     )
#     endpoint = os.getenv("OLLAMA_HOST", "http://ollama:11434").rstrip("/")
#     url = f"{endpoint}/api/generate"
#
#     print(f"Sending prompt to {url!r} ...", flush=True)
#     try:
#         response = requests.post(url, json=_build_payload(prompt), timeout=120)
#         response.raise_for_status()
#     except requests.RequestException as exc:
#         print(f"Request to Ollama failed: {exc}", file=sys.stderr)
#         return 1
#
#     data = response.json()
#     llm_output = data.get("response", "").strip()
#     print("Prompt:\n" + textwrap.indent(prompt, "  "))
#     print("\nLLM response:\n" + textwrap.indent(llm_output, "  "))
#     return 0
#
#
# if __name__ == "__main__":
#     raise SystemExit(main())
