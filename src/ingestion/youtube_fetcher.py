import re
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Could not extract video ID from: {url}")
    return match.group(1)


def fetch_transcript(video_id: str) -> List[dict]:
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)
    return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
