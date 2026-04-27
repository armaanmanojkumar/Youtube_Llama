from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.generation.ollama_client import chat
from src.generation.prompt_builder import build_prompt
from src.ingestion.embedder import embed_texts
from src.retrieval.retriever import Retriever
from src.retrieval.vector_store import VectorStore

router = APIRouter()
store = VectorStore(persist_dir=settings.chroma_persist_dir)
retriever = Retriever(store)


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


@router.post("/query")
def query_videos(req: QueryRequest):
    try:
        top_k = req.top_k or settings.top_k
        query_embedding = embed_texts([req.query], model=settings.embed_model, host=settings.ollama_host)[0]
        chunks = retriever.retrieve(query_embedding, top_k=top_k)
        if not chunks:
            return {"answer": "No relevant content found.", "sources": []}
        messages = build_prompt(req.query, chunks)
        answer = chat(messages, model=settings.model, host=settings.ollama_host, temperature=settings.temperature)
        return {
            "answer": answer,
            "sources": [
                {
                    "video_id": c["metadata"]["video_id"],
                    "video_url": c["metadata"]["video_url"],
                    "chunk": c["document"],
                    "score": c["score"],
                    "start_time": c["metadata"].get("start_time"),
                }
                for c in chunks
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos")
def list_videos():
    return VectorStore(persist_dir=settings.chroma_persist_dir).get_indexed_videos()
