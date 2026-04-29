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


SYSTEM_PROMPT = """You are an expert assistant for YouTube videos.
You have access to transcript snippets with timestamps and source links.

Always answer in clear, structured language.
- If asked for times, return timestamps like [MM:SS].
- If asked for summaries, provide a short heading, bullets, and a conclusion.
- If you quote evidence, include a source label and timestamp.
- If you cannot answer from the transcript, say so clearly.
"""


def build_prompt(query: str, chunks: List[dict]) -> list:
    context = build_context(chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "The transcript context is below. Use only the provided text to answer. "
                "If the user asks for timestamps, provide them in [MM:SS] format.\n\n"
                f"Transcript context:\n\n{context}\n\nQuestion: {query}"
            ),
        },
    ]
