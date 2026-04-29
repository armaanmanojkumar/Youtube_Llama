from typing import List, Optional

from .vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore):
        self.store = store

    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        video_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        results = self.store.query(query_embedding, top_k=top_k, video_ids=video_ids)
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append(
                {
                    "document": doc,
                    "metadata": meta,
                    "score": round(1 - dist, 4),
                }
            )
        return chunks
