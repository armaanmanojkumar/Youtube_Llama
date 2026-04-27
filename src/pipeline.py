from typing import List, Optional

from .config import Settings
from .embeddings import embed_texts
from .transcript import chunk_transcript, extract_video_id, fetch_transcript
from .vector_store import VectorStore


class RAGPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = VectorStore(persist_dir=settings.chroma_persist_dir)

    def index_video(self, url: str) -> dict:
        video_id = extract_video_id(url)
        transcript = fetch_transcript(video_id)
        chunks = chunk_transcript(
            transcript,
            video_id,
            url,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts, self.settings.embedding_model)
        self.store.add_chunks(chunks, embeddings)
        return {"video_id": video_id, "chunks": len(chunks)}

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        video_ids: Optional[List[str]] = None,
    ) -> dict:
        k = top_k or self.settings.top_k
        query_embedding = embed_texts([query], self.settings.embedding_model)[0]
        return self.store.query(query_embedding, top_k=k, video_ids=video_ids)

    def get_indexed_videos(self) -> List[dict]:
        return self.store.get_indexed_videos()

    def delete_video(self, video_id: str) -> None:
        self.store.delete_video(video_id)
