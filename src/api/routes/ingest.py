from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.ingestion.chunker import chunk_transcript
from src.ingestion.embedder import embed_texts
from src.ingestion.youtube_fetcher import extract_video_id, fetch_transcript
from src.retrieval.vector_store import VectorStore

router = APIRouter()
store = VectorStore(persist_dir=settings.chroma_persist_dir)


class IngestRequest(BaseModel):
    url: str


@router.post("/ingest")
def ingest_video(req: IngestRequest):
    try:
        video_id = extract_video_id(req.url)
        transcript = fetch_transcript(video_id)
        chunks = chunk_transcript(
            transcript,
            video_id,
            req.url,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        embeddings = embed_texts(
            [c.text for c in chunks],
            model=settings.embed_model,
            host=settings.ollama_host,
        )
        store.add_chunks(chunks, embeddings)
        return {"video_id": video_id, "chunks_indexed": len(chunks), "status": "indexed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/video/{video_id}")
def delete_video(video_id: str):
    store.delete_video(video_id)
    return {"status": "deleted", "video_id": video_id}
