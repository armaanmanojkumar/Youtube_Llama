import json
import re
from typing import Dict, List, Optional

import httpx
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

PREFERRED_TRANSCRIPT_LANGUAGES = ("en", "en-US", "en-GB")


class TranscriptRateLimitError(RuntimeError):
    pass


def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Could not extract video ID from: {url}")
    return match.group(1)


def fetch_video_metadata(video_id: str) -> Dict[str, object]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"quiet": True, "skip_download": True, "nocheckcertificate": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    metadata = {
        "video_id": video_id,
        "title": info.get("title"),
        "description": info.get("description"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "uploader": info.get("uploader"),
        "view_count": info.get("view_count"),
        "upload_date": info.get("upload_date"),
    }
    return metadata


def fetch_transcript(video_id: str) -> List[dict]:
    last_error: Exception | None = None
    api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id, languages=PREFERRED_TRANSCRIPT_LANGUAGES)
        return _normalize_transcript(fetched)
    except Exception as exc:
        last_error = exc

    try:
        transcript_list = list(api.list(video_id))
        fallback = _select_fallback_transcript(transcript_list)
        if fallback is not None:
            return _normalize_transcript(fallback.fetch())
    except Exception as exc:
        last_error = exc

    try:
        transcript = fetch_transcript_with_yt_dlp(video_id)
        if not transcript:
            raise RuntimeError(f"No transcript tracks were available for video {video_id}.")
        return transcript
    except TranscriptRateLimitError:
        raise
    except Exception as exc:
        last_error = exc

    raise RuntimeError(f"Transcript could not be obtained for {video_id}. Last error: {last_error}")


def _normalize_transcript(fetched) -> List[dict]:
    return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]


def _select_fallback_transcript(transcripts):
    if not transcripts:
        return None

    for language in PREFERRED_TRANSCRIPT_LANGUAGES:
        for transcript in transcripts:
            if transcript.language_code == language:
                return transcript

    for transcript in transcripts:
        if not transcript.is_generated:
            return transcript

    return transcripts[0]


def fetch_transcript_with_yt_dlp(video_id: str) -> List[dict]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"quiet": True, "skip_download": True, "nocheckcertificate": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    captions = _merge_caption_maps(info.get("subtitles") or {}, info.get("automatic_captions") or {})
    if not captions:
        return []

    saw_rate_limit = False
    last_error: Exception | None = None
    for caption_url in _caption_urls_by_preference(captions):
        try:
            response = httpx.get(
                caption_url,
                timeout=30.0,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code == 429:
                saw_rate_limit = True
                continue
            continue
        except httpx.HTTPError as exc:
            last_error = exc
            continue

        transcript = _parse_caption_payload(response.text)
        if transcript:
            return transcript

    if saw_rate_limit:
        raise TranscriptRateLimitError(
            "YouTube is rate limiting transcript downloads from this network. "
            "Wait a few minutes, try another video, or use a different network/VPN."
        )
    if last_error:
        raise RuntimeError(f"Could not download transcript captions: {last_error}")
    return []


def _merge_caption_maps(*caption_maps: dict) -> dict:
    merged: dict = {}
    for caption_map in caption_maps:
        for language, tracks in caption_map.items():
            merged.setdefault(language, []).extend(tracks or [])
    return merged


def _caption_urls_by_preference(captions: dict) -> List[str]:
    languages = list(PREFERRED_TRANSCRIPT_LANGUAGES)
    languages.extend(language for language in captions if language not in languages)

    urls: List[str] = []
    seen = set()
    for language in languages:
        tracks = sorted(captions.get(language, []), key=_caption_track_priority)
        for track in tracks:
            url = track.get("url")
            if url and url not in seen:
                urls.append(url)
                seen.add(url)
    return urls


def _caption_track_priority(track: dict) -> int:
    ext = track.get("ext")
    if ext == "json3":
        return 0
    if ext == "vtt":
        return 1
    return 2


def _parse_caption_payload(payload: str) -> List[dict]:
    payload = payload.strip()
    if payload.startswith("{"):
        try:
            return _parse_json_captions(json.loads(payload))
        except Exception:
            pass
    return _parse_vtt(payload)


def _parse_json_captions(data: dict) -> List[dict]:
    events = data.get("events", [])
    transcript = []
    for event in events:
        segs = event.get("segs") or []
        text = "".join(seg.get("utf8", "") for seg in segs).strip()
        if not text:
            continue
        start = event.get("t", 0) / 1000.0
        duration = event.get("d", 0) / 1000.0
        transcript.append({"text": text, "start": start, "duration": duration})
    return transcript


def _parse_vtt(data: str) -> List[dict]:
    lines = [line.strip() for line in data.splitlines()]
    transcript = []
    current_start: Optional[float] = None
    current_text: List[str] = []

    for line in lines:
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if "-->" in line:
            if current_start is not None and current_text:
                transcript.append({"text": " ".join(current_text).strip(), "start": current_start, "duration": 0.0})
            current_start = _parse_timestamp(line.split("-->", 1)[0].strip())
            current_text = []
            continue
        if current_start is not None:
            current_text.append(line)

    if current_start is not None and current_text:
        transcript.append({"text": " ".join(current_text).strip(), "start": current_start, "duration": 0.0})
    return transcript


def _parse_timestamp(timestamp: str) -> float:
    parts = timestamp.split(":")
    if len(parts) == 3:
        hours, minutes, rest = parts
        seconds = float(rest.replace(",", "."))
        return int(hours) * 3600 + int(minutes) * 60 + seconds
    if len(parts) == 2:
        minutes, rest = parts
        seconds = float(rest.replace(",", "."))
        return int(minutes) * 60 + seconds
    return 0.0
