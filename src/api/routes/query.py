import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.generation.ollama_client import chat
from src.generation.prompt_builder import build_prompt
from src.ingestion.embedder import embed_texts
from src.retrieval.retriever import Retriever
from src.retrieval.vector_store import VectorStore

logger = logging.getLogger("rag.query")

router = APIRouter()
store = VectorStore(persist_dir=settings.chroma_persist_dir)
retriever = Retriever(store)

PERF_FILE = Path("data/performance.json")
PERF_FILE.parent.mkdir(parents=True, exist_ok=True)

_BROAD_KEYWORDS = {"summary", "summarize", "overview", "topics", "timestamps", "timeframes", "when", "all"}


def _is_broad_query(q: str) -> bool:
    return bool(_BROAD_KEYWORDS & set(q.lower().split()))


def _load_perf() -> list:
    if PERF_FILE.exists():
        return json.loads(PERF_FILE.read_text())
    return []


def _save_perf(records: list) -> None:
    PERF_FILE.write_text(json.dumps(records, indent=2))


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    model: Optional[str] = None
    video_id: Optional[str] = None


@router.post("/query")
def query_videos(req: QueryRequest):
    try:
        model = req.model or settings.model
        top_k = req.top_k or (10 if _is_broad_query(req.query) else settings.top_k)
        logger.info(f"Query: '{req.query}' | model={model} | top_k={top_k}")

        logger.info("Embedding query...")
        query_embedding = embed_texts([req.query], model=settings.embed_model, host=settings.ollama_host)[0]

        logger.info("Retrieving relevant chunks...")
        video_ids = [req.video_id] if req.video_id else None
        chunks = retriever.retrieve(query_embedding, top_k=top_k, video_ids=video_ids)
        logger.info(f"Retrieved {len(chunks)} chunks — scores: {[c['score'] for c in chunks]}")

        if not chunks:
            return {"answer": "No relevant content found.", "sources": [], "meta": {"model": model, "chunks": 0}}

        logger.info(f"Sending to LLM '{model}'...")
        messages = build_prompt(req.query, chunks)

        t0 = time.time()
        answer = chat(messages, model=model, host=settings.ollama_host, temperature=settings.temperature)
        elapsed = round(time.time() - t0, 2)

        logger.info(f"LLM answered ({len(answer)} chars) in {elapsed}s")

        records = _load_perf()
        records.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "query": req.query,
            "response_time_s": elapsed,
            "answer_chars": len(answer),
            "chunks_retrieved": len(chunks),
            "top_score": chunks[0]["score"] if chunks else None,
        })
        _save_perf(records)

        return {
            "answer": answer,
            "meta": {"model": model, "response_time_s": elapsed, "chunks": len(chunks)},
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
        logger.error("Query failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos")
def list_videos():
    return VectorStore(persist_dir=settings.chroma_persist_dir).get_indexed_videos()


@router.get("/stats")
def stats():
    s = VectorStore(persist_dir=settings.chroma_persist_dir)
    videos = s.get_indexed_videos()
    all_items = s.collection.get(include=["metadatas"])
    total_chunks = len(all_items["ids"])
    per_video = {}
    for m in all_items["metadatas"]:
        vid = m["video_id"]
        if vid not in per_video:
            per_video[vid] = {"video_id": vid, "video_url": m.get("video_url", ""), "chunks": 0}
        per_video[vid]["chunks"] += 1
    return {"total_videos": len(videos), "total_chunks": total_chunks, "videos": list(per_video.values())}


@router.get("/models")
def list_models():
    try:
        resp = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"models": models, "current": settings.model}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")


@router.get("/performance")
def performance():
    records = _load_perf()
    if not records:
        return {"records": [], "summary": []}

    summary: dict = {}
    for r in records:
        m = r["model"]
        if m not in summary:
            summary[m] = {"model": m, "queries": 0, "total_time_s": 0, "avg_time_s": 0, "avg_chars": 0, "total_chars": 0}
        summary[m]["queries"] += 1
        summary[m]["total_time_s"] += r["response_time_s"]
        summary[m]["total_chars"] += r["answer_chars"]

    for m in summary:
        summary[m]["avg_time_s"] = round(summary[m]["total_time_s"] / summary[m]["queries"], 2)
        summary[m]["avg_chars"] = round(summary[m]["total_chars"] / summary[m]["queries"])

    return {"records": records[-50:], "summary": list(summary.values())}


@router.get("/health")
def health():
    return {"status": "ok", "model": settings.model, "videos_indexed": len(store.get_indexed_videos())}
