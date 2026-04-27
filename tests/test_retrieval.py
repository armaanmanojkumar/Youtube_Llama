import tempfile

from src.ingestion.chunker import Chunk
from src.retrieval.retriever import Retriever
from src.retrieval.vector_store import VectorStore

DIM = 768


def _make_chunks(n: int = 3) -> list[Chunk]:
    return [
        Chunk(text=f"chunk {i}", video_id="vid1", video_url="https://youtu.be/vid1", start_time=float(i), chunk_index=i)
        for i in range(n)
    ]


def test_add_and_query():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir)
        chunks = _make_chunks(3)
        embeddings = [[0.1] * DIM for _ in chunks]
        store.add_chunks(chunks, embeddings)
        results = store.query([0.1] * DIM, top_k=2)
        assert len(results["documents"][0]) == 2


def test_get_indexed_videos():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir)
        store.add_chunks(_make_chunks(2), [[0.1] * DIM, [0.2] * DIM])
        videos = store.get_indexed_videos()
        assert len(videos) == 1
        assert videos[0]["video_id"] == "vid1"


def test_delete_video():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir)
        store.add_chunks(_make_chunks(2), [[0.1] * DIM, [0.2] * DIM])
        store.delete_video("vid1")
        assert store.get_indexed_videos() == []


def test_retriever_scores():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir)
        store.add_chunks(_make_chunks(3), [[0.1] * DIM for _ in range(3)])
        retriever = Retriever(store)
        results = retriever.retrieve([0.1] * DIM, top_k=2)
        assert len(results) == 2
        assert all(0 <= r["score"] <= 1 for r in results)
