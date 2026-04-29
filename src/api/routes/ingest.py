import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.ingestion.chunker import chunk_transcript
from src.ingestion.embedder import embed_texts
from src.ingestion.transcript_cache import TranscriptCache
from src.ingestion.youtube_fetcher import (
    extract_video_id,
    fetch_transcript,
    fetch_video_metadata,
)
from src.retrieval.vector_store import VectorStore

logger = logging.getLogger("rag.ingest")
router = APIRouter()
store = VectorStore(persist_dir=settings.chroma_persist_dir)
cache = TranscriptCache(settings.transcript_cache_dir)


class IngestRequest(BaseModel):
    url: str


@router.post("/ingest")
def ingest_video(req: IngestRequest):
    try:
        logger.info(f"Received URL: {req.url}")
        video_id = extract_video_id(req.url)
        logger.info(f"Video ID: {video_id}")

        cache_entry = cache.load(video_id)
        if cache_entry:
            transcript = cache_entry["transcript"]
            metadata = cache_entry["metadata"]
            logger.info("Loaded transcript from cache")
        else:
            metadata = fetch_video_metadata(video_id)
            transcript = fetch_transcript(video_id)
            cache.save(video_id, transcript, metadata)
            logger.info("Fetched and cached fresh transcript")

        if not transcript:
            raise ValueError("Transcript could not be obtained for this video.")

        logger.info("Chunking transcript...")
        chunks = chunk_transcript(
            transcript,
            video_id,
            req.url,
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
        logger.info("Embeddings complete")

        logger.info("Storing vectors in ChromaDB...")
        store.add_chunks(chunks, embeddings)
        logger.info(f"Indexed {len(chunks)} chunks for {video_id}")

        return {
            "video_id": video_id,
            "title": metadata.get("title"),
            "uploader": metadata.get("uploader"),
            "duration": metadata.get("duration"),
            "chunks_indexed": len(chunks),
            "status": "indexed",
        }
    except Exception as e:
        logger.error("Ingest failed", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/video/{video_id}")
def delete_video(video_id: str):
    logger.info(f"Deleting video %s", video_id)
    store.delete_video(video_id)
    return {"status": "deleted", "video_id": video_id}
