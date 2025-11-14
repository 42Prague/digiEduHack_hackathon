from __future__ import annotations

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_MODEL_LICENSE = "MIT"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load the embedding model once and keep it in memory."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")


def embed_text(text: str) -> List[float]:
    """Return a normalized embedding vector for the given text."""
    model = _load_model()
    embedding = model.encode([text], normalize_embeddings=True)
    return embedding[0].tolist()
