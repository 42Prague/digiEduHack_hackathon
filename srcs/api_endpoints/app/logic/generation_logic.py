import os
from typing import List
from openai import OpenAI

# Ensure your Featherless API key is available
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
if not FEATHERLESS_API_KEY:
    raise ValueError("Missing FEATHERLESS_API_KEY environment variable.")

# Initialize the client for Featherless AI
client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=FEATHERLESS_API_KEY,
)

# Choose the model
MODEL_NAME = "unsloth/Llama-3.3-70B-Instruct"


def build_prompt(question: str, context_chunks: List[str]) -> (str, str):
    """Return system_text and user_text for the model."""
    context_text = "\n\n---\n\n".join(context_chunks)
    system_text = (
        "You are a highly concise assistant. "
        "Use ONLY the provided context to answer the question. "
        "DO NOT include any reasoning, explanations, or commentary. "
        "DO NOT start with phrases like 'Okay', 'Let me explain', or 'First' etc. "
        "Answer in 1–3 sentences maximum, directly and factually. "
        "If the answer is not in the context, respond with exactly: 'I don't know.'"
    )

    user_text = f"Context:\n{context_text}\n\nQuestion: {question}"
    return system_text, user_text


def generate_answer(question: str, context_chunks: List[str]) -> str:
    """Query Featherless AI through OpenAI-compatible SDK."""
    system_text, user_text = build_prompt(question, context_chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        max_tokens=300,
        temperature=0.0,
    )

    return response.choices[0].message.content

def build_data_prompt(question: str, context_chunks: List[str]) -> (str, str):
    context_text = "\n\n---\n\n".join(context_chunks)
    system_text = (
        "You are a data-generation assistant. "
        "Using ONLY the provided context, generate a dataset formatted STRICTLY as JSON. "
        "The JSON must contain a list of objects, each representing a row. "
        "Do not add explanations, comments, or extra text. "
        "If data cannot be extracted, return exactly: []"
    )

    user_text = f"Context:\n{context_text}\n\nQuestion: {question}\n\nReturn ONLY valid JSON:"
    return system_text, user_text


def generate_structured_data(question: str, context_chunks: List[str]):
    system_text, user_text = build_data_prompt(question, context_chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        max_tokens=500,
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON safely
    import json
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []

