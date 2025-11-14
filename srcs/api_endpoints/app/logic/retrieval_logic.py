import math
from collections import Counter
from typing import Dict, List, Tuple
from ..db.vector_store import VectorStore

TOKEN_RE = __import__("re").compile(r"\w+")

def tokens(text: str):
    return TOKEN_RE.findall(text.lower())

def token_counts(text: str) -> Dict[str,int]:
    return dict(Counter(tokens(text)))

def dot_product(a: Dict[str,int], b: Dict[str,int]) -> float:
    s = 0.0
    # iterate smaller dict
    if len(a) < len(b):
        for k,v in a.items():
            s += v * b.get(k, 0)
    else:
        for k,v in b.items():
            s += v * a.get(k, 0)
    return s

def magnitude(a: Dict[str,int]) -> float:
    return math.sqrt(sum(v*v for v in a.values()))

def cosine_sim(a: Dict[str,int], b: Dict[str,int]) -> float:
    mag_a = magnitude(a)
    mag_b = magnitude(b)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product(a,b) / (mag_a * mag_b)


import json

def retrieve(query: str, regions: list, top_k: int = 3) -> list:
    q_tokens = token_counts(query)
    store = VectorStore()
    rows = store.all_chunks()
    scored = []

    for r in rows:
        metadata = r.get("metadata", {})

        # Parse metadata if it's a JSON string
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        chunk_regions = metadata.get("regions", [])

        # Filter by regions if any are specified
        if regions:
            # Make comparison case-insensitive
            if not any(reg.lower() in [c.lower() for c in chunk_regions] for reg in regions):
                continue  # skip this chunk if no region matches

        # Compute similarity
        score = cosine_sim(q_tokens, r["tokens"])
        scored.append((score, r, metadata))  # keep metadata for correct return

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top_k with positive score
    top = [(s, r, m) for s, r, m in scored[:top_k] if s > 0]

    # Return properly
    return [{"id": r["id"], "chunk": r["chunk"], "metadata": m} for s, r, m in top]


