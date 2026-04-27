from typing import List, Optional

import chromadb

from src.ingestion.chunker import Chunk


class VectorStore:
    def __init__(self, persist_dir: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="youtube_rag",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        self.collection.upsert(
            ids=[f"{c.video_id}_{c.chunk_index}" for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "video_id": c.video_id,
                    "video_url": c.video_url,
                    "start_time": c.start_time,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        video_ids: Optional[List[str]] = None,
    ) -> dict:
        where = {"video_id": {"$in": video_ids}} if video_ids else None
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def get_indexed_videos(self) -> List[dict]:
        try:
            all_items = self.collection.get(include=["metadatas"])
            seen: dict[str, str] = {}
            for m in all_items["metadatas"]:
                if m and m["video_id"] not in seen:
                    seen[m["video_id"]] = m.get("video_url", "")
            return [{"video_id": vid, "video_url": url} for vid, url in seen.items()]
        except Exception:
            return []

    def delete_video(self, video_id: str) -> None:
        results = self.collection.get(where={"video_id": video_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
