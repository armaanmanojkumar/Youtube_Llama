import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.ingestion.chunker import chunk_transcript
from src.ingestion.embedder import embed_texts
from src.ingestion.youtube_fetcher import extract_video_id, fetch_transcript
from src.retrieval.vector_store import VectorStore

logger = logging.getLogger("rag.ingest")

router = APIRouter()
store = VectorStore(persist_dir=settings.vector_store_dir)


class IngestRequest(BaseModel):
    url: str


@router.post("/ingest")
def ingest_video(req: IngestRequest):
    try:
        logger.info(f"Received URL: {req.url}")

        video_id = extract_video_id(req.url)
        logger.info(f"Video ID: {video_id}")

        logger.info("Fetching transcript from YouTube...")
        transcript = fetch_transcript(video_id)
        logger.info(f"Transcript fetched: {len(transcript)} entries")

        logger.info("Chunking transcript...")
        chunks = chunk_transcript(
            transcript, video_id, req.url,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        logger.info(f"Created {len(chunks)} chunks")

        logger.info(f"Embedding {len(chunks)} chunks with {settings.embed_model}...")
        embeddings = embed_texts(
            [c.text for c in chunks],
            model=settings.embed_model,
            host=settings.ollama_host,
        )
        logger.info("Embeddings done")

        logger.info("Storing vectors...")
        store.add_chunks(chunks, embeddings)
        logger.info(f"Done! {len(chunks)} chunks indexed for {video_id}")

        return {"video_id": video_id, "chunks_indexed": len(chunks), "status": "indexed"}
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/video/{video_id}")
def delete_video(video_id: str):
    logger.info(f"Deleting video {video_id}")
    store.delete_video(video_id)
    return {"status": "deleted", "video_id": video_id}
