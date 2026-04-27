from src.ingestion.chunker import Chunk, chunk_transcript
from src.ingestion.youtube_fetcher import extract_video_id


def test_extract_video_id_standard():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_shorts():
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid():
    import pytest
    with pytest.raises(ValueError):
        extract_video_id("https://example.com/not-a-video")


def test_chunk_transcript_basic():
    transcript = [{"text": "a" * 100, "start": float(i)} for i in range(10)]
    chunks = chunk_transcript(transcript, "vid1", "https://youtu.be/vid1", chunk_size=400, overlap=50)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.video_id == "vid1" for c in chunks)


def test_chunk_transcript_overlap():
    transcript = [{"text": "word " * 50, "start": 0.0}]
    chunks = chunk_transcript(transcript, "v", "url", chunk_size=100, overlap=20)
    assert len(chunks) >= 1
