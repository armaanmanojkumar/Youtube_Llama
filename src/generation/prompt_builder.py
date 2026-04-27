from typing import List


def _format_timestamp(seconds: float) -> str:
    s = int(seconds)
    mins, secs = divmod(s, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def build_context(chunks: List[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        url = meta.get("video_url", "")
        start = meta.get("start_time", 0)
        ts = _format_timestamp(start)
        timestamp_url = f"{url}&t={int(start)}" if "youtube" in url else url
        parts.append(f"[Source {i} | {ts}] {timestamp_url}\n{chunk['document']}")
    return "\n\n---\n\n".join(parts)


SYSTEM_PROMPT = """\
You are an AI assistant that answers questions about YouTube video transcripts.

Each source chunk includes a timestamp in [MM:SS] format showing when it appears in the video.

Guidelines:
- Timeframe questions ("when does X happen", "at what time", "what timestamps"): list every relevant timestamp in [MM:SS] format, cite the source, and link to it.
- Summary requests: give a structured summary with the main topics and key points in order.
- Topic / explanation questions: explain clearly using transcript evidence, cite [Source N] with its timestamp.
- Always format timestamps as [MM:SS] inline in your answer, e.g. "At 4:32, the speaker explains..."
- If the context lacks enough information, say so — do not invent content.
"""


def build_prompt(query: str, chunks: List[dict]) -> list:
    context = build_context(chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript context:\n\n{context}\n\nQuestion: {query}"},
    ]
