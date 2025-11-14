import re
from typing import List, Dict
from . import retrieval_logic  # for token functions
from ..db.vector_store import VectorStore

# simple chunker: split by sentences and group to approx chunk_size words
def split_sentences(text: str) -> List[str]:
    # This regex splits on ., !, ?, but keeps abbreviations intact
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, chunk_size_words: int = 75, overlap_words: int = 10) -> List[str]:
    sentences = split_sentences(text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        words_in_sentence = sentence.split()
        sentence_len = len(words_in_sentence)

        if current_len + sentence_len > chunk_size_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            # For overlap, keep last `overlap_words` words
            overlap = current_chunk[-overlap_words:] if overlap_words < len(current_chunk) else current_chunk
            current_chunk = overlap.copy()
            current_len = len(current_chunk)

        current_chunk.extend(words_in_sentence)
        current_len += sentence_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def tokenize(text: str) -> Dict[str,int]:
    # reuse retrieval logic's tokenizer for consistent tokens
    return retrieval_logic.token_counts(text)

def ingest_document(text: str, metadata: dict = None) -> dict:
    chunks = chunk_text(text)
    store = VectorStore()
    inserted_count = 0

    for i, chunk in enumerate(chunks):
        tokens = tokenize(chunk)
        # Optionally, you can add per-chunk metadata
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update({"chunk_index": i})
        store.insert_chunks([chunk], [tokens], metadata=chunk_metadata)
        inserted_count += 1

    return {
        "inserted_chunks": inserted_count,
        "status": "ok"
    }
