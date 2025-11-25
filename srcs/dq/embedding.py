from sentence_transformers import SentenceTransformer

class Embedding:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    def embed_text(self, *texts):
        return self.model.encode(texts)
