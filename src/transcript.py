import re
from dataclasses import dataclass
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi


@dataclass
class Chunk:
    text: str
    video_id: str
    video_url: str
    start_time: float
    chunk_index: int


def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Could not extract video ID from: {url}")
    return match.group(1)


def fetch_transcript(video_id: str) -> List[dict]:
    return YouTubeTranscriptApi.get_transcript(video_id)


def chunk_transcript(
    transcript: List[dict],
    video_id: str,
    video_url: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> List[Chunk]:
    chunks: List[Chunk] = []
    buffer = ""
    buffer_start = 0.0
    chunk_index = 0

    for entry in transcript:
        if not buffer:
            buffer_start = entry["start"]
        buffer += entry["text"] + " "

        while len(buffer) >= chunk_size:
            chunk_text = buffer[:chunk_size].strip()
            chunks.append(
                Chunk(
                    text=chunk_text,
                    video_id=video_id,
                    video_url=video_url,
                    start_time=buffer_start,
                    chunk_index=chunk_index,
                )
            )
            buffer = buffer[chunk_size - overlap :]
            buffer_start = entry["start"]
            chunk_index += 1

    if buffer.strip():
        chunks.append(
            Chunk(
                text=buffer.strip(),
                video_id=video_id,
                video_url=video_url,
                start_time=buffer_start,
                chunk_index=chunk_index,
            )
        )

    return chunks
