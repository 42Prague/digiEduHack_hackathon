from srcs.dq.prompt import map_feature

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# import numpy as np
# from embedding import Embedding
import uuid


class Storage:
    def __init__(self, name, embedding_size):
        self.client = QdrantClient(host="qdrant", port=6333, timeout=60.0)
        self.collection_name = name

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_size, distance=Distance.COSINE
                ),
            )

    def load_vectors_in_batches(self, vectors, texts, batch_size=100):
        for i in range(0, len(vectors), batch_size):
            data = texts[i : i + batch_size]
            embedded_data = vectors[i : i + batch_size]

            self.load_vectors(embedded_data, data)

    def load_vectors(self, vectors, texts):
        namespace = uuid.NAMESPACE_DNS

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=str(uuid.uuid5(namespace, texts[idx])),
                    vector=vector.tolist(),
                    payload={"col": texts[idx]},
                )
                for idx, vector in enumerate(vectors)
            ],
            wait=True,
        )

    def smart_load(self, vector, text, feature_values, threshold=0.8):
        hits = self.client.search(
            collection_name=self.collection_name, query_vector=vector.tolist(), limit=1
        )

        if hits and hits[0].score > threshold:
            existing_name = hits[0].payload.get("col", "Unknown")
            return False, existing_name
        else:
            llm_res = map_feature(text, feature_values, self.list_data())
            if llm_res == "NAN":
                self.load_vectors_in_batches([vector], [text])
                return True, text

            return False, llm_res

    def search_similarities(self, query_vector, limit):
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit,
        )
        return hits

    def my_size(self):
        return self.client.count(collection_name=self.collection_name, exact=True)

    def my_info(
        self,
    ):
        return self.client.get_collection(collection_name=self.collection_name)

    def get_all_vectors(self, page_size=100):
        all_points = []
        offset = None

        while True:
            points, next_page_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=page_size,
                with_payload=True,
                with_vectors=True,
                offset=offset,
            )

            all_points.extend(points)

            if next_page_offset is None:
                break

            offset = next_page_offset

        return all_points

    def list_data(self):
        ret = []
        all_stored_data = self.get_all_vectors()

        for point in all_stored_data:
            ret.append(point.payload.get("col"))

        return ret
